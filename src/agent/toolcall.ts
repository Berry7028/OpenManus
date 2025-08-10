import { ReActAgent } from "./react";
import { Message, ToolCall, ToolChoice, AgentState } from "../schema";
import { logger } from "../logger";
import { SYSTEM_PROMPT, NEXT_STEP_PROMPT } from "../prompt/toolcall";
import { ToolCollection } from "../tool/toolCollection";
import { Terminate } from "../tool/terminate";

export class ToolCallAgent extends ReActAgent {
  name = "toolcall";
  description = "an agent that can execute tool calls.";

  system_prompt = SYSTEM_PROMPT;
  next_step_prompt = NEXT_STEP_PROMPT;

  available_tools = new ToolCollection(new Terminate());
  tool_choices: ToolChoice = "auto";
  special_tool_names: string[] = [new Terminate().name];

  tool_calls: ToolCall[] = [];
  private _current_base64_image: string | null = null;

  max_steps = 30;
  max_observe: number | boolean | null = null;

  async think(): Promise<boolean> {
    if (this.next_step_prompt) {
      const user_msg = Message.user_message(this.next_step_prompt);
      this.messages = [...this.messages, user_msg];
    }

    const response = await this.llm.ask_tool({
      messages: this.messages,
      system_msgs: this.system_prompt ? [Message.system_message(this.system_prompt)] : undefined,
      tools: this.available_tools.toParams(),
      tool_choice: this.tool_choices,
    });

    this.tool_calls = response.tool_calls ?? [];
    const content = response.content ?? "";

    logger.info(`${this.name}'s thoughts: ${content}`);
    logger.info(`${this.name} selected ${this.tool_calls.length} tools to use`);
    if (this.tool_calls.length) {
      logger.info(`Tools being prepared: ${this.tool_calls.map((c) => c.function.name).join(", ")}`);
    }

    const assistant_msg = this.tool_calls.length
      ? Message.from_tool_calls({ tool_calls: this.tool_calls, content })
      : Message.assistant_message(content ?? undefined);
    this.messages = [...this.messages, assistant_msg];

    if (this.tool_choices === "none") return Boolean(content);
    if (this.tool_choices === "required" && !this.tool_calls.length) return true;
    if (this.tool_choices === "auto" && !this.tool_calls.length) return Boolean(content);
    return Boolean(this.tool_calls.length);
  }

  async act(): Promise<string> {
    if (!this.tool_calls.length) {
      if (this.tool_choices === "required") throw new Error("Tool calls required but none provided");
      return this.messages[this.messages.length - 1]?.content || "No content or commands to execute";
    }

    const results: string[] = [];
    for (const command of this.tool_calls) {
      this._current_base64_image = null;
      const result = await this.execute_tool(command);
      const observation = this.max_observe ? String(result).slice(0, Number(this.max_observe)) : String(result);
      const tool_msg = Message.tool_message(observation, command.function.name, command.id, this._current_base64_image);
      this.messages = [...this.messages, tool_msg];
      results.push(String(observation));
    }
    return results.join("\n\n");
  }

  private async execute_tool(command: ToolCall): Promise<string> {
    if (!command?.function?.name) return "Error: Invalid command format";
    const name = command.function.name;
    if (!this.available_tools.tool_map[name]) return `Error: Unknown tool '${name}'`;

    try {
      const args = JSON.parse(command.function.arguments || "{}");
      const result = await this.available_tools.execute(name, args);
      await this.handle_special_tool(name, result);
      if ((result as any).base64_image) this._current_base64_image = (result as any).base64_image;
      return result ? `Observed output of cmd \`${name}\` executed:\n${String(result)}` : `Cmd \`${name}\` completed with no output`;
    } catch (e: any) {
      if (e?.name === "SyntaxError") return `Error parsing arguments for ${name}: Invalid JSON format`;
      return `Error: Tool '${name}' encountered a problem: ${e?.message ?? String(e)}`;
    }
  }

  private async handle_special_tool(name: string, _result: unknown) {
    if (!this.is_special_tool(name)) return;
    // terminate always finishes for now
    this.state = "FINISHED";
  }

  private is_special_tool(name: string) {
    return this.special_tool_names.map((n) => n.toLowerCase()).includes(name.toLowerCase());
  }
}