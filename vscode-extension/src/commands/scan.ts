import * as vscode from "vscode";
import * as path from "path";
import {
  runJsonCommand,
  getCliPath,
  getScanOnSave,
  getWorkspaceRoot,
} from "../cli";
import { DiagnosticsManager, PatternMatch } from "../diagnostics";
import { CodeMarshalCodeLensProvider } from "../codelens";
import { normalizeFsPath, debounce } from "../utils";

type PatternScanResponse = {
  success: boolean;
  matches_found: number;
  matches: PatternMatch[];
  errors?: string[];
  error?: string;
};

// Note: outputChannel, matchStore, diagnostics, and codelensProvider are passed in from activate()
export function registerScanCommands(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel,
  matchStore: Map<string, PatternMatch[]>,
  diagnostics: DiagnosticsManager,
  codelensProvider: CodeMarshalCodeLensProvider,
): void {
  async function scanFile(uri: vscode.Uri): Promise<void> {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `CodeMarshal: Scanning ${path.basename(uri.fsPath)}`,
        cancellable: false,
      },
      async () => {
        const cliPath = getCliPath();
        const result = await runJsonCommand<PatternScanResponse>(cliPath, [
          "pattern",
          "scan",
          uri.fsPath,
          "--output=json",
        ]);
        if (!result.data) {
          const errorMessage = `CodeMarshal: Pattern scan failed for ${path.basename(uri.fsPath)}. ${result.error || result.run.stderr}`;
          vscode.window.showErrorMessage(errorMessage);
          outputChannel.appendLine(errorMessage);
          return;
        }
        const matches = result.data.matches || [];
        const normalized = normalizeFsPath(uri.fsPath);
        const filtered = matches.filter(
          (match) => normalizeFsPath(match.file) === normalized,
        );
        matchStore.set(normalized, filtered);
        diagnostics.updateForFile(uri, filtered);
        codelensProvider.refresh();
        vscode.window.showInformationMessage(
          `CodeMarshal: Found ${filtered.length} pattern matches in ${path.basename(uri.fsPath)}.`,
        );
      },
    );
  }

  async function scanWorkspace(): Promise<void> {
    const root = getWorkspaceRoot();
    if (!root) {
      vscode.window.showWarningMessage(
        "CodeMarshal: No workspace folder found.",
      );
      return;
    }

    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "CodeMarshal: Scanning workspace for patterns...",
        cancellable: false,
      },
      async () => {
        const cliPath = getCliPath();
        const result = await runJsonCommand<PatternScanResponse>(cliPath, [
          "pattern",
          "scan",
          root,
          "--output=json",
        ]);
        if (!result.data) {
          const errorMessage = `CodeMarshal: Pattern scan failed for workspace. ${result.error || result.run.stderr}`;
          vscode.window.showErrorMessage(errorMessage);
          outputChannel.appendLine(errorMessage);
          return;
        }
        const matches = result.data.matches || [];
        const matchesByFile = new Map<string, PatternMatch[]>();
        for (const match of matches) {
          const key = normalizeFsPath(match.file);
          const list = matchesByFile.get(key) || [];
          list.push(match);
          matchesByFile.set(key, list);
        }
        matchStore.clear();
        for (const [filePath, fileMatches] of matchesByFile.entries()) {
          matchStore.set(filePath, fileMatches);
          diagnostics.updateForFile(
            vscode.Uri.file(filePath),
            fileMatches,
          );
        }
        codelensProvider.refresh();
        vscode.window.showInformationMessage(
          `CodeMarshal: Found ${matches.length} pattern matches in the workspace.`,
        );
      },
    );
  }

  const debouncedScanFile = debounce(scanFile, 500);

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemarshal.scanPatterns",
      async () => {
        await scanWorkspace();
      },
    ),
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (!getScanOnSave()) {
        return;
      }
      // Don't scan `.git` files, output channels, etc.
      if (document.uri.scheme !== "file") {
        return;
      }
      debouncedScanFile(document.uri);
    }),
  );
}
