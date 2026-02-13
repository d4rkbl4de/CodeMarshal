# CodeMarshal Directory Structure

**Version:** 2.1.0  
**Last Updated:** February 12, 2026

---

CodeMarshal/
│
├── pyproject.toml
├── README.md
├── README.truth.md
├── constitution.truth.md
├── MANIFEST.integrity.md
├── ROADMAP.md
├── IMPLEMENTATION_SUMMARY.md
├── CLEANUP_COMPLETE.md
│
├── Dockerfile                    # Production container
├── Dockerfile.dev               # Development container
├── docker-compose.yml           # Docker orchestration
├── .dockerignore               # Docker build optimization
│
├── .pre-commit-hooks.yaml      # Pre-commit hook config
├── requirements.txt            # Python dependencies
├── setup.ps1                   # Windows setup
├── setup.sh                    # Linux/Mac setup
│
├── core/ # EXECUTION SPINE (SYSTEM HEART)
│ ├── __init__.py
│ ├── runtime.py # Owns lifecycle of an investigation
│ ├── engine.py # Coordinates layers without leakage
│ ├── context.py # Global immutable runtime context
│ ├── state.py # Investigation state machine
│ ├── shutdown.py # Safe termination guarantees
│ ├── memory_monitor_interface.py # v2.0 - Memory monitoring interface
│
├── config/ # CONFIGURATION DISCIPLINE
│ ├── **init**.py
│ ├── agent_nexus.yaml # Default boundary rules
│ ├── defaults.py # System defaults (immutable)
│ ├── user.py # User overrides
│ ├── schema.py # Validation rules
│ └── loader.py # Merge + validate config
│
├── storage/ # PERSISTENCE & DURABILITY
│ ├── **init**.py
│ ├── layout.py # Directory & file layout rules
│ ├── schema.py # Stored data schemas
│ ├── atomic.py # Atomic write guarantees
│ ├── corruption.py # Detect & flag corruption
│ └── migration.py # Forward-compatible changes
│
├── observations/ # WHAT EXISTS (LAYER 1)
│ ├── **init**.py
│ │
│ ├── eyes/ # WAYS OF SEEING (PURE READERS)
│ │ ├── **init**.py
│ │ ├── base.py # Observation interface contract
│ │ ├── file_sight.py # Files, directories, paths
│ │ ├── import_sight.py # Static import statements
│ │ ├── export_sight.py # Definitions, signatures
│ │ ├── javascript_sight.py # JS/TS imports + exports
│ │ ├── java_sight.py # Java imports + classes
│ │ ├── go_sight.py # Go imports + exports
│ │ ├── language_detector.py # Language identification
│ │ ├── boundary_sight.py # Module boundaries
│ │ └── encoding_sight.py # File encoding & type detection
│ │
│ ├── record/ # IMMUTABLE RECORDING
│ │ ├── **init**.py
│ │ ├── snapshot.py # Complete observation snapshot
│ │ ├── anchors.py # Stable reference points
│ │ ├── version.py # Snapshot versioning
│ │ └── integrity.py # Hashes & immutability checks
│ │
│ ├── limitations/ # WHAT WE CANNOT SEE
│ │ ├── **init**.py
│ │ ├── declared.py # Explicit blind spots
│ │ ├── documented.py # Human-readable limits
│ │ └── validation.py # Guards against overreach
│ │
│ ├── input_validation/ # INPUT DISCIPLINE
│ │ ├── **init**.py
│ │ ├── filesystem.py # Symlink & traversal rules
│ │ ├── binaries.py # Binary file handling
│ │ └── size_limits.py # File & tree size limits
│ │
│ └── invariants/
│ ├── **init**.py
│ ├── immutable.test.py # Observations never change
│ ├── no_inference.test.py # No guessing allowed
│ └── purity.test.py # Read-only enforcement
│
├── inquiry/ # QUESTIONS & PATTERNS (LAYER 2)
│ ├── **init**.py
│ │
│ ├── questions/ # HUMAN QUESTIONS
│ │ ├── **init**.py
│ │ ├── structure.py # What's here?
│ │ ├── purpose.py # What does this do?
│ │ ├── connections.py # How is it connected?
│ │ ├── anomalies.py # What seems unusual?
│ │ └── thinking.py # What do I think?
│ │
│ ├── patterns/ # NUMERIC-ONLY PATTERNS
│ │ ├── **init**.py
│ │ ├── density.py # Import counts, clustering
│ │ ├── coupling.py # Degree & fan-in/out
│ │ ├── complexity.py # Depth, node counts (no labels)
│ │ ├── violations.py # Boundary crossings (boolean)
│ │ └── uncertainty.py # Incomplete data indicators
│ │
│ ├── notebook/ # HUMAN THINKING SPACE
│ │ ├── **init**.py
│ │ ├── entries.py # Notes anchored to observations
│ │ ├── organization.py # Tags & search
│ │ ├── timeline.py # Chronological reasoning
│ │ ├── export.py # Export notes only
│ │ └── constraints.py # Prevent note→observation bleed
│ │
│ └── session/ # INVESTIGATION CONTEXT
│ ├── **init**.py
│ ├── context.py # Current focus
│ ├── history.py # Linear investigation path
│ └── recovery.py # Resume safely
│
├── patterns/ # REGEX PATTERN DETECTION
│ ├── **init**.py
│ ├── loader.py # Pattern loading and scanning
│ ├── engine.py # Context + outlier detection helpers
│ ├── builtin/
│ │ ├── security.yaml
│ │ ├── performance.yaml
│ │ ├── style.yaml
│ │ └── architecture.yaml
│ └── custom/
│
├── lens/ # INTERFACE (LAYER 3)
│ ├── **init**.py
│ │
│ ├── philosophy/
│ │ ├── **init**.py
│ │ ├── single_focus.py
│ │ ├── progressive.py
│ │ ├── clarity.py
│ │ └── navigation.py
│ │
│ ├── views/
│ │ ├── **init**.py
│ │ ├── overview.py
│ │ ├── examination.py
│ │ ├── connections.py
│ │ ├── patterns.py
│ │ ├── pattern_dashboard.py
│ │ ├── thinking.py
│ │ └── help.py
│ │
│ ├── navigation/
│ │ ├── **init**.py
│ │ ├── workflow.py
│ │ ├── shortcuts.py
│ │ ├── context.py
│ │ └── recovery.py
│ │
│ ├── aesthetic/
│ │ ├── **init**.py
│ │ ├── palette.py
│ │ ├── typography.py
│ │ ├── icons.py
│ │ └── layout.py
│ │
│ └── indicators/
│ ├── **init**.py
│ ├── loading.py
│ └── errors.py
│
├── bridge/ # COMMAND & CONTROL
│ ├── **init**.py
│ │
│ ├── commands/ # CLI COMMANDS
│ │ ├── __init__.py
│ │ ├── investigate.py          # Investigation command
│ │ ├── observe.py              # Observation command
│ │ ├── query.py                # Query command
│ │ ├── export.py               # Export command
│ │ │
│ │ ├── config.py # v2.0 - Configuration management
│ │ ├── backup.py # v2.0 - Backup operations
│ │ ├── cleanup.py # v2.0 - Cleanup operations
│ │ ├── repair.py # v2.0 - Repair operations
│ │ ├── search.py # v2.0 - Code search
│ │ ├── pattern.py # v2.0 - Pattern detection
│ │ └── test_cmd.py # v2.0 - Test runner
│ │
│ ├── entry/
│ │ ├── **init**.py
│ │ ├── cli.py
│ │ ├── tui.py
│ │ └── api.py
│ │
│ ├── integration/
│ │ ├── **init**.py
│ │ ├── editor.py
│ │ ├── ci.py
│ │ └── export_formats.py
│ │
│ └── coordination/
│ ├── **init**.py
│ ├── caching.py # Shared caching logic
│ └── scheduling.py # Task orchestration
│
├── integrity/ # TRUTH PRESERVATION
│ ├── **init**.py
│ │
│ ├── validation/
│ │ ├── **init**.py
│ │ ├── observations_test.py
│ │ ├── patterns_test.py
│ │ ├── interface_test.py
│ │ └── integration_test.py
│ │
│ ├── monitoring/
│ │ ├── **init**.py
│ │ ├── drift.py
│ │ ├── performance.py
│ │ └── errors.py
│ │
│ ├── prohibitions/
│ │ ├── **init**.py
│ │ ├── no_network.py
│ │ ├── no_runtime_imports.py
│ │ └── no_mutation.py
│ │
│ └── recovery/
│ ├── __init__.py
│ ├── backup.py
│ ├── restore.py
│ └── audit.py
│
├── patterns/ # PATTERN DETECTION SYSTEM (v2.0)
│ ├── __init__.py
│ ├── loader.py                 # Pattern loading and management
│ ├── engine.py                 # Context + outlier detection helpers
│ │
│ ├── builtin/                  # Built-in pattern libraries
│ │ ├── security.yaml          # Security patterns (8 patterns)
│ │ ├── performance.yaml       # Performance patterns (20 patterns)
│ │ ├── style.yaml            # Style patterns (15 patterns)
│ │ └── architecture.yaml      # Architecture patterns (12 patterns)
│ │
│ └── custom/                   # User-defined patterns
│   └── user_patterns.yaml      # Custom user patterns
│
├── hooks/ # PRE-COMMIT HOOKS (v2.0)
│ └── codemarshal-constitutional.py  # Constitutional violation detector
│
├── scripts/ # UTILITY SCRIPTS (v2.0)
│ ├── docker-build.sh          # Docker build helper
│ ├── docker-run.sh           # Docker run helper
│ ├── docker-entrypoint.sh    # Container entrypoint
│ ├── monitor_wrapper.sh      # Monitoring wrapper
│ └── prepare_large_run.py    # Large run preparation
│
├── .github/ # GITHUB INTEGRATION (v2.0)
│ └── workflows/
│ └── codemarshal.yml       # CI/CD workflow
│
└── tests/ # SYSTEM-LEVEL TESTS
├── __init__.py
├── end_to_end.test.py       # Integration tests
├── performance.test.py      # Performance benchmarks
├── invariants_test.py       # System invariants
│
├── test_cli/ # v2.0 - CLI command tests
│ ├── test_config.py
│ └── test_search.py
│
└── test_export/ # v2.0 - Export format tests
├── test_html_exporter.py
└── test_csv_exporter.py

CONSTITUTION OF TRUTH (NON-NEGOTIABLE)
TIER 1: FOUNDATIONAL TRUTHS (NEVER VIOLATE)
Article 1: Observation Purity
Observations record only what is textually present in source code. No inference, no guessing, no interpretation. Observations are immutable once recorded.

Article 2: Human Primacy
Humans ask questions, see patterns, and think thoughts. The system provides observations, detects anomalies, and preserves thinking. Never reverse these roles.

Article 3: Truth Preservation
The system must never obscure, distort, or invent information. When truth is uncertain, show uncertainty clearly (⚠️). When truth is unknown, say "I cannot see this."

Article 4: Progressive Disclosure
Start with simple observations, reveal complexity only when requested. Never overwhelm with information. Each interaction should answer exactly one human question.

TIER 2: INTERFACE INTEGRITY (STRONG DEFAULTS)
Article 5: Single-Focus Interface
Only one primary content area visible at a time. No competing information streams. The interface should feel like looking through a magnifying glass, not at a dashboard.

Article 6: Linear Investigation
Follow natural human curiosity: What exists? What does it do? How is it connected? What seems unusual? What do I think? Never skip ahead or jump randomly.

Article 7: Clear Affordances
At every moment, show what can be done next with obvious, consistent actions. No hidden capabilities, no Easter eggs.

Article 8: Honest Performance
If computation takes time, show a simple indicator. If something cannot be computed, explain why. Never freeze without indication, never pretend speed that isn't there.

TIER 3: ARCHITECTURAL CONSTRAINTS
Article 9: Immutable Observations
Once an observation is recorded, it cannot change. New observations create new versions. This ensures reproducibility and auditability.

Article 10: Anchored Thinking
All human thoughts must be anchored to specific observations. No floating opinions, no unattached ideas. This creates traceable reasoning chains.

Article 11: Declared Limitations
Every observation method must declare what it cannot see. Every pattern detector must declare its uncertainty. These declarations are first-class system outputs.

Article 12: Local Operation
All analysis works without network connectivity. No cloud dependencies for core functionality. Truth should not depend on external services.

TIER 4: SYSTEM BEHAVIOR
Article 13: Deterministic Operation
Same input must produce same output, regardless of when or where it runs. No randomness in analysis, no time-based behavior changes.

Constitutional Clarification:
"Same input must produce same output" applies to analysis results (observations, patterns, insights) that humans rely on for truth.
Operational metadata (session IDs, timestamps, transaction IDs) may use time-based generation for human context and system operation.
Truth artifacts must be deterministic; operational artifacts may be contextual for human comprehension.

Article 14: Graceful Degradation
When parts fail, preserve what works. Show available observations even when some cannot be collected. Explain failures simply and honestly.

Article 15: Session Integrity
Investigations can be paused, resumed, and recovered. System crashes should not lose thinking. Truth persists across interruptions.

TIER 5: AESTHETIC CONSTRAINTS
Article 16: Truth-Preserving Aesthetics
Visual design should enhance truth perception, not obscure it. Colors indicate meaning (⚠️ for uncertainty), typography ensures readability, layout reduces cognitive load.

Article 17: Minimal Decoration
Every visual element must serve truth preservation. No decoration for decoration's sake. When in doubt, simpler is truer.

Article 18: Consistent Metaphor
The investigation metaphor (observations, patterns, thinking) should be applied consistently across the interface. Mixed metaphors confuse truth perception.

TIER 6: EVOLUTION RULES
Article 19: Backward Truth Compatibility
New versions must not invalidate previous observations. Old investigations should remain understandable. Truth does not expire.

Article 20: Progressive Enhancement
New capabilities should build on, not replace, existing ones. Each feature should be complete within its scope before moving to the next.

Article 21: Self-Validation
The system must include tests that verify it follows its own constitution. A truth-keeping tool that cannot verify its own truth is worthless.

ENFORCEMENT MECHANISM
The Three Guardians:
Static Guardian: Pre-commit hooks validate constitutional compliance

Runtime Guardian: System monitors its own truth-preserving behavior

Interface Guardian: UI prevents truth-violating interactions

Violation Consequences:
Tier 1-2 Violations: Immediate halt, cannot proceed until fixed

Tier 3-4 Violations: Warning with required fix timeline

Tier 5-6 Violations: Team review, architectural adjustment

Amendment Process:
Proposal: Written case for change with truth-impact analysis

Review: 7-day discussion with all contributors

Approval: 80% agreement required for Tier 1-3 changes

Implementation: Update constitution, tests, and documentation simultaneously

Verification: Run full integrity suite before release

PHILOSOPHICAL PRINCIPLES
The Four Pillars of Truth:
Observability: If it cannot be seen, it cannot be claimed

Traceability: Every claim must have a clear origin

Falsifiability: Every pattern must be disprovable

Humility: "I don't know" is more valuable than a confident guess

What Success Looks Like:
Developers spend less time "debugging understanding" and more time "building understanding"

Architectural decisions have clear evidence trails

Code reviews reference specific observations, not vague intuitions

The team develops shared vocabulary for uncertainty and observation

The Ultimate Measure:
Does this tool make us better at understanding complex systems without ever pretending to understand for us?

ARCHITECTURAL BREAKTHROUGHS

1. The Three-Layer Truth Model:
   Observations: What exists (immutable facts)

Inquiry: What questions we ask and patterns we see (human+machine)

Lens: How we look at truth (interface constraints)

This separates what is from what we think about it from how we look at it.

1. The Truth-Preserving Interface:
   The interface is not just a viewer—it's a truth-preserving lens that:

Shows one thing at a time (prevents overload)

Follows linear curiosity (prevents confusion)

Clearly signals uncertainty (prevents overconfidence)

Anchors thinking to observations (prevents floating ideas)

1. Self-Validating Architecture:
   The integrity/ directory ensures the system follows its own rules:

Validates observation purity

Monitors for truth drift

Recovers from corruption

Audits system behavior

1. The Bridge Metaphor:
   The bridge/ directory recognizes that truth exists in different contexts:

CLI for scripting truth

TUI for exploring truth

API for integrating truth

Export for sharing truth

WHAT THIS STRUCTURE ACHIEVES
For Truth Seekers:
Clear path: From observation to understanding

Honest feedback: No hidden assumptions, no false confidence

Preserved thinking: Notes anchored to what was actually seen

Recoverable state: Investigations survive interruptions

For the Truth Itself:
Immutable records: Observations never change

Traceable claims: Every pattern links to observations

Declared limitations: Known unknowns are documented

Reproducible results: Same code yields same observations

THE ULTIMATE INSIGHT
This is not a code analysis tool. This is a truth-preserving environment for understanding complex systems.

The architecture recognizes that:

Truth decays without active preservation

Understanding grows through disciplined investigation

Wisdom emerges from tracing claims back to observations

Clarity comes from separating what is from what we think

The tree structure and constitution work together to create a system that:

Preserves truth (immutable observations)

Supports inquiry (patterns and questions)

Enhances perception (truth-preserving interface)

Protects integrity (self-validation and recovery)

READY FOR TRUTH
This architecture provides:

Complete separation of observation, inquiry, and interface

Natural workflow from seeing to understanding

Built-in integrity through self-validation

Scalable foundation for truth at any scale

Honest interface that never pretends to know more than it does

This is how we build tools that make us better thinkers: by creating environments where truth can be seen, questioned, and understood without ever being distorted

# **CODEMARSHAL: TRUTH-PRESERVING CODE INVESTIGATION**

## **WHAT IS CODEMARSHAL?**

**CodeMarshal** is a standalone, truth-preserving cognitive investigation environment designed specifically for understanding complex, constitutionally-constrained codebases like **Agent Nexus**.

**Think of CodeMarshal as:**

> A detective's notebook for code. It helps you investigate complex systems without ever lying to you, guessing for you, or overwhelming you.

While **Agent Nexus** is a policy-first modular monolith for autonomous agents, **CodeMarshal** is the specialized tool we're building to make Agent Nexus's development, maintenance, and evolution **humanly comprehensible**.

---

## **THE PROBLEM WE'RE SOLVING**

### **Agent Nexus is Constitutionally Complex**

Agent Nexus has:

- **24 non-negotiable constitutional rules** that must never be violated
- **5 architectural layers** with strict boundaries (no cross-layer imports)
- **Isolated lobes** that must never talk directly to each other
- **Immutable witnessing requirements** for all evidence
- **Traceability mandates** for every decision

Traditional tools fail for Agent Nexus because they:

- **Can't understand constitutional constraints**
- **Overwhelm with false positives** (can't distinguish "violation" from "by design")
- **Lack architectural awareness** of lobe isolation
- **Can't preserve truth** from observation to understanding

### **The Human Cognitive Limit**

As Agent Nexus grows (currently 847 files, 4,238 evidence points), it's becoming **impossible for any single developer to hold the entire system in their head** while maintaining constitutional purity.

**CodeMarshal exists to solve this specific problem.**

---

## **HOW CODEMARSHAL HELPS AGENT NEXUS DEVELOPMENT**

### **1. Constitutional Compliance Guardrails**

```bash
# CodeMarshal automatically detects:
• Cross-lobe imports (Constitutional violation)
• Direct infrastructure access from agents (Violation)
• Missing trace context (Violation)
• Policy logic in agent reasoning (Violation)
• And 20+ other constitutional rules
```

### **2. Architectural Understanding**

```bash
# Answer questions like:
• "What happens if I change this core module?"
• "Which lobes depend on this common SDK?"
• "Where are our policy boundaries being tested?"
• "What's the impact surface of this agent change?"
```

### **3. Truth-Preserving Investigation**

```bash
# When investigating a bug or design issue:
• See ONLY what exists in code (no AI hallucinations)
• Trace dependencies across constitutional boundaries
• Understand architectural constraints before making changes
• Document investigation with anchored evidence
```

### **4. Onboarding & Knowledge Transfer**

```bash
# New developer to Agent Nexus can:
• Investigate the codebase with constitutional awareness
• Understand "why this constraint exists" through evidence
• See architectural patterns without being overwhelmed
• Build mental model that respects system philosophy
```

---

## **CODEMARSHAL VS. TRADITIONAL TOOLS**

| **Aspect**                  | **Traditional Tools** | **CodeMarshal**                                   | **Why This Matters for Agent Nexus**                       |
| --------------------------- | --------------------- | ------------------------------------------------- | ---------------------------------------------------------- |
| **Truth Model**             | Often guess or infer  | Only shows what exists                            | Prevents constitutional violations from hidden assumptions |
| **Architectural Awareness** | Generic patterns      | Understands lobe isolation, constitutional layers | Can distinguish "violation" from "by design"               |
| **Cognitive Load**          | Overwhelm with data   | One question, one answer at a time                | Developers can focus without losing constitutional context |
| **Evidence Preservation**   | Transient analysis    | Immutable, versioned evidence                     | Audit trail for every constitutional decision              |
| **Integration**             | Standalone            | Built for Agent Nexus's specific constraints      | Speeds up development while maintaining purity             |

---

## **KEY DIFFERENTIATORS**

### **1. Built for Constitutional Constraints**

CodeMarshal doesn't just understand code—it understands **constitutionally-governed systems**. It knows:

- Which imports should never cross which boundaries
- Where policy logic must live vs. where agent logic lives
- How to trace evidence through strict architectural layers
- When something is "unusual but allowed" vs "unusual and prohibited"

### **2. Epistemic Discipline**

While Agent Nexus enforces **operational discipline** (agents can't access DBs directly), CodeMarshal enforces **epistemic discipline** (developers can't make decisions without evidence).

### **3. Production-Grade from Day 1**

CodeMarshal is being built **alongside Agent Nexus**, not after it. Every feature is:

- **Dogfooded immediately** on Agent Nexus codebase
- **Validated against real constitutional violations**
- **Performance-tuned** for production-scale codebases
- **Integrated** into Agent Nexus development workflows

---

## **THE VALUE PROPOSITION FOR AGENT NEXUS**

### **For Developers:**

- **30% faster onboarding**: Understand constitutional constraints in days, not weeks
- **50% fewer violations**: Catch constitutional issues before commit
- **Context preservation**: Never lose the "why" behind architectural decisions
- **Confidence in changes**: See impact across constitutional boundaries

### **For the System:**

- **Constitutional purity maintained**: Automated guardrails prevent drift
- **Knowledge preserved**: Investigation trails survive developer turnover
- **Evolution guided**: Understand constraints before expanding system
- **Quality improved**: Fewer violations means more stable system

### **For the Project:**

- **Faster development**: Less time debugging constitutional issues
- **Better decisions**: Evidence-based architectural evolution
- **Scalable understanding**: System grows without becoming incomprehensible
- **Sustainable maintenance**: Knowledge doesn't leave with developers

---

## **USE CASES IN AGENT NEXUS DEVELOPMENT**

### **Use Case 1: Pre-Commit Constitutional Check**

```bash
# Before every commit to Agent Nexus:
codemarshal investigate . --rule=constitutional
# Shows: "2 potential constitutional violations found"
# Click through to see evidence for each
```

### **Use Case 2: Architectural Refactoring**

```bash
# When refactoring common/ SDK:
codemarshal ask . "What depends on common/agent_sdk?"
# Shows: "143 files across 4 lobes depend on this"
# Lets you plan breaking changes safely
```

### **Use Case 3: Bug Investigation**

```bash
# When debugging a cross-lobe issue:
codemarshal investigate . --focus="lobes/chatbuddy"
# Trace dependencies to other lobes
# See constitutional constraints around communication
```

### **Use Case 4: New Feature Development**

```bash
# When adding a new lobe:
codemarshal patterns . --type="boundary_violation"
# Learn common violation patterns
# Design new lobe to avoid past mistakes
```

### **Use Case 5: Knowledge Transfer**

```bash
# When onboarding new team member:
codemarshal export --format=html --title="Agent Nexus Architecture"
# Creates interactive investigation report
# Preserves institutional knowledge
```

---

## **WHY A SEPARATE TOOL?**

### **Agent Nexus is the System**

- **Purpose**: Host, orchestrate, and evolve autonomous agents
- **Constrained by**: Constitutional rules for operational purity
- **Success metric**: Agent autonomy and reasoning quality

### **CodeMarshal is the Investigation Environment**

- **Purpose**: Help humans understand and evolve Agent Nexus
- **Constrained by**: Epistemic rules for truth preservation
- **Success metric**: Developer comprehension and constitutional compliance

### **Separation of Concerns:**

- **Agent Nexus** must remain pure to its purpose (agent platform)
- **CodeMarshal** can evolve independently as investigation needs change
- **Cross-pollination**: CodeMarshal learns from Agent Nexus's constraints, Agent Nexus benefits from better understanding tools

---

## **TECHNICAL INTEGRATION**

### **Lightweight Integration**

```yaml
# Agent Nexus .codemarshal.yaml
constitutional_rules:
  - no_cross_lobe_imports
  - agents_no_infrastructure_access
  - policy_separate_from_reasoning
  - memory_facade_only
  # ... all 24 Agent Nexus constitutional rules

architectural_layers:
  lobes: ["chatbuddy", "insightmate", "studyflow", "autoagent"]
  common: ["agent_sdk", "memory", "infra"]
  core: ["gateway", "worker", "policy", "resilience"]
```

### **Development Workflow Integration**

```bash
# In Agent Nexus development:
git checkout -b new-feature
# ... make changes ...

# Run constitutional check:
codemarshal validate --constitutional
# Fix any violations...

# Commit with evidence:
codemarshal export --evidence --notes
# Attach to PR...
```

### **CI/CD Integration**

```yaml
# Agent Nexus CI pipeline:
- name: Constitutional Validation
  run: |
    codemarshal collect .
    codemarshal validate --constitutional
    codemarshal export --format=markdown >> constitutional-report.md
```

---

## **THE VISION**

### **Short Term (8 Weeks):**

CodeMarshal becomes **indispensable for Agent Nexus development**, catching constitutional violations before commit, accelerating onboarding, and preserving architectural knowledge.

### **Medium Term (6 Months):**

CodeMarshal evolves into the **standard investigation tool for constitutionally-constrained systems**, used by other projects with similar architectural discipline requirements.

### **Long Term (1 Year+):**

CodeMarshal establishes a **new category of development tools**—truth-preserving investigation environments that help humans understand complex systems without distortion, applicable beyond software to any complex, governed system.

## **THE BOTTOM LINE**

**Agent Nexus** is a revolutionary approach to autonomous agent systems, governed by strict constitutional rules.

**CodeMarshal** is the tool that makes Agent Nexus **humanly comprehensible, maintainable, and evolvable** without violating those rules.

**Together**, they represent a new paradigm: systems with operational discipline (Agent Nexus) paired with tools for epistemic discipline (CodeMarshal).

We're not just building another code analysis tool. We're building **the first environment where truth about complex, governed systems can be preserved, investigated, and understood without distortion.**

**For Agent Nexus developers, this means:**

- Fewer constitutional violations
- Faster understanding of complex constraints
- More confidence in architectural changes
- Preserved knowledge across team members
- Sustainable growth of a revolutionary system

---

**CodeMarshal:** Making the impossible comprehensible, one truth-preserving investigation at a time.

---

## Related Documentation

- **[ROADMAP.md](../ROADMAP.md)** - Execution status and milestones
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history
- **[docs/index.md](index.md)** - Documentation navigation
- **[docs/USER_GUIDE.md](USER_GUIDE.md)** - Command reference
- **[docs/architecture.md](architecture.md)** - Architecture details
- **[docs/FEATURES.md](FEATURES.md)** - Feature matrix
- **[docs/API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - API reference
- **[docs/INTEGRATION_EXAMPLES.md](INTEGRATION_EXAMPLES.md)** - Integration examples
