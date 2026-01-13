#!/usr/bin/env python3
"""
Production deployment configuration for Agent Nexus 50K analysis.
Optimized based on 5K test results.
"""

from observations.interface import MinimalObservationInterface
from core.context import RuntimeContext
from integrity.monitoring.memory import setup_memory_monitoring
from pathlib import Path
import uuid
import time
import gc

# Production configuration optimized for 50K files
PRODUCTION_CONFIG = {
    # Checkpoint every 2000 files (vs 500 in test)
    'checkpoint_interval': 2000,
    
    # Progress reporting every 1000 files (vs 100 in test)
    'progress_interval': 1000,
    
    # Memory thresholds
    'memory_warning_mb': 3000,
    'memory_critical_mb': 4000,
    
    # Expected metrics based on 5K test scaling
    'expected_files': 5004,  # Current test data
    'expected_time_minutes': 57,  # Scaled from 5.67 minutes
    'expected_memory_gb': 2.0,   # Scaled from <1GB
    'expected_storage_mb': 320,   # Scaled from ~32MB
}

def setup_production_environment():
    """Setup optimized production environment."""
    
    # Optimize Python garbage collection for long-running process
    gc.set_threshold(700, 10, 10)
    
    print("=" * 70)
    print("AGENT NEXUS 50K PRODUCTION DEPLOYMENT")
    print("=" * 70)
    print(f"📊 Configuration:")
    print(f"   Checkpoint interval: {PRODUCTION_CONFIG['checkpoint_interval']} files")
    print(f"   Progress reporting: {PRODUCTION_CONFIG['progress_interval']} files")
    print(f"   Memory warning: {PRODUCTION_CONFIG['memory_warning_mb']}MB")
    print(f"   Memory critical: {PRODUCTION_CONFIG['memory_critical_mb']}MB")
    print("-" * 70)
    
    return PRODUCTION_CONFIG

def run_production_analysis(target_path="test_agent_nexus"):
    """Run optimized production analysis."""
    
    config = setup_production_environment()
    
    # Setup context with production optimizations
    context = RuntimeContext(
        investigation_root=Path(target_path).resolve(),
        constitution_hash='0000000000000000000000000000000000000000000000000000000000000000000',
        code_version_hash='0000000000000000000000000000000000000000000000000000000000000000000',
        execution_mode='CLI',
        session_id=uuid.uuid4()
    )
    
    # Setup memory monitoring with production thresholds
    memory_monitor = setup_memory_monitoring(
        context,
        warning_threshold_mb=config['memory_warning_mb'],
        critical_threshold_mb=config['memory_critical_mb']
    )
    
    # Create interface
    interface = MinimalObservationInterface()
    
    # Setup observation request for constitutional analysis
    request = {
        'intent': 'OBSERVE',
        'target_path': Path(target_path),
        'parameters': {
            'observation_types': ['file_sight', 'import_sight', 'boundary_sight'],
            'constitutional': True,
            'streaming': True,
            'checkpoint_interval': config['checkpoint_interval'],
            'progress_interval': config['progress_interval']
        },
        'requestor': 'agent_nexus_production'
    }
    
    interface._last_request = request
    
    print(f"🎯 Target: {context.investigation_root}")
    print(f"🆔 Session ID: {context.session_id}")
    print(f"⚡ Memory monitoring: Active (warning at {config['memory_warning_mb']}MB)")
    print("-" * 70)
    
    # Start timing
    start_time = time.time()
    
    try:
        # Run observation with production optimizations
        result = interface.observe_directory(
            Path(target_path),
            streaming=True,
            session_id=str(context.session_id)
        )
        
        # Calculate metrics
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("🎉 PRODUCTION ANALYSIS COMPLETED")
        print("=" * 70)
        print(f"⏱️  Total time: {elapsed_time:.2f} seconds ({elapsed_time/3600:.2f} hours)")
        print(f"📁 Files processed: {result.get('files_processed', 'N/A')}")
        print(f"📝 Observations: {result.get('observations_written', 'N/A')}")
        print(f"📋 Manifest ID: {result.get('manifest_id', 'N/A')}")
        
        # Performance metrics
        if result.get('files_processed', 0) > 0:
            files_per_sec = result['files_processed'] / elapsed_time
            print(f"⚡ Processing speed: {files_per_sec:.1f} files/second")
            
            # Compare with expectations
            expected_files = config['expected_files']
            actual_files = result['files_processed']
            completion_rate = (actual_files / expected_files) * 100
            
            print(f"📊 Completion rate: {completion_rate:.1f}%")
            
            if completion_rate >= 100:
                print("✅ FULL SUCCESS - All files processed!")
            elif completion_rate >= 95:
                print("⚠️  NEAR SUCCESS - Most files processed")
            else:
                print("❌ INCOMPLETE - Significant issues detected")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Production analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = run_production_analysis()
    if result:
        print("\n🚀 Agent Nexus production deployment successful!")
    else:
        print("\n⚠️  Production deployment failed - check logs")
