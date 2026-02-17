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
const diagnostics_1 = require("./diagnostics");
const codelens_1 = require("./codelens");
const hover_1 = require("./hover");
const scan_1 = require("./commands/scan");
const investigation_1 = require("./commands/investigation");
const patterns_1 = require("./commands/patterns");
const config_1 = require("./commands/config");
const historyTreeDataProvider_1 = require("./historyTreeDataProvider");
const historyManager_1 = require("./historyManager");
function activate(context) {
    // Core services and state
    const output = vscode.window.createOutputChannel("CodeMarshal");
    const matchStore = new Map();
    const diagnosticsCollection = vscode.languages.createDiagnosticCollection("CodeMarshal");
    const diagnostics = new diagnostics_1.DiagnosticsManager(diagnosticsCollection);
    const codelensProvider = new codelens_1.CodeMarshalCodeLensProvider(matchStore);
    const hoverProvider = new hover_1.CodeMarshalHoverProvider(matchStore);
    const historyManager = new historyManager_1.HistoryManager(context);
    // --- Status Bar Indicator ---
    const statusBarIndicator = vscode.window.createStatusBarItem("codemarshal.status", vscode.StatusBarAlignment.Right, 100);
    statusBarIndicator.text = "$(search) CodeMarshal: No matches";
    statusBarIndicator.command = "codemarshal.showPatternsForFile";
    statusBarIndicator.show();
    // --- Tree View Registration ---
    const historyDataProvider = new historyTreeDataProvider_1.HistoryTreeDataProvider(historyManager);
    vscode.window.createTreeView("codemarshal.historyView", {
        treeDataProvider: historyDataProvider,
    });
    context.subscriptions.push(vscode.commands.registerCommand("codemarshal.history.search", async () => {
        const query = await vscode.window.showInputBox({
            prompt: "Search investigation history",
            placeHolder: "Enter search terms (ID, scope, intent, target, date...)",
        });
        if (query !== undefined && query !== null && query !== "") {
            historyDataProvider.setSearchQuery(query);
        }
    }));
    // --- Command Registration ---
    (0, scan_1.registerScanCommands)(context, output, matchStore, diagnostics, codelensProvider);
    (0, investigation_1.registerInvestigationCommands)(context, output, historyManager, historyDataProvider);
    (0, patterns_1.registerPatternCommands)(context, output, matchStore);
    (0, config_1.registerConfigCommands)(context);
    // --- Update status bar when file changes ---
    const updateStatusBar = (document) => {
        const matches = matchStore.get(document.uri.fsPath);
        const filteredMatches = matches?.filter((match) => {
            const severity = match.severity?.toLowerCase();
            const config = vscode.workspace.getConfiguration("codemarshal");
            if (severity === "critical")
                return true;
            if (severity === "warning" && config.get("showWarnings", true))
                return true;
            if (severity === "info" && config.get("showInfo", true))
                return true;
            return false;
        });
        if (filteredMatches && filteredMatches.length > 0) {
            statusBarIndicator.text = `$(search) CodeMarshal: ${filteredMatches.length} match${filteredMatches.length > 1 ? 'es' : ''}`;
            statusBarIndicator.tooltip = `${filteredMatches.length} pattern matches in ${document.fileName}`;
        }
        else {
            statusBarIndicator.text = "$(search) CodeMarshal: No matches";
            statusBarIndicator.tooltip = "Run 'CodeMarshal: Scan Patterns' to scan files";
        }
        statusBarIndicator.show();
    };
    // --- Context Menu Registration ---
    const fileContext = vscode.window.createTextEditorDecorationType({
        borderWidth: "2px",
        borderStyle: "solid",
        borderColor: "transparent",
    });
    context.subscriptions.push(vscode.commands.registerCommand("codemarshal.history.refresh", () => historyDataProvider.refresh()), vscode.commands.registerCommand("codemarshal.history.clear", async () => {
        await historyManager.clear();
        historyDataProvider.refresh();
    }), vscode.commands.registerCommand("codemarshal.applyQuickFix", async (match) => {
        if (!match.fix) {
            vscode.window.showWarningMessage("No fix available for this pattern");
            return;
        }
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage("No active editor found");
            return;
        }
        const line = Math.max(0, (match.line || 1) - 1);
        const start = new vscode.Position(line, 0);
        const end = new vscode.Position(line, Math.max(1, (match.matched || "").length));
        await editor.edit((edit) => {
            edit.replace(new vscode.Range(start, end), match.fix || "");
        });
        vscode.window.showInformationMessage(`Applied fix for: ${match.pattern_name || match.pattern_id || "Pattern"}`);
    }), vscode.commands.registerCommand("codemarshal.goToPattern", async (params) => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.uri.toString() !== params.uri.toString()) {
            await vscode.window.showTextDocument(params.uri);
        }
        const position = new vscode.Position(params.line, 0);
        await vscode.window.activeTextEditor?.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
        if (params.match && params.match.severity) {
            const severity = params.match.severity.toLowerCase();
            const color = severity === "critical" ? "#f48771" : severity === "warning" ? "#cca700" : "#75beff";
            const decoration = vscode.window.createTextEditorDecorationType({
                borderWidth: "2px",
                borderStyle: "solid",
                borderColor: color,
            });
            const range = new vscode.Range(params.line, 0, params.line, 9999);
            if (editor) {
                editor.setDecorations(decoration, [range]);
                setTimeout(() => {
                    if (editor) {
                        editor.setDecorations(decoration, []);
                    }
                }, 3000);
            }
        }
        vscode.window.showInformationMessage(`Navigated to pattern: ${params.patternName}`);
    }));
    // --- Event Subscriptions ---
    context.subscriptions.push(vscode.languages.registerCodeLensProvider({ scheme: "file" }, codelensProvider), vscode.languages.registerHoverProvider({ scheme: "file" }, hoverProvider), output, diagnosticsCollection, statusBarIndicator, vscode.workspace.onDidOpenTextDocument(updateStatusBar), vscode.workspace.onDidChangeTextDocument((event) => {
        if (event.document.uri.scheme !== "file")
            return;
        updateStatusBar(event.document);
    }), vscode.workspace.onDidCloseTextDocument((document) => {
        statusBarIndicator.text = "$(search) CodeMarshal: No matches";
    }));
}
function deactivate() {
    // no-op
}
//# sourceMappingURL=extension.js.map