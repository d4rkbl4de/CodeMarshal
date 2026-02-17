"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HistoryManager = void 0;
const HISTORY_KEY = "codemarshal.investigationHistory";
class HistoryManager {
    constructor(context) {
        this.context = context;
    }
    async add(investigation) {
        const history = this.getAll();
        const newInvestigation = {
            ...investigation,
            timestamp: Date.now(),
        };
        history.unshift(newInvestigation); // Add to the beginning
        await this.context.globalState.update(HISTORY_KEY, history);
    }
    getAll() {
        return this.context.globalState.get(HISTORY_KEY, []);
    }
    search(query) {
        const all = this.getAll();
        const lowerQuery = query.toLowerCase();
        return all.filter((inv) => {
            return (inv.id.toLowerCase().includes(lowerQuery) ||
                inv.scope.toLowerCase().includes(lowerQuery) ||
                inv.intent.toLowerCase().includes(lowerQuery) ||
                inv.target.toLowerCase().includes(lowerQuery) ||
                inv.tags?.some((tag) => tag.toLowerCase().includes(lowerQuery)) ||
                new Date(inv.timestamp).toLocaleDateString().includes(lowerQuery));
        });
    }
    async clear() {
        await this.context.globalState.update(HISTORY_KEY, []);
    }
}
exports.HistoryManager = HistoryManager;
//# sourceMappingURL=historyManager.js.map