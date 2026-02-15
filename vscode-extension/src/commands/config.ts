import * as vscode from "vscode";
import { getCliPath } from "../cli";

export function registerConfigCommands(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemarshal.setCliPath",
      async () => {
        const newCliPath = await vscode.window.showInputBox({
          prompt: "Enter the path to the CodeMarshal CLI executable",
          value: getCliPath(),
        });
        if (newCliPath === undefined) {
          return; // User cancelled
        }
        await vscode.workspace
          .getConfiguration("codemarshal")
          .update("cliPath", newCliPath, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(
          `CodeMarshal CLI path updated to: ${newCliPath}`,
        );
      },
    ),
  );
}
