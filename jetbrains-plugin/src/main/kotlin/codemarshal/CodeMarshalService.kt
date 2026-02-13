package codemarshal

import com.intellij.openapi.components.Service
import com.intellij.openapi.project.Project
import java.io.File

@Service
class CodeMarshalService(private val project: Project) {
    fun runCli(args: List<String>): String {
        val cliPath = "codemarshal"
        val baseDir = project.basePath?.let { File(it) }
        val process = ProcessBuilder(listOf(cliPath) + args)
            .directory(baseDir)
            .redirectErrorStream(true)
            .start()
        return process.inputStream.bufferedReader().readText()
    }
}
