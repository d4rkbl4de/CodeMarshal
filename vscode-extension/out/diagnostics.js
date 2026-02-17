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
exports.DiagnosticsManager = void 0;
const vscode = __importStar(require("vscode"));
function severityToDiagnostic(severity) {
    switch (severity.toLowerCase()) {
        case "critical":
            return vscode.DiagnosticSeverity.Error;
        case "warning":
            return vscode.DiagnosticSeverity.Warning;
        case "info":
        default:
            return vscode.DiagnosticSeverity.Information;
    }
}
class DiagnosticsManager {
    constructor(collection) {
        this.collection = collection;
    }
    updateForFile(uri, matches, options) {
        const showWarnings = options?.showWarnings ?? true;
        const showInfo = options?.showInfo ?? true;
        const quickFixes = options?.quickFixes ?? false;
        const diagnostics = matches
            .filter((match) => {
            const severity = match.severity?.toLowerCase();
            if (severity === "critical")
                return true;
            if (severity === "warning" && showWarnings)
                return true;
            if (severity === "info" && showInfo)
                return true;
            return false;
        })
            .map((match) => {
            const lineIndex = Math.max(0, (match.line || 1) - 1);
            const start = new vscode.Position(lineIndex, 0);
            const end = new vscode.Position(lineIndex, Math.max(1, (match.matched || "").length));
            const diagnostic = new vscode.Diagnostic(new vscode.Range(start, end), match.message || match.pattern_name || "CodeMarshal pattern match", severityToDiagnostic(match.severity || "info"));
            diagnostic.source = "CodeMarshal";
            diagnostic.code = match.pattern_id;
            return diagnostic;
        });
        this.collection.set(uri, diagnostics);
    }
    clear(uri) {
        this.collection.delete(uri);
    }
}
exports.DiagnosticsManager = DiagnosticsManager;
//# sourceMappingURL=diagnostics.js.map