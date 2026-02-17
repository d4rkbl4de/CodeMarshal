"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PatternCache = void 0;
class PatternCache {
    static get(uri) {
        const key = uri.toString();
        const cached = this.cache.get(key);
        if (!cached)
            return null;
        if (Date.now() - cached.timestamp > this.MAX_AGE) {
            this.cache.delete(key);
            return null;
        }
        return cached.data;
    }
    static set(uri, data) {
        const key = uri.toString();
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
        });
    }
    static clear() {
        this.cache.clear();
    }
    static clearExpired() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > this.MAX_AGE) {
                this.cache.delete(key);
            }
        }
    }
}
exports.PatternCache = PatternCache;
PatternCache.cache = new Map();
PatternCache.MAX_AGE = 5 * 60 * 1000; // 5 minutes
//# sourceMappingURL=patternCache.js.map