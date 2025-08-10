import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { BaseTool, ToolResult } from "./base";

export class StrReplaceEditor extends BaseTool {
  name = "str_replace_editor";
  description = "Replace a string in a text file in the workspace";
  parameters = {
    type: "object",
    properties: {
      file_path: { type: "string" },
      old_string: { type: "string" },
      new_string: { type: "string" },
    },
    required: ["file_path", "old_string", "new_string"],
  } as const;

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    try {
      const file_path = String(args?.file_path ?? "");
      const old_string = String(args?.old_string ?? "");
      const new_string = String(args?.new_string ?? "");
      if (!file_path || !old_string) return new ToolResult({ error: "file_path and old_string required" });
      const abs = resolve(process.cwd(), file_path);
      const content = readFileSync(abs, "utf-8");
      const updated = content.replace(old_string, new_string);
      writeFileSync(abs, updated, "utf-8");
      return new ToolResult({ output: `Updated ${file_path}` });
    } catch (e: any) {
      return new ToolResult({ error: e?.message ?? String(e) });
    }
  }
}