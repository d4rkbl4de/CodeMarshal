#!/usr/bin/env python3
"""
Test resume functionality with actual interruption.
"""

from observations.interface import MinimalObservationInterface
from core.context import RuntimeContext
from pathlib import Path
import time
import uuid
import signal
import sys

def test_resume_with_interrupt():
    print("=" * 60)
    print("RESUME WITH INTERRUPT TEST")
    print("=" * 60)
    
    # Create runtime context
    context = RuntimeContext(
        investigation_root=Path('test_agent_nexus').resolve(),
        constitution_hash='0000000000000000000000000000000000000000000000000000000000000000000000',
        code_version_hash='0000000000000000000000000000000000000000000000000000000000000000000000',
        execution_mode='API',
        session_id=uuid.uuid4()
    )
    
    # Test session ID
    session_id = 'test_interrupt_001'
    
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
    
    print("Phase 1: Starting observation (will interrupt after 500 files)...")
    
    # Override write_file_observation to interrupt after 500 files
    from core.storage_integration import InvestigationStorage
    
    # Get the class
    from core.storage_integration import StreamingObservation
    original_write = StreamingObservation.write_file_observation
    
    def interrupting_write(self, file_path, observations):
        result = original_write(self, file_path, observations)
        if self.files_processed >= 500:
            print(f"\n*** INTERRUPTING at file {self.files_processed} ***")
            # Force exit without completing the context manager
            raise KeyboardInterrupt("Simulated interruption")
        return result
    
    StreamingObservation.write_file_observation = interrupting_write
    
    try:
        # Start observation
        start_time = time.time()
        result = interface.observe_directory(
            Path('test_agent_nexus'),
            streaming=True,
            session_id=session_id
        )
        print("ERROR: Should have been interrupted!")
    except KeyboardInterrupt:
        print(f"\nPhase 1 interrupted after ~500 files")
        elapsed_time = time.time() - start_time
        print(f"Time elapsed: {elapsed_time:.2f}s")
    
    # Restore original method
    StreamingObservation.write_file_observation = original_write
    
    # Wait a moment
    time.sleep(2)
    
    print("\nPhase 2: Resuming from interruption...")
    
    # Create new interface for resume
    resume_interface = MinimalObservationInterface()
    resume_interface._last_request = mock_request
    
    # Test resume
    try:
        with InvestigationStorage().create_streaming_observation(session_id) as resume_stream:
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
    except Exception as e:
        print(f"Resume failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("RESUME INTERRUPT TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_resume_with_interrupt()
