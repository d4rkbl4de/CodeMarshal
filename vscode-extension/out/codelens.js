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
exports.CodeMarshalCodeLensProvider = void 0;
const vscode = __importStar(require("vscode"));
const utils_1 = require("./utils");
class CodeMarshalCodeLensProvider {
    constructor(matchStore) {
        this.matchStore = matchStore;
        this._onDidChangeCodeLenses = new vscode.EventEmitter();
        this.onDidChangeCodeLenses = this._onDidChangeCodeLenses.event;
    }
    refresh() {
        this._onDidChangeCodeLenses.fire();
    }
    provideCodeLenses(document) {
        const key = (0, utils_1.normalizeFsPath)(document.uri.fsPath);
        const matches = this.matchStore.get(key) || [];
        if (matches.length === 0) {
            return [];
        }
        const codeLenses = [];
        matches.forEach((match) => {
            const lineIndex = Math.max(0, (match.line || 1) - 1);
            const range = new vscode.Range(lineIndex, 0, lineIndex, 9999);
            const severity = match.severity?.toLowerCase();
            const color = severity === "critical" ? "#f48771" : severity === "warning" ? "#cca700" : "#75beff";
            const codeLens = new vscode.CodeLens(range, {
                title: `${match.pattern_name || match.pattern_id || "Pattern"}${match.line ? ` (${match.line})` : ""}`,
                command: "codemarshal.goToPattern",
                arguments: [
                    {
                        uri: document.uri,
                        line: lineIndex,
                        match: match,
                        patternName: match.pattern_name || match.pattern_id || "Pattern",
                        message: match.message,
                    },
                ],
                tooltip: `${match.pattern_name || match.pattern_id || "Pattern"}\n${match.message || "No message"}\nLine: ${match.line || "N/A"}\nSeverity: ${severity || "info"}`,
            });
            codeLenses.push(codeLens);
        });
        return codeLenses;
    }
}
exports.CodeMarshalCodeLensProvider = CodeMarshalCodeLensProvider;
//# sourceMappingURL=codelens.js.map