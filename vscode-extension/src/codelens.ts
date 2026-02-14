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
    const title = matches.length
      ? `CodeMarshal: ${matches.length} pattern matches`
      : "CodeMarshal: no pattern matches";
    const range = new vscode.Range(0, 0, 0, 0);
    const command: vscode.Command = {
      title,
      command: "codemarshal.showPatternsForFile",
      arguments: [document.uri],
    };
    return [new vscode.CodeLens(range, command)];
  }
}
