#!/usr/bin/env python3
"""
Test resume functionality for streaming observations.
"""

from observations.interface import MinimalObservationInterface
from core.context import RuntimeContext
from pathlib import Path
import time
import uuid

def test_resume_functionality():
    print("=" * 60)
    print("RESUME FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Create runtime context
    context = RuntimeContext(
        investigation_root=Path('test_agent_nexus').resolve(),
        constitution_hash='0000000000000000000000000000000000000000000000000000000000000000000',
        code_version_hash='0000000000000000000000000000000000000000000000000000000000000000000',
        execution_mode='API',
        session_id=uuid.uuid4()
    )
    
    # Test session ID
    session_id = 'test_resume_001'
    
    interface = MinimalObservationInterface()
    
    # Set observation types
    from core.engine import CoordinationRequest, HighLevelIntent
    mock_request = CoordinationRequest.create(
        intent=HighLevelIntent.OBSERVE,
        target_path=Path('test_agent_nexus'),
        parameters={
            'observation_types': ['file_sight', 'import_sight', 'boundary_sight'],
            'constitutional': True
        },
        requestor='test'
    )
    interface._last_request = mock_request
    
    print("Phase 1: Starting observation (will interrupt after 1000 files)...")
    
    # Start observation
    start_time = time.time()
    
    # Create a custom streaming observation to test interrupt
    from core.storage_integration import InvestigationStorage
    storage = InvestigationStorage()
    
    with storage.create_streaming_observation(session_id) as stream:
        all_files = sorted(Path('test_agent_nexus').rglob("*.py"))
        
        print(f"Processing {len(all_files)} files...")
        
        for idx, file_path in enumerate(all_files):
            # Simulate observation
            file_observations = [{
                "type": "file_sight",
                "result": {"file": str(file_path), "size": file_path.stat().st_size if file_path.exists() else 0}
            }]
            
            stream.write_file_observation(str(file_path), file_observations)
            
            # Show progress
            if (idx + 1) % 100 == 0:
                progress = stream.get_progress()
                print(f"Progress: {idx + 1}/{len(all_files)} files, {progress['observations_written']} observations")
            
            # Interrupt after 1000 files
            if idx >= 1000:
                print(f"\n*** INTERRUPTING at file {idx + 1} ***")
                break
    
    print(f"\nPhase 1 completed: {stream.get_progress()['files_processed']} files processed")
    
    # Wait a moment
    time.sleep(2)
    
    print("\nPhase 2: Resuming from interruption...")
    
    # Create new interface for resume
    resume_interface = MinimalObservationInterface()
    resume_interface._last_request = mock_request
    
    # Test resume
    with storage.create_streaming_observation(session_id) as resume_stream:
        if resume_stream.can_resume_from(session_id):
            resume_info = resume_stream.resume_from(session_id)
            print(f"Resume successful: {resume_info}")
            
            # Continue processing remaining files
            all_files = sorted(Path('test_agent_nexus').rglob("*.py"))
            start_index = resume_stream.files_processed
            
            print(f"Continuing from file {start_index + 1}...")
            
            for idx in range(start_index, len(all_files)):
                file_path = all_files[idx]
                file_observations = [{
                    "type": "file_sight", 
                    "result": {"file": str(file_path), "size": file_path.stat().st_size if file_path.exists() else 0}
                }]
                
                resume_stream.write_file_observation(str(file_path), file_observations)
                
                if (idx + 1) % 100 == 0:
                    progress = resume_stream.get_progress()
                    print(f"Resume progress: {idx + 1}/{len(all_files)} files, {progress['observations_written']} observations")
        else:
            print("No resumable session found")
    
    final_progress = resume_stream.get_progress()
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("RESUME TEST COMPLETE")
    print("=" * 60)
    print(f"Total files processed: {final_progress['files_processed']}")
    print(f"Total observations: {final_progress['observations_written']}")
    print(f"Manifest ID: {resume_stream.manifest_id}")
    print(f"Total time: {elapsed_time:.2f}s")
    print(f"Files/second: {final_progress['files_processed'] / elapsed_time:.1f}")
    print("=" * 60)

if __name__ == '__main__':
    test_resume_functionality()
