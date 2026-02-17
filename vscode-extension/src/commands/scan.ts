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
import { PatternCache } from "../patternCache";

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
        PatternCache.set(uri, filtered);
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

  const config = vscode.workspace.getConfiguration("codemarshal");
  const debounceTime = config.get<number>("debounceTime", 500);
  const showWarnings = config.get<boolean>("showWarnings", true);
  const showInfo = config.get<boolean>("showInfo", true);
  const includeGitignore = config.get<boolean>("includeGitignore", true);

  const debouncedScanFile = debounce(scanFile, debounceTime);

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
      const fileName = path.basename(document.fileName);
      if (fileName.startsWith(".git") || fileName.startsWith(".")) {
        return;
      }
      debouncedScanFile(document.uri);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("codemarshal.cache.clear", async () => {
      PatternCache.clear();
      vscode.window.showInformationMessage("CodeMarshal: Cache cleared.");
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemarshal.scanPatternsForFile",
      async (uri?: vscode.Uri) => {
        const targetUri =
          uri || vscode.window.activeTextEditor?.document.uri;
        if (!targetUri) {
          vscode.window.showWarningMessage(
            "CodeMarshal: No file selected.",
          );
          return;
        }

        await scanFile(targetUri);
      },
    ),
    vscode.commands.registerCommand(
      "codemarshal.scanPatternsForFolder",
      async (uri?: vscode.Uri) => {
        const targetUri =
          uri || vscode.workspace.workspaceFolders?.[0]?.uri;
        if (!targetUri) {
          vscode.window.showWarningMessage(
            "CodeMarshal: No folder selected.",
          );
          return;
        }

        if (targetUri.scheme !== "file") {
          vscode.window.showWarningMessage(
            "CodeMarshal: Cannot scan non-file URI.",
          );
          return;
        }

        const folderPath = targetUri.fsPath;
        await scanFolder(folderPath, matchStore, diagnostics, codelensProvider);
      },
    ),
  );
}

async function scanFolder(
  folderPath: string,
  matchStore: Map<string, PatternMatch[]>,
  diagnostics: DiagnosticsManager,
  codelensProvider: CodeMarshalCodeLensProvider,
): Promise<void> {
  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: `CodeMarshal: Scanning folder ${path.basename(folderPath)}...`,
      cancellable: false,
    },
    async () => {
      const cliPath = getCliPath();
      const result = await runJsonCommand<PatternScanResponse>(cliPath, [
        "pattern",
        "scan",
        folderPath,
        "--output=json",
      ]);

      if (!result.data) {
        const errorMessage = `CodeMarshal: Pattern scan failed for folder. ${result.error || result.run.stderr}`;
        vscode.window.showErrorMessage(errorMessage);
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
        `CodeMarshal: Found ${matches.length} pattern matches in folder ${path.basename(folderPath)}.`,
      );
    },
  );
}
