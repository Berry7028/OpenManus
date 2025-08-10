import { BaseTool, ToolResult } from "./base";

export class AskHuman extends BaseTool {
  name = "ask_human";
  description = "Ask the human operator for information or decision";
  parameters = {
    type: "object",
    properties: {
      question: { type: "string" },
    },
    required: ["question"],
  } as const;

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    const question = String(args?.question ?? "");
    if (!question) return new ToolResult({ error: "question required" });
    return new ToolResult({ output: `Question for human: ${question}` });
  }
}