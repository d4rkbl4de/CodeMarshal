import * as vscode from "vscode";

export class InvestigationResultViewer {
  public static currentPanel: InvestigationResultViewer | undefined;
  private readonly panel: vscode.WebviewPanel;
  private readonly extensionUri: vscode.Uri;
  private disposables: vscode.Disposable[] = [];

  public static createOrShow(extensionUri: vscode.Uri, content: any) {
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
    const panel = vscode.window.createWebviewPanel(
      "investigationResult", // Identifies the type of the webview. Used internally
      "Investigation Result", // Title of the panel displayed to the user
      column || vscode.ViewColumn.One, // Editor column to show the new webview panel in.
      {
        enableScripts: true,
        localResourceRoots: [vscode.Uri.joinPath(extensionUri, "media")],
      },
    );

    InvestigationResultViewer.currentPanel = new InvestigationResultViewer(
      panel,
      extensionUri,
    );
    InvestigationResultViewer.currentPanel.update(content);
  }

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this.panel = panel;
    this.extensionUri = extensionUri;

    // Set the webview's initial html content
    this.panel.webview.html = this.getHtmlForWebview();

    // Listen for when the panel is disposed
    // This happens when the user closes the panel or right-click
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
  }

  public update(content: any) {
    this.panel.webview.postMessage({
      command: "update",
      content: content,
    });
  }

  public dispose() {
    InvestigationResultViewer.currentPanel = undefined;
    this.panel.dispose();
    while (this.disposables.length) {
      const x = this.disposables.pop();
      if (x) {
        x.dispose();
      }
    }
  }

  private getHtmlForWebview() {
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
