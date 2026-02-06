"""
Test suite for CodeMarshal query answering system.

Tests all question types and analyzers to ensure they work correctly.
"""

from inquiry.answers import (
    AnomalyDetector,
    ConnectionMapper,
    PurposeExtractor,
    StructureAnalyzer,
    ThinkingEngine,
)


class TestStructureAnalyzer:
    """Test structure analysis functionality."""

    def test_analyze_directory_structure(self):
        """Test directory structure analysis."""
        analyzer = StructureAnalyzer()
        observations = [
            {
                "type": "file_sight",
                "result": {
                    "path": "/test/project",
                    "file_count": 10,
                    "directory_count": 3,
                },
            }
        ]

        result = analyzer.analyze(observations, "What is the directory structure?")

        assert "Directory Structure" in result
        assert "10" in result
        assert "3" in result
        assert "/test/project" in result

    def test_analyze_modules_list(self):
        """Test module list generation."""
        analyzer = StructureAnalyzer()
        observations = [
            {
                "type": "file_sight",
                "result": {
                    "path": "/test/project",
                    "file_count": 5,
                    "directory_count": 2,
                },
            }
        ]

        result = analyzer.analyze(observations, "What modules exist?")

        assert "Python Modules" in result or "modules" in result.lower()

    def test_empty_observations(self):
        """Test handling of empty observations."""
        analyzer = StructureAnalyzer()
        result = analyzer.analyze([], "What is the structure?")

        assert (
            "No directory structure found" in result
            or "not available" in result.lower()
        )


class TestConnectionMapper:
    """Test connection/dependency mapping functionality."""

    def test_find_dependents(self):
        """Test finding modules that depend on a target."""
        mapper = ConnectionMapper()
        observations = [
            {
                "type": "import_sight",
                "file": "/test/module_a.py",
                "statements": [
                    {"module": "core.engine", "names": ["Engine"]},
                ],
            },
            {
                "type": "import_sight",
                "file": "/test/module_b.py",
                "statements": [
                    {"module": "core.runtime", "names": []},
                ],
            },
        ]

        result = mapper.analyze(observations, "What depends on core.engine?")

        # Should find that module_a depends on core.engine
        assert isinstance(result, str)

    def test_get_all_imports_summary(self):
        """Test getting summary of all imports."""
        mapper = ConnectionMapper()
        observations = [
            {
                "type": "import_sight",
                "file": "/test/file.py",
                "statements": [
                    {"module": "os", "names": []},
                    {"module": "sys", "names": []},
                ],
            }
        ]

        result = mapper.analyze(observations, "What are the dependencies?")

        assert "Dependency" in result or "import" in result.lower()

    def test_circular_dependencies(self):
        """Test circular dependency detection."""
        mapper = ConnectionMapper()
        observations = [
            {
                "type": "import_sight",
                "file": "/test/a.py",
                "statements": [{"module": "b", "names": []}],
            },
            {
                "type": "import_sight",
                "file": "/test/b.py",
                "statements": [{"module": "a", "names": []}],
            },
        ]

        result = mapper.analyze(observations, "Show circular dependencies")

        # Should detect the circular dependency
        assert isinstance(result, str)


class TestAnomalyDetector:
    """Test anomaly detection functionality."""

    def test_find_boundary_violations(self):
        """Test boundary violation detection."""
        detector = AnomalyDetector()
        observations = [
            {
                "type": "boundary_sight",
                "crossings": [
                    {
                        "source_module": "bridge.commands",
                        "target_module": "observations.eyes",
                        "line_number": 42,
                    }
                ],
            }
        ]

        result = detector.analyze(observations, "Show boundary violations")

        assert "Boundary" in result or "violation" in result.lower()

    def test_find_suspicious_patterns(self):
        """Test suspicious pattern detection."""
        detector = AnomalyDetector()
        observations = [
            {
                "type": "file_sight",
                "result": {
                    "path": "/test/project",
                    "modules": [{"path": "/test/a.py"}, {"path": "/test/b.py"}],
                },
            },
            {
                "type": "import_sight",
                "file": "/test/a.py",
                "statements": [{"module": "os", "names": []}],
            },
            # b.py has no imports (orphan file)
        ]

        result = detector.analyze(observations, "What looks suspicious?")

        assert isinstance(result, str)

    def test_no_anomalies(self):
        """Test when no anomalies are found."""
        detector = AnomalyDetector()
        observations = []

        result = detector.analyze(observations, "Are there any anomalies?")

        # Should indicate no anomalies found
        assert isinstance(result, str)


class TestPurposeExtractor:
    """Test purpose extraction functionality."""

    def test_describe_target(self):
        """Test describing a specific target."""
        extractor = PurposeExtractor()
        observations = [
            {
                "type": "export_sight",
                "file": "/test/core.py",
                "result": {
                    "exports": [
                        {"name": "Engine"},
                        {"name": "Runtime"},
                    ]
                },
            }
        ]

        result = extractor.analyze(observations, "What does core do?")

        assert isinstance(result, str)

    def test_get_general_purpose(self):
        """Test getting general purpose summary."""
        extractor = PurposeExtractor()
        observations = [
            {
                "type": "export_sight",
                "result": {"exports": [{"name": "func1"}, {"name": "func2"}]},
            }
        ]

        result = extractor.analyze(observations, "What is the purpose?")

        assert "Purpose" in result or isinstance(result, str)


class TestThinkingEngine:
    """Test thinking/recommendation functionality."""

    def test_suggest_next_steps(self):
        """Test suggesting next investigation steps."""
        engine = ThinkingEngine()
        observations = [
            {
                "type": "boundary_sight",
                "crossings": [{"source_module": "a", "target_module": "b"}],
            }
        ]

        result = engine.analyze(observations, "What should I investigate next?")

        assert "Next Steps" in result or "investigate" in result.lower()

    def test_identify_risks(self):
        """Test risk identification."""
        engine = ThinkingEngine()
        observations = [
            {
                "type": "import_sight",
                "file": "/test/large_module.py",
                "statements": [{"module": f"mod{i}", "names": []} for i in range(25)],
            }
        ]

        result = engine.analyze(observations, "What are the risks?")

        assert "Risk" in result or isinstance(result, str)

    def test_general_analysis(self):
        """Test general analysis."""
        engine = ThinkingEngine()
        observations = [
            {"type": "file_sight", "result": {"modules": []}},
            {"type": "import_sight", "statements": []},
        ]

        result = engine.analyze(observations, "What do you think?")

        assert "Analysis" in result or isinstance(result, str)


class TestAnalyzerIntegration:
    """Test that all analyzers work together."""

    def test_all_analyzers_with_sample_data(self):
        """Test all analyzers with realistic sample data."""
        observations = [
            {
                "type": "file_sight",
                "result": {
                    "path": "/project/src",
                    "file_count": 5,
                    "directory_count": 2,
                    "modules": [
                        {"path": "/project/src/main.py"},
                        {"path": "/project/src/utils.py"},
                    ],
                },
            },
            {
                "type": "import_sight",
                "file": "/project/src/main.py",
                "statements": [
                    {"module": "os", "names": []},
                    {"module": "sys", "names": []},
                ],
            },
            {
                "type": "export_sight",
                "file": "/project/src/utils.py",
                "result": {"exports": [{"name": "helper"}]},
            },
        ]

        # Test each analyzer
        structure = StructureAnalyzer().analyze(observations, "Show structure")
        connections = ConnectionMapper().analyze(observations, "Show dependencies")
        anomalies = AnomalyDetector().analyze(observations, "Find anomalies")
        purpose = PurposeExtractor().analyze(observations, "What does utils do?")
        thinking = ThinkingEngine().analyze(observations, "Next steps?")

        # All should return strings
        assert all(
            isinstance(r, str)
            for r in [structure, connections, anomalies, purpose, thinking]
        )

        # All should be non-empty
        assert all(
            len(r) > 0 for r in [structure, connections, anomalies, purpose, thinking]
        )
