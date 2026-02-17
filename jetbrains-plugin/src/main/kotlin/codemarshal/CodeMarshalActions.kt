package codemarshal

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBTextArea
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.popup.JPopupFactory
import com.intellij.ui.speedSearch.TextComponentSpeedSearch
import com.intellij.util.ui.UIUtil
import java.io.File
import javax.swing.JPanel
import javax.swing.JSplitPane

abstract class CodeMarshalActionBase(private val title: String) : AnAction(title) {
    protected fun updateToolWindow(project: Project, output: String) {
        val textArea = CodeMarshalToolWindowState.get(project) ?: return
        textArea.text = output
        textArea.caretPosition = 0
    }

    protected fun currentFilePath(project: Project): String? {
        val editor = FileEditorManager.getInstance(project).selectedEditor ?: return null
        return editor.file?.path
    }

    protected fun showError(project: Project, message: String) {
        updateToolWindow(project, buildErrorOutput(message))
    }

    protected fun buildErrorOutput(message: String): String {
        return """CodeMarshal Error
════════════════════════════════════════════════════════════
$message
════════════════════════════════════════════════════════════
"""
    }

    protected fun buildSuccessOutput(message: String): String {
        return """CodeMarshal Success
════════════════════════════════════════════════════════════
$message
════════════════════════════════════════════════════════════
"""
    }

    protected fun formatJsonOutput(json: String): String {
        return try {
            val parsed = com.fasterxml.jackson.module.kotlin.jacksonObjectMapper()
                .readTree(json)
            com.fasterxml.jackson.module.kotlin.jacksonObjectMapper()
                .writerWithDefaultPrettyPrinter()
                .writeValueAsString(parsed)
        } catch (e: Exception) {
            json
        }
    }
}

class CodeMarshalInvestigateAction : CodeMarshalActionBase("CodeMarshal: Investigate") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)

        if (!service.isValidCliPath()) {
            showError(project, "CodeMarshal CLI is not properly configured. Please check settings.")
            return
        }

        val filePath = currentFilePath(project)
        val target = filePath?.let { File(it).parentFile?.path } ?: project.basePath

        if (target == null) {
            showError(project, "No target selected. Please open a file or folder first.")
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "CodeMarshal: Investigating", true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "CodeMarshal: Running investigation..."

                    val args = listOf(
                        "investigate",
                        target,
                        "--scope=${project.service<CodeMarshalSettings>().scanScope}",
                        "--intent=initial_scan",
                        "--output=json"
                    )

                    val output = service.runCli(args) { line ->
                        indicator.text = "Processing: $line"
                    }

                    val formatted = formatJsonOutput(output)
                    updateToolWindow(project, formatted)

                    if (formatted.contains("error") || formatted.contains("ERROR")) {
                        showError(project, "Investigation completed with errors. Check output for details.")
                    } else {
                        updateToolWindow(project, buildSuccessOutput("Investigation completed successfully."))
                    }
                } catch (e: CodeMarshalException) {
                    updateToolWindow(project, buildErrorOutput(e.message ?: "Unknown error"))
                } catch (e: Exception) {
                    updateToolWindow(project, buildErrorOutput("Unexpected error: ${e.message}"))
                }
            }
        })
    }
}

class CodeMarshalPatternScanAction : CodeMarshalActionBase("CodeMarshal: Scan Patterns") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)

        if (!service.isValidCliPath()) {
            showError(project, "CodeMarshal CLI is not properly configured. Please check settings.")
            return
        }

        val filePath = currentFilePath(project)

        if (filePath == null) {
            showError(project, "No file selected. Please open a file to scan.")
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "CodeMarshal: Scanning", true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "CodeMarshal: Running pattern scan..."

                    val args = listOf(
                        "pattern",
                        "scan",
                        filePath,
                        "--output=json",
                        "--format=${project.service<CodeMarshalSettings>().scanOutputFormat}"
                    )

                    val output = service.runCli(args) { line ->
                        indicator.text = "Processing: $line"
                    }

                    val formatted = formatJsonOutput(output)
                    updateToolWindow(project, formatted)

                    if (formatted.contains("error") || formatted.contains("ERROR")) {
                        showError(project, "Scan completed with errors. Check output for details.")
                    } else {
                        updateToolWindow(project, buildSuccessOutput("Pattern scan completed successfully."))
                    }
                } catch (e: CodeMarshalException) {
                    updateToolWindow(project, buildErrorOutput(e.message ?: "Unknown error"))
                } catch (e: Exception) {
                    updateToolWindow(project, buildErrorOutput("Unexpected error: ${e.message}"))
                }
            }
        })
    }
}

class CodeMarshalObserveAction : CodeMarshalActionBase("CodeMarshal: Observe") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)

        if (!service.isValidCliPath()) {
            showError(project, "CodeMarshal CLI is not properly configured. Please check settings.")
            return
        }

        val filePath = currentFilePath(project)
        val target = filePath ?: project.basePath

        if (target == null) {
            showError(project, "No target selected. Please open a file or folder first.")
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "CodeMarshal: Observing", true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "CodeMarshal: Running observation..."

                    val args = listOf(
                        "observe",
                        target,
                        "--scope=${project.service<CodeMarshalSettings>().scanScope}",
                        "--output=json"
                    )

                    val output = service.runCli(args) { line ->
                        indicator.text = "Processing: $line"
                    }

                    val formatted = formatJsonOutput(output)
                    updateToolWindow(project, formatted)

                    if (formatted.contains("error") || formatted.contains("ERROR")) {
                        showError(project, "Observation completed with errors. Check output for details.")
                    } else {
                        updateToolWindow(project, buildSuccessOutput("Observation completed successfully."))
                    }
                } catch (e: CodeMarshalException) {
                    updateToolWindow(project, buildErrorOutput(e.message ?: "Unknown error"))
                } catch (e: Exception) {
                    updateToolWindow(project, buildErrorOutput("Unexpected error: ${e.message}"))
                }
            }
        })
    }
}

class CodeMarshalListPatternsAction : CodeMarshalActionBase("CodeMarshal: List Patterns") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)

        if (!service.isValidCliPath()) {
            showError(project, "CodeMarshal CLI is not properly configured. Please check settings.")
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "CodeMarshal: Listing Patterns", true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "CodeMarshal: Fetching pattern list..."

                    val output = service.runCli(listOf("pattern", "list", "--output=json"))

                    updateToolWindow(project, output)

                    if (output.contains("error") || output.contains("ERROR")) {
                        showError(project, "Failed to list patterns. Check output for details.")
                    } else {
                        updateToolWindow(project, buildSuccessOutput("Pattern list retrieved successfully."))
                    }
                } catch (e: CodeMarshalException) {
                    updateToolWindow(project, buildErrorOutput(e.message ?: "Unknown error"))
                } catch (e: Exception) {
                    updateToolWindow(project, buildErrorOutput("Unexpected error: ${e.message}"))
                }
            }
        })
    }
}

class CodeMarshalQueryAction : CodeMarshalActionBase("CodeMarshal: Query") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)

        if (!service.isValidCliPath()) {
            showError(project, "CodeMarshal CLI is not properly configured. Please check settings.")
            return
        }

        val query = JPopupFactory.getInstance()
            .createBasicPopupBuilder(
                JPanel().apply {
                    add(JBLabel("Enter your query:"))
                    add(JBTextArea("latest").apply {
                        columns = 30
                        rows = 2
                        preferredSize = UIUtil.size(300, 50)
                        border = javax.swing.border.EmptyBorder(5, 5, 5, 5)
                    })
                }
            )
            .setResizable(true)
            .setMovable(true)
            .setTitle("CodeMarshal Query")
            .showInPopup()
            .selection.data

        if (query.isNullOrEmpty()) {
            showError(project, "Query cannot be empty.")
            return
        }

        val question = JPopupFactory.getInstance()
            .createBasicPopupBuilder(
                JPanel().apply {
                    add(JBLabel("Enter your question:"))
                    add(JBTextArea("Tell me about this code").apply {
                        columns = 30
                        rows = 3
                        preferredSize = UIUtil.size(300, 70)
                        border = javax.swing.border.EmptyBorder(5, 5, 5, 5)
                    })
                }
            )
            .setResizable(true)
            .setMovable(true)
            .setTitle("CodeMarshal Query")
            .showInPopup()
            .selection.data

        if (question.isNullOrEmpty()) {
            showError(project, "Question cannot be empty.")
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, "CodeMarshal: Querying", true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "CodeMarshal: Running query..."

                    val args = listOf(
                        "query",
                        query,
                        "--question=$question",
                        "--output=json"
                    )

                    val output = service.runCli(args) { line ->
                        indicator.text = "Processing: $line"
                    }

                    val formatted = formatJsonOutput(output)
                    updateToolWindow(project, formatted)

                    if (formatted.contains("error") || formatted.contains("ERROR")) {
                        showError(project, "Query completed with errors. Check output for details.")
                    } else {
                        updateToolWindow(project, buildSuccessOutput("Query completed successfully."))
                    }
                } catch (e: CodeMarshalException) {
                    updateToolWindow(project, buildErrorOutput(e.message ?: "Unknown error"))
                } catch (e: Exception) {
                    updateToolWindow(project, buildErrorOutput("Unexpected error: ${e.message}"))
                }
            }
        })
    }
}
