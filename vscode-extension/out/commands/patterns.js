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
exports.registerPatternCommands = registerPatternCommands;
const vscode = __importStar(require("vscode"));
const cli_1 = require("../cli");
const utils_1 = require("../utils");
function registerPatternCommands(context, outputChannel, matchStore) {
    context.subscriptions.push(vscode.commands.registerCommand("codemarshal.listPatterns", async () => {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "CodeMarshal: Listing patterns...",
            cancellable: false,
        }, async () => {
            const result = await (0, cli_1.runJsonCommand)((0, cli_1.getCliPath)(), ["pattern", "list", "--output=json"]);
            outputChannel.show(true);
            if (!result.data) {
                const errorMessage = `CodeMarshal: Pattern list failed. ${result.error || result.run.stderr}`;
                vscode.window.showErrorMessage(errorMessage);
                outputChannel.appendLine(errorMessage);
                return;
            }
            outputChannel.appendLine(`Available patterns: ${result.data.total_count}`);
            for (const pattern of result.data.patterns) {
                outputChannel.appendLine(`${pattern.id} - ${pattern.name} (${pattern.severity})`);
            }
        });
    }), vscode.commands.registerCommand("codemarshal.showPatternsForFile", async (uri) => {
        const targetUri = uri || vscode.window.activeTextEditor?.document.uri;
        if (!targetUri) {
            vscode.window.showWarningMessage("CodeMarshal: No file selected.");
            return;
        }
        const matches = matchStore.get((0, utils_1.normalizeFsPath)(targetUri.fsPath)) || [];
        outputChannel.show(true);
        outputChannel.appendLine(`--- Pattern matches for ${targetUri.fsPath} (${matches.length}) ---`);
        if (matches.length === 0) {
            outputChannel.appendLine("No pattern matches found for this file.");
        }
        else {
            for (const match of matches) {
                outputChannel.appendLine(`- [${match.severity}] ${match.pattern_name || match.pattern_id}: ${match.message} (Line: ${match.line})`);
            }
        }
    }));
}
//# sourceMappingURL=patterns.js.map