"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.runCodemarshal = runCodemarshal;
exports.runJsonCommand = runJsonCommand;
const child_process_1 = require("child_process");
function extractJsonPayload(text) {
    const trimmed = text.trim();
    if (!trimmed) {
        return null;
    }
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
        return trimmed;
    }
    const firstBrace = trimmed.indexOf("{");
    const lastBrace = trimmed.lastIndexOf("}");
    if (firstBrace >= 0 && lastBrace > firstBrace) {
        return trimmed.slice(firstBrace, lastBrace + 1);
    }
    return null;
}
function runCodemarshal(cliPath, args, cwd) {
    return new Promise((resolve) => {
        const proc = (0, child_process_1.spawn)(cliPath, args, {
            cwd,
            shell: false,
            windowsHide: true,
        });
        let stdout = "";
        let stderr = "";
        proc.stdout.on("data", (chunk) => {
            stdout += chunk.toString();
        });
        proc.stderr.on("data", (chunk) => {
            stderr += chunk.toString();
        });
        proc.on("close", (code) => {
            resolve({
                stdout,
                stderr,
                exitCode: typeof code === "number" ? code : 1,
            });
        });
        proc.on("error", (err) => {
            resolve({
                stdout: "",
                stderr: String(err),
                exitCode: 1,
            });
        });
    });
}
async function runJsonCommand(cliPath, args, cwd) {
    const run = await runCodemarshal(cliPath, args, cwd);
    const payload = extractJsonPayload(run.stdout);
    if (!payload) {
        return {
            data: null,
            error: run.stderr || "No JSON payload detected",
            run,
        };
    }
    try {
        return {
            data: JSON.parse(payload),
            error: null,
            run,
        };
    }
    catch (err) {
        return {
            data: null,
            error: String(err),
            run,
        };
    }
}
//# sourceMappingURL=cli.js.map