import { BaseTool, ToolResult } from "./base";
import { LLM } from "../llm";
import { Message } from "../schema";

export class CreateChatCompletion extends BaseTool {
  name = "create_chat_completion";
  description = "Create a chat completion using the configured LLM";
  parameters = {
    type: "object",
    properties: {
      prompt: { type: "string" },
    },
    required: ["prompt"],
  } as const;

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    const prompt = String(args?.prompt ?? "");
    if (!prompt) return new ToolResult({ error: "prompt required" });
    const llm = new LLM();
    const content = await llm.ask({ messages: [Message.user_message(prompt)] });
    return new ToolResult({ output: content });
  }
}