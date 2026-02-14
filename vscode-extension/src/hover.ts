import * as vscode from "vscode";
import { normalizeFsPath } from "./utils";
import { PatternMatch } from "./diagnostics";


export class CodeMarshalHoverProvider implements vscode.HoverProvider {
  constructor(
    private readonly matchStore: Map<string, PatternMatch[]>,
  ) {}

  provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
  ): vscode.ProviderResult<vscode.Hover> {
    const key = normalizeFsPath(document.uri.fsPath);
    const matches = this.matchStore.get(key) || [];
    const lineNumber = position.line + 1;
    const lineMatches = matches.filter(
      (match) => match.line === lineNumber,
    );
    if (lineMatches.length === 0) {
      return null;
    }
    const markdown = new vscode.MarkdownString();
    markdown.appendMarkdown("**CodeMarshal Matches**\n");
    for (const match of lineMatches) {
      markdown.appendMarkdown(
        `- ${match.pattern_name || match.pattern_id || "Pattern"}: ${
          match.message || "Match"
        }\n`,
      );
      if (match.severity) {
        markdown.appendMarkdown(`  - Severity: ${match.severity}\n`);
      }
    }
    return new vscode.Hover(markdown);
  }
}
