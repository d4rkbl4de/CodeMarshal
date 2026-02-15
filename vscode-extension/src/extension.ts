import * as vscode from "vscode";
import { DiagnosticsManager, PatternMatch } from "./diagnostics";
import { CodeMarshalCodeLensProvider } from "./codelens";
import { CodeMarshalHoverProvider } from "./hover";
import { registerScanCommands } from "./commands/scan";
import { registerInvestigationCommands } from "./commands/investigation";
import { registerPatternCommands } from "./commands/patterns";
import { registerConfigCommands } from "./commands/config";
import { HistoryTreeDataProvider } from "./historyTreeDataProvider";

export function activate(context: vscode.ExtensionContext): void {
  // Core services and state
  const output = vscode.window.createOutputChannel("CodeMarshal");
  const matchStore = new Map<string, PatternMatch[]>();
  const diagnosticsCollection =
    vscode.languages.createDiagnosticCollection("CodeMarshal");
  const diagnostics = new DiagnosticsManager(diagnosticsCollection);
  const codelensProvider = new CodeMarshalCodeLensProvider(matchStore);
  const hoverProvider = new CodeMarshalHoverProvider(matchStore);

  // --- Command Registration ---
  registerScanCommands(context, output, matchStore, diagnostics, codelensProvider);
  registerInvestigationCommands(context, output);
  registerPatternCommands(context, output, matchStore);
  registerConfigCommands(context);

  // --- Tree View Registration ---
  const historyDataProvider = new HistoryTreeDataProvider();
  vscode.window.createTreeView("codemarshal.historyView", {
    treeDataProvider: historyDataProvider,
  });

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
  );
}

export function deactivate(): void {
  // no-op
}
