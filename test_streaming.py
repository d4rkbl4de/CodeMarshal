"""
Test streaming observation implementation.
"""
from observations.interface import MinimalObservationInterface
from core.context import RuntimeContext
from integrity.monitoring.memory import setup_memory_monitoring
from pathlib import Path
import time
import uuid

def test_streaming():
    print("=" * 60)
    print("STREAMING OBSERVATION TEST")
    print("=" * 60)
    
    # Create runtime context for memory monitoring
    context = RuntimeContext(
        investigation_root=Path('test_agent_nexus').resolve(),
        constitution_hash='0000000000000000000000000000000000000000000000000000000000000000',
        code_version_hash='0000000000000000000000000000000000000000000000000000000000000000',
        execution_mode='API',  # Valid modes: CLI, TUI, API
        session_id=uuid.uuid4()
    )
    
    # Setup memory monitoring
    memory_monitor = setup_memory_monitoring(
        context,
        warning_threshold_mb=2048,
        critical_threshold_mb=4096
    )
    
    # Test streaming mode
    start = time.time()
    interface = MinimalObservationInterface()
    
    # Set observation types for constitutional analysis
    # Workaround: Create a mock request object to provide parameters
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
    
    print("Starting streaming observation on test_agent_nexus/...\n")
    result = interface.observe_directory(
        Path('test_agent_nexus'),
        streaming=True,
        session_id='test_stream_001'
    )
    
    elapsed = time.time() - start
    
    # Print results
    print("\n" + "=" * 60)
    print("STREAMING TEST COMPLETE")
    print("=" * 60)
    print(f"Files processed: {result.get('file_count', 0)}")
    print(f"Observations written: {result.get('observations_written', 0)}")
    print(f"Boundary crossings: {len(result.get('boundary_crossings', []))}")
    print(f"Streaming mode: {result.get('streaming', False)}")
    print(f"Manifest ID: {result.get('manifest_id', 'N/A')}")
    print(f"\nMemory (from monitor):")
    print(f"  RSS: {result.get('memory_usage', {}).get('current_rss_mb', 0):.1f}MB")
    print(f"  Chunking enabled: {result.get('memory_usage', {}).get('chunking_enabled', False)}")
    print(f"\nElapsed time: {elapsed:.2f}s")
    if result.get('file_count', 0) > 0:
        print(f"Files/second: {result.get('file_count', 0) / elapsed:.1f}")
    
    # Print boundary crossings if any
    if result.get('boundary_crossings'):
        print(f"\nBoundary violations found:")
        for cross in result.get('boundary_crossings', [])[:5]:  # Show first 5
            print(f"  {cross.get('source')} -> {cross.get('target')}")
        if len(result.get('boundary_crossings', [])) > 5:
            print(f"  ... and {len(result.get('boundary_crossings', [])) - 5} more")
    
    print("=" * 60)

if __name__ == '__main__':
    test_streaming()
