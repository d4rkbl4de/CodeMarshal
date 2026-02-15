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

async function handleCliNotFoundError(cliPath: string) {
  const item = await vscode.window.showErrorMessage(
    `CodeMarshal: CLI not found at '${cliPath}'. Please check your 'codemarshal.cliPath' setting.`,
    "Go to Settings",
  );
  if (item === "Go to Settings") {
    await vscode.commands.executeCommand(
      "workbench.action.openSettings",
      "@ext:codemarshal-inc.codemarshal codemarshal.cliPath",
    );
  }
}

export function runCodemarshal(
  cliPath: string,
  args: string[],
  cwd?: string,
): Promise<RunResult> {
  return new Promise(async (resolve) => {
    try {
      await fs.promises.stat(cliPath);
    } catch (err) {
      if ((err as any).code === "ENOENT") {
        await handleCliNotFoundError(cliPath);
        return resolve({ stdout: "", stderr: `CLI not found at ${cliPath}`, exitCode: 1 });
      }
    }

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
      resolve({
        stdout,
        stderr,
        exitCode: typeof code === "number" ? code : 1,
      });
    });
    proc.on("error", (err) => {
      resolve({
        stdout: "",
        stderr: String(err),
        exitCode: 1,
      });
    });
  });
}

export async function runJsonCommand<T>(
  cliPath: string,
  args: string[],
  cwd?: string,
): Promise<JsonResult<T>> {
  const run = await runCodemarshal(cliPath, args, cwd);
  const payload = extractJsonPayload(run.stdout);
  if (!payload) {
    return {
      data: null,
      error: run.stderr || "No JSON payload detected",
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
    return {
      data: null,
      error: String(err),
      run,
    };
  }
}
