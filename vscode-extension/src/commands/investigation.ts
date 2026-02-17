import * as vscode from "vscode";
import * as path from "path";
import {
  runCodemarshal,
  runJsonCommand,
  getCliPath,
  getWorkspaceRoot,
  RunResult,
} from "../cli";
import { InvestigationResultViewer } from "../webview/InvestigationResultViewer";
import { HistoryManager } from "../historyManager";
import { HistoryTreeDataProvider } from "../historyTreeDataProvider";

// This function will be called from activate() in extension.ts
// It's responsible for registering all commands related to investigations.
export function registerInvestigationCommands(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
  historyManager: HistoryManager,
  historyDataProvider: HistoryTreeDataProvider,
): void {
  // Helper function defined inside to capture the outputChannel
  async function runAndLog(
    args: string[],
    cwd?: string,
    showOutput: boolean = true,
  ): Promise<boolean> {
    const cliPath = getCliPath();
    if (showOutput) {
      outputChannel.show(true);
      outputChannel.appendLine(`> ${cliPath} ${args.join(" ")}`);
    }

    let result: RunResult;
    try {
      result = await runCodemarshal(cliPath, args, cwd);
    } catch (err: any) {
      const errorMessage = `CodeMarshal: Failed to run CLI. Please check your 'codemarshal.cliPath' setting. Error: ${err.message || err}`;
      if (showOutput) {
        outputChannel.appendLine(errorMessage);
      }
      vscode.window.showErrorMessage(errorMessage);
      return false;
    }

    if (result.stdout) {
      if (showOutput) {
        outputChannel.appendLine(result.stdout);
      }
    }
    if (result.stderr) {
      if (showOutput) {
        outputChannel.appendLine(result.stderr);
      }
      vscode.window.showErrorMessage(
        `CodeMarshal CLI Error: ${result.stderr}`,
      );
      return false;
    }
    if (result.exitCode !== 0) {
      const errorMessage = `CodeMarshal command failed with exit code ${result.exitCode}. See output channel for details.`;
      if (showOutput) {
        outputChannel.appendLine(errorMessage);
      }
      vscode.window.showErrorMessage(errorMessage);
      return false;
    }
    return true;
  }

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemarshal.investigate",
      async () => {
        const scope = await vscode.window.showQuickPick(
          ["file", "module", "package", "project"],
          { placeHolder: "Select investigation scope" },
        );
        if (!scope) return;

        const intent = await vscode.window.showQuickPick(
          [
            "initial_scan",
            "constitutional_check",
            "dependency_analysis",
            "architecture_review",
          ],
          { placeHolder: "Select investigation intent" },
        );
        if (!intent) return;

        const activeFile = vscode.window.activeTextEditor?.document.uri.fsPath;
        const target = activeFile
          ? path.dirname(activeFile)
          : getWorkspaceRoot();
        if (!target) {
          vscode.window.showWarningMessage(
            "CodeMarshal: No target selected for investigation.",
          );
          return;
        }

        await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: `CodeMarshal: Investigating ${path.basename(target)}...`,
            cancellable: false,
          },
          async () => {
            const result = await runJsonCommand<{
              investigation_id: string;
            }>(getCliPath(), [
              "investigate",
              target,
              `--scope=${scope}`,
              `--intent=${intent}`,
              "--output=json",
            ]);

            if (result.data) {
              await historyManager.add({
                id: result.data.investigation_id,
                scope,
                intent,
                target,
              });
              historyDataProvider.refresh();
              InvestigationResultViewer.createOrShow(context.extensionUri, result.data);
              vscode.window.showInformationMessage(
                `CodeMarshal: Investigation '${result.data.investigation_id}' started.`,
              );
            } else {
              const errorMessage = `CodeMarshal: Investigation failed. ${result.error || result.run.stderr}`;
              vscode.window.showErrorMessage(errorMessage);
              outputChannel.appendLine(errorMessage);
            }
          },
        );
      },
    ),

    vscode.commands.registerCommand(
      "codemarshal.observe",
      async () => {
        const scope = await vscode.window.showQuickPick(
          ["file", "module", "package", "project"],
          { placeHolder: "Select observation scope" },
        );
        if (!scope) return;

        const args: string[] = ["observe"];
        const activeFile = vscode.window.activeTextEditor?.document.uri.fsPath;
        const target = activeFile || getWorkspaceRoot();
        if (!target) {
          vscode.window.showWarningMessage(
            "CodeMarshal: No target selected for observation.",
          );
          return;
        }
        args.push(target, `--scope=${scope}`);

        // Quick pick for boolean flags
        const constitutional = await vscode.window.showQuickPick(["Yes", "No"], {
          placeHolder: "Include constitutional checks?",
        });
        if (constitutional === "Yes") args.push("--constitutional");

        await vscode.window.withProgress(
          {
            location: vscode.ProgressLocation.Notification,
            title: `CodeMarshal: Observing ${path.basename(target)}...`,
            cancellable: false,
          },
          () => runAndLog(args),
        );
      },
    ),

    vscode.commands.registerCommand("codemarshal.query", async () => {
      const investigationId = await vscode.window.showInputBox({
        prompt: "Enter Investigation/session ID (or 'latest')",
        value: "latest",
      });
      if (!investigationId) return;

      const question = await vscode.window.showInputBox({
        prompt: "Question to ask",
      });
      if (!question) return;

      const questionType = await vscode.window.showQuickPick(
        ["structure", "purpose", "connections", "anomalies", "thinking"],
        { placeHolder: "Select question type" },
      );
      if (!questionType) return;

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: "CodeMarshal: Running query...",
          cancellable: false,
        },
        async () => {
          const result = await runJsonCommand<{ answer: string }>(
            getCliPath(),
            [
              "query",
              investigationId,
              "--question",
              question,
              `--question-type=${questionType}`,
              "--output=json",
            ],
          );

          if (result.data) {
            InvestigationResultViewer.createOrShow(context.extensionUri, result.data);
            vscode.window.showInformationMessage(
              `CodeMarshal: Query answered.`,
            );
          } else {
            const errorMessage = `CodeMarshal: Query failed. ${result.error || result.run.stderr}`;
            vscode.window.showErrorMessage(errorMessage);
            outputChannel.appendLine(errorMessage);
          }
        },
      );
    }),

    vscode.commands.registerCommand("codemarshal.export", async () => {
      const investigationId = await vscode.window.showInputBox({
        prompt: "Enter Investigation/session ID (or 'latest')",
        value: "latest",
      });
      if (!investigationId) return;

      const format = await vscode.window.showQuickPick(
        ["markdown", "json", "html", "text", "csv", "jupyter", "pdf", "svg"],
        { placeHolder: "Select export format" },
      );
      if (!format) return;

      const outputUri = await vscode.window.showSaveDialog({
        saveLabel: "Export",
        filters: { "Export Target": [format] },
      });
      if (!outputUri) return;

      await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: "CodeMarshal: Exporting...",
          cancellable: false,
        },
        () =>
          runAndLog([
            "export",
            investigationId,
            `--format=${format}`,
            `--output=${outputUri.fsPath}`,
            "--confirm-overwrite",
          ]),
      );
    }),
  );
}
