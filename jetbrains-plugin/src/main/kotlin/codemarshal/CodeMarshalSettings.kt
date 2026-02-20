package codemarshal

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.service
import com.intellij.openapi.options.SearchableConfigurable
import com.intellij.openapi.options.ShowSettingsUtil
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBTextField
import java.awt.BorderLayout
import java.awt.GridLayout
import javax.swing.JComponent
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.border.EmptyBorder

@Service(Service.Level.APP)
@State(name = "CodeMarshalSettings", storages = [Storage("codemarshal.xml")])
class CodeMarshalSettings : PersistentStateComponent<CodeMarshalSettings.StateData> {
    data class StateData(
        var cliPath: String = "codemarshal",
        var scanOnSave: Boolean = true,
        var scanScope: String = "file",
        var scanOutputFormat: String = "json",
        var showWarnings: Boolean = true,
        var showInfo: Boolean = true,
        var debounceTimeMs: Int = 500,
        var autoRefresh: Boolean = true
    )

    private var state = StateData()

    override fun getState(): StateData = state

    override fun loadState(state: StateData) {
        this.state = state
    }

    var cliPath: String
        get() = state.cliPath
        set(value) {
            state.cliPath = value
        }

    var scanOnSave: Boolean
        get() = state.scanOnSave
        set(value) {
            state.scanOnSave = value
        }

    var scanScope: String
        get() = state.scanScope
        set(value) {
            state.scanScope = value
        }

    var scanOutputFormat: String
        get() = state.scanOutputFormat
        set(value) {
            state.scanOutputFormat = value
        }

    var showWarnings: Boolean
        get() = state.showWarnings
        set(value) {
            state.showWarnings = value
        }

    var showInfo: Boolean
        get() = state.showInfo
        set(value) {
            state.showInfo = value
        }

    var debounceTimeMs: Int
        get() = state.debounceTimeMs
        set(value) {
            state.debounceTimeMs = value
        }

    var autoRefresh: Boolean
        get() = state.autoRefresh
        set(value) {
            state.autoRefresh = value
        }
}

class CodeMarshalSettingsAction : AnAction("CodeMarshal Settings", "Open CodeMarshal settings", null) {
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project
        ShowSettingsUtil.getInstance().showSettingsDialog(project, CodeMarshalSettingsConfigurable::class.java)
    }
}

class CodeMarshalSettingsConfigurable : SearchableConfigurable {
    private var rootPanel: JPanel? = null
    private lateinit var cliPathField: JBTextField
    private lateinit var scanScopeField: JBTextField
    private lateinit var outputFormatField: JBTextField
    private lateinit var debounceField: JBTextField
    private lateinit var scanOnSaveCheckBox: JBCheckBox
    private lateinit var showWarningsCheckBox: JBCheckBox
    private lateinit var showInfoCheckBox: JBCheckBox
    private lateinit var autoRefreshCheckBox: JBCheckBox

    override fun getId(): String = "codemarshalSettings"

    override fun getDisplayName(): String = "CodeMarshal"

    override fun createComponent(): JComponent {
        val settings = service<CodeMarshalSettings>()

        cliPathField = JBTextField(settings.cliPath, 32)
        scanScopeField = JBTextField(settings.scanScope, 12)
        outputFormatField = JBTextField(settings.scanOutputFormat, 12)
        debounceField = JBTextField(settings.debounceTimeMs.toString(), 12)
        scanOnSaveCheckBox = JBCheckBox("Scan on Save", settings.scanOnSave)
        showWarningsCheckBox = JBCheckBox("Show Warnings", settings.showWarnings)
        showInfoCheckBox = JBCheckBox("Show Info", settings.showInfo)
        autoRefreshCheckBox = JBCheckBox("Auto Refresh", settings.autoRefresh)

        val fields = JPanel(GridLayout(0, 2, 8, 8)).apply {
            border = EmptyBorder(8, 8, 8, 8)
            add(JLabel("CLI Path"))
            add(cliPathField)
            add(JLabel("Scan Scope"))
            add(scanScopeField)
            add(JLabel("Output Format"))
            add(outputFormatField)
            add(JLabel("Debounce (ms)"))
            add(debounceField)
        }

        val flags = JPanel(GridLayout(0, 1, 8, 8)).apply {
            border = EmptyBorder(8, 8, 8, 8)
            add(scanOnSaveCheckBox)
            add(showWarningsCheckBox)
            add(showInfoCheckBox)
            add(autoRefreshCheckBox)
        }

        rootPanel = JPanel(BorderLayout(8, 8)).apply {
            border = EmptyBorder(12, 12, 12, 12)
            add(fields, BorderLayout.NORTH)
            add(flags, BorderLayout.CENTER)
        }

        return rootPanel as JPanel
    }

    override fun isModified(): Boolean {
        val settings = service<CodeMarshalSettings>()
        return cliPathField.text.trim() != settings.cliPath ||
            scanScopeField.text.trim() != settings.scanScope ||
            outputFormatField.text.trim() != settings.scanOutputFormat ||
            debounceField.text.trim().toIntOrNull() != settings.debounceTimeMs ||
            scanOnSaveCheckBox.isSelected != settings.scanOnSave ||
            showWarningsCheckBox.isSelected != settings.showWarnings ||
            showInfoCheckBox.isSelected != settings.showInfo ||
            autoRefreshCheckBox.isSelected != settings.autoRefresh
    }

    override fun apply() {
        val settings = service<CodeMarshalSettings>()
        settings.cliPath = cliPathField.text.trim().ifBlank { "codemarshal" }
        settings.scanScope = scanScopeField.text.trim().ifBlank { "file" }
        settings.scanOutputFormat = outputFormatField.text.trim().ifBlank { "json" }
        settings.debounceTimeMs = debounceField.text.trim().toIntOrNull() ?: 500
        settings.scanOnSave = scanOnSaveCheckBox.isSelected
        settings.showWarnings = showWarningsCheckBox.isSelected
        settings.showInfo = showInfoCheckBox.isSelected
        settings.autoRefresh = autoRefreshCheckBox.isSelected
    }

    override fun reset() {
        val settings = service<CodeMarshalSettings>()
        cliPathField.text = settings.cliPath
        scanScopeField.text = settings.scanScope
        outputFormatField.text = settings.scanOutputFormat
        debounceField.text = settings.debounceTimeMs.toString()
        scanOnSaveCheckBox.isSelected = settings.scanOnSave
        showWarningsCheckBox.isSelected = settings.showWarnings
        showInfoCheckBox.isSelected = settings.showInfo
        autoRefreshCheckBox.isSelected = settings.autoRefresh
    }

    override fun disposeUIResources() {
        rootPanel = null
    }
}
