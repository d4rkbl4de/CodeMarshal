"""
observations.invariants - CONSTITUTIONAL ENFORCEMENT (LAYER 1)

Single responsibility of this package:

Enforce the non-negotiable laws of observation through executable proof.

These tests do not check correctness of results.
They check correctness of behavior under temptation.

Structural rules for this directory:

Tests here must:
1. Be deterministic
2. Be hostile
3. Assume future violations will be subtle
4. Be strict, slow, and annoying

A failure here is Tier-1 and must halt execution

Contents:
immutable.test.py - Enforces Articles 1 & 9: "Observations never change"
no_inference.test.py - Enforces Articles 1, 3 & Four Pillars: "No guessing allowed"
purity.test.py - Enforces Article 1: "Read-only enforcement"

These tests exist to make system decay expensive and visible.
"""

# Package declaration only - no logic belongs here
# This file exists to:
# 1. Enable explicit import scoping
# 2. Prevent test discovery ambiguity
# 3. Signal "this directory is intentional"

__version__ = "1.0.0"
__all__: list[str] = []  # No public exports - tests are run via test framework
