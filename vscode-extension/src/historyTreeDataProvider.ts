import * as vscode from "vscode";
import { HistoryManager, Investigation } from "./historyManager";

export class HistoryTreeDataProvider
  implements vscode.TreeDataProvider<HistoryItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    HistoryItem | undefined | null | void
  > = new vscode.EventEmitter<HistoryItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    HistoryItem | undefined | null | void
  > = this._onDidChangeTreeData.event;
  private searchQuery: string = "";

  constructor(private historyManager: HistoryManager) {}

  setSearchQuery(query: string): void {
    this.searchQuery = query;
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: HistoryItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: HistoryItem): Thenable<HistoryItem[]> {
    if (element) {
      return Promise.resolve([]); // No children for now
    } else {
      let history: Investigation[];

      if (this.searchQuery.trim() === "") {
        history = this.historyManager.getAll();
      } else {
        history = this.historyManager.search(this.searchQuery);
      }

      return Promise.resolve(history.map((inv) => new HistoryItem(inv)));
    }
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }
}

class HistoryItem extends vscode.TreeItem {
  constructor(public readonly investigation: Investigation) {
    super(
      `${investigation.id} - ${investigation.scope}:${investigation.intent}`,
      vscode.TreeItemCollapsibleState.None,
    );
    this.tooltip = `${investigation.id} - ${new Date(investigation.timestamp).toLocaleString()}`;
    this.description = new Date(investigation.timestamp).toLocaleString();
    this.contextValue = "codemarshal.investigation";
  }

  // TODO: Add command to view investigation details
  // command = {
  //   command: 'codemarshal.viewInvestigation',
  //   title: 'View Investigation',
  //   arguments: [this.investigation],
  // };
}
