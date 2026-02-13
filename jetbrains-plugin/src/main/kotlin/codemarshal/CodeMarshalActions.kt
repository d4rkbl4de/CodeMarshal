package codemarshal

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.fileEditor.FileEditorManager
import com.intellij.openapi.project.Project
import java.io.File

abstract class CodeMarshalActionBase(private val title: String) : AnAction(title) {
    protected fun updateToolWindow(project: Project, output: String) {
        val textArea = CodeMarshalToolWindowState.get(project)
        textArea?.text = output
    }

    protected fun currentFilePath(project: Project): String? {
        val editor = FileEditorManager.getInstance(project).selectedEditor
        return editor?.file?.path
    }
}

class CodeMarshalInvestigateAction : CodeMarshalActionBase("CodeMarshal: Investigate") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)
        val filePath = currentFilePath(project)
        val target = filePath?.let { File(it).parentFile?.path } ?: project.basePath
        if (target == null) {
            updateToolWindow(project, "No target selected.")
            return
        }
        val output = service.runCli(
            listOf("investigate", target, "--scope=module", "--intent=initial_scan")
        )
        updateToolWindow(project, output)
    }
}

class CodeMarshalPatternScanAction : CodeMarshalActionBase("CodeMarshal: Scan Patterns") {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val service = project.getService(CodeMarshalService::class.java)
        val filePath = currentFilePath(project)
        if (filePath == null) {
            updateToolWindow(project, "No file selected.")
            return
        }
        val output = service.runCli(
            listOf("pattern", "scan", filePath, "--output=json")
        )
        updateToolWindow(project, output)
    }
}
