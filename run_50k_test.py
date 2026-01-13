#!/usr/bin/env python3
"""
Run 50K production test using Python API with streaming.
"""

from observations.interface import MinimalObservationInterface
from core.context import RuntimeContext
from core.engine import CoordinationRequest, HighLevelIntent
from integrity.monitoring.memory import setup_memory_monitoring
from pathlib import Path
import uuid
import time

def run_50k_test():
    print("=" * 70)
    print("AGENT NEXUS 50K PRODUCTION TEST")
    print("=" * 70)
    
    # Setup context
    context = RuntimeContext(
        investigation_root=Path('test_agent_nexus').resolve(),
        constitution_hash='0000000000000000000000000000000000000000000000000000000000000000000',
        code_version_hash='0000000000000000000000000000000000000000000000000000000000000000000',
        execution_mode='CLI',
        session_id=uuid.uuid4()
    )
    
    # Setup memory monitoring
    memory_monitor = setup_memory_monitoring(
        context,
        warning_threshold_mb=2048,
        critical_threshold_mb=4096
    )
    
    # Create interface
    interface = MinimalObservationInterface()
    
    # Setup observation request for constitutional analysis
    request = CoordinationRequest.create(
        intent=HighLevelIntent.OBSERVE,
        target_path=Path('test_agent_nexus'),
        parameters={
            'observation_types': ['file_sight', 'import_sight', 'boundary_sight'],
            'constitutional': True,
            'streaming': True  # Enable streaming mode
        },
        requestor='50k_production_test'
    )
    
    interface._last_request = request
    
    print(f"Target: {context.investigation_root}")
    print(f"Session ID: {context.session_id}")
    print(f"Memory monitoring: Active (warning at 2GB, critical at 4GB)")
    print("-" * 70)
    
    # Start timing
    start_time = time.time()
    
    try:
        # Run observation with streaming
        result = interface.observe_directory(
            Path('test_agent_nexus'),
            streaming=True,  # Force streaming mode
            session_id=str(context.session_id)
        )
        
        # Calculate metrics
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("50K PRODUCTION TEST COMPLETED")
        print("=" * 70)
        print(f"Total time: {elapsed_time:.2f} seconds ({elapsed_time/3600:.2f} hours)")
        print(f"Files processed: {result.get('files_processed', 'N/A')}")
        print(f"Observations: {result.get('observations_written', 'N/A')}")
        print(f"Manifest ID: {result.get('manifest_id', 'N/A')}")
        print(f"Memory monitoring: Active (check emergency_monitor.py logs for warnings)")
        
        # Performance metrics
        if result.get('files_processed', 0) > 0:
            files_per_sec = result['files_processed'] / elapsed_time
            print(f"Processing speed: {files_per_sec:.1f} files/second")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = run_50k_test()
    if result:
        print("\n🎉 50K PRODUCTION TEST SUCCESSFUL!")
    else:
        print("\n⚠️ 50K PRODUCTION TEST FAILED!")
