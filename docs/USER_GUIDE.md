# **CODEMARSHAL USER GUIDE**

**Version:** 0.1.0  
**Last Updated:** January 16, 2026  

---

## **GETTING STARTED**

### **Installation**

#### **Option 1: Install from Source**
```bash
git clone https://github.com/codemarshal/codemarshal.git
cd codemarshal
pip install -e .
```

#### **Option 2: Install from PyPI (Future)**
```bash
pip install codemarshal
```

#### **Verify Installation**
```bash
codemarshal --version
codemarshal --help
```

---

## **QUICK START**

### **Your First Investigation**
```bash
# Start investigating your current codebase
codemarshal investigate .

# Start with a specific directory
codemarshal investigate ./src --scope=directory

# Get help at any time
codemarshal investigate --help
```

### **What You'll See**
```
🕵️ CODEMARSHAL - Investigating: my-project
────────────────────────────────────────────
📂 Case File: What exists here?
  ├─ src/ (4 directories, 142 files)
  ├─ tests/ (2 directories, 23 files)
  └─ docs/ (1 directory, 8 files)

────────────────────────────────────────────
[Enter] Inspect  [Q] Questions  [H] Hypotheses  [N] Notes  [B] Back
```

---

## **CORE CONCEPTS**

### **The Investigation Metaphor**
CodeMarshal uses a **detective investigation** metaphor:

- **🔍 Observe**: Collect evidence without interpretation
- **❓ Question**: Ask what exists and how it connects
- **🧠 Pattern**: Find relationships and anomalies
- **📝 Think**: Record your insights anchored to evidence
- **📋 Export**: Share your findings

### **Truth Preservation**
- **What you see**: Only facts from source code
- **What you think**: Your human insights, not AI guesses
- **No inference**: System never assumes or interprets
- **Immutable**: Evidence never changes once recorded

---

## **COMMAND LINE INTERFACE**

### **Basic Commands**

#### **Investigate**
```bash
# Basic investigation
codemarshal investigate <path>

# With options
codemarshal investigate <path> --scope=project --intent=initial_scan
codemarshal investigate <path> --depth=3 --confirm-large

# Common patterns
codemarshal investigate . --scope=directory      # What's here?
codemarshal investigate . --scope=dependencies   # How does it connect?
codemarshal investigate . --scope=patterns       # What patterns emerge?
```

#### **Export**
```bash
# Export investigation results
codemarshal export <session_id> --format=json --output=results.json
codemarshal export <session_id> --format=markdown --output=report.md
codemarshal export <session_id> --format=html --output=report.html

# Export with options
codemarshal export latest --format=json --output=results.json --confirm-overwrite
codemarshal export latest --include-evidence --include-notes
```

#### **Query**
```bash
# Ask specific questions
codemarshal query <path> "What are the main modules?"
codemarshal query <path> "What depends on core/engine.py?"
codemarshal query <path> "Show me circular dependencies"

# Query with analysis
codemarshal query <path> "What are the top-level modules?" --analyze
codemarshal query <path> "Find architectural boundaries" --scope=project
```

### **Advanced Options**

#### **Investigation Options**
```bash
--scope=<type>          # directory, dependencies, patterns, anomalies
--intent=<type>         # initial_scan, deep_analysis, specific_question
--depth=<number>         # How deep to explore (default: unlimited)
--confirm-large         # Warn for large codebases
--session=<name>        # Name this investigation session
```

#### **Export Options**
```bash
--format=<type>          # json, markdown, html, csv
--output=<path>         # Output file path
--include-evidence      # Include raw observations
--include-notes         # Include investigation notes
--include-timeline      # Include investigation timeline
--confirm-overwrite     # Overwrite existing files
```

---

## **INTERACTIVE TUI**

### **Navigation**
```
[Enter] Inspect     # Dive into selected item
[Q] Questions       # Ask questions about current view
[H] Hypotheses    # View detected patterns
[N] Notes          # Add/edit investigation notes
[B] Back           # Go back to previous view
[?] Help           # Show available commands
[Esc] Exit         # Save and exit investigation
```

### **Views**

#### **📂 Case File (Overview)**
- **What it shows**: Directory structure and statistics
- **When to use**: Start of investigation
- **Navigation**: Arrow keys to explore, Enter to inspect

#### **🔍 Evidence Room (Observations)**
- **What it shows**: File contents, imports, exports
- **When to use**: Understanding specific components
- **Navigation**: Tab between file types, Enter to view details

#### **🕸️ Connection Map (Dependencies)**
- **What it shows**: Import relationships and dependencies
- **When to use**: Understanding architecture
- **Navigation**: Arrow keys to explore graph, Enter for details

#### **🧠 Hypothesis Board (Patterns)**
- **What it shows**: Detected patterns with uncertainty indicators
- **When to use**: Finding architectural insights
- **Navigation**: Arrow keys to browse patterns, Enter for evidence

#### **📝 Detective's Notes (Thinking)**
- **What it shows**: Your investigation notes anchored to evidence
- **When to use**: Recording insights and decisions
- **Navigation**: Arrow keys to browse notes, Enter to edit

---

## **WORKFLOW EXAMPLES**

### **Example 1: Understanding a New Codebase**

#### **Step 1: Initial Reconnaissance**
```bash
# Start with broad overview
codemarshal investigate . --scope=directory --intent=initial_scan

# In TUI:
# 1. Browse Case File to understand structure
# 2. Look for main entry points
# 3. Identify key directories
```

#### **Step 2: Dependency Analysis**
```bash
# Focus on how components connect
codemarshal investigate . --scope=dependencies

# In TUI:
# 1. View Connection Map
# 2. Look for circular dependencies
# 3. Identify architectural layers
```

#### **Step 3: Pattern Detection**
```bash
# Find patterns and anomalies
codemarshal investigate . --scope=patterns

# In TUI:
# 1. Review Hypothesis Board
# 2. Look for ⚠️ uncertainty indicators
# 3. Investigate interesting patterns
```

#### **Step 4: Document Findings**
```bash
# Export your investigation
codemarshal export latest --format=markdown --include-evidence --include-notes

# Review the generated report
cat investigation_report.md
```

### **Example 2: Investigating a Specific Issue**

#### **Step 1: Targeted Investigation**
```bash
# Focus on specific component
codemarshal investigate ./src/core --scope=dependencies

# In TUI:
# 1. Use Evidence Room to examine core files
# 2. Use Connection Map to trace dependencies
# 3. Add notes about findings
```

#### **Step 2: Ask Specific Questions**
```bash
# Get targeted answers
codemarshal query ./src/core "What depends on engine.py?"
codemarshal query ./src/core "Are there circular dependencies?"

# Review the answers
codemarshal query ./src/core "Show me all entry points" --analyze
```

#### **Step 3: Export Focused Report**
```bash
# Export specific investigation
codemarshal export latest --format=json --output=core_analysis.json

# Use the data for further analysis
```

---

## **INVESTIGATION TECHNIQUES**

### **Reading the Codebase**

#### **Start with Structure**
1. **Case File**: Get the lay of the land
2. **Entry Points**: Find main(), __init__.py files
3. **Directory Organization**: Understand the architecture

#### **Follow Dependencies**
1. **Connection Map**: See how modules import each other
2. **Import Analysis**: Look for patterns in imports
3. **Layer Boundaries**: Identify architectural separation

#### **Look for Patterns**
1. **Hypothesis Board**: Review detected patterns
2. **Uncertainty Indicators**: Pay attention to ⚠️ markers
3. **Anomaly Detection**: Find unusual structures

### **Taking Notes**

#### **Anchor Everything**
- Always link notes to specific evidence
- Use the "Evidence → Question → Pattern → Note" flow
- Record your reasoning, not just conclusions

#### **Progressive Disclosure**
- Start broad, then dive deep
- One question at a time
- Don't jump between unrelated areas

### **Truth Preservation**

#### **What You See vs. What You Think**
- **Observations**: Facts from code (what exists)
- **Thinking**: Your insights (what it means)
- **No Inference**: System never guesses for you

#### **Handling Uncertainty**
- **⚠️ Markers**: Pay attention to uncertainty
- **"I Don't Know"**: It's OK to admit limits
- **Evidence-Based**: Always ground thoughts in evidence

---

## **CONFIGURATION**

### **Setting Up Your Environment**

#### **Configuration File**
Create `~/.codemarshal/config.yaml`:
```yaml
investigation:
  default_depth: 5
  max_file_size: 10MB
  auto_save: true
  
display:
  theme: dark
  show_line_numbers: true
  unicode_symbols: true
  
storage:
  base_path: ~/.codemarshal/investigations
  backup_enabled: true
  compression: gzip
```

#### **Environment Variables**
```bash
export CODEMARSHAL_CONFIG_PATH=~/.codemarshal/config.yaml
export CODEMARSHAL_STORAGE_PATH=~/.codemarshal/investigations
export CODEMARSHAL_LOG_LEVEL=INFO
```

### **Project-Specific Configuration**

Create `.codemarshal.yaml` in your project:
```yaml
project:
  name: "My Project"
  type: "python"
  
investigation:
  exclude_patterns:
    - "**/__pycache__/**"
    - "**/node_modules/**"
    - "**/.git/**"
  include_patterns:
    - "**/*.py"
    - "**/*.md"
    - "**/*.yaml"
  
constitutional:
  enforce_single_focus: true
  require_evidence_anchoring: true
  validate_observations: true
```

---

## **TROUBLESHOOTING**

### **Common Issues**

#### **"Cannot see this" Errors**
```
Problem: System reports it cannot observe certain files
Solution: 
1. Check file permissions
2. Verify file is text-based (not binary)
3. Check exclude patterns in config
```

#### **Investigation Too Slow**
```
Problem: Large codebase investigation is slow
Solution:
1. Use --depth to limit scope
2. Exclude unnecessary directories
3. Use targeted queries instead of full investigation
```

#### **Export Fails**
```
Problem: Export command fails
Solution:
1. Check output directory permissions
2. Verify session ID exists
3. Use --confirm-overwrite if file exists
```

#### **TUI Display Issues**
```
Problem: TUI display is garbled or unreadable
Solution:
1. Check terminal supports Unicode
2. Try --no-color flag
3. Verify terminal size (minimum 80x24)
```

### **Getting Help**

#### **Built-in Help**
```bash
# General help
codemarshal --help

# Command-specific help
codemarshal investigate --help
codemarshal export --help
codemarshal query --help
```

#### **Constitutional Validation**
```bash
# Check system compliance
python -m integrity.validation.complete_constitutional

# Check network prohibition
python -m integrity.prohibitions.network_prohibition

# Check crash recovery
python -m tests.crash_recovery
```

---

## **BEST PRACTICES**

### **Effective Investigation**

#### **1. Start Broad, Then Focus**
- Begin with directory structure
- Identify key components
- Dive deep into specific areas

#### **2. Follow the Evidence**
- Let observations guide your questions
- Ground all patterns in evidence
- Don't jump to conclusions

#### **3. Document Your Thinking**
- Take notes as you investigate
- Link notes to specific evidence
- Record your reasoning process

#### **4. Use Progressive Disclosure**
- One question at a time
- Don't overwhelm yourself
- Follow natural curiosity

### **Team Collaboration**

#### **Sharing Investigations**
```bash
# Export for team review
codemarshal export session_id --format=markdown --output=team_review.md

# Share specific insights
codemarshal query . "What are the main architectural decisions?" --output=decisions.json
```

#### **Consistent Investigation**
- Use consistent terminology
- Follow established patterns
- Document assumptions and constraints

### **Performance Tips**

#### **Large Codebases**
```bash
# Limit investigation scope
codemarshal investigate . --depth=3 --exclude="tests/**"

# Use targeted queries
codemarshal query ./src "What are the main modules?"

# Export incrementally
codemarshal export latest --format=json --output=partial_results.json
```

#### **Memory Management**
```bash
# Configure memory limits
export CODEMARSHAL_MAX_MEMORY=2GB

# Use streaming for large exports
codemarshal export latest --format=json --stream --output=large_export.json
```

---

## **ADVANCED FEATURES**

### **Custom Patterns**
```yaml
# .codemarshal.yaml
patterns:
  custom_rules:
    - name: "no_direct_db_access"
      description: "Database access must go through data layer"
      pattern: "import.*(sqlite3|psycopg2|mysql)"
      confidence: "medium"
    - name: "service_isolation"
      description: "Services must not import each other directly"
      pattern: "from services\\.(\\w+) import.*services\\.(?!\\1)"
      confidence: "high"
```

### **Integration Hooks**
```python
# Custom investigation hooks
import codemarshal

@codemarshal.hook("pre_investigation")
def before_investigation(path, context):
    print(f"Starting investigation of: {path}")
    return path, context

@codemarshal.hook("post_observation")
def after_observation(evidence):
    print(f"Collected {len(evidence)} observations")
    return evidence
```

---

## **KEYBOARD SHORTCUTS**

### **TUI Navigation**
```
Arrow Keys: Navigate lists and menus
Enter: Select item or dive deeper
Tab: Switch between panels
Esc: Go back or exit
/: Search in current view
n: Create new note
q: Quick question mode
h: Toggle help
F1: Comprehensive help
```

### **Search and Filter**
```
/: Open search bar
Ctrl+F: Find in current view
Ctrl+R: Recent investigations
Ctrl+S: Save current state
Ctrl+L: Clear filters
```

---

## **COMMUNITY AND SUPPORT**

### **Getting Help**
- **Documentation**: This guide and API documentation
- **Examples**: `docs/examples/` directory
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions

### **Contributing**
- **Code**: Follow contribution guidelines
- **Documentation**: Help improve this guide
- **Tests**: Add test cases for edge cases
- **Design**: Participate in architectural discussions

### **Staying Updated**
- **Releases**: Follow GitHub releases
- **Roadmap**: Check project milestones
- **Blog**: Follow development blog
- **Community**: Join discussions and forums

---

**User Guide Version: 0.1.0**  
**Last Updated: January 16, 2026**  
**Next Update: Based on user feedback and feature releases**
