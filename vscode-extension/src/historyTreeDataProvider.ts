import * as vscode from "vscode";

export class HistoryTreeDataProvider
  implements vscode.TreeDataProvider<HistoryItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    HistoryItem | undefined | null | void
  > = new vscode.EventEmitter<HistoryItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    HistoryItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private data: HistoryItem[];

  constructor() {
    this.data = [
      new HistoryItem("Investigation 1", "Completed"),
      new HistoryItem("Investigation 2", "Running"),
      new HistoryItem("Investigation 3", "Failed"),
    ];
  }

  getTreeItem(element: HistoryItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: HistoryItem): Thenable<HistoryItem[]> {
    if (element) {
      return Promise.resolve([]); // No children
    } else {
      return Promise.resolve(this.data);
    }
  }

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }
}

class HistoryItem extends vscode.TreeItem {
  constructor(public readonly label: string, private readonly status: string) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.tooltip = `${this.label}-${this.status}`;
    this.description = this.status;
  }

  // TODO: Use a real icon
  // iconPath = {
  //   light: path.join(__filename, '..', '..', 'resources', 'light', 'dependency.svg'),
  //   dark: path.join(__filename, '..', '..', 'resources', 'dark', 'dependency.svg')
  // };
}
