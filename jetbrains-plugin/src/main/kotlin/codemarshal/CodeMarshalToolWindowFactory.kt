package codemarshal

import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Key
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.openapi.options.ShowSettingsUtil
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextArea
import com.intellij.ui.content.ContentFactory
import java.awt.BorderLayout
import java.awt.FlowLayout
import javax.swing.JButton
import javax.swing.JPanel
import javax.swing.border.EmptyBorder

object CodeMarshalToolWindowState {
    private val key: Key<JBTextArea> = Key.create("codemarshal.toolwindow.textarea")

    fun set(project: Project, textArea: JBTextArea) {
        project.putUserData(key, textArea)
    }

    fun get(project: Project): JBTextArea? = project.getUserData(key)
}

class CodeMarshalToolWindowFactory : ToolWindowFactory {
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val outputArea = JBTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            text = "CodeMarshal output will appear here."
            border = EmptyBorder(8, 8, 8, 8)
        }
        CodeMarshalToolWindowState.set(project, outputArea)

        val controls = JPanel(FlowLayout(FlowLayout.LEFT, 8, 0)).apply {
            border = EmptyBorder(0, 0, 8, 0)
            add(JButton("Clear").apply {
                addActionListener { outputArea.text = "" }
            })
            add(JButton("Settings").apply {
                addActionListener {
                    ShowSettingsUtil.getInstance()
                        .showSettingsDialog(project, CodeMarshalSettingsConfigurable::class.java)
                }
            })
            add(JBLabel("Use Tools menu: CodeMarshal"))
        }

        val root = JPanel(BorderLayout(0, 0)).apply {
            border = EmptyBorder(10, 10, 10, 10)
            add(controls, BorderLayout.NORTH)
            add(JBScrollPane(outputArea), BorderLayout.CENTER)
        }

        val content = ContentFactory.getInstance().createContent(root, "", false)
        toolWindow.contentManager.addContent(content)
    }
}
