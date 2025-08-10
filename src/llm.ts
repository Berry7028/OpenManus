import OpenAI from "openai";
import { config } from "./config";
import { Message as LocalMessage, ToolCall } from "./schema";

export class LLMResponseWithTools {
  content?: string | null;
  tool_calls?: ToolCall[] | null;
}

export class LLM {
  private client: OpenAI;
  private model: string;
  private max_tokens: number;
  private temperature: number;
  private base_url: string;
  private api_key: string;

  constructor(configName = "default") {
    const candidate = config.llm[configName];
    const llmConfig = candidate ?? config.llm.default;
    if (!llmConfig) throw new Error("LLM configuration is missing");
    this.model = llmConfig.model!;
    this.max_tokens = (llmConfig.max_tokens as number) ?? 4096;
    this.temperature = (llmConfig.temperature as number) ?? 1.0;
    this.base_url = llmConfig.base_url!;
    this.api_key = llmConfig.api_key!;
    this.client = new OpenAI({ apiKey: this.api_key, baseURL: this.base_url });
  }

  private toOpenAIMessages(messages: LocalMessage[]): OpenAI.Chat.Completions.ChatCompletionMessageParam[] {
    return messages.map((m) => {
      if (m.base64_image) {
        // minimal image support: send as text-only fallback
        return { role: m.role, content: m.content ?? "" } as any;
      }
      const base: any = { role: m.role, content: m.content ?? "" };
      if (m.name) base.name = m.name;
      if (m.tool_call_id) base.tool_call_id = m.tool_call_id;
      if (m.tool_calls) base.tool_calls = m.tool_calls as any;
      return base;
    });
  }

  async ask(params: {
    messages: LocalMessage[];
    system_msgs?: LocalMessage[];
    temperature?: number;
  }): Promise<string> {
    const messages = [
      ...(params.system_msgs ?? []),
      ...params.messages,
    ];

    const res = await this.client.chat.completions.create({
      model: this.model,
      messages: this.toOpenAIMessages(messages),
      temperature: params.temperature ?? this.temperature,
      max_tokens: this.max_tokens,
    });

    const choice = res.choices[0];
    const content = choice?.message?.content ?? "";
    return content;
  }

  async ask_tool(params: {
    messages: LocalMessage[];
    system_msgs?: LocalMessage[];
    tools: any[];
    tool_choice?: "none" | "auto" | "required";
  }): Promise<LLMResponseWithTools> {
    const messages = [
      ...(params.system_msgs ?? []),
      ...params.messages,
    ];

    const res = await this.client.chat.completions.create({
      model: this.model,
      messages: this.toOpenAIMessages(messages),
      tools: params.tools as any,
      tool_choice: params.tool_choice ?? "auto",
      temperature: this.temperature,
      max_tokens: this.max_tokens,
    });

    const m = res.choices[0]?.message;
    const tool_calls = (m?.tool_calls ?? []).map((tc) => ({
      id: tc.id!,
      type: "function" as const,
      function: {
        name: tc.function!.name,
        arguments: tc.function!.arguments,
      },
    }));
    return { content: m?.content ?? null, tool_calls };
  }
}