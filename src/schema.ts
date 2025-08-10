export type Role = "system" | "user" | "assistant" | "tool";
export const ROLE_VALUES: Role[] = ["system", "user", "assistant", "tool"];

export type ToolChoice = "none" | "auto" | "required";
export const TOOL_CHOICE_VALUES: ToolChoice[] = ["none", "auto", "required"];

export type AgentState = "IDLE" | "RUNNING" | "FINISHED" | "ERROR";

export interface FunctionCallDef {
  name: string;
  arguments: string; // JSON string per OpenAI
}

export interface ToolCall {
  id: string;
  type: "function";
  function: FunctionCallDef;
}

export interface MessageInit {
  role: Role;
  content?: string | null;
  tool_calls?: ToolCall[] | null;
  name?: string | null;
  tool_call_id?: string | null;
  base64_image?: string | null;
}

export class Message implements MessageInit {
  role: Role;
  content?: string | null;
  tool_calls?: ToolCall[] | null;
  name?: string | null;
  tool_call_id?: string | null;
  base64_image?: string | null;

  constructor(init: MessageInit) {
    this.role = init.role;
    this.content = init.content ?? null;
    this.tool_calls = init.tool_calls ?? null;
    this.name = init.name ?? null;
    this.tool_call_id = init.tool_call_id ?? null;
    this.base64_image = init.base64_image ?? null;
  }

  static user_message(content: string, base64_image?: string | null): Message {
    return new Message({ role: "user", content, base64_image: base64_image ?? null });
    }

  static system_message(content: string): Message {
    return new Message({ role: "system", content });
  }

  static assistant_message(content?: string | null, base64_image?: string | null): Message {
    return new Message({ role: "assistant", content: content ?? null, base64_image: base64_image ?? null });
  }

  static tool_message(
    content: string,
    name: string,
    tool_call_id: string,
    base64_image?: string | null
  ): Message {
    return new Message({ role: "tool", content, name, tool_call_id, base64_image: base64_image ?? null });
  }

  static from_tool_calls(params: { tool_calls: ToolCall[]; content?: string | string[]; base64_image?: string | null }): Message {
    const content = Array.isArray(params.content) ? params.content.join("\n") : (params.content ?? "");
    return new Message({ role: "assistant", content, tool_calls: params.tool_calls, base64_image: params.base64_image ?? null });
  }
}

export class Memory {
  messages: Message[] = [];
  max_messages = 100;

  add_message(message: Message) {
    this.messages.push(message);
    if (this.messages.length > this.max_messages) {
      this.messages = this.messages.slice(-this.max_messages);
    }
  }

  add_messages(messages: Message[]) {
    this.messages.push(...messages);
    if (this.messages.length > this.max_messages) {
      this.messages = this.messages.slice(-this.max_messages);
    }
  }

  clear() {
    this.messages = [];
  }

  get_recent_messages(n: number) {
    return this.messages.slice(-n);
  }
}