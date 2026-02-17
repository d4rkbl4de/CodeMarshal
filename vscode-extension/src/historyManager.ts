import * as vscode from "vscode";

const HISTORY_KEY = "codemarshal.investigationHistory";

export interface Investigation {
  id: string;
  timestamp: number;
  scope: string;
  intent: string;
  target: string;
  tags?: string[];
}

export class HistoryManager {
  constructor(private context: vscode.ExtensionContext) {}

  async add(investigation: Omit<Investigation, "timestamp">): Promise<void> {
    const history = this.getAll();
    const newInvestigation: Investigation = {
      ...investigation,
      timestamp: Date.now(),
    };
    history.unshift(newInvestigation); // Add to the beginning
    await this.context.globalState.update(HISTORY_KEY, history);
  }

  getAll(): Investigation[] {
    return this.context.globalState.get<Investigation[]>(HISTORY_KEY, []);
  }

  search(query: string): Investigation[] {
    const all = this.getAll();
    const lowerQuery = query.toLowerCase();
    return all.filter((inv) => {
      return (
        inv.id.toLowerCase().includes(lowerQuery) ||
        inv.scope.toLowerCase().includes(lowerQuery) ||
        inv.intent.toLowerCase().includes(lowerQuery) ||
        inv.target.toLowerCase().includes(lowerQuery) ||
        inv.tags?.some((tag) => tag.toLowerCase().includes(lowerQuery)) ||
        new Date(inv.timestamp).toLocaleDateString().includes(lowerQuery)
      );
    });
  }

  async clear(): Promise<void> {
    await this.context.globalState.update(HISTORY_KEY, []);
  }
}
