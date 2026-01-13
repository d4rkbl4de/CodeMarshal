"""
Smoke test for constitutional boundary detection.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from observations.eyes.boundary_sight import BoundarySight
from observations.eyes.import_sight import ImportSight
from config.boundaries import load_boundary_config

def main():
    print("="*80)
    print("CONSTITUTIONAL ANALYSIS SMOKE TEST")
    print("="*80)
    
    # Setup paths
    test_dir = Path(__file__).parent / "test_violations"
    config_path = test_dir / "test_config.yaml"
    
    print(f"\nTest Directory: {test_dir}")
    print(f"Config File: {config_path}")
    
    # Load boundary configuration
    print("\n" + "="*80)
    print("STEP 1: Loading Boundary Configuration")
    print("="*80)
    
    try:
        boundary_config = load_boundary_config(config_path)
        print(f"✅ Loaded {len(boundary_config.boundary_definitions)} boundary definitions")
        
        for bd in boundary_config.boundary_definitions:
            print(f"  - {bd.name}: {bd.pattern} ({bd.boundary_type})")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Initialize observation eyes
    print("\n" + "="*80)
    print("STEP 2: Collecting Imports")
    print("="*80)
    
    import_sight = ImportSight()
    all_imports = []
    
    for py_file in test_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        print(f"\n📄 Scanning: {py_file.relative_to(test_dir)}")
        result = import_sight._observe_impl(py_file)
        
        if result.is_successful:
            observation = result.raw_payload
            if observation.statements:
                print(f"  Found {len(observation.statements)} imports:")
                for stmt in observation.statements:
                    module = stmt.module or "(relative)"
                    print(f"    Line {stmt.line_number}: {module}")
                    all_imports.append((py_file, stmt))
            else:
                print(f"  No imports found")
        else:
            print(f"  ⚠️  Failed: {result.errors}")
    
    # Run boundary analysis
    print("\n" + "="*80)
    print("STEP 3: Detecting Boundary Violations")
    print("="*80)
    
    boundary_sight = BoundarySight(
        boundary_definitions=boundary_config.boundary_definitions,
        project_root=test_dir  # Pass project root for correct module resolution
    )
    
    # Analyze the entire directory at once (not individual files)
    print(f"\nAnalyzing entire directory: {test_dir}")
    result = boundary_sight._observe_impl(test_dir)
    
    violations_found = []
    
    if result.is_successful:
        observation = result.raw_payload
        
        # Show module boundary assignments
        print(f"\nModule Boundary Assignments:")
        module_boundaries = dict(observation.module_boundaries)
        for module_name, boundary_name in sorted(module_boundaries.items()):
            print(f"  - {module_name}: {boundary_name}")
        
        # Show crossings (violations)
        print(f"\nBoundary Crossings Detected: {len(observation.crossings)}")
        for crossing in observation.crossings:
            print(f"\n  Crossing:")
            print(f"    Source: {crossing.source_module} ({crossing.source_boundary})")
            print(f"    Target: {crossing.target_module} ({crossing.target_boundary})")
            print(f"    Line: {crossing.line_number}")
            print(f"    Import: {crossing.import_statement}")
            print(f"    Allowed: {crossing.allowed_exception}")
            
            # Only count as violation if not allowed
            if not crossing.allowed_exception:
                violations_found.append({
                    'type': f"{crossing.source_boundary} -> {crossing.target_boundary}",
                    'source': crossing.source_module,
                    'target': crossing.target_module,
                    'line': crossing.line_number,
                    'evidence': crossing.import_statement
                })
    else:
        print(f"  Analysis failed: {result.errors}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\n📊 Total Files Scanned: {len(list(test_dir.rglob('*.py')))}")
    print(f"📦 Total Imports Found: {len(all_imports)}")
    print(f"❌ Total Violations: {len(violations_found)}")
    
    if violations_found:
        print("\n🔴 VIOLATIONS DETECTED:")
        for i, v in enumerate(violations_found, 1):
            print(f"\n  {i}. {v['type']}")
            print(f"     File: {v['source']}")
            print(f"     Line: {v.get('line', 'N/A')}")
            print(f"     Import: {v['target']}")
            print(f"     Evidence: {v.get('evidence', 'N/A')}")
    else:
        print("\n✅ NO VIOLATIONS DETECTED")
    
    # Expected vs Actual
    print("\n" + "="*80)
    print("EXPECTED vs ACTUAL")
    print("="*80)
    
    expected = 2
    actual = len(violations_found)
    
    print(f"\nExpected violations: {expected}")
    print(f"Actual violations: {actual}")
    
    if actual == expected:
        print("✅ TEST PASSED")
        return 0
    else:
        print(f"❌ TEST FAILED (expected {expected}, got {actual})")
        return 1

if __name__ == "__main__":
    sys.exit(main())
