"""
inquiry - Human+algorithmic investigation layer

The inquiry layer bridges raw observations and human understanding.
It transforms immutable facts into actionable insights through patterns,
questions, and anchored thinking.

This layer is where human investigators interact with observed code,
asking questions, detecting patterns, and recording thoughts that are
tied directly to evidence.

Components:
    - questions: Human inquiry system for structured questioning
    - patterns: Algorithmic pattern detection (complexity, coupling, etc.)
    - answers: Analysis engines that provide evidence-based answers
    - notebook: Investigation journaling with constraint tracking
    - session: Investigation session management and persistence

Constitutional Context:
    - Article 2: Human Primacy (humans drive inquiry)
    - Article 9: Question-Driven (inquiry starts with questions)
    - Article 12: Anchored Thinking (thoughts tied to evidence)

Example:
    >>> from inquiry.questions import PurposeQuestion
    >>> question = PurposeQuestion(target="src/auth.py")
    >>> answer = question.ask()
"""
