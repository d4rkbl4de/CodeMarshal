import * as vscode from "vscode";
import { DiagnosticsManager, PatternMatch } from "./diagnostics";
import { CodeMarshalCodeLensProvider } from "./codelens";
import { CodeMarshalHoverProvider } from "./hover";
import { registerScanCommands } from "./commands/scan";
import { registerInvestigationCommands } from "./commands/investigation";
import { registerPatternCommands } from "./commands/patterns";
import { registerConfigCommands } from "./commands/config";
import { HistoryTreeDataProvider } from "./historyTreeDataProvider";
import { HistoryManager } from "./historyManager";

export function activate(context: vscode.ExtensionContext): void {
  // Core services and state
  const output = vscode.window.createOutputChannel("CodeMarshal");
  const matchStore = new Map<string, PatternMatch[]>();
  const diagnosticsCollection =
    vscode.languages.createDiagnosticCollection("CodeMarshal");
  const diagnostics = new DiagnosticsManager(diagnosticsCollection);
  const codelensProvider = new CodeMarshalCodeLensProvider(matchStore);
  const hoverProvider = new CodeMarshalHoverProvider(matchStore);
  const historyManager = new HistoryManager(context);

  // --- Status Bar Indicator ---
  const statusBarIndicator = vscode.window.createStatusBarItem(
    "codemarshal.status",
    vscode.StatusBarAlignment.Right,
    100,
  );
  statusBarIndicator.text = "$(search) CodeMarshal: No matches";
  statusBarIndicator.command = "codemarshal.showPatternsForFile";
  statusBarIndicator.show();

  // --- Tree View Registration ---
  const historyDataProvider = new HistoryTreeDataProvider(historyManager);
  vscode.window.createTreeView("codemarshal.historyView", {
    treeDataProvider: historyDataProvider,
  });

  context.subscriptions.push(
    vscode.commands.registerCommand("codemarshal.history.search", async () => {
      const query = await vscode.window.showInputBox({
        prompt: "Search investigation history",
        placeHolder: "Enter search terms (ID, scope, intent, target, date...)",
      });
      if (query !== undefined && query !== null && query !== "") {
        historyDataProvider.setSearchQuery(query);
      }
    }),
  );

  // --- Command Registration ---
  registerScanCommands(context, output, matchStore, diagnostics, codelensProvider);
  registerInvestigationCommands(context, output, historyManager, historyDataProvider);
  registerPatternCommands(context, output, matchStore);
  registerConfigCommands(context);

  // --- Update status bar when file changes ---
  const updateStatusBar = (document: vscode.TextDocument): void => {
    const matches = matchStore.get(document.uri.fsPath);
    const filteredMatches = matches?.filter((match) => {
      const severity = match.severity?.toLowerCase();
      const config = vscode.workspace.getConfiguration("codemarshal");
      if (severity === "critical") return true;
      if (severity === "warning" && config.get<boolean>("showWarnings", true)) return true;
      if (severity === "info" && config.get<boolean>("showInfo", true)) return true;
      return false;
    });

    if (filteredMatches && filteredMatches.length > 0) {
      statusBarIndicator.text = `$(search) CodeMarshal: ${filteredMatches.length} match${filteredMatches.length > 1 ? 'es' : ''}`;
      statusBarIndicator.tooltip = `${filteredMatches.length} pattern matches in ${document.fileName}`;
    } else {
      statusBarIndicator.text = "$(search) CodeMarshal: No matches";
      statusBarIndicator.tooltip = "Run 'CodeMarshal: Scan Patterns' to scan files";
    }
    statusBarIndicator.show();
  };

  // --- Context Menu Registration ---
  const fileContext = vscode.window.createTextEditorDecorationType({
    borderWidth: "2px",
    borderStyle: "solid",
    borderColor: "transparent",
  });

  context.subscriptions.push(
    vscode.commands.registerCommand("codemarshal.history.refresh", () =>
      historyDataProvider.refresh(),
    ),
    vscode.commands.registerCommand("codemarshal.history.clear", async () => {
      await historyManager.clear();
      historyDataProvider.refresh();
    }),
    vscode.commands.registerCommand("codemarshal.applyQuickFix", async (match: PatternMatch) => {
      if (!match.fix) {
        vscode.window.showWarningMessage("No fix available for this pattern");
        return;
      }

      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("No active editor found");
        return;
      }

      const line = Math.max(0, (match.line || 1) - 1);
      const start = new vscode.Position(line, 0);
      const end = new vscode.Position(line, Math.max(1, (match.matched || "").length));

      await editor.edit((edit) => {
        edit.replace(new vscode.Range(start, end), match.fix || "");
      });

      vscode.window.showInformationMessage(
        `Applied fix for: ${match.pattern_name || match.pattern_id || "Pattern"}`,
      );
    }),
    vscode.commands.registerCommand("codemarshal.goToPattern", async (params) => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.document.uri.toString() !== params.uri.toString()) {
        await vscode.window.showTextDocument(params.uri);
      }

      const position = new vscode.Position(params.line, 0);
      await vscode.window.activeTextEditor?.revealRange(
        new vscode.Range(position, position),
        vscode.TextEditorRevealType.InCenter,
      );

      if (params.match && params.match.severity) {
        const severity = params.match.severity.toLowerCase();
        const color = severity === "critical" ? "#f48771" : severity === "warning" ? "#cca700" : "#75beff";
        const decoration = vscode.window.createTextEditorDecorationType({
          borderWidth: "2px",
          borderStyle: "solid",
          borderColor: color,
        });

        const range = new vscode.Range(params.line, 0, params.line, 9999);
        if (editor) {
          editor.setDecorations(decoration, [range]);

          setTimeout(() => {
            if (editor) {
              editor.setDecorations(decoration, []);
            }
          }, 3000);
        }
      }

      vscode.window.showInformationMessage(
        `Navigated to pattern: ${params.patternName}`,
      );
    }),
  );

  // --- Event Subscriptions ---
  context.subscriptions.push(
    vscode.languages.registerCodeLensProvider(
      { scheme: "file" },
      codelensProvider,
    ),
    vscode.languages.registerHoverProvider(
      { scheme: "file" },
      hoverProvider,
    ),
    output,
    diagnosticsCollection,
    statusBarIndicator,
    vscode.workspace.onDidOpenTextDocument(updateStatusBar),
    vscode.workspace.onDidChangeTextDocument((event) => {
      if (event.document.uri.scheme !== "file") return;
      updateStatusBar(event.document);
    }),
    vscode.workspace.onDidCloseTextDocument((document) => {
      statusBarIndicator.text = "$(search) CodeMarshal: No matches";
    }),
  );
}

export function deactivate(): void {
  // no-op
}
