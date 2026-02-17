# CodeMarshal JetBrains Plugin

Enhanced CodeMarshal IDE integration for JetBrains products (IntelliJ IDEA, PyCharm, WebStorm, etc.).

## Features

### Enhanced User Interface
- **Improved Tool Window Layout**: Split-pane design with separate output and status areas
- **Progress Indicators**: Real-time progress feedback for long-running operations
- **Better Error Handling**: Comprehensive error messages with actionable guidance
- **Configurable Settings**: Fine-grained control over CLI path, scan scope, and more
- **Context Menu Integration**: Quick access to actions from editor context menus
- **Keyboard Shortcuts**: F5 to refresh output area

### Additional Commands
1. **Investigate** - Run code investigation with real-time progress
2. **Observe** - Run code observation with detailed feedback
3. **Query** - Ask questions about code with dialog prompts
4. **List Patterns** - View all available pattern definitions
5. **Scan Patterns** - Scan current file with JSON output formatting
6. **Settings** - Configure plugin behavior and CLI path

### Configuration Options
- **CLI Path**: Custom path to CodeMarshal CLI executable
- **Scan Scope**: Default scope for investigations (file, module, package, project)
- **Output Format**: JSON or text output format
- **Scan on Save**: Auto-scan files when saved
- **Show Warnings/Info**: Control diagnostic visibility
- **Debounce Time**: Delay before scanning (milliseconds)
- **Auto Refresh**: Automatic UI updates

### Technical Improvements
- **Async Operations**: Background tasks with proper progress reporting
- **Error Recovery**: Retry logic and graceful error handling
- **JSON Formatting**: Auto-formatted JSON output with syntax highlighting
- **Status Bar**: Real-time operation status and match counts
- **Settings Management**: Persistent configuration with IDE settings dialog
- **Context Menu Actions**: File-specific actions accessible via right-click

## Installation

### From Source

1. **Prerequisites:**
   - Java 11 or higher
   - Kotlin 1.9.22
   - Gradle 8.x

2. **Build the plugin:**
   ```bash
   ./gradlew build
   ```

3. **Install in IntelliJ IDEA:**
   - Go to `Settings/Preferences` → `Plugins`
   - Click the gear icon ⚙️ → `Install Plugin from Disk...`
   - Select the built `.zip` file from `build/distributions/`
   - Restart IntelliJ IDEA

### From Marketplace

Coming soon to JetBrains Marketplace!

## Usage

### Basic Operations

1. **Open the CodeMarshal Tool Window**
   - View → CodeMarshal

2. **Scan Current File**
   - Tools → CodeMarshal → Scan Patterns
   - Right-click in editor → CodeMarshal → Scan Current File

3. **Investigate Code**
   - Tools → CodeMarshal → Investigate
   - Right-click → CodeMarshal → Investigate Current Scope

4. **Observe Code**
   - Tools → CodeMarshal → Observe
   - Right-click → CodeMarshal → Observe Current Scope

5. **Ask Questions**
   - Tools → CodeMarshal → Query
   - Provides dialog prompts for investigation ID and question

### Configuration

1. **Open Settings**
   - Tools → CodeMarshal → Settings
   - IntelliJ IDEA → Settings → Tools → CodeMarshal

2. **Configure CLI Path**
   - Set the path to your CodeMarshal CLI executable
   - Default: `codemarshal` (searches in PATH)

3. **Adjust Scan Settings**
   - Choose default scan scope (file, module, package, project)
   - Select output format (JSON, text)
   - Configure debounce time for file operations
   - Enable/disable auto-scan on save

### Output Format

### JSON Output Example
```json
{
  "investigation_id": "inv_123",
  "scope": "file",
  "intent": "initial_scan",
  "matches_found": 3,
  "matches": [
    {
      "pattern_id": "pattern_001",
      "pattern_name": "Security Issue",
      "severity": "critical",
      "message": "SQL injection detected",
      "line": 42,
      "file": "src/main.js"
    }
  ]
}
```

## Keyboard Shortcuts

- **F5**: Refresh output area
- **Ctrl+S**: Scan on save (if enabled)
- **Right-click**: Access context menu actions

## Command Reference

### CodeMarshal Actions

| Action | Description | Shortcut |
|--------|-------------|----------|
| Investigate | Run investigation on current scope | - |
| Observe | Run observation on current scope | - |
| Query | Ask a question about the code | - |
| List Patterns | Display all available patterns | - |
| Scan Patterns | Scan current file for patterns | - |
| Settings | Open configuration dialog | - |

### Context Menu Actions

| Action | Description | Location |
|--------|-------------|----------|
| Scan Current File | Scan currently open file | Editor popup, Navigation popup |
| Investigate Current Scope | Run investigation on scope | Editor popup, Navigation popup |
| Observe Current Scope | Run observation on scope | Editor popup, Navigation popup |

## Troubleshooting

### Plugin Not Loading

1. **Verify IntelliJ Version**: Plugin requires IntelliJ IDEA 2023.2 or higher
2. **Check Dependencies**: Ensure all required libraries are installed
3. **Restart IDE**: Sometimes required after installation

### CLI Not Found

1. **Verify CLI Path**: Go to Settings → CodeMarshal → Settings
2. **Check PATH**: Ensure `codemarshal` CLI is in system PATH
3. **Install CLI**: Download and install CodeMarshal CLI from official repository

### No Output in Tool Window

1. **Check Permissions**: Ensure write permissions in output directory
2. **Verify JSON Format**: Ensure CLI returns valid JSON output
3. **Enable Logs**: View IDE logs for detailed error messages

### Build Errors

1. **Java Version**: Ensure Java 11 or higher is installed
2. **Gradle Version**: Use Gradle 8.x or higher
3. **Dependencies**: Check for missing Maven dependencies

## Development

### Project Structure
```
jetbrains-plugin/
├── build.gradle.kts       # Gradle build configuration
├── settings.gradle.kts    # Gradle settings
├── src/
│   └── main/
│       ├── kotlin/codemarshal/
│       │   ├── CodeMarshalActions.kt       # Action implementations
│       │   ├── CodeMarshalService.kt        # CLI service layer
│       │   ├── CodeMarshalSettings.kt       # Configuration management
│       │   └── CodeMarshalToolWindowFactory.kt  # UI factory
│       └── resources/
│           └── META-INF/
│               └── plugin.xml                # Plugin manifest
```

### Building
```bash
# Build the plugin
./gradlew build

# Run tests
./gradlew test

# Run IntelliJ with plugin in development mode
./gradlew runIde

# Clean build artifacts
./gradlew clean
```

### Adding New Actions

1. Create a new action class extending `CodeMarshalActionBase`
2. Register the action in `plugin.xml` under appropriate group
3. Implement `actionPerformed` method
4. Add to context menus if needed

```kotlin
class MyNewAction : CodeMarshalActionBase("My New Action") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "Processing", true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    val output = service.runCli(listOf("my", "command"))
                    updateToolWindow(project, output)
                } catch (e: Exception) {
                    showError(project, e.message ?: "Unknown error")
                }
            }
        })
    }
}
```

## Known Limitations

1. **JSON Highlighting**: Basic syntax highlighting only (no advanced formatting)
2. **File Scanning**: Currently limited to single file operations
3. **Async Operations**: Some operations may block UI thread for extended periods
4. **Memory Usage**: Large outputs may consume significant memory
5. **Platform Support**: Primarily tested on Windows and macOS

## Future Enhancements

- [ ] Syntax highlighting for various languages
- [ ] Export results to file formats (CSV, JSON, HTML)
- [ ] Pattern filtering and search
- [ ] Integration with editor search functionality
- [ ] CodeLens support for pattern matches
- [ ] Inline diagnostics display
- [ ] Color-coded error highlighting
- [ ] History tracking for investigations
- [ ] Export functionality for results
- [ ] Mobile-responsive tool window

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See LICENSE file for details.

## Support

- **Documentation**: https://codemarshal.local/docs
- **Issues**: https://github.com/codemarshal/jetbrains-plugin/issues
- **Email**: support@codemarshal.local

## Changelog

### Version 1.0.0 (2026-02-15)

**Major Features:**
- Enhanced UI with split-pane tool window
- Progress indicators for all operations
- Comprehensive error handling and recovery
- Configuration settings dialog
- Multiple CLI command integrations
- Context menu integration
- JSON output formatting
- Status bar integration

**Technical Improvements:**
- Asynchronous operations with proper progress reporting
- Settings persistence
- Better error messages with actionable guidance
- Code quality improvements
- Dependency management with Gradle

**Bug Fixes:**
- Fixed CLI path validation
- Improved process management
- Enhanced UI responsiveness
- Better error handling throughout

**Breaking Changes:**
- Plugin version bumped to 1.0.0
- Tool window API changes
- Configuration format changes

## Credits

- JetBrains IntelliJ Platform Team for the plugin SDK
- CodeMarshal team for the CLI tool
- JetBrains Community for Kotlin support

---

**Note**: This plugin requires a valid CodeMarshal CLI installation to function properly.