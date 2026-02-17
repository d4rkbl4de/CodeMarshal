import * as vscode from "vscode";

export class PatternCache {
  private static cache = new Map<string, { data: any; timestamp: number }>();
  private static readonly MAX_AGE = 5 * 60 * 1000; // 5 minutes

  static get(uri: vscode.Uri): any | null {
    const key = uri.toString();
    const cached = this.cache.get(key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > this.MAX_AGE) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  static set(uri: vscode.Uri, data: any): void {
    const key = uri.toString();
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  static clear(): void {
    this.cache.clear();
  }

  static clearExpired(): void {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.MAX_AGE) {
        this.cache.delete(key);
      }
    }
  }
}