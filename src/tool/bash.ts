import { exec } from "node:child_process";
import { promisify } from "node:util";
import { BaseTool, ToolResult } from "./base";

const pexec = promisify(exec);

export class Bash extends BaseTool {
  name = "bash";
  description = "Execute a bash command in the workspace";
  parameters = {
    type: "object",
    properties: {
      command: { type: "string", description: "Shell command to execute" },
      timeout: { type: "number", description: "Timeout ms", default: 300000 },
    },
    required: ["command"],
  } as const;

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    const command = String(args?.command ?? "");
    const timeout = Number(args?.timeout ?? 300000);
    if (!command) return new ToolResult({ error: "Empty command" });
    try {
      const { stdout, stderr } = await pexec(command, { timeout, cwd: process.cwd(), maxBuffer: 10 * 1024 * 1024 });
      const out = [stdout, stderr].filter(Boolean).join("\n").trim();
      return new ToolResult({ output: out || "(no output)" });
    } catch (e: any) {
      return new ToolResult({ error: e?.stderr || e?.message || String(e) });
    }
  }
}