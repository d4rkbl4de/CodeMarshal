"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.getCliPath = getCliPath;
exports.getScanOnSave = getScanOnSave;
exports.getWorkspaceRoot = getWorkspaceRoot;
exports.runCodemarshal = runCodemarshal;
exports.runJsonCommand = runJsonCommand;
exports.runJsonCommandSafe = runJsonCommandSafe;
const child_process_1 = require("child_process");
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
function getCliPath() {
    return (vscode.workspace
        .getConfiguration("codemarshal")
        .get("cliPath") || "codemarshal");
}
function getScanOnSave() {
    return (vscode.workspace
        .getConfiguration("codemarshal")
        .get("scanOnSave") ?? true);
}
function getWorkspaceRoot() {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
        return null;
    }
    return folders[0].uri.fsPath;
}
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
async function handleCliNotFoundError(cliPath) {
    const item = await vscode.window.showErrorMessage(`CodeMarshal: CLI not found at '${cliPath}'. Please check your 'codemarshal.cliPath' setting.`, "Go to Settings", "Try Reinstalling");
    if (item === "Go to Settings") {
        await vscode.commands.executeCommand("workbench.action.openSettings", "@ext:codemarshal.codemarshal codemarshal.cliPath");
    }
    else if (item === "Try Reinstalling") {
        await vscode.env.openExternal(vscode.Uri.parse("https://github.com/codemarshal/cli"));
    }
}
async function handleExecutionError(errorMessage, exitCode) {
    const retryActions = ["Retry", "View Output", "Ignore"];
    const item = await vscode.window.showWarningMessage(`CodeMarshal command failed (exit code: ${exitCode}).`, ...retryActions);
    if (item === "Retry") {
        return;
    }
    else if (item === "View Output") {
        const outputChannel = vscode.window.createOutputChannel("CodeMarshal");
        outputChannel.show(true);
        outputChannel.appendLine(errorMessage);
        return;
    }
    else if (item === "Ignore") {
        return;
    }
}
async function runCodemarshal(cliPath, args, cwd, options) {
    const maxRetries = options?.maxRetries || 1;
    const delay = options?.delay || 1000;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            await fs.promises.stat(cliPath);
        }
        catch (err) {
            if (err.code === "ENOENT") {
                await handleCliNotFoundError(cliPath);
                return {
                    stdout: "",
                    stderr: `CLI not found at ${cliPath}`,
                    exitCode: 1,
                };
            }
        }
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
                const exitCode = typeof code === "number" ? code : 1;
                if (exitCode !== 0) {
                    const errorMessage = `Command exited with code ${exitCode}. Stderr: ${stderr}`;
                    if (attempt < maxRetries) {
                        options?.onRetry?.(attempt, new Error(errorMessage));
                    }
                    else {
                        handleExecutionError(errorMessage, exitCode);
                    }
                }
                resolve({
                    stdout,
                    stderr,
                    exitCode,
                });
            });
            proc.on("error", (err) => {
                if (attempt < maxRetries) {
                    options?.onRetry?.(attempt, err);
                }
                else {
                    handleExecutionError(String(err), 1);
                }
                resolve({
                    stdout: "",
                    stderr: String(err),
                    exitCode: 1,
                });
            });
        });
    }
    throw new Error(`Max retries (${maxRetries}) exceeded`);
}
async function runJsonCommand(cliPath, args, cwd, options) {
    const run = await runCodemarshal(cliPath, args, cwd, options);
    const payload = extractJsonPayload(run.stdout);
    if (!payload) {
        const error = run.stderr || "No JSON payload detected";
        const tryAction = await vscode.window.showWarningMessage(`Failed to parse JSON output: ${error}. Try raw output?`, "Try Raw Output", "Dismiss");
        if (tryAction === "Try Raw Output") {
            const outputChannel = vscode.window.createOutputChannel("CodeMarshal");
            outputChannel.show(true);
            outputChannel.appendLine("Raw output:");
            outputChannel.appendLine(run.stdout);
            outputChannel.appendLine("Stderr:");
            outputChannel.appendLine(run.stderr);
        }
        return {
            data: null,
            error,
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
        const tryAction = await vscode.window.showWarningMessage(`Failed to parse JSON: ${String(err)}. Try raw output?`, "Try Raw Output", "Dismiss");
        if (tryAction === "Try Raw Output") {
            const outputChannel = vscode.window.createOutputChannel("CodeMarshal");
            outputChannel.show(true);
            outputChannel.appendLine("Raw output:");
            outputChannel.appendLine(run.stdout);
            outputChannel.appendLine("Stderr:");
            outputChannel.appendLine(run.stderr);
        }
        return {
            data: null,
            error: String(err),
            run,
        };
    }
}
async function runJsonCommandSafe(cliPath, args, cwd, options) {
    const result = await runJsonCommand(cliPath, args, cwd, options);
    const parsedData = result.data;
    if (parsedData === null) {
        return result;
    }
    const safeData = parsedData;
    return {
        data: safeData,
        error: null,
        run: result.run,
    };
}
//# sourceMappingURL=cli.js.map