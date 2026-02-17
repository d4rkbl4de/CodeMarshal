plugins {
    kotlin("jvm") version "1.9.22"
    id("org.jetbrains.intellij") version "1.17.2"
}

group = "codemarshal"
version = "2.2.0-rc1"

repositories {
    mavenCentral()
}

intellij {
    version.set("2023.2")
    type.set("IC")
}

dependencies {
    implementation("com.fasterxml.jackson.core:jackson-databind:2.15.2")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.15.2")
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
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        tokens.set(mapOf(
            "pomVersion" to "2.2.0-rc1",
            "versionName" to "2.2.0-rc1"
        ))
    }
}

kotlin {
    jvmToolchain(11)
}
