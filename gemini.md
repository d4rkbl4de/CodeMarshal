# CODEMARSHAL: TRUTH-PRESERVING CODE INVESTIGATION SYSTEM

## AI Analysis Guide for Gemini CLI

## PROJECT IDENTITY & CORE PHILOSOPHY

### What CodeMarshal Is

CodeMarshal is **not** a traditional code analysis tool. It is a **truth-preserving cognitive investigation environment** built specifically for understanding constitutionally-constrained codebases. Think of it as:

> "A detective's notebook for code that never lies, guesses, or overwhelms."

### Foundational Metaphor: The Three-Layer Truth Model

1. **Observations Layer**: Immutable facts about what exists in code (never infers)
2. **Inquiry Layer**: Human questions + machine pattern detection
3. **Lens Layer**: Truth-preserving interface constraints

## CONSTITUTIONAL ARCHITECTURE (NON-NEGOTIABLE)

### Tier 1: Foundational Truths (Never Violate)

- **Article 1**: Observation Purity - Only records what's textually present
- **Article 2**: Human Primacy - Humans ask questions, system provides observations
- **Article 3**: Truth Preservation - Never obscures, distorts, or invents information
- **Article 4**: Progressive Disclosure - Start simple, reveal complexity only when requested

### Tier 2: Interface Integrity

- **Article 5**: Single-Focus Interface - One primary content area visible at a time
- **Article 6**: Linear Investigation - Follows natural human curiosity flow
- **Article 7**: Clear Affordances - Always show what can be done next
- **Article 8**: Honest Performance - Show computation time, never pretend speed

### Tier 3-6: Architectural & System Constraints

(Complete constitutional text available in CONSTITUTIONAL_AUDIT_REPORT.md)

## ARCHITECTURAL OVERVIEW

### Core Directory Structure & Responsibilities

CodeMarshal/
├── bridge/ # Truth in different contexts (CLI, TUI, API, Export)
├── config/ # Boundary definitions and user configuration
├── core/ # Engine, runtime, and state management
├── inquiry/ # Human questions, patterns, and session management
├── integrity/ # Self-validation and constitutional compliance
├── lens/ # Truth-preserving interface (TUI philosophy)
├── observations/ # Immutable fact collection ("eyes")
└── storage/ # Atomic, transactional, versioned truth storage

### Key Architectural Breakthroughs

#### 1. The Bridge Metaphor

- **CLI**: `bridge/entry/cli.py` - Scriptable truth investigation
- **TUI**: `bridge/entry/tui.py` - Interactive truth exploration
- **API**: `bridge/entry/api.py` - Programmatic truth access
- **Export**: `bridge/integration/export_formats.py` - Shareable truth artifacts

#### 2. The Observation System

- **FileSight**: `observations/eyes/file_sight.py` - File existence and structure
- **ImportSight**: `observations/eyes/import_sight.py` - Import relationship mapping
- **BoundarySight**: `observations/eyes/boundary_sight.py` - Architectural violations
- **EncodingSight**: `observations/eyes/encoding_sight.py` - File encoding validation
- **ExportSight**: `observations/eyes/export_sight.py` - Export/import pattern analysis

#### 3. The Integrity System

- **Monitoring**: `integrity/monitoring/` - Truth drift detection
- **Prohibitions**: `integrity/prohibitions/` - Constitutional violation tests
- **Recovery**: `integrity/recovery/` - Corruption recovery mechanisms
- **Validation**: `integrity/validation/` - Self-consistency validation

## HOW TO ANALYZE CODEMARSHAL (AI GUIDELINES)

### 1. Start with Constitutional Compliance

When analyzing CodeMarshal, first verify it follows its own constitution:

```python
# Check: Does CodeMarshal violate its own rules?
- Look for inference in observations/ (violates Article 1)
- Check if interface overwhelms (violates Article 4)
- Verify immutability in storage/ (violates Article 9)
- Test single-focus in lens/ (violates Article 5)
```

### 2. Analyze the Truth-Preserving Mechanisms

#### Observation Purity Checks

```python
# File: observations/eyes/base.py
# MUST: Only record textual facts
# MUST NOT: Infer, guess, or interpret

# File: observations/record/snapshot.py
# MUST: Create immutable observation records
# MUST NOT: Allow modification after creation
```

#### Interface Constraint Checks

```python
# File: lens/philosophy/single_focus.py
# MUST: Show one primary content area
# MUST NOT: Show competing information streams

# File: lens/navigation/workflow.py
# MUST: Follow linear investigation flow
# MUST NOT: Allow random jumps or skipping
```

### 3. Evaluate the Self-Validating Architecture

#### Integrity Monitoring

```python
# File: integrity/monitoring/drift.py
# Checks: Truth preservation over time
# Key metric: Observation consistency across runs

# File: integrity/validation/interface.test.py
# Validates: Interface follows constitutional constraints
```

#### Recovery Mechanisms

```python
# File: integrity/recovery/backup.py
# Purpose: Truth recovery from corruption
# Method: Versioned, atomic storage operations


### 4. Trace the Investigation Workflow

Follow the exact user journey:

```

User Action → System Response

1. `codemarshal observe` → Pure fact collection
2. `codemarshal investigate` → Human+machine inquiry
3. `codemarshal query` → Targeted question answering
4. `codemarshal export` → Shareable truth artifacts

## KEY ANALYSIS QUESTIONS FOR AI

### Architectural Questions

1. **Does the separation of Observation/Inquiry/Lens prevent truth distortion?**
2. **How does the immutable storage guarantee reproducibility?**
3. **What prevents the interface from misleading users?**
4. **Where are the declared limitations actually enforced?**

### Philosophical Questions

1. **How does "epistemic humility" manifest in code?**
2. **Where does the system say "I cannot see this" vs guessing?**
3. **How are human thoughts anchored to specific observations?**
4. **What prevents confirmation bias in pattern detection?**

### Implementation Questions

1. **How are constitutional violations prevented at compile/runtime?**
2. **What ensures observations remain immutable?**
3. **How does the TUI maintain single-focus while showing context?**
4. **Where are the performance/truth tradeoffs documented?**

## PATTERNS TO IDENTIFY

### Constitutional Compliance Patterns

```python
# Pattern: Truth preservation through immutability
# Files: storage/atomic.py, storage/transactional.py
# Indicator: Write-once, append-only operations

# Pattern: Declared limitation enforcement
# Files: observations/limitations/declared.py
# Indicator: "cannot_see_" prefixes in method names

# Pattern: Human primacy in inquiry
# Files: inquiry/interface.py, inquiry/session/context.py
# Indicator: Human questions driving machine analysis
```

### Anti-Patterns (Constitutional Violations)

```python
# Anti-pattern: Inference in observations
# Violates: Article 1 (Observation Purity)
# Location: Any .py file in observations/ that guesses

# Anti-pattern: Interface overload
# Violates: Article 5 (Single-Focus Interface)
# Location: lens/views/ with multiple competing elements

# Anti-pattern: Hidden capabilities
# Violates: Article 7 (Clear Affordances)
# Location: Undocumented features or "Easter eggs"
```

## SPECIFIC FILES FOR DEEP ANALYSIS

### Core Truth Mechanisms

1. **`core/engine.py`** - The main orchestrator (truth flow control)
2. **`observations/interface.py`** - Observation collection entry point
3. **`storage/atomic.py`** - Immutable truth storage implementation
4. **`integrity/monitoring/drift.py`** - Truth preservation monitoring

### Interface Truth Preservation

1. **`lens/philosophy/clarity.py`** - Visual truth enhancement principles
2. **`lens/views/overview.py`** - Single-focus view implementation
3. **`bridge/entry/tui.py`** - Interactive truth exploration interface

### Constitutional Enforcement

1. **`integrity/prohibitions/no_inference.test.py`** - Article 1 validation
2. **`integrity/validation/interface.test.py`** - Interface rule validation
3. **`observations/invariants/purity.test.py`** - Observation purity tests

## UNIQUE CHARACTERISTICS TO NOTE

### 1. The "Three Guardians" System

- **Static Guardian**: Pre-commit constitutional validation
- **Runtime Guardian**: Real-time truth preservation monitoring
- **Interface Guardian**: UI prevention of truth-violating interactions

### 2. Truth Decay Prevention

CodeMarshal recognizes that "truth decays without active preservation" and implements:

- Versioned observations (prevents revisionism)
- Anchored thinking (prevents floating opinions)
- Declared limitations (prevents overclaiming)

### 3. The Investigation Metaphor

Not "analysis" but "investigation" - key differences:

- **Analysis**: Machine-centric, comprehensive, often overwhelming
- **Investigation**: Human-led, focused, truth-preserving, anchored

## SUCCESS METRICS FOR CODEMARSHAL

### Technical Success

- [ ] Same input → Same output (deterministic operation)
- [ ] Observations remain immutable once recorded
- [ ] Interface never overwhelms with information
- [ ] Constitutional violations are caught and prevented

### Human Success

- [ ] Developers spend less time "debugging understanding"
- [ ] Architectural decisions have clear evidence trails
- [ ] Code reviews reference specific observations
- [ ] Team develops shared vocabulary for uncertainty

### Philosophical Success

- [ ] "I don't know" is more valuable than confident guessing
- [ ] Truth perception is enhanced, not obscured
- [ ] Understanding grows through disciplined investigation
- [ ] Wisdom emerges from tracing claims to observations

## INSTRUCTIONS FOR GEMINI CLI

### When Analyzing CodeMarshal

1. **First** verify constitutional compliance in the file you're examining
2. **Always** separate what exists (observations) from what humans think (inquiry)
3. **Look for** the declared limitations in each module
4. **Check** that interfaces maintain single-focus and linear flow
5. **Validate** that storage operations are atomic and immutable

### Questions to Continuously Ask

- "Is this preserving truth or potentially distorting it?"
- "What are the declared limitations of this analysis?"
- "How is human primacy maintained here?"
- "Where would uncertainty be shown vs hidden?"

### Output Format for Analysis

# CODEMARSHAL ANALYSIS:

CONSTITUTIONAL COMPLIANCE:
• Article X: [Compliance status]
• Article Y: [Potential violation]

TRUTH PRESERVATION:
• Observations: [Pure/Inferential]
• Limitations: [Declared/Hidden]
• Immutability: [Guaranteed/Potentially violated]

INTERFACE INTEGRITY:
• Single-focus: [Maintained/Broken]
• Linear flow: [Followed/Skipped]
• Affordances: [Clear/Hidden]

RECOMMENDED INVESTIGATION PATH:

1. [Next file to examine]
2. [Specific constitutional check]
3. [Truth preservation validation]

## FINAL PRINCIPLE FOR AI ANALYSIS

**CodeMarshal is not just code to analyze - it's a truth-preserving environment to understand.**

When examining any part of CodeMarshal, ask: "Does this make humans better at understanding complex systems without ever pretending to understand for them?"

The ultimate test: If CodeMarshal were used to analyze itself, would it find itself constitutionally compliant?

This `codemarshal.gemini.md` file provides Gemini CLI with:

1. **Architectural understanding** of CodeMarshal's unique structure
2. **Constitutional awareness** of the non-negotiable rules
3. **Specific analysis guidelines** for truth-preservation checking
4. **Key files and patterns** to examine
5. **Philosophical context** for why CodeMarshal exists
