plugins {
    kotlin("jvm") version "1.9.22"
    id("org.jetbrains.intellij") version "1.17.2"
}

group = "codemarshal"
version = "2.2.0"

repositories {
    mavenCentral()
}

intellij {
    version.set("2023.2")
    type.set("IC")
    downloadSources.set(false)
}

tasks {
    patchPluginXml {
        sinceBuild.set("232")
        untilBuild.set("241.*")
        pluginDescription.set("""
            <p>CodeMarshal IDE integration for JetBrains products. Provides pattern scanning, code investigation, and observation capabilities.</p>
            <p>Features:</p>
            <ul>
                <li>Pattern scanning with JSON output</li>
                <li>Code investigation and observation</li>
                <li>Query capabilities for code analysis</li>
                <li>Progress indicators for long operations</li>
                <li>Configurable settings and CLI path</li>
                <li>Context menu integration</li>
            </ul>
        """.trimIndent())
    }

    signPlugin {
        // Keep local builds deterministic: only configure signing when CI secrets exist.
        val certChain = providers.environmentVariable("CERTIFICATE_CHAIN")
        val privateKeyValue = providers.environmentVariable("PRIVATE_KEY")
        val privateKeyPassword = providers.environmentVariable("PRIVATE_KEY_PASSWORD")
        if (certChain.isPresent && privateKeyValue.isPresent && privateKeyPassword.isPresent) {
            certificateChain.set(certChain.get())
            privateKey.set(privateKeyValue.get())
            password.set(privateKeyPassword.get())
        }
    }

    publishPlugin {
        // Local build/test should not require publish credentials.
        val publishToken = providers.environmentVariable("PUBLISH_TOKEN")
        if (publishToken.isPresent) {
            token.set(publishToken.get())
        }
    }
}

kotlin {
    jvmToolchain(17)
}
