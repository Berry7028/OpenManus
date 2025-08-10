import { spawn } from "node:child_process";
import { BaseTool, ToolResult } from "./base";

export class PythonExecute extends BaseTool {
  name = "python_execute";
  description = "Execute Python code in a separate process and return stdout/stderr";
  parameters = {
    type: "object",
    properties: {
      code: { type: "string" },
      timeout: { type: "number", default: 60000 },
    },
    required: ["code"],
  } as const;

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    const code = String(args?.code ?? "");
    const timeout = Number(args?.timeout ?? 60000);
    if (!code) return new ToolResult({ error: "code required" });

    return await new Promise<ToolResult>((resolve) => {
      const proc = spawn("python3", ["-c", code], { stdio: ["ignore", "pipe", "pipe"] });
      let stdout = "";
      let stderr = "";
      const timer = setTimeout(() => {
        proc.kill("SIGKILL");
        resolve(new ToolResult({ error: "Timeout" }));
      }, timeout);
      proc.stdout.on("data", (d) => (stdout += String(d)));
      proc.stderr.on("data", (d) => (stderr += String(d)));
      proc.on("close", (code) => {
        clearTimeout(timer);
        if (code === 0) resolve(new ToolResult({ output: stdout.trim() }));
        else resolve(new ToolResult({ error: stderr.trim() || `Exited with code ${code}` }));
      });
    });
  }
}