package codemarshal

import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import com.intellij.util.ui.UIUtil
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

@Service
class CodeMarshalService(private val project: Project) {
    private val logger = com.intellij.openapi.diagnostic.Logger.getInstance(CodeMarshalService::class.java)

    fun runCli(
        args: List<String>,
        timeout: Long = 60000,
        progressListener: ((String) -> Unit)? = null
    ): String {
        val cliPath = getCliPath()
        val baseDir = project.basePath?.let { File(it) }

        if (!File(cliPath).exists()) {
            throw CodeMarshalException("CodeMarshal CLI not found at: $cliPath")
        }

        if (baseDir == null) {
            throw CodeMarshalException("No project base directory found")
        }

        try {
            val process = ProcessBuilder(listOf(cliPath) + args)
                .directory(baseDir)
                .redirectErrorStream(true)
                .start()

            val reader = BufferedReader(InputStreamReader(process.inputStream))
            var output = StringBuilder()
            var line: String?

            while (reader.readLine().also { line = it } != null) {
                output.append(line).append("\n")
                progressListener?.invoke(line)
                Thread.sleep(10)
            }

            val exitCode = process.waitFor()

            if (exitCode != 0) {
                throw CodeMarshalException("CodeMarshal command failed with exit code $exitCode\nOutput: ${output.toString()}")
            }

            return output.toString().trim()
        } catch (e: InterruptedException) {
            process.destroyForcibly()
            throw CodeMarshalException("Command interrupted: ${e.message}", e)
        } catch (e: Exception) {
            throw CodeMarshalException("Failed to run CodeMarshal: ${e.message}", e)
        }
    }

    fun runCliAsync(
        args: List<String>,
        taskTitle: String = "CodeMarshal",
        onFinish: (Result<String>) -> Unit = {}
    ) {
        ProgressManager.getInstance().run(object : Task.Backgroundable(project, taskTitle, true) {
            override fun run(indicator: ProgressIndicator) {
                try {
                    indicator.setText("Running CodeMarshal command...")
                    indicator.fraction = 0.1
                    val output = runCli(args) { line ->
                        indicator.setText("Processing: $line")
                        indicator.fraction = 0.5
                    }
                    onFinish.invoke(Result.success(output))
                } catch (e: Exception) {
                    onFinish.invoke(Result.failure(CodeMarshalException("Operation failed", e)))
                }
            }

            override fun onFinished() {
                // Called automatically
            }
        })
    }

    private fun getCliPath(): String {
        return project.service<CodeMarshalSettings>().cliPath
    }

    fun getAvailableCommands(): List<String> {
        try {
            val output = runCli(listOf("--help"))
            return extractCommandsFromHelp(output)
        } catch (e: Exception) {
            logger.warn("Failed to get available commands: ${e.message}")
            return emptyList()
        }
    }

    private fun extractCommandsFromHelp(help: String): List<String> {
        val commands = mutableListOf<String>()
        val lines = help.split("\n")
        for (line in lines) {
            if (line.contains("Available commands:") || line.contains("Commands:")) {
                // Extract commands from the help output
                val commandPattern = Regex("""\s+(\w+):""")
                commandPattern.findAll(line).forEach { match ->
                    commands.add(match.groupValues[1])
                }
            }
        }
        return commands
    }

    fun isValidCliPath(): Boolean {
        val cliPath = getCliPath()
        return try {
            File(cliPath).exists() && File(cliPath).canExecute()
        } catch (e: Exception) {
            false
        }
    }
}

class CodeMarshalException(message: String, cause: Throwable? = null) : Exception(message, cause)

class CodeMarshalSettings {
    var cliPath: String = "codemarshal"
    var scanOnSave: Boolean = true
    var scanScope: String = "file"
    var scanOutputFormat: String = "json"
    var showWarnings: Boolean = true
    var showInfo: Boolean = true
    var debounceTime: Long = 500
}
