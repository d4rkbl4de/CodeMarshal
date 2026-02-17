import * as vscode from "vscode";

export interface PatternMatch {
  file: string;
  line: number;
  message: string;
  severity: string;
  matched: string;
  pattern_id?: string;
  pattern_name?: string;
  description?: string;
  fix?: string;
}

function severityToDiagnostic(severity: string): vscode.DiagnosticSeverity {
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

export class DiagnosticsManager {
  constructor(private readonly collection: vscode.DiagnosticCollection) {}

  updateForFile(
    uri: vscode.Uri,
    matches: PatternMatch[],
    options?: {
      showWarnings?: boolean;
      showInfo?: boolean;
      quickFixes?: boolean;
    },
  ): void {
    const showWarnings = options?.showWarnings ?? true;
    const showInfo = options?.showInfo ?? true;
    const quickFixes = options?.quickFixes ?? false;

    const diagnostics = matches
      .filter((match) => {
        const severity = match.severity?.toLowerCase();
        if (severity === "critical") return true;
        if (severity === "warning" && showWarnings) return true;
        if (severity === "info" && showInfo) return true;
        return false;
      })
      .map((match) => {
        const lineIndex = Math.max(0, (match.line || 1) - 1);
        const start = new vscode.Position(lineIndex, 0);
        const end = new vscode.Position(
          lineIndex,
          Math.max(1, (match.matched || "").length),
        );
        const diagnostic = new vscode.Diagnostic(
          new vscode.Range(start, end),
          match.message || match.pattern_name || "CodeMarshal pattern match",
          severityToDiagnostic(match.severity || "info"),
        );
        diagnostic.source = "CodeMarshal";
        diagnostic.code = match.pattern_id;

        return diagnostic;
      });

    this.collection.set(uri, diagnostics);
  }

  clear(uri: vscode.Uri): void {
    this.collection.delete(uri);
  }
}
