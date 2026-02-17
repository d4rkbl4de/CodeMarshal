package codemarshal

import com.intellij.openapi.options.SettingsScreen
import com.intellij.openapi.project.Project
import com.intellij.ui.JBColor
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.UIUtil
import java.awt.BorderLayout
import java.awt.Component
import java.awt.GridLayout
import javax.swing.JPanel
import javax.swing.border.EmptyBorder
import javax.swing.border.LineBorder

class CodeMarshalSettingsAction : com.intellij.openapi.actionSystem.AnAction("CodeMarshal Settings", "Open CodeMarshal settings", null) {
    override fun actionPerformed(e: com.intellij.openapi.actionSystem.AnActionEvent) {
        val project = e.project ?: return
        val settings = project.service<CodeMarshalSettings>()
        settings.showSettings()
    }
}

class CodeMarshalSettings {
    var cliPath: String = "codemarshal"
    var scanOnSave: Boolean = true
    var scanScope: String = "file"
    var scanOutputFormat: String = "json"
    var showWarnings: Boolean = true
    var showInfo: Boolean = true
    var debounceTime: Long = 500
    var maxHistoryItems: Int = 50
    var autoRefresh: Boolean = true

    fun showSettings() {
        val settingsWindow = com.intellij.openapi.options.ConfigurableExtensionHelper
            .showSettingsDialog("CodeMarshal", CodeMarshalSettingsConfigurable::class.java)
        settingsWindow?.show()
    }

    fun saveSettings() {
        // Settings are automatically persisted by JetBrains
    }
}

class CodeMarshalSettingsConfigurable : com.intellij.openapi.options.Configurable {
    private var mySettingsPanel: SettingsPanel? = null

    override fun createComponent(): Component? {
        mySettingsPanel = SettingsPanel()
        return mySettingsPanel
    }

    override fun isModified(): Boolean {
        return mySettingsPanel?.isModified() ?: false
    }

    override fun apply() {
        mySettingsPanel?.applySettings()
    }

    override fun reset() {
        mySettingsPanel?.resetSettings()
    }

    override fun getDisplayName(): String = "CodeMarshal"

    private inner class SettingsPanel : JPanel(BorderLayout()) {
        private val cliPathField = JBTextField(settings.cliPath).apply {
            columns = 30
        }

        private val scanScopeField = JBTextField(settings.scanScope).apply {
            columns = 10
        }

        private val outputFormatField = JBTextField(settings.scanOutputFormat).apply {
            columns = 10
        }

        private val debounceTimeField = JBTextField(settings.debounceTime.toString()).apply {
            columns = 10
        }

        init {
            border = EmptyBorder(10, 10, 10, 10)
            layout = BorderLayout(5, 5)

            val settingsPanel = JPanel(GridLayout(0, 2, 10, 10)).apply {
                add(JBLabel("CLI Path:"))
                add(cliPathField)
                add(JBLabel("Scan Scope:"))
                add(scanScopeField)
                add(JBLabel("Output Format:"))
                add(outputFormatField)
                add(JBLabel("Debounce Time (ms):"))
                add(debounceTimeField)
                border = EmptyBorder(10, 10, 10, 10)
            }

            val checkboxesPanel = JPanel(GridLayout(2, 2, 10, 10)).apply {
                add(JBCheckBox("Scan on Save", settings.scanOnSave))
                add(JBCheckBox("Show Warnings", settings.showWarnings))
                add(JBCheckBox("Show Info", settings.showInfo))
                add(JBCheckBox("Auto Refresh", settings.autoRefresh))
                border = EmptyBorder(10, 10, 10, 10)
            }

            add(settingsPanel, BorderLayout.NORTH)
            add(checkboxesPanel, BorderLayout.CENTER)

            add(JBLabel("Note: Changes require plugin reload to take effect.", JBColor.GRAY), BorderLayout.SOUTH)
            border = EmptyBorder(5, 5, 5, 5)
        }

        fun isModified(): Boolean {
            return cliPathField.text != settings.cliPath ||
                    scanScopeField.text != settings.scanScope ||
                    outputFormatField.text != settings.scanOutputFormat ||
                    debounceTimeField.text.toLongOrNull() != settings.debounceTime ||
                    !scanOnSaveCheckBox.isSelected ||
                    !showWarningsCheckBox.isSelected ||
                    !showInfoCheckBox.isSelected ||
                    !autoRefreshCheckBox.isSelected
        }

        fun applySettings() {
            settings.cliPath = cliPathField.text.trim()
            settings.scanScope = scanScopeField.text.trim()
            settings.scanOutputFormat = outputFormatField.text.trim()
            settings.debounceTime = debounceTimeField.text.toLongOrNull() ?: 500L
            settings.scanOnSave = scanOnSaveCheckBox.isSelected
            settings.showWarnings = showWarningsCheckBox.isSelected
            settings.showInfo = showInfoCheckBox.isSelected
            settings.autoRefresh = autoRefreshCheckBox.isSelected
        }

        fun resetSettings() {
            cliPathField.text = settings.cliPath
            scanScopeField.text = settings.scanScope
            outputFormatField.text = settings.scanOutputFormat
            debounceTimeField.text = settings.debounceTime.toString()
            scanOnSaveCheckBox.isSelected = settings.scanOnSave
            showWarningsCheckBox.isSelected = settings.showWarnings
            showInfoCheckBox.isSelected = settings.showInfo
            autoRefreshCheckBox.isSelected = settings.autoRefresh
        }
    }
}