import { spawn } from "child_process";
import { normalizeFsPath } from "./utils";

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


export function runCodemarshal(
  cliPath: string,
  args: string[],
  cwd?: string,
): Promise<RunResult> {
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
