#!/usr/bin/env python3
"""
Test boundary violation detection.

This script demonstrates the boundary checking system
with Agent Nexus constitutional rules.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observations.boundary_checker import (
    BoundaryViolationChecker, 
    create_agent_nexus_boundaries,
    Boundary,
    Violation
)


def test_agent_nexus_boundaries():
    """Test Agent Nexus boundary violations."""
    print("🧪 Testing Agent Nexus Boundary Violation Detection")
    print("=" * 60)
    
    # Create checker with Agent Nexus boundaries
    checker = BoundaryViolationChecker(create_agent_nexus_boundaries())
    
    # Test cases
    test_cases = [
        {
            "name": "Valid: Core imports infrastructure",
            "source": Path("core/engine.py"),
            "target": Path("infrastructure/logger.py"),
            "should_violate": False
        },
        {
            "name": "Violation: ChatBuddy imports InsightMate",
            "source": Path("lobes/chatbuddy/agent.py"),
            "target": Path("lobes/insightmate/analyzer.py"),
            "should_violate": True
        },
        {
            "name": "Violation: DataMiner imports Analyzer",
            "source": Path("lobes/dataminer/processor.py"),
            "target": Path("lobes/analyzer/validator.py"),
            "should_violate": True
        },
        {
            "name": "Valid: ChatBuddy imports common",
            "source": Path("lobes/chatbuddy/utils.py"),
            "target": Path("common/formats.py"),
            "should_violate": False
        },
        {
            "name": "Violation: InsightMate imports ChatBuddy",
            "source": Path("lobes/insightmate/insight.py"),
            "target": Path("lobes/chatbuddy/conversation.py"),
            "should_violate": True
        }
    ]
    
    print("\n📋 Test Cases:")
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Source: {test['source']}")
        print(f"   Target: {test['target']}")
        
        # Check for violation
        violation = checker.check_boundary_violation(test['source'], test['target'])
        
        if violation:
            print(f"   ❌ VIOLATION DETECTED:")
            print(f"      Type: {violation.type}")
            print(f"      Rule: {violation.rule}")
            print(f"      Source Boundary: {violation.source_boundary}")
            print(f"      Target Boundary: {violation.target_boundary}")
            
            if test['should_violate']:
                print("   ✓ Expected violation detected")
            else:
                print("   ⚠️ Unexpected violation")
        else:
            print("   ✅ No violation")
            
            if test['should_violate']:
                print("   ⚠️ Expected violation but none detected")
            else:
                print("   ✓ Correctly allowed")
    
    # Show boundary summary
    print("\n📊 Configured Boundaries:")
    summary = checker.get_boundary_summary()
    for boundary in summary['boundaries']:
        print(f"\n🔸 {boundary['name']} ({boundary['level']})")
        print(f"   Patterns: {', '.join(boundary['path_patterns'])}")
        if boundary['allowed_imports']:
            print(f"   Allowed: {', '.join(boundary['allowed_imports'])}")
        if boundary['prohibited_imports']:
            print(f"   Prohibited: {', '.join(boundary['prohibited_imports'])}")
        print(f"   Description: {boundary['description']}")


def test_import_statements():
    """Test boundary checking with actual import statements."""
    print("\n\n🧪 Testing Import Statement Analysis")
    print("=" * 60)
    
    checker = BoundaryViolationChecker(create_agent_nexus_boundaries())
    
    # Sample import statements
    import_statements = [
        {
            "type": "import",
            "module": "core.engine",
            "line": 5
        },
        {
            "type": "from_import",
            "module": "lobes.insightmate.analyzer",
            "names": ["analyze_data"],
            "line": 10
        },
        {
            "type": "import",
            "module": "infrastructure.logging",
            "line": 15
        }
    ]
    
    source_file = Path("lobes/chatbuddy/agent.py")
    
    print(f"\n📁 Checking imports in: {source_file}")
    violations = checker.check_file_imports(source_file, import_statements)
    
    if violations:
        print(f"\n❌ Found {len(violations)} violations:")
        for violation in violations:
            print(f"\n   Line {violation.line_number}: {violation.type}")
            print(f"   Rule: {violation.rule}")
            print(f"   {violation.source_boundary} → {violation.target_boundary}")
    else:
        print("\n✅ No boundary violations found")


def create_test_files():
    """Create test files to demonstrate boundary detection."""
    print("\n\n📝 Creating Test Files")
    print("=" * 60)
    
    test_dir = Path("test_boundaries")
    test_dir.mkdir(exist_ok=True)
    
    # Create lobe structure
    (test_dir / "lobes" / "chatbuddy").mkdir(parents=True, exist_ok=True)
    (test_dir / "lobes" / "insightmate").mkdir(parents=True, exist_ok=True)
    (test_dir / "core").mkdir(parents=True, exist_ok=True)
    (test_dir / "common").mkdir(parents=True, exist_ok=True)
    
    # ChatBuddy agent with cross-lobe import
    chatbuddy_code = '''"""ChatBuddy Agent - Conversational AI"""

# Valid import
from core.engine import Engine

# VIOLATION: Import from another lobe
from lobes.insightmate.analyzer import DataAnalyzer

class ChatBuddyAgent:
    def __init__(self):
        self.engine = Engine()
        self.analyzer = DataAnalyzer()  # This violates boundaries
'''
    
    (test_dir / "lobes" / "chatbuddy" / "agent.py").write_text(chatbuddy_code)
    
    # InsightMate analyzer
    insightmate_code = '''"""InsightMate Analyzer - Data Analysis"""

# Valid import
from common.formats import DataFormat

class DataAnalyzer:
    def __init__(self):
        self.formatter = DataFormat()
'''
    
    (test_dir / "lobes" / "insightmate" / "analyzer.py").write_text(insightmate_code)
    
    # Core engine
    core_code = '''"""Core Engine - System Coordinator"""

import logging

class Engine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
'''
    
    (test_dir / "core" / "engine.py").write_text(core_code)
    
    # Common utilities
    common_code = '''"""Common Utilities - Shared Components"""

class DataFormat:
    def __init__(self):
        self.format = "json"
'''
    
    (test_dir / "common" / "formats.py").write_text(common_code)
    
    print(f"✓ Test files created in {test_dir}")
    print("\nFiles created:")
    for file in test_dir.rglob("*.py"):
        print(f"   {file.relative_to(test_dir)}")


if __name__ == "__main__":
    # Run all tests
    test_agent_nexus_boundaries()
    test_import_statements()
    create_test_files()
    
    print("\n\n✅ Boundary violation testing complete!")
    print("\nTo test with actual files:")
    print("1. python scripts/test_boundaries.py")
    print("2. python -m bridge.entry.cli observe test_boundaries --constitutional")
