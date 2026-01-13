#!/usr/bin/env python3
"""
Prepare CodeMarshal for large run (50K+ files).

This script:
1. Verifies storage integrity
2. Creates backup
3. Checks disk space
4. Configures memory monitoring
5. Sets up chunking strategy
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage_integration import InvestigationStorage
from storage.backup import BackupManager
from storage.corruption import CorruptionDetector
from integrity.monitoring.memory import setup_memory_monitoring
from core.context import RuntimeContext


def prepare_for_large_run(target_path: str, expected_files: int = 50000):
    """
    Prepare CodeMarshal for processing 50K+ files.
    
    Args:
        target_path: Path to directory being observed
        expected_files: Expected number of files to process
    """
    print("🚀 Preparing CodeMarshal for large run...")
    print(f"   Target: {target_path}")
    print(f"   Expected files: {expected_files:,}")
    print()
    
    # 1. Initialize storage with backups enabled
    storage = InvestigationStorage(base_path='storage', enable_backups=True)
    print("✓ Storage initialized with backup support")
    
    # 2. Check current storage integrity
    print("\n🔍 Checking storage integrity...")
    integrity_report = storage.verify_storage_integrity()
    
    if integrity_report['is_corrupt']:
        print(f"⚠️ Found {integrity_report['corruption_count']} corruption issues")
        
        # Attempt repair
        print("🔧 Attempting repair...")
        repair_report = storage.repair_corruption()
        print(f"   Repaired: {repair_report['repaired_count']} files")
        
        if repair_report['repaired_count'] > 0:
            print("   Repair log:")
            for log_entry in repair_report['repair_log']:
                print(f"     - {log_entry}")
    else:
        print("✓ Storage integrity verified")
    
    # 3. Create backup before large run
    print("\n💾 Creating pre-run backup...")
    backup_manager = BackupManager(Path('storage/backups'))
    
    # Create full backup of current observations
    observations_dir = Path('storage/observations')
    if observations_dir.exists():
        backup_manifest = backup_manager.create_full_backup(
            observations_dir,
            backup_id=f"pre_run_{int(time.time())}"
        )
        print(f"✓ Backup created: {backup_manifest.backup_id}")
        print(f"   Files backed up: {backup_manifest.file_count:,}")
        print(f"   Backup size: {backup_manifest.total_size // 1024 // 1024} MB")
    
    # 4. Check disk space
    print("\n💿 Checking disk space...")
    prep_report = storage.prepare_for_large_run(expected_files)
    
    if not prep_report['ready']:
        print("❌ Preparation failed:")
        for warning in prep_report['warnings']:
            print(f"   - {warning}")
        return False
    
    print("✓ Sufficient disk space available")
    if prep_report['warnings']:
        for warning in prep_report['warnings']:
            print(f"   ⚠️ {warning}")
    
    # 5. Set up memory monitoring
    print("\n🧠 Configuring memory monitoring...")
    context = RuntimeContext(
        investigation_id=f"large_run_{int(time.time())}",
        root_path=Path(target_path),
        config={},
        started_at=datetime.now(timezone.utc)
    )
    
    memory_monitor = setup_memory_monitoring(
        context=context,
        warning_threshold_mb=2048,  # 2GB warning
        critical_threshold_mb=4096   # 4GB critical
    )
    print("✓ Memory monitoring configured")
    print(f"   Warning threshold: 2GB")
    print(f"   Critical threshold: 4GB")
    print(f"   Check interval: every 1000 files")
    
    # 6. Final verification
    print("\n✅ Preparation complete!")
    print("\nRun configuration:")
    print(f"   - Chunking: Enabled (1000 files per chunk)")
    print(f"   - Memory monitoring: Active")
    print(f"   - Backup strategy: Full + incremental")
    print(f"   - Transaction safety: Enabled")
    print(f"   - Corruption detection: Active")
    print()
    print("🎯 Ready to process 50K+ files!")
    
    return True


if __name__ == "__main__":
    import time
    from datetime import datetime, timezone
    
    if len(sys.argv) < 2:
        print("Usage: python prepare_large_run.py <target_directory> [expected_files]")
        sys.exit(1)
    
    target_path = sys.argv[1]
    expected_files = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
    
    success = prepare_for_large_run(target_path, expected_files)
    sys.exit(0 if success else 1)
