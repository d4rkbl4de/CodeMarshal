package codemarshal

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.components.service
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import java.io.File

abstract class CodeMarshalActionBase(private val actionTitle: String) : AnAction(actionTitle) {
    protected fun currentFilePath(project: Project): String? {
        val editor = FileEditorManager.getInstance(project).selectedEditor ?: return null
        return editor.file?.path
    }

    protected fun writeOutput(project: Project, output: String) {
        val textArea = CodeMarshalToolWindowState.get(project) ?: return
        textArea.text = output
        textArea.caretPosition = 0
    }

    protected fun writeError(project: Project, message: String) {
        writeOutput(project, "CodeMarshal Error\n$message")
    }

    protected fun runCommand(
        project: Project,
        taskTitle: String,
        argsProvider: () -> List<String>,
        onSuccessMessage: String
    ) {
        val cliService = project.getService(CodeMarshalService::class.java)
        if (!cliService.isValidCliPath()) {
            writeError(project, "CodeMarshal CLI is not configured or not executable.")
            return
        }

        ProgressManager.getInstance().run(object : Task.Backgroundable(project, taskTitle, true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.text = "$taskTitle..."
                    val output = cliService.runCli(argsProvider()) { line ->
                        indicator.text = line.take(120)
                    }
                    writeOutput(project, formatOutput(output).ifBlank { onSuccessMessage })
                } catch (e: CodeMarshalException) {
                    writeError(project, e.message ?: "Unknown CodeMarshal error.")
                } catch (e: Exception) {
                    writeError(project, "Unexpected error: ${e.message}")
                }
            }
        })
    }

    private fun formatOutput(text: String): String = text
}

class CodeMarshalInvestigateAction : CodeMarshalActionBase("CodeMarshal: Investigate") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val settings = service<CodeMarshalSettings>()
        val filePath = currentFilePath(project)
        val target = filePath?.let { File(it).parentFile?.path } ?: project.basePath
        if (target.isNullOrBlank()) {
            writeError(project, "No target selected. Open a file or folder first.")
            return
        }

        runCommand(
            project = project,
            taskTitle = "CodeMarshal: Investigating",
            argsProvider = {
                listOf(
                    "investigate",
                    target,
                    "--scope=${settings.scanScope}",
                    "--intent=initial_scan",
                    "--output=${settings.scanOutputFormat}"
                )
            },
            onSuccessMessage = "Investigation completed."
        )
    }
}

class CodeMarshalPatternScanAction : CodeMarshalActionBase("CodeMarshal: Scan Patterns") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val settings = service<CodeMarshalSettings>()
        val filePath = currentFilePath(project)
        if (filePath.isNullOrBlank()) {
            writeError(project, "No file selected. Open a file to scan.")
            return
        }

        runCommand(
            project = project,
            taskTitle = "CodeMarshal: Scanning Patterns",
            argsProvider = {
                listOf(
                    "pattern",
                    "scan",
                    filePath,
                    "--output=${settings.scanOutputFormat}"
                )
            },
            onSuccessMessage = "Pattern scan completed."
        )
    }
}

class CodeMarshalObserveAction : CodeMarshalActionBase("CodeMarshal: Observe") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val settings = service<CodeMarshalSettings>()
        val target = currentFilePath(project) ?: project.basePath
        if (target.isNullOrBlank()) {
            writeError(project, "No target selected. Open a file or folder first.")
            return
        }

        runCommand(
            project = project,
            taskTitle = "CodeMarshal: Observing",
            argsProvider = {
                listOf(
                    "observe",
                    target,
                    "--scope=${settings.scanScope}",
                    "--output=${settings.scanOutputFormat}"
                )
            },
            onSuccessMessage = "Observation completed."
        )
    }
}

class CodeMarshalListPatternsAction : CodeMarshalActionBase("CodeMarshal: List Patterns") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val settings = service<CodeMarshalSettings>()
        runCommand(
            project = project,
            taskTitle = "CodeMarshal: Listing Patterns",
            argsProvider = { listOf("pattern", "list", "--output=${settings.scanOutputFormat}") },
            onSuccessMessage = "Pattern list retrieved."
        )
    }
}

class CodeMarshalQueryAction : CodeMarshalActionBase("CodeMarshal: Query") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val settings = service<CodeMarshalSettings>()

        val queryTarget = Messages.showInputDialog(
            project,
            "Enter query target (for example: latest):",
            "CodeMarshal Query",
            null,
            "latest",
            null
        )
        if (queryTarget.isNullOrBlank()) {
            writeError(project, "Query target cannot be empty.")
            return
        }

        val question = Messages.showInputDialog(
            project,
            "Enter your question:",
            "CodeMarshal Query",
            null,
            "Tell me about this code.",
            null
        )
        if (question.isNullOrBlank()) {
            writeError(project, "Question cannot be empty.")
            return
        }

        runCommand(
            project = project,
            taskTitle = "CodeMarshal: Querying",
            argsProvider = {
                listOf(
                    "query",
                    queryTarget,
                    "--question=$question",
                    "--output=${settings.scanOutputFormat}"
                )
            },
            onSuccessMessage = "Query completed."
        )
    }
}
