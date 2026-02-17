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
exports.InvestigationResultViewer = void 0;
const vscode = __importStar(require("vscode"));
class InvestigationResultViewer {
    static createOrShow(extensionUri, content) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;
        // If we already have a panel, show it.
        if (InvestigationResultViewer.currentPanel) {
            InvestigationResultViewer.currentPanel.panel.reveal(column);
            InvestigationResultViewer.currentPanel.update(content);
            return;
        }
        // Otherwise, create a new panel.
        const panel = vscode.window.createWebviewPanel("investigationResult", // Identifies the type of the webview. Used internally
        "Investigation Result", // Title of the panel displayed to the user
        column || vscode.ViewColumn.One, // Editor column to show the new webview panel in.
        {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(extensionUri, "media")],
        });
        InvestigationResultViewer.currentPanel = new InvestigationResultViewer(panel, extensionUri);
        InvestigationResultViewer.currentPanel.update(content);
    }
    constructor(panel, extensionUri) {
        this.disposables = [];
        this.panel = panel;
        this.extensionUri = extensionUri;
        // Set the webview's initial html content
        this.panel.webview.html = this.getHtmlForWebview();
        // Listen for when the panel is disposed
        // This happens when the user closes the panel or right-click
        this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    }
    update(content) {
        this.panel.webview.postMessage({
            command: "update",
            content: content,
        });
    }
    dispose() {
        InvestigationResultViewer.currentPanel = undefined;
        this.panel.dispose();
        while (this.disposables.length) {
            const x = this.disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
    getHtmlForWebview() {
        // A very basic HTML structure
        return `<!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Investigation Result</title>
      </head>
      <body>
        <h1>Investigation Result</h1>
        <pre id="content"></pre>
        <script>
          const vscode = acquireVsCodeApi();
          const contentElement = document.getElementById('content');
          window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
              case 'update':
                contentElement.textContent = JSON.stringify(message.content, null, 2);
                break;
            }
          });
        </script>
      </body>
      </html>`;
    }
}
exports.InvestigationResultViewer = InvestigationResultViewer;
//# sourceMappingURL=InvestigationResultViewer.js.map