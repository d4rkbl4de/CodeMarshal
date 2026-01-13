"""
Test script to verify boundary configuration loading
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_defaults():
    """Test default configuration."""
    print("=" * 60)
    print("TEST 1: Default Configuration")
    print("=" * 60)
    
    from config.defaults import get_observation_defaults, get_preset_config
    
    # Test default observation config
    defaults = get_observation_defaults()
    print("\n📋 OBSERVATION_DEFAULTS:")
    print(f"  Enabled eyes: {defaults['enabled_eyes']}")
    print(f"  Use boundary sight: {defaults['use_boundary_sight']}")
    print(f"  Detect circular deps: {defaults['detect_circular_deps']}")
    
    # Test constitutional preset
    constitutional = get_preset_config("constitutional")
    print("\n🏛️  PRESET_CONSTITUTIONAL:")
    print(f"  Enabled eyes: {constitutional['enabled_eyes']}")
    print(f"  Use boundary sight: {constitutional['use_boundary_sight']}")
    print(f"  Check boundaries: {constitutional['check_boundaries']}")
    
    # Test quick preset
    quick = get_preset_config("quick")
    print("\n⚡ PRESET_QUICK:")
    print(f"  Enabled eyes: {quick['enabled_eyes']}")
    print(f"  Use boundary sight: {quick['use_boundary_sight']}")
    
    print("\n✅ Default configuration test PASSED\n")


def test_boundary_config_loader():
    """Test boundary configuration loading."""
    print("=" * 60)
    print("TEST 2: Boundary Configuration Loader")
    print("=" * 60)
    
    from config.boundaries import load_boundary_config, find_config_file
    
    # Find config file
    config_path = find_config_file(project_root=Path(__file__).parent)
    
    if config_path:
        print(f"\n📍 Found config: {config_path}")
        
        # Load configuration
        config = load_boundary_config(config_path)
        
        print(f"\n📦 Project: {config.project_name}")
        print(f"   Architecture: {config.architecture}")
        print(f"   Strictness: {config.boundary_strictness}")
        
        print(f"\n🚧 Boundaries defined: {len(config.boundary_definitions)}")
        for boundary in config.boundary_definitions:
            print(f"   • {boundary.name}")
            print(f"     Type: {boundary.boundary_type.name}")
            print(f"     Pattern: {boundary.pattern}")
            if boundary.allowed_targets:
                print(f"     Allowed: {', '.join(boundary.allowed_targets)}")
        
        print(f"\n👁️  Enabled observation eyes: {', '.join(config.enabled_eyes)}")
        print(f"   Uses boundary sight: {config.uses_boundary_sight}")
        print(f"   Detect circular: {config.detect_circular}")
        
        print("\n✅ Boundary configuration test PASSED\n")
    else:
        print("\n⚠️  No config file found (this is OK for default usage)")
        print("   Create config/agent_nexus.yaml to enable boundary analysis\n")


def test_boundary_sight():
    """Test BoundarySight initialization."""
    print("=" * 60)
    print("TEST 3: BoundarySight Initialization")
    print("=" * 60)
    
    from observations.eyes.boundary_sight import (
        BoundarySight,
        BoundaryDefinition,
        BoundaryType,
        create_layer_boundary,
        create_package_boundary
    )
    
    # Create test boundaries
    boundaries = [
        create_layer_boundary(
            name="core",
            pattern="core/*",
            allowed_targets=[]
        ),
        create_package_boundary(
            package_name="lobes.chatbuddy",
            allowed_targets=["common/*", "core/*"]
        ),
        create_package_boundary(
            package_name="lobes.insightmate",
            allowed_targets=["common/*", "core/*"]
        ),
    ]
    
    print(f"\n🔍 Created {len(boundaries)} test boundaries:")
    for boundary in boundaries:
        print(f"   • {boundary.name} ({boundary.boundary_type.name})")
    
    # Initialize BoundarySight
    sight = BoundarySight(boundary_definitions=boundaries)
    
    capabilities = sight.get_capabilities()
    print(f"\n📊 BoundarySight capabilities:")
    print(f"   Name: {capabilities['name']}")
    print(f"   Version: {capabilities['version']}")
    print(f"   Deterministic: {capabilities['deterministic']}")
    print(f"   Side-effect free: {capabilities['side_effect_free']}")
    print(f"   Boundary rules: {capabilities['boundary_rule_count']}")
    print(f"   Supports cycle detection: {capabilities['supports_cycle_detection']}")
    
    print("\n✅ BoundarySight initialization test PASSED\n")


def test_observation_types():
    """Test ObservationType enum."""
    print("=" * 60)
    print("TEST 4: ObservationType Enum")
    print("=" * 60)
    
    from bridge.commands.observe import ObservationType
    
    print("\n👁️  Available observation types:")
    for obs_type in ObservationType:
        print(f"   • {obs_type.name} = '{obs_type.value}'")
    
    # Verify BOUNDARY_SIGHT exists
    assert ObservationType.BOUNDARY_SIGHT in list(ObservationType), \
        "BOUNDARY_SIGHT not found in ObservationType!"
    
    print("\n✅ ObservationType test PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CodeMarshal Constitutional Analysis Configuration Tests")
    print("=" * 60 + "\n")
    
    try:
        test_defaults()
        test_boundary_config_loader()
        test_boundary_sight()
        test_observation_types()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Review CONSTITUTIONAL_ANALYSIS.md for usage guide")
        print("  2. Run: codemarshal observe . --scope=project --constitutional")
        print("  3. Check for boundary violations in your codebase")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
