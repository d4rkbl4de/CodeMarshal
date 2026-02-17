import { spawn } from "child_process";
import * as vscode from "vscode";
import * as fs from "fs";
import { normalizeFsPath } from "./utils";

export function getCliPath(): string {
  return (
    vscode.workspace
      .getConfiguration("codemarshal")
      .get<string>("cliPath") || "codemarshal"
  );
}

export function getScanOnSave(): boolean {
  return (
    vscode.workspace
      .getConfiguration("codemarshal")
      .get<boolean>("scanOnSave") ?? true
  );
}

export function getWorkspaceRoot(): string | null {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    return null;
  }
  return folders[0].uri.fsPath;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export interface JsonResult<T> {
  data: T | null;
  error: string | null;
  run: RunResult;
}

export interface RetryOptions {
  maxRetries?: number;
  delay?: number;
  onRetry?: (attempt: number, error: Error) => void;
}

function extractJsonPayload(text: string): string | null {
  const trimmed = text.trim();
  if (!trimmed) {
    return null;
  }
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    return trimmed;
  }
  const firstBrace = trimmed.indexOf("{");
  const lastBrace = trimmed.lastIndexOf("}");
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    return trimmed.slice(firstBrace, lastBrace + 1);
  }
  return null;
}

async function handleCliNotFoundError(cliPath: string): Promise<void> {
  const item = await vscode.window.showErrorMessage(
    `CodeMarshal: CLI not found at '${cliPath}'. Please check your 'codemarshal.cliPath' setting.`,
    "Go to Settings",
    "Try Reinstalling",
  );
  if (item === "Go to Settings") {
    await vscode.commands.executeCommand(
      "workbench.action.openSettings",
      "@ext:codemarshal.codemarshal codemarshal.cliPath",
    );
  } else if (item === "Try Reinstalling") {
    await vscode.env.openExternal(vscode.Uri.parse("https://github.com/codemarshal/cli"));
  }
}

async function handleExecutionError(
  errorMessage: string,
  exitCode: number,
): Promise<void> {
  const retryActions = ["Retry", "View Output", "Ignore"];
  const item = await vscode.window.showWarningMessage(
    `CodeMarshal command failed (exit code: ${exitCode}).`,
    ...retryActions,
  );

  if (item === "Retry") {
    return;
  } else if (item === "View Output") {
    const outputChannel = vscode.window.createOutputChannel("CodeMarshal");
    outputChannel.show(true);
    outputChannel.appendLine(errorMessage);
    return;
  } else if (item === "Ignore") {
    return;
  }
}

export async function runCodemarshal(
  cliPath: string,
  args: string[],
  cwd?: string,
  options?: RetryOptions,
): Promise<RunResult> {
  const maxRetries = options?.maxRetries || 1;
  const delay = options?.delay || 1000;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await fs.promises.stat(cliPath);
    } catch (err) {
      if ((err as any).code === "ENOENT") {
        await handleCliNotFoundError(cliPath);
        return {
          stdout: "",
          stderr: `CLI not found at ${cliPath}`,
          exitCode: 1,
        };
      }
    }

    return new Promise((resolve) => {
      const proc = spawn(cliPath, args, {
        cwd,
        shell: false,
        windowsHide: true,
      });
      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (chunk) => {
        stdout += chunk.toString();
      });
      proc.stderr.on("data", (chunk) => {
        stderr += chunk.toString();
      });
      proc.on("close", (code) => {
        const exitCode = typeof code === "number" ? code : 1;
        if (exitCode !== 0) {
          const errorMessage = `Command exited with code ${exitCode}. Stderr: ${stderr}`;
          if (attempt < maxRetries) {
            options?.onRetry?.(attempt, new Error(errorMessage));
          } else {
            handleExecutionError(errorMessage, exitCode);
          }
        }
        resolve({
          stdout,
          stderr,
          exitCode,
        });
      });
      proc.on("error", (err) => {
        if (attempt < maxRetries) {
          options?.onRetry?.(attempt, err);
        } else {
          handleExecutionError(String(err), 1);
        }
        resolve({
          stdout: "",
          stderr: String(err),
          exitCode: 1,
        });
      });
    });
  }

  throw new Error(`Max retries (${maxRetries}) exceeded`);
}

export async function runJsonCommand<T>(
  cliPath: string,
  args: string[],
  cwd?: string,
  options?: RetryOptions,
): Promise<JsonResult<T>> {
  const run = await runCodemarshal(cliPath, args, cwd, options);
  const payload = extractJsonPayload(run.stdout);

  if (!payload) {
    const error = run.stderr || "No JSON payload detected";
    const tryAction = await vscode.window.showWarningMessage(
      `Failed to parse JSON output: ${error}. Try raw output?`,
      "Try Raw Output",
      "Dismiss",
    );
    if (tryAction === "Try Raw Output") {
      const outputChannel = vscode.window.createOutputChannel("CodeMarshal");
      outputChannel.show(true);
      outputChannel.appendLine("Raw output:");
      outputChannel.appendLine(run.stdout);
      outputChannel.appendLine("Stderr:");
      outputChannel.appendLine(run.stderr);
    }
    return {
      data: null,
      error,
      run,
    };
  }

  try {
    return {
      data: JSON.parse(payload) as T,
      error: null,
      run,
    };
  } catch (err) {
    const tryAction = await vscode.window.showWarningMessage(
      `Failed to parse JSON: ${String(err)}. Try raw output?`,
      "Try Raw Output",
      "Dismiss",
    );
    if (tryAction === "Try Raw Output") {
      const outputChannel = vscode.window.createOutputChannel("CodeMarshal");
      outputChannel.show(true);
      outputChannel.appendLine("Raw output:");
      outputChannel.appendLine(run.stdout);
      outputChannel.appendLine("Stderr:");
      outputChannel.appendLine(run.stderr);
    }
    return {
      data: null,
      error: String(err),
      run,
    };
  }
}

export async function runJsonCommandSafe<T>(
  cliPath: string,
  args: string[],
  cwd?: string,
  options?: RetryOptions,
): Promise<JsonResult<T>> {
  const result = await runJsonCommand<T>(cliPath, args, cwd, options);
  const parsedData = result.data;
  if (parsedData === null) {
    return result;
  }
  const safeData = parsedData as T & { error: string };
  return {
    data: safeData,
    error: null,
    run: result.run,
  };
}
