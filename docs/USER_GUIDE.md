# **CODEMARSHAL USER GUIDE**

**Version:** 0.1.0  
**Last Updated:** February 5, 2026  
**Status:** Production Ready

---

## **TABLE OF CONTENTS**

1. [When to Use CodeMarshal](#when-to-use-codemarshal)
2. [Quick Start](#quick-start)
3. [Terminal Commands Reference](#terminal-commands-reference)
4. [Detailed Usage Guide](#detailed-usage-guide)
5. [Query System](#query-system)
6. [Export System](#export-system)
7. [TUI (Text User Interface)](#tui-text-user-interface)
8. [Boundary Configuration](#boundary-configuration)
9. [Examples & Workflows](#examples--workflows)
10. [Troubleshooting](#troubleshooting)

---

## **WHEN TO USE CODEMARSHAL**

### **Perfect For:**

#### 1. **Onboarding to a New Codebase**

- Just joined a team? Use CodeMarshal to understand the architecture
- Learn module dependencies without reading every file
- Identify entry points and core components quickly

#### 2. **Code Reviews & Audits**

- Reviewing a large PR? Check for architectural violations
- Auditing legacy code? Find circular dependencies
- Due diligence on acquisition? Generate comprehensive reports

#### 3. **Refactoring Projects**

- Planning a major refactor? Map dependencies first
- Identifying dead code? Find orphan files
- Breaking monoliths? Visualize module boundaries

#### 4. **Architecture Reviews**

- Enforcing layer independence? Check boundary violations
- Documenting architecture? Export to markdown/HTML
- Onboarding documentation? Generate automatically

#### 5. **Troubleshooting Issues**

- Tracking down bugs? Follow dependency chains
- Understanding imports? Query specific modules
- Finding anomalies? Use pattern detection

### **Not Suitable For:**

- ❌ Runtime debugging (use a debugger)
- ❌ Performance profiling (use profilers)
- ❌ Dynamic analysis (CodeMarshal is static analysis only)

---

## **QUICK START**

### **Installation**

```bash
# Clone the repository
git clone https://github.com/codemarshal/codemarshal.git
cd codemarshal

# Install dependencies
pip install -e .

# Verify installation
codemarshal --help
```

### **Your First Investigation (30 seconds)**

```bash
# Navigate to any Python project
cd /path/to/your/project

# Start an investigation
codemarshal investigate . --scope=module --intent=initial_scan

# Query the investigation
codemarshal query investigation_<id> --question="What modules exist?" --question-type=structure

# Export results
codemarshal export investigation_<id> --format=markdown --output=my_report.md --confirm-overwrite
```

---

## **TERMINAL COMMANDS REFERENCE**

### **Command Overview**

CodeMarshal provides 5 main commands:

1. `investigate` - Create a tracked investigation
2. `observe` - Collect observations only
3. `query` - Ask questions about investigations
4. `export` - Export investigation results
5. `tui` - Launch interactive interface

---

### **1. INVESTIGATE COMMAND**

**Purpose:** Create a new investigation with a unique ID that tracks all observations, queries, and notes.

**Syntax:**

```bash
codemarshal investigate <path> [options]
```

**Required Arguments:**

- `<path>` - Path to directory or file to investigate

**Options:**

- `--scope=<level>` - Investigation scope: `file`, `module`, `package`, `project`
- `--intent=<type>` - Investigation purpose: `initial_scan`, `dependency_analysis`, `architecture_review`, `constitutional_check`
- `--name=<string>` - Custom name for the investigation
- `--confirm-large` - Confirm before investigating large codebases (>1000 files)

**Examples:**

```bash
# Basic investigation
codemarshal investigate .

# Specific scope
codemarshal investigate ./src --scope=package

# With intent
codemarshal investigate . --scope=project --intent=architecture_review --name="Project Audit"

# Large codebase with confirmation
codemarshal investigate . --scope=project --confirm-large
```

**Output:**

```
INVESTIGATION STARTED
================================================================================
ID:          investigation_1770293977936_0f331c82
Path:        /path/to/project
Scope:       project
Intent:      architecture_review
Status:      investigation_running

Next steps:
  codemarshal query investigation_1770293977936_0f331c82 --question='...'
  codemarshal export investigation_1770293977936_0f331c82 --format=markdown
================================================================================
```

---

### **2. OBSERVE COMMAND**

**Purpose:** Collect observations without creating a tracked investigation. Faster for quick checks.

**Syntax:**

```bash
codemarshal observe <path> [options]
```

**Required Arguments:**

- `<path>` - Path to observe

**Options:**

- `--scope=<level>` - Observation scope: `file`, `module`, `package`, `project`
- `--constitutional` - Enable constitutional analysis (boundary checking)

**Examples:**

```bash
# Quick observation
codemarshal observe .

# With constitutional analysis
codemarshal observe ./src --scope=module --constitutional

# Single file
codemarshal observe ./main.py --scope=file
```

**Output:**

```
OBSERVATION COLLECTED
================================================================================
Observation ID: obs_a52c4838bc43dde6
Status:         collecting
Target Path:    ./src
Session ID:     66104b0d-2809-42df-b094-d20cf86bbb6e
Types:          file_sight, import_sight, export_sight, boundary_sight

LIMITATIONS:
  file_sight:
    • no_inference
    • textual_only
    • immutable_once_recorded
================================================================================
```

---

### **3. QUERY COMMAND**

**Purpose:** Ask questions about an investigation and get fact-based answers.

**Syntax:**

```bash
codemarshal query <investigation_id> --question=<text> --question-type=<type> [options]
```

**Required Arguments:**

- `<investigation_id>` - ID from investigate command (e.g., `investigation_1770293977936_0f331c82`)
- `--question=<text>` - Your question as a string
- `--question-type=<type>` - Type of question (see below)

**Options:**

- `--limit=<number>` - Limit number of results (default: 50)
- `--focus=<path>` - Focus on specific file or directory

**Question Types:**

#### **structure** - Questions about code structure

Examples:

```bash
# What modules exist?
codemarshal query <id> --question="What modules exist?" --question-type=structure

# Directory structure
codemarshal query <id> --question="What is the directory structure?" --question-type=structure

# Files in specific directory
codemarshal query <id> --question="What files are in core/?" --question-type=structure
```

#### **connections** - Questions about dependencies

Examples:

```bash
# What depends on X?
codemarshal query <id> --question="What depends on core/engine.py?" --question-type=connections

# What does X import?
codemarshal query <id> --question="What does bridge/cli.py import?" --question-type=connections

# Show all dependencies
codemarshal query <id> --question="What are the dependencies?" --question-type=connections

# Circular dependencies
codemarshal query <id> --question="Show circular dependencies" --question-type=connections
```

#### **anomalies** - Questions about issues

Examples:

```bash
# General anomalies
codemarshal query <id> --question="Are there any anomalies?" --question-type=anomalies

# Boundary violations
codemarshal query <id> --question="Show me boundary violations" --question-type=anomalies

# Suspicious patterns
codemarshal query <id> --question="What looks suspicious?" --question-type=anomalies
```

#### **purpose** - Questions about what code does

Examples:

```bash
# Module purpose
codemarshal query <id> --question="What does core do?" --question-type=purpose

# Specific file
codemarshal query <id> --question="What is the purpose of bridge/commands.py?" --question-type=purpose
```

#### **thinking** - Questions for recommendations

Examples:

```bash
# Next steps
codemarshal query <id> --question="What should I investigate next?" --question-type=thinking

# Risks
codemarshal query <id> --question="What are the risks?" --question-type=thinking

# General analysis
codemarshal query <id> --question="What concerns you about this code?" --question-type=thinking
```

**Output Example:**

```
QUERY RESULT
================================================================================
Question:    What modules exist?
Type:        structure
Investigation: investigation_1770293977936_0f331c82

Answer:
Python Modules Information:
==================================================
Total Files Observed: 10

Paths Observed:
  • C:\project\core
  • C:\project\bridge
  • C:\project\observations

Contains approximately 10 files across 3 directories
================================================================================
```

---

### **4. EXPORT COMMAND**

**Purpose:** Export investigation results to various formats for sharing or further analysis.

**Syntax:**

```bash
codemarshal export <investigation_id> --format=<type> --output=<path> [options]
```

**Required Arguments:**

- `<investigation_id>` - Investigation ID to export
- `--format=<type>` - Export format: `json`, `markdown`, `html`, `plain`
- `--output=<path>` - Output file path

**Options:**

- `--confirm-overwrite` - Overwrite existing file without prompting
- `--include-notes` - Include investigation notes
- `--include-patterns` - Include detected patterns

**Export Formats:**

#### **JSON** - Structured data for programmatic use

```bash
codemarshal export <id> --format=json --output=report.json --confirm-overwrite
```

Output: Machine-readable JSON with investigation metadata, observations, and results

#### **Markdown** - Human-readable documentation

```bash
codemarshal export <id> --format=markdown --output=report.md --confirm-overwrite
```

Output: Formatted markdown report with sections for metadata, observations, and findings

#### **HTML** - Styled web report

```bash
codemarshal export <id> --format=html --output=report.html --confirm-overwrite
```

Output: Self-contained HTML file with CSS styling

#### **Plaintext** - Simple text format

```bash
codemarshal export <id> --format=plain --output=report.txt --confirm-overwrite
```

Output: Plain text with ASCII formatting

**Output:**

```
EXPORT COMPLETE
================================================================================
Export ID:      aea673d3-198b-4608-8012-53c53b277aaa
Format:         json
Output:         report.json
Size:           1.6K
================================================================================
```

---

### **5. TUI COMMAND**

**Purpose:** Launch the interactive Text User Interface for guided investigation.

**Syntax:**

```bash
codemarshal tui --path=<path>
```

**Options:**

- `--path=<path>` - Starting path (default: current directory)

**Examples:**

```bash
# Launch TUI in current directory
codemarshal tui

# Launch TUI in specific directory
codemarshal tui --path=./src
```

**TUI Controls:**

| Key   | Action                  | When Available      |
| ----- | ----------------------- | ------------------- |
| `q`   | Quit                    | Always              |
| `h`   | Help                    | Always              |
| `o`   | Observe                 | Initial state       |
| `s`   | Ask structural question | After observation   |
| `p`   | Analyze patterns        | After observation   |
| `n`   | Add note                | After observation   |
| `e`   | Export                  | After observation   |
| `y`   | Yes (confirm)           | During confirmation |
| `x`   | No (cancel)             | During confirmation |
| ↑/↓   | Navigate choices        | During selection    |
| Enter | Select/Confirm          | During input        |

**TUI Workflow:**

1. Start in AWAITING_PATH state
2. Press `o` to observe, enter path
3. After observation, use `s`, `p`, `n`, or `e`
4. Press `q` to quit

---

## **DETAILED USAGE GUIDE**

### **Complete Workflow Example**

```bash
# Step 1: Start an investigation
codemarshal investigate . --scope=project --intent=architecture_review --name="Codebase Audit"
# Note the investigation ID from output

# Step 2: Query for structure
codemarshal query investigation_<id> --question="What is the directory structure?" --question-type=structure

# Step 3: Query for dependencies
codemarshal query investigation_<id> --question="What are the main dependencies?" --question-type=connections

# Step 4: Check for issues
codemarshal query investigation_<id> --question="Are there any anomalies?" --question-type=anomalies

# Step 5: Get recommendations
codemarshal query investigation_<id> --question="What should I investigate next?" --question-type=thinking

# Step 6: Export comprehensive report
codemarshal export investigation_<id> --format=markdown --output=audit_report.md --confirm-overwrite --include-notes --include-patterns

# Step 7: View the report
cat audit_report.md
```

---

## **QUERY SYSTEM**

### **How It Works**

The query system uses specialized analyzers based on question type:

1. **StructureAnalyzer** - Analyzes file structure, directories, modules
2. **ConnectionMapper** - Maps imports and dependencies
3. **AnomalyDetector** - Finds boundary violations and suspicious patterns
4. **PurposeExtractor** - Extracts module purposes from exports
5. **ThinkingEngine** - Provides recommendations and analysis

### **Question Types in Detail**

#### **Structure Questions**

- "What modules exist?"
- "What is the directory structure?"
- "What files are in [directory]?"
- "Show me the structure"

**Use when:** You need to understand the layout of the codebase

#### **Connections Questions**

- "What depends on [module]?"
- "What does [module] import?"
- "Show import relationships"
- "Are there circular dependencies?"

**Use when:** You need to understand how components connect

#### **Anomalies Questions**

- "Are there any anomalies?"
- "Show me boundary violations"
- "What looks suspicious?"
- "Find code smells"

**Use when:** You want to find issues or violations

#### **Purpose Questions**

- "What does [module] do?"
- "What is the purpose of [file]?"
- "Explain [component]"

**Use when:** You need to understand what a specific component does

#### **Thinking Questions**

- "What should I investigate next?"
- "What are the risks?"
- "What concerns you about this code?"
- "Suggest next steps"

**Use when:** You want guidance on where to focus

---

## **EXPORT SYSTEM**

### **Export Format Details**

#### **JSON Export**

```json
{
  "export_metadata": {
    "version": "1.0",
    "exported_at": "2026-02-05T18:20:30",
    "format": "json",
    "tool": "CodeMarshal"
  },
  "investigation": {
    "id": "investigation_...",
    "path": "/path/to/project",
    "state": "presentation_complete"
  },
  "observations": [...],
  "notes": [...],
  "patterns": [...]
}
```

**Best for:** Programmatic analysis, CI/CD integration, further processing

#### **Markdown Export**

```markdown
# CodeMarshal Investigation Report

**Exported:** 2026-02-05 18:20:31
**Format:** Markdown

---

## Investigation Metadata

- **ID:** investigation\_...
- **Path:** /path/to/project
- **State:** presentation_complete

---

## Observations Summary

Total Observations: 1
```

**Best for:** Documentation, team sharing, README files

#### **HTML Export**

- Styled web page with tables
- Responsive layout
- Self-contained (no external dependencies)

**Best for:** Presentations, web sharing, visual reports

#### **Plaintext Export**

- ASCII formatted text
- Simple structure
- Maximum compatibility

**Best for:** Piping to other tools, terminal viewing

---

## **TUI (TEXT USER INTERFACE)**

### **When to Use TUI**

Use TUI when you want:

- Interactive exploration
- Guided investigation workflow
- Real-time observation collection
- Visual navigation

### **TUI vs CLI Commands**

| Feature        | CLI Commands              | TUI                    |
| -------------- | ------------------------- | ---------------------- |
| Speed          | Faster for specific tasks | Slower but more guided |
| Automation     | Scriptable                | Interactive only       |
| Exploration    | Command-based             | Visual navigation      |
| Learning Curve | Steeper                   | More intuitive         |
| Best For       | Repeated tasks, CI/CD     | Learning, exploration  |

### **TUI States**

1. **INITIAL** - Starting state
2. **AWAITING_PATH** - Waiting for path input
3. **OBSERVING** - Collecting observations
4. **QUESTIONING** - Asking questions
5. **PATTERN_ANALYSIS** - Analyzing patterns
6. **NOTING** - Taking notes
7. **EXPORTING** - Exporting results
8. **REFUSING** - Error state
9. **EXITING** - Shutting down

---

## **BOUNDARY CONFIGURATION**

### **What Are Boundaries?**

Boundaries enforce architectural rules:

- Which layers can import from which
- Cross-layer import restrictions
- Module isolation

### **Default Boundaries (agent_nexus.yaml)**

Located at: `config/agent_nexus.yaml`

**Layers:**

1. **core_layer** - Independent (no imports)
2. **bridge_layer** - Can access all layers
3. **observations_layer** - Config only
4. **inquiry_layer** - Core, observations, config, storage
5. **lens_layer** - Core, observations, inquiry, config
6. **storage_layer** - Config only
7. **config_layer** - Independent
8. **integrity_layer** - Core, bridge, observations, config

### **Checking Boundary Violations**

```bash
# Observe with constitutional analysis
codemarshal observe . --scope=module --constitutional

# Query for violations
codemarshal query <id> --question="Show me boundary violations" --question-type=anomalies
```

---

## **EXAMPLES & WORKFLOWS**

### **Example 1: New Developer Onboarding**

```bash
# Day 1: Understand structure
codemarshal investigate . --scope=project --intent=initial_scan --name="Onboarding"
# ID: investigation_123

# Get overview
codemarshal query investigation_123 --question="What is the directory structure?" --question-type=structure

# Understand main components
codemarshal query investigation_123 --question="What does the core module do?" --question-type=purpose
codemarshal query investigation_123 --question="What does the bridge module do?" --question-type=purpose

# Check dependencies
codemarshal query investigation_123 --question="What are the main dependencies?" --question-type=connections

# Export for reference
codemarshal export investigation_123 --format=markdown --output=onboarding_guide.md --confirm-overwrite
```

### **Example 2: Architecture Review**

```bash
# Start comprehensive review
codemarshal investigate . --scope=project --intent=architecture_review --name="Q1 Review"
# ID: investigation_456

# Check structure
codemarshal query investigation_456 --question="What modules exist?" --question-type=structure

# Analyze dependencies
codemarshal query investigation_456 --question="Show circular dependencies" --question-type=connections

# Find issues
codemarshal query investigation_456 --question="Are there any anomalies?" --question-type=anomalies
codemarshal query investigation_456 --question="Show me boundary violations" --question-type=anomalies

# Get recommendations
codemarshal query investigation_456 --question="What are the risks?" --question-type=thinking
codemarshal query investigation_456 --question="What should we refactor first?" --question-type=thinking

# Export full report
codemarshal export investigation_456 --format=html --output=architecture_review.html --confirm-overwrite --include-notes --include-patterns
```

### **Example 3: Refactoring Preparation**

```bash
# Before refactoring core/engine.py
codemarshal investigate ./core --scope=module --intent=dependency_analysis --name="Refactor Prep"
# ID: investigation_789

# What depends on it?
codemarshal query investigation_789 --question="What depends on core/engine.py?" --question-type=connections

# What does it depend on?
codemarshal query investigation_789 --question="What does core/engine.py import?" --question-type=connections

# Check for issues
codemarshal query investigation_789 --question="Are there any anomalies in core/?" --question-type=anomalies

# Export impact analysis
codemarshal export investigation_789 --format=json --output=refactor_impact.json --confirm-overwrite
```

---

## **TROUBLESHOOTING**

### **Common Issues**

#### **"Investigation not found"**

```bash
# Problem: Investigation ID doesn't exist
# Solution: Use the fallback - it will use most recent session
codemarshal query any_id --question="..."  # Falls back to latest

# Or list investigations:
ls storage/sessions/*.session.json
```

#### **"No answer provided"**

```bash
# Problem: Query might not have data
# Solution: Ensure you observed the path first
codemarshal observe <path> --scope=module
# Then query
```

#### **Export file not created**

```bash
# Problem: Permission or path issue
# Solution: Use --confirm-overwrite and check path
codemarshal export <id> --format=json --output=./report.json --confirm-overwrite
```

#### **TUI not available**

```bash
# Problem: windows-curses not installed
# Solution:
pip install windows-curses
```

### **Performance Tips**

```bash
# For large codebases, limit scope
codemarshal investigate ./src --scope=package --confirm-large

# Use targeted queries instead of full investigation
codemarshal query <id> --question="What depends on X?" --focus=./src/core

# Export only what you need
codemarshal export <id> --format=json --output=minimal.json  # Without --include-notes
```

---

## **CONSTITUTIONAL PRINCIPLES**

CodeMarshal operates under strict principles:

1. **Truth Preservation** - Only facts from source code
2. **No Inference** - Never guesses or assumes
3. **Human Primacy** - Your thinking, not AI interpretation
4. **Immutable Observations** - Evidence never changes
5. **Explicit Limitations** - Always shows what it cannot see

### **What This Means**

- ✅ CodeMarshal shows exactly what's in the code
- ✅ It won't interpret or guess intent
- ✅ You must draw your own conclusions
- ✅ All answers are grounded in observations
- ❌ It won't tell you "this is bad code"
- ❌ It won't suggest fixes (except boundaries)
- ❌ It won't make architectural decisions

---

## **COMMAND REFERENCE CARD**

# QUICK REFERENCE

Investigate:
codemarshal investigate <path> [--scope=level] [--intent=type] [--name=name]

Observe:
codemarshal observe <path> [--scope=level] [--constitutional]

Query:
codemarshal query <id> --question="..." --question-type=type
Types: structure, connections, anomalies, purpose, thinking

Export:
codemarshal export <id> --format=type --output=file [--confirm-overwrite]
Formats: json, markdown, html, plain

TUI:
codemarshal tui [--path=directory]

Help:
codemarshal --help
codemarshal <command> --help

---

**User Guide Version: 0.1.0**
**Last Updated: February 5, 2026**
**CodeMarshal Status: Production Ready**

For updates and examples, see: <https://github.com/d4rkblade/codemarshal>