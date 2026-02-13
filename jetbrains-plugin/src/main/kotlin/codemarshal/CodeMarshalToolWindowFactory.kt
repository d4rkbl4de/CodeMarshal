package codemarshal

import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Key
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextArea
import com.intellij.ui.content.ContentFactory

object CodeMarshalToolWindowState {
    val KEY: Key<JBTextArea> = Key.create("codemarshal.toolwindow.textarea")

    fun set(project: Project, textArea: JBTextArea) {
        project.putUserData(KEY, textArea)
    }

    fun get(project: Project): JBTextArea? {
        return project.getUserData(KEY)
    }
}

class CodeMarshalToolWindowFactory : ToolWindowFactory {
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val textArea = JBTextArea()
        textArea.isEditable = false

        val content = ContentFactory.getInstance().createContent(
            JBScrollPane(textArea),
            "CodeMarshal",
            false
        )
        toolWindow.contentManager.addContent(content)
        CodeMarshalToolWindowState.set(project, textArea)
    }
}
