package codemarshal

import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.util.concurrent.TimeUnit

@Service(Service.Level.PROJECT)
class CodeMarshalService(private val project: Project) {
    private val logger = Logger.getInstance(CodeMarshalService::class.java)

    fun runCli(
        args: List<String>,
        timeoutMs: Long = 60_000,
        progressListener: ((String) -> Unit)? = null
    ): String {
        val cliPath = service<CodeMarshalSettings>().cliPath
        if (cliPath.isBlank()) {
            throw CodeMarshalException("CodeMarshal CLI path is empty. Configure it in Settings.")
        }

        val baseDir = project.basePath?.let(::File)
            ?: throw CodeMarshalException("No project base directory found.")

        val cliFile = File(cliPath)
        if ((cliPath.contains("\\") || cliPath.contains("/")) && !cliFile.exists()) {
            throw CodeMarshalException("CodeMarshal CLI not found at: $cliPath")
        }

        var process: Process? = null
        return try {
            process = ProcessBuilder(listOf(cliPath) + args)
                .directory(baseDir)
                .redirectErrorStream(true)
                .start()

            val output = StringBuilder()
            BufferedReader(InputStreamReader(process.inputStream)).use { reader ->
                while (true) {
                    val line = reader.readLine() ?: break
                    output.append(line).append('\n')
                    progressListener?.invoke(line)
                }
            }

            val finished = process.waitFor(timeoutMs, TimeUnit.MILLISECONDS)
            if (!finished) {
                process.destroyForcibly()
                throw CodeMarshalException("CodeMarshal command timed out after ${timeoutMs}ms.")
            }

            val exitCode = process.exitValue()
            val stdout = output.toString().trim()
            if (exitCode != 0) {
                throw CodeMarshalException(
                    "CodeMarshal command failed with exit code $exitCode.\nOutput:\n$stdout"
                )
            }

            stdout
        } catch (e: CodeMarshalException) {
            throw e
        } catch (e: Exception) {
            logger.warn("Failed to run CodeMarshal CLI", e)
            throw CodeMarshalException("Failed to run CodeMarshal command.", e)
        } finally {
            process?.destroy()
        }
    }

    fun isValidCliPath(): Boolean {
        val cliPath = service<CodeMarshalSettings>().cliPath
        if (cliPath.isBlank()) {
            return false
        }

        return try {
            val command = if (System.getProperty("os.name").contains("Windows", ignoreCase = true)) {
                listOf("cmd", "/c", cliPath, "--help")
            } else {
                listOf(cliPath, "--help")
            }
            val process = ProcessBuilder(command)
                .directory(project.basePath?.let(::File))
                .redirectErrorStream(true)
                .start()
            val finished = process.waitFor(10, TimeUnit.SECONDS)
            finished && process.exitValue() == 0
        } catch (_: Exception) {
            false
        }
    }
}

class CodeMarshalException(message: String, cause: Throwable? = null) : Exception(message, cause)
