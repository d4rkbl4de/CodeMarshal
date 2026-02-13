from patterns.loader import PatternLoader


def test_builtin_pattern_counts() -> None:
    loader = PatternLoader()

    performance = loader.load_builtin_patterns("performance")
    style = loader.load_builtin_patterns("style")
    architecture = loader.load_builtin_patterns("architecture")

    assert len(performance) == 20
    assert len(style) == 15
    assert len(architecture) == 12

    for pattern in performance + style + architecture:
        assert pattern.id
        assert pattern.name
