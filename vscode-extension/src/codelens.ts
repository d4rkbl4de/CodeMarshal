import * as vscode from "vscode";
import { normalizeFsPath } from "./utils";
import { PatternMatch } from "./diagnostics";

export class CodeMarshalCodeLensProvider implements vscode.CodeLensProvider {
  private readonly _onDidChangeCodeLenses =
    new vscode.EventEmitter<void>();
  public readonly onDidChangeCodeLenses =
    this._onDidChangeCodeLenses.event;

  constructor(
    private readonly matchStore: Map<string, PatternMatch[]>,
  ) {}

  refresh(): void {
    this._onDidChangeCodeLenses.fire();
  }

  provideCodeLenses(
    document: vscode.TextDocument,
  ): vscode.CodeLens[] {
    const key = normalizeFsPath(document.uri.fsPath);
    const matches = this.matchStore.get(key) || [];

    if (matches.length === 0) {
      return [];
    }

    const codeLenses: vscode.CodeLens[] = [];

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
