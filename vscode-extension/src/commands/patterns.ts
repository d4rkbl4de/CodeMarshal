import * as vscode from "vscode";
import * as path from "path";
import { runJsonCommand, getCliPath } from "../cli";
import { PatternMatch } from "../diagnostics";
import { normalizeFsPath } from "../utils";

export function registerPatternCommands(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
  matchStore: Map<string, PatternMatch[]>,
): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemarshal.listPatterns",
      async () => {
        await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: "CodeMarshal: Listing patterns...",
            cancellable: false,
          },
          async () => {
            const result = await runJsonCommand<{
              total_count: number;
              patterns: Array<{ id: string; name: string; severity: string }>;
            }>(getCliPath(), ["pattern", "list", "--output=json"]);

            outputChannel.show(true);
            if (!result.data) {
              const errorMessage = `CodeMarshal: Pattern list failed. ${result.error || result.run.stderr}`;
              vscode.window.showErrorMessage(errorMessage);
              outputChannel.appendLine(errorMessage);
              return;
            }

            outputChannel.appendLine(
              `Available patterns: ${result.data.total_count}`,
            );
            for (const pattern of result.data.patterns) {
              outputChannel.appendLine(
                `${pattern.id} - ${pattern.name} (${pattern.severity})`,
              );
            }
          },
        );
      },
    ),

    vscode.commands.registerCommand(
      "codemarshal.showPatternsForFile",
      async (uri?: vscode.Uri) => {
        const targetUri =
          uri || vscode.window.activeTextEditor?.document.uri;
        if (!targetUri) {
          vscode.window.showWarningMessage(
            "CodeMarshal: No file selected.",
          );
          return;
        }

        const matches =
          matchStore.get(normalizeFsPath(targetUri.fsPath)) || [];
        outputChannel.show(true);
        outputChannel.appendLine(
          `--- Pattern matches for ${targetUri.fsPath} (${matches.length}) ---`,
        );

        if (matches.length === 0) {
          outputChannel.appendLine("No pattern matches found for this file.");
        } else {
          for (const match of matches) {
            outputChannel.appendLine(
              `- [${match.severity}] ${match.pattern_name || match.pattern_id}: ${match.message} (Line: ${match.line})`,
            );
          }
        }
      },
    ),
  );
}
