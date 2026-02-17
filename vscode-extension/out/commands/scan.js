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
exports.registerScanCommands = registerScanCommands;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const cli_1 = require("../cli");
const utils_1 = require("../utils");
const patternCache_1 = require("../patternCache");
// Note: outputChannel, matchStore, diagnostics, and codelensProvider are passed in from activate()
function registerScanCommands(context, outputChannel, matchStore, diagnostics, codelensProvider) {
    async function scanFile(uri) {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: `CodeMarshal: Scanning ${path.basename(uri.fsPath)}`,
            cancellable: false,
        }, async () => {
            const cliPath = (0, cli_1.getCliPath)();
            const result = await (0, cli_1.runJsonCommand)(cliPath, [
                "pattern",
                "scan",
                uri.fsPath,
                "--output=json",
            ]);
            if (!result.data) {
                const errorMessage = `CodeMarshal: Pattern scan failed for ${path.basename(uri.fsPath)}. ${result.error || result.run.stderr}`;
                vscode.window.showErrorMessage(errorMessage);
                outputChannel.appendLine(errorMessage);
                return;
            }
            const matches = result.data.matches || [];
            const normalized = (0, utils_1.normalizeFsPath)(uri.fsPath);
            const filtered = matches.filter((match) => (0, utils_1.normalizeFsPath)(match.file) === normalized);
            matchStore.set(normalized, filtered);
            patternCache_1.PatternCache.set(uri, filtered);
            diagnostics.updateForFile(uri, filtered);
            codelensProvider.refresh();
            vscode.window.showInformationMessage(`CodeMarshal: Found ${filtered.length} pattern matches in ${path.basename(uri.fsPath)}.`);
        });
    }
    async function scanWorkspace() {
        const root = (0, cli_1.getWorkspaceRoot)();
        if (!root) {
            vscode.window.showWarningMessage("CodeMarshal: No workspace folder found.");
            return;
        }
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "CodeMarshal: Scanning workspace for patterns...",
            cancellable: false,
        }, async () => {
            const cliPath = (0, cli_1.getCliPath)();
            const result = await (0, cli_1.runJsonCommand)(cliPath, [
                "pattern",
                "scan",
                root,
                "--output=json",
            ]);
            if (!result.data) {
                const errorMessage = `CodeMarshal: Pattern scan failed for workspace. ${result.error || result.run.stderr}`;
                vscode.window.showErrorMessage(errorMessage);
                outputChannel.appendLine(errorMessage);
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
    const config = vscode.workspace.getConfiguration("codemarshal");
    const debounceTime = config.get("debounceTime", 500);
    const showWarnings = config.get("showWarnings", true);
    const showInfo = config.get("showInfo", true);
    const includeGitignore = config.get("includeGitignore", true);
    const debouncedScanFile = (0, utils_1.debounce)(scanFile, debounceTime);
    context.subscriptions.push(vscode.commands.registerCommand("codemarshal.scanPatterns", async () => {
        await scanWorkspace();
    }), vscode.workspace.onDidSaveTextDocument((document) => {
        if (!(0, cli_1.getScanOnSave)()) {
            return;
        }
        // Don't scan `.git` files, output channels, etc.
        if (document.uri.scheme !== "file") {
            return;
        }
        const fileName = path.basename(document.fileName);
        if (fileName.startsWith(".git") || fileName.startsWith(".")) {
            return;
        }
        debouncedScanFile(document.uri);
    }));
    context.subscriptions.push(vscode.commands.registerCommand("codemarshal.cache.clear", async () => {
        patternCache_1.PatternCache.clear();
        vscode.window.showInformationMessage("CodeMarshal: Cache cleared.");
    }));
    context.subscriptions.push(vscode.commands.registerCommand("codemarshal.scanPatternsForFile", async (uri) => {
        const targetUri = uri || vscode.window.activeTextEditor?.document.uri;
        if (!targetUri) {
            vscode.window.showWarningMessage("CodeMarshal: No file selected.");
            return;
        }
        await scanFile(targetUri);
    }), vscode.commands.registerCommand("codemarshal.scanPatternsForFolder", async (uri) => {
        const targetUri = uri || vscode.workspace.workspaceFolders?.[0]?.uri;
        if (!targetUri) {
            vscode.window.showWarningMessage("CodeMarshal: No folder selected.");
            return;
        }
        if (targetUri.scheme !== "file") {
            vscode.window.showWarningMessage("CodeMarshal: Cannot scan non-file URI.");
            return;
        }
        const folderPath = targetUri.fsPath;
        await scanFolder(folderPath, matchStore, diagnostics, codelensProvider);
    }));
}
async function scanFolder(folderPath, matchStore, diagnostics, codelensProvider) {
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: `CodeMarshal: Scanning folder ${path.basename(folderPath)}...`,
        cancellable: false,
    }, async () => {
        const cliPath = (0, cli_1.getCliPath)();
        const result = await (0, cli_1.runJsonCommand)(cliPath, [
            "pattern",
            "scan",
            folderPath,
            "--output=json",
        ]);
        if (!result.data) {
            const errorMessage = `CodeMarshal: Pattern scan failed for folder. ${result.error || result.run.stderr}`;
            vscode.window.showErrorMessage(errorMessage);
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
        vscode.window.showInformationMessage(`CodeMarshal: Found ${matches.length} pattern matches in folder ${path.basename(folderPath)}.`);
    });
}
//# sourceMappingURL=scan.js.map