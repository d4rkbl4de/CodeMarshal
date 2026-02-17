package codemarshal

import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Key
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextArea
import com.intellij.ui.content.ContentFactory
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBComboBox
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import javax.swing.JPanel
import javax.swing.JSplitPane
import javax.swing.SwingConstants
import javax.swing.border.EmptyBorder
import java.awt.BorderLayout
import java.awt.GridLayout
import java.awt.event.ActionEvent
import java.awt.event.ActionListener

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
        val rootPanel = JPanel(BorderLayout()).apply {
            border = EmptyBorder(10, 10, 10, 10)
            preferredSize = UIUtil.size(800, 600)
        }

        val toolbar = createToolbar(project)
        val splitPane = createSplitPane(project)

        rootPanel.add(toolbar, BorderLayout.NORTH)
        rootPanel.add(splitPane, BorderLayout.CENTER)

        val content = ContentFactory.getInstance().createContent(rootPanel, "CodeMarshal", false)
        toolWindow.contentManager.addContent(content)
        CodeMarshalToolWindowState.set(project, splitPane.bottomComponent as JBTextArea)
    }

    private fun createToolbar(project: Project): JPanel {
        val toolbar = JPanel(BorderLayout()).apply {
            border = EmptyBorder(0, 0, 10, 0)
        }

        val scanSettings = project.service<CodeMarshalSettings>()

        val settingsPanel = JPanel(GridLayout(2, 4, 5, 5)).apply {
            border = EmptyBorder(5, 5, 5, 5)
            add(JBLabel("CLI Path:"))
            add(JBTextField(scanSettings.cliPath).apply {
                border = EmptyBorder(3, 3, 3, 3)
                columns = 30
                border = EmptyBorder(3, 3, 3, 3)
            })
            add(JBLabel("Output Format:"))
            add(JBComboBox(arrayOf("json", "text")).apply {
                selectedItem = scanSettings.scanOutputFormat
                border = EmptyBorder(3, 3, 3, 3)
            })
        }

        toolbar.add(settingsPanel, BorderLayout.NORTH)

        val actionsPanel = JPanel(GridLayout(1, 3, 5, 5)).apply {
            border = EmptyBorder(5, 5, 5, 5)
            add(createActionButton(project, "Refresh", "Reload output"))
            add(createActionButton(project, "Clear", "Clear tool window"))
            add(createActionButton(project, "Settings", "Open settings"))
        }

        toolbar.add(actionsPanel, BorderLayout.SOUTH)

        return toolbar
    }

    private fun createSplitPane(project: Project): JSplitPane {
        val textArea = JBTextArea().apply {
            isEditable = false
            lineWrap = true
            wrapStyleWord = true
            font = font.deriveFont(14f)
            border = EmptyBorder(5, 5, 5, 5)
            addKeyListener(object : java.awt.event.KeyAdapter() {
                override fun keyPressed(e: java.awt.event.KeyEvent) {
                    if (e.keyCode == java.awt.event.KeyEvent.VK_F5) {
                        onRefresh(project)
                    }
                }
            })
        }

        val scrollPane = JBScrollPane(textArea).apply {
            border = EmptyBorder(0, 0, 0, 0)
        }

        val statusLabel = JBLabel("Ready").apply {
            border = EmptyBorder(5, 5, 5, 5)
            foreground = UIUtil.getLinkColor()
        }

        val statusPanel = JPanel(BorderLayout()).apply {
            add(statusLabel, BorderLayout.WEST)
            border = EmptyBorder(5, 5, 5, 5)
        }

        val panel = JPanel(BorderLayout()).apply {
            add(scrollPane, BorderLayout.CENTER)
            add(statusPanel, BorderLayout.SOUTH)
        }

        val splitPane = JSplitPane(JSplitPane.VERTICAL_SPLIT).apply {
            orientation = JSplitPane.VERTICAL_SPLIT
            topComponent = panel
            bottomComponent = JBLabel("Output area (press F5 to refresh)").apply {
                foreground = UIUtil.getLinkColor()
            }
            dividerLocation = 300
            isOneTouchExpandable = true
        }

        return splitPane
    }

    private fun createActionButton(project: Project, text: String, tooltip: String): com.intellij.icons.AllIcons.Actions.Button {
        val button = com.intellij.icons.AllIcons.Actions.Button().apply {
            val action = object : com.intellij.openapi.actionSystem.AnAction(text, tooltip, null) {
                override fun actionPerformed(e: com.intellij.openapi.actionSystem.AnActionEvent) {
                    when (text) {
                        "Refresh" -> onRefresh(project)
                        "Clear" -> onClear(project)
                        "Settings" -> onSettings(project)
                    }
                }
            }
            setEnabled(true)
        }

        return button
    }

    private fun onRefresh(project: Project) {
        val textArea = CodeMarshalToolWindowState.get(project) ?: return
        textArea.text = "Press a button to start..."
    }

    private fun onClear(project: Project) {
        val textArea = CodeMarshalToolWindowState.get(project) ?: return
        textArea.text = ""
    }

    private fun onSettings(project: Project) {
        project.service<CodeMarshalSettings>().showSettings()
    }
}
