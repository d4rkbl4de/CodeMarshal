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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const cli_1 = require("./cli");
const diagnostics_1 = require("./diagnostics");
const codelens_1 = require("./codelens");
const hover_1 = require("./hover");
const utils_1 = require("./utils"); // Ensure this is imported from utils
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
function activate(context) {
    // Core services and state
    const output = vscode.window.createOutputChannel("CodeMarshal");
    const matchStore = new Map();
    const diagnosticsCollection = vscode.languages.createDiagnosticCollection("CodeMarshal");
    const diagnostics = new diagnostics_1.DiagnosticsManager(diagnosticsCollection);
    const codelensProvider = new codelens_1.CodeMarshalCodeLensProvider(matchStore);
    const hoverProvider = new hover_1.CodeMarshalHoverProvider(matchStore);
    // Helper functions used by commands/subscriptions (defined within activate to capture context)
    async function runAndLog(args, cwd, showOutput = true) {
        const cliPath = getCliPath();
        if (showOutput) {
            output.show(true);
            output.appendLine(`> ${cliPath} ${args.join(" ")}`);
        }
        let result;
        try {
            result = await (0, cli_1.runCodemarshal)(cliPath, args, cwd);
        }
        catch (err) {
            const errorMessage = `CodeMarshal: Failed to run CLI. Please check your 'codemarshal.cliPath' setting. Error: ${err.message || err}`;
            if (showOutput) {
                output.appendLine(errorMessage);
            }
            vscode.window.showErrorMessage(errorMessage);
            return false;
        }
        if (result.stdout) {
            if (showOutput) {
                output.appendLine(result.stdout);
            }
        }
        if (result.stderr) {
            if (showOutput) {
                output.appendLine(result.stderr);
            }
            vscode.window.showErrorMessage(`CodeMarshal CLI Error: ${result.stderr}`);
            return false;
        }
        if (result.exitCode !== 0) {
            const errorMessage = `CodeMarshal command failed with exit code ${result.exitCode}. See output channel for details.`;
            if (showOutput) {
                output.appendLine(errorMessage);
            }
            vscode.window.showErrorMessage(errorMessage);
            return false;
        }
        return true;
    }
    async function scanFile(uri) {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `CodeMarshal: Scanning ${path.basename(uri.fsPath)}`,
            cancellable: false,
        }, async (progress) => {
            const cliPath = getCliPath();
            const result = await (0, cli_1.runJsonCommand)(cliPath, [
                "pattern",
                "scan",
                uri.fsPath,
                "--output=json",
            ]);
            if (!result.data) {
                const errorMessage = `CodeMarshal: Pattern scan failed for ${path.basename(uri.fsPath)}. ${result.error || result.run.stderr}`;
                vscode.window.showErrorMessage(errorMessage);
                output.appendLine(errorMessage);
                return;
            }
            const matches = result.data.matches || [];
            const normalized = (0, utils_1.normalizeFsPath)(uri.fsPath);
            const filtered = matches.filter((match) => (0, utils_1.normalizeFsPath)(match.file) === normalized);
            matchStore.set(normalized, filtered);
            diagnostics.updateForFile(uri, filtered);
            codelensProvider.refresh();
            vscode.window.showInformationMessage(`CodeMarshal: Found ${filtered.length} pattern matches in ${path.basename(uri.fsPath)}.`);
        });
    }
    async function scanWorkspace() {
        const root = getWorkspaceRoot();
        if (!root) {
            vscode.window.showWarningMessage("CodeMarshal: No workspace folder found.");
            return;
        }
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "CodeMarshal: Scanning workspace for patterns...",
            cancellable: false,
        }, async (progress) => {
            const cliPath = getCliPath();
            const result = await (0, cli_1.runJsonCommand)(cliPath, [
                "pattern",
                "scan",
                root,
                "--output=json",
            ]);
            if (!result.data) {
                const errorMessage = `CodeMarshal: Pattern scan failed for workspace. ${result.error || result.run.stderr}`;
                vscode.window.showErrorMessage(errorMessage);
                output.appendLine(errorMessage);
                return;
            }
            const matches = result.data.matches || [];
            const matchesByFile = new Map();
            for (const match of matches) {
                const key = (0, utils_1.normalizeFsPath)(match.file);
                const list = matchesByFile.get(key) || [];
                list.push(match);
                matchesByFile.set(key, list);
            }
            matchStore.clear();
            for (const [filePath, fileMatches] of matchesByFile.entries()) {
                matchStore.set(filePath, fileMatches);
                diagnostics.updateForFile(vscode.Uri.file(filePath), fileMatches);
            }
            codelensProvider.refresh();
            vscode.window.showInformationMessage(`CodeMarshal: Found ${matches.length} pattern matches in the workspace.`);
        });
    }
    // --- Command Registration ---
    function registerCommands(context) {
        context.subscriptions.push(vscode.commands.registerCommand("codemarshal.investigate", async () => {
            const scope = await vscode.window.showQuickPick(["file", "module", "package", "project"], { placeHolder: "Select investigation scope" });
            if (!scope) {
                return;
            }
            const intent = await vscode.window.showQuickPick([
                "initial_scan",
                "constitutional_check",
                "dependency_analysis",
                "architecture_review",
            ], { placeHolder: "Select investigation intent" });
            if (!intent) {
                return;
            }
            const activeFile = vscode.window.activeTextEditor?.document
                .uri.fsPath;
            const target = activeFile
                ? path.dirname(activeFile)
                : getWorkspaceRoot();
            if (!target) {
                vscode.window.showWarningMessage("CodeMarshal: No target selected for investigation.");
                return;
            }
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `CodeMarshal: Investigating ${path.basename(target)} with scope ${scope} and intent ${intent}...`,
                cancellable: false,
            }, async () => {
                const cliPath = getCliPath();
                const result = await (0, cli_1.runJsonCommand)(cliPath, [
                    "investigate",
                    target,
                    `--scope=${scope}`,
                    `--intent=${intent}`,
                    "--output=json", // Request JSON output
                ]);
                if (result.data) {
                    const doc = await vscode.workspace.openTextDocument({
                        content: JSON.stringify(result.data, null, 2),
                        language: "json",
                    });
                    await vscode.window.showTextDocument(doc, { preview: false });
                    vscode.window.showInformationMessage(`CodeMarshal: Investigation '${result.data.investigation_id}' started. Results displayed in new tab.`);
                }
                else {
                    const errorMessage = `CodeMarshal: Investigation failed. ${result.error || result.run.stderr}`;
                    vscode.window.showErrorMessage(errorMessage);
                    output.appendLine(errorMessage);
                }
            });
        }), vscode.commands.registerCommand("codemarshal.observe", async () => {
            const scope = await vscode.window.showQuickPick(["file", "module", "package", "project"], { placeHolder: "Select observation scope" });
            if (!scope) {
                return;
            }
            const args = ["observe"];
            const activeFile = vscode.window.activeTextEditor?.document
                .uri.fsPath;
            const target = activeFile || getWorkspaceRoot();
            if (!target) {
                vscode.window.showWarningMessage("CodeMarshal: No target selected for observation.");
                return;
            }
            args.push(target);
            args.push(`--scope=${scope}`);
            const constitutional = await vscode.window.showQuickPick(["Yes", "No"], { placeHolder: "Include constitutional checks? (--constitutional)" });
            if (constitutional === "Yes") {
                args.push("--constitutional");
            }
            const includeBinary = await vscode.window.showQuickPick(["Yes", "No"], { placeHolder: "Include binary files? (--include-binary)" });
            if (includeBinary === "Yes") {
                args.push("--include-binary");
            }
            const followSymlinks = await vscode.window.showQuickPick(["Yes", "No"], { placeHolder: "Follow symlinks? (--follow-symlinks)" });
            if (followSymlinks === "Yes") {
                args.push("--follow-symlinks");
            }
            const persist = await vscode.window.showQuickPick(["Yes", "No"], { placeHolder: "Persist observations? (--persist)" });
            if (persist === "Yes") {
                args.push("--persist");
            }
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `CodeMarshal: Observing ${path.basename(target)} with scope ${scope}...`,
                cancellable: false,
            }, async () => {
                await runAndLog(args);
            });
        }), vscode.commands.registerCommand("codemarshal.scanPatterns", async () => {
            await scanWorkspace();
        }), vscode.commands.registerCommand("codemarshal.listPatterns", async () => {
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "CodeMarshal: Listing patterns...",
                cancellable: false,
            }, async () => {
                const result = await (0, cli_1.runJsonCommand)(getCliPath(), ["pattern", "list", "--output=json"]);
                output.show(true);
                if (!result.data) {
                    const errorMessage = `CodeMarshal: Pattern list failed. ${result.error || result.run.stderr}`;
                    vscode.window.showErrorMessage(errorMessage);
                    output.appendLine(errorMessage);
                    return;
                }
                output.appendLine(`Available patterns: ${result.data.total_count}`);
                for (const pattern of result.data.patterns) {
                    output.appendLine(`${pattern.id} - ${pattern.name} (${pattern.severity})`);
                }
            });
        }), vscode.commands.registerCommand("codemarshal.query", async () => {
            const investigationId = await vscode.window.showQuickPick(["latest", "Enter ID..."], {
                placeHolder: "Investigation/session ID (type 'latest' for the most recent)",
            });
            if (!investigationId) {
                return;
            }
            let finalInvestigationId = investigationId;
            if (investigationId === "Enter ID...") {
                const inputId = await vscode.window.showInputBox({
                    prompt: "Enter Investigation/session ID",
                });
                if (!inputId) {
                    return;
                }
                finalInvestigationId = inputId;
            }
            const question = await vscode.window.showInputBox({
                prompt: "Question to ask",
            });
            if (!question) {
                return;
            }
            // Prompt for question type
            const questionType = await vscode.window.showQuickPick(["structure", "purpose", "connections", "anomalies", "thinking"], { placeHolder: "Select question type" });
            if (!questionType) {
                return;
            }
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "CodeMarshal: Running query...",
                cancellable: false,
            }, async () => {
                const cliPath = getCliPath();
                const result = await (0, cli_1.runJsonCommand)(cliPath, [
                    "query",
                    finalInvestigationId,
                    "--question",
                    question,
                    `--question-type=${questionType}`,
                    "--output=json", // Request JSON output
                ]);
                if (result.data) {
                    const doc = await vscode.workspace.openTextDocument({
                        content: JSON.stringify(result.data, null, 2),
                        language: "json",
                    });
                    await vscode.window.showTextDocument(doc, { preview: false });
                    vscode.window.showInformationMessage(`CodeMarshal: Query result for '${question}' displayed in new tab.`);
                }
                else {
                    const errorMessage = `CodeMarshal: Query failed. ${result.error || result.run.stderr}`;
                    vscode.window.showErrorMessage(errorMessage);
                    output.appendLine(errorMessage);
                }
            });
        }), vscode.commands.registerCommand("codemarshal.export", async () => {
            const investigationId = await vscode.window.showQuickPick(["latest", "Enter ID..."], {
                placeHolder: "Investigation/session ID (type 'latest' for the most recent)",
            });
            if (!investigationId) {
                return;
            }
            let finalInvestigationId = investigationId;
            if (investigationId === "Enter ID...") {
                const inputId = await vscode.window.showInputBox({
                    prompt: "Enter Investigation/session ID",
                });
                if (!inputId) {
                    return;
                }
                finalInvestigationId = inputId;
            }
            const format = await vscode.window.showQuickPick(["markdown", "json", "html", "text", "csv", "jupyter", "pdf", "svg"], { placeHolder: "Export format" });
            if (!format) {
                return;
            }
            const outputUri = await vscode.window.showSaveDialog({
                saveLabel: "Export",
                filters: {
                    "CodeMarshal Export": [format],
                },
            });
            if (!outputUri) {
                return;
            }
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "CodeMarshal: Exporting...",
                cancellable: false,
            }, async () => {
                await runAndLog([
                    "export",
                    finalInvestigationId,
                    `--format=${format}`,
                    `--output=${outputUri.fsPath}`,
                    "--confirm-overwrite",
                ]);
            });
        }), vscode.commands.registerCommand("codemarshal.showPatternsForFile", async (uri) => {
            const targetUri = uri || vscode.window.activeTextEditor?.document.uri;
            if (!targetUri) {
                vscode.window.showWarningMessage("CodeMarshal: No file selected to show patterns for.");
                return;
            }
            const matches = matchStore.get((0, utils_1.normalizeFsPath)(targetUri.fsPath)) || [];
            output.show(true);
            output.appendLine(`--- Pattern matches for ${targetUri.fsPath} (${matches.length}) ---`);
            if (matches.length === 0) {
                output.appendLine("No pattern matches found for this file.");
                vscode.window.showInformationMessage(`CodeMarshal: No pattern matches found for ${path.basename(targetUri.fsPath)}.`);
            }
            else {
                for (const match of matches) {
                    output.appendLine(`- [${match.severity}] ${match.pattern_name || match.pattern_id}: ${match.message} (Line: ${match.line})`);
                }
                vscode.window.showInformationMessage(`CodeMarshal: Displaying ${matches.length} pattern matches for ${path.basename(targetUri.fsPath)} in output channel.`);
            }
        }), vscode.commands.registerCommand("codemarshal.setCliPath", async () => {
            const newCliPath = await vscode.window.showInputBox({
                prompt: "Enter the path to the CodeMarshal CLI executable",
                value: getCliPath(),
            });
            if (newCliPath === undefined) {
                return; // User cancelled
            }
            await vscode.workspace
                .getConfiguration("codemarshal")
                .update("cliPath", newCliPath, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage(`CodeMarshal CLI path updated to: ${newCliPath}`);
        }));
    }
    // --- Event Subscriptions ---
    function registerSubscriptions(context) {
        context.subscriptions.push(vscode.workspace.onDidSaveTextDocument((document) => {
            if (!getScanOnSave()) {
                return;
            }
            void scanFile(document.uri);
        }), vscode.languages.registerCodeLensProvider({ scheme: "file" }, codelensProvider), vscode.languages.registerHoverProvider({ scheme: "file" }, hoverProvider), output, diagnosticsCollection);
    }
    // Register all commands and subscriptions
    registerCommands(context);
    registerSubscriptions(context);
}
function deactivate() {
    // no-op
}
//# sourceMappingURL=extension.js.map