import * as vscode from "vscode";
import * as path from "path";
import { runCodemarshal, runJsonCommand, normalizeFsPath } from "./cli";
import { DiagnosticsManager, PatternMatch } from "./diagnostics";
import { CodeMarshalCodeLensProvider } from "./codelens";
import { CodeMarshalHoverProvider } from "./hover";

type PatternScanResponse = {
  success: boolean;
  matches_found: number;
  matches: PatternMatch[];
  errors?: string[];
  error?: string;
};

function getCliPath(): string {
  return (
    vscode.workspace
      .getConfiguration("codemarshal")
      .get<string>("cliPath") || "codemarshal"
  );
}

function getScanOnSave(): boolean {
  return (
    vscode.workspace
      .getConfiguration("codemarshal")
      .get<boolean>("scanOnSave") ?? true
  );
}

function getWorkspaceRoot(): string | null {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    return null;
  }
  return folders[0].uri.fsPath;
}

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel("CodeMarshal");
  const matchStore = new Map<string, PatternMatch[]>();
  const diagnosticsCollection =
    vscode.languages.createDiagnosticCollection("CodeMarshal");
  const diagnostics = new DiagnosticsManager(diagnosticsCollection);
  const codelensProvider = new CodeMarshalCodeLensProvider(matchStore);
  const hoverProvider = new CodeMarshalHoverProvider(matchStore);

  async function runAndLog(args: string[], cwd?: string): Promise<void> {
    output.show(true);
    output.appendLine(`codemarshal ${args.join(" ")}`);
    const result = await runCodemarshal(getCliPath(), args, cwd);
    if (result.stdout) {
      output.appendLine(result.stdout);
    }
    if (result.stderr) {
      output.appendLine(result.stderr);
    }
  }

  async function scanFile(uri: vscode.Uri): Promise<void> {
    const cliPath = getCliPath();
    const result = await runJsonCommand<PatternScanResponse>(cliPath, [
      "pattern",
      "scan",
      uri.fsPath,
      "--output=json",
    ]);
    if (!result.data) {
      output.appendLine(
        `Pattern scan failed: ${result.error || result.run.stderr}`,
      );
      return;
    }
    const matches = result.data.matches || [];
    const normalizedFile = normalizeFsPath(uri.fsPath);
    const filtered = matches.filter(
      (match) => normalizeFsPath(match.file) === normalizedFile,
    );
    matchStore.set(normalizedFile, filtered);
    diagnostics.updateForFile(uri, filtered);
    codelensProvider.refresh();
  }

  async function scanWorkspace(): Promise<void> {
    const root = getWorkspaceRoot();
    if (!root) {
      vscode.window.showWarningMessage(
        "CodeMarshal: no workspace folder found.",
      );
      return;
    }
    const cliPath = getCliPath();
    const result = await runJsonCommand<PatternScanResponse>(cliPath, [
      "pattern",
      "scan",
      root,
      "--output=json",
    ]);
    if (!result.data) {
      output.appendLine(
        `Pattern scan failed: ${result.error || result.run.stderr}`,
      );
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
  }

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codemarshal.investigate",
      async () => {
        const activeFile = vscode.window.activeTextEditor?.document
          .uri.fsPath;
        const target =
          activeFile ? path.dirname(activeFile) : getWorkspaceRoot();
        if (!target) {
          vscode.window.showWarningMessage(
            "CodeMarshal: no target selected.",
          );
          return;
        }
        await runAndLog([
          "investigate",
          target,
          "--scope=module",
          "--intent=initial_scan",
        ]);
      },
    ),
    vscode.commands.registerCommand(
      "codemarshal.observe",
      async () => {
        const activeFile = vscode.window.activeTextEditor?.document
          .uri.fsPath;
        const target = activeFile || getWorkspaceRoot();
        if (!target) {
          vscode.window.showWarningMessage(
            "CodeMarshal: no target selected.",
          );
          return;
        }
        await runAndLog([
          "observe",
          target,
          "--scope=module",
          "--constitutional",
        ]);
      },
    ),
    vscode.commands.registerCommand(
      "codemarshal.scanPatterns",
      async () => {
        await scanWorkspace();
      },
    ),
    vscode.commands.registerCommand(
      "codemarshal.listPatterns",
      async () => {
        const result = await runJsonCommand<{
          total_count: number;
          patterns: Array<{
            id: string;
            name: string;
            severity: string;
          }>;
        }>(getCliPath(), ["pattern", "list", "--output=json"]);
        output.show(true);
        if (!result.data) {
          output.appendLine(
            `Pattern list failed: ${result.error || result.run.stderr}`,
          );
          return;
        }
        output.appendLine(
          `Available patterns: ${result.data.total_count}`,
        );
        for (const pattern of result.data.patterns) {
          output.appendLine(
            `${pattern.id} - ${pattern.name} (${pattern.severity})`,
          );
        }
      },
    ),
    vscode.commands.registerCommand("codemarshal.query", async () => {
      const investigationId = await vscode.window.showInputBox({
        prompt: "Investigation/session ID",
      });
      if (!investigationId) {
        return;
      }
      const question = await vscode.window.showInputBox({
        prompt: "Question to ask",
      });
      if (!question) {
        return;
      }
      await runAndLog([
        "query",
        investigationId,
        "--question",
        question,
        "--question-type=connections",
      ]);
    }),
    vscode.commands.registerCommand("codemarshal.export", async () => {
      const investigationId = await vscode.window.showInputBox({
        prompt: "Investigation/session ID",
      });
      if (!investigationId) {
        return;
      }
      const format = await vscode.window.showQuickPick(
        ["markdown", "json", "html", "text"],
        { placeHolder: "Export format" },
      );
      if (!format) {
        return;
      }
      const outputUri = await vscode.window.showSaveDialog({
        saveLabel: "Export",
      });
      if (!outputUri) {
        return;
      }
      await runAndLog([
        "export",
        investigationId,
        `--format=${format}`,
        `--output=${outputUri.fsPath}`,
        "--confirm-overwrite",
      ]);
    }),
    vscode.commands.registerCommand(
      "codemarshal.showPatternsForFile",
      async (uri?: vscode.Uri) => {
        const targetUri =
          uri || vscode.window.activeTextEditor?.document.uri;
        if (!targetUri) {
          return;
        }
        const matches =
          matchStore.get(normalizeFsPath(targetUri.fsPath)) || [];
        output.show(true);
        output.appendLine(
          `Pattern matches for ${targetUri.fsPath}: ${matches.length}`,
        );
        for (const match of matches) {
          output.appendLine(
            `- ${match.pattern_name || match.pattern_id}: ${match.message}`,
          );
        }
      },
    ),
  );

  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (!getScanOnSave()) {
        return;
      }
      void scanFile(document.uri);
    }),
  );

  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider(
      { scheme: "file" },
      codelensProvider,
    ),
    vscode.languages.registerHoverProvider(
      { scheme: "file" },
      hoverProvider,
    ),
  );

  context.subscriptions.push(output, diagnosticsCollection);
}

export function deactivate(): void {
  // no-op
}
