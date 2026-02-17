"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.HistoryTreeDataProvider = void 0;
const vscode = __importStar(require("vscode"));
class HistoryTreeDataProvider {
    constructor(historyManager) {
        this.historyManager = historyManager;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.searchQuery = "";
    }
    setSearchQuery(query) {
        this.searchQuery = query;
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element) {
            return Promise.resolve([]); // No children for now
        }
        else {
            let history;
            if (this.searchQuery.trim() === "") {
                history = this.historyManager.getAll();
            }
            else {
                history = this.historyManager.search(this.searchQuery);
            }
            return Promise.resolve(history.map((inv) => new HistoryItem(inv)));
        }
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
}
exports.HistoryTreeDataProvider = HistoryTreeDataProvider;
class HistoryItem extends vscode.TreeItem {
    constructor(investigation) {
        super(`${investigation.id} - ${investigation.scope}:${investigation.intent}`, vscode.TreeItemCollapsibleState.None);
        this.investigation = investigation;
        this.tooltip = `${investigation.id} - ${new Date(investigation.timestamp).toLocaleString()}`;
        this.description = new Date(investigation.timestamp).toLocaleString();
        this.contextValue = "codemarshal.investigation";
    }
}
//# sourceMappingURL=historyTreeDataProvider.js.map