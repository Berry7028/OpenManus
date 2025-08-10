import { ToolCallAgent } from "./toolcall";
import { SYSTEM_PROMPT, NEXT_STEP_PROMPT } from "../prompt/toolcall";
import { Terminate } from "../tool/terminate";
import { ToolCollection } from "../tool/toolCollection";
import { config } from "../config";

export class Manus extends ToolCallAgent {
  name = "Manus";
  description = "A versatile agent that can solve various tasks using multiple tools";

  system_prompt = SYSTEM_PROMPT.replace("{directory}", config.workspace_root);
  next_step_prompt = NEXT_STEP_PROMPT;

  max_observe = 10000;
  max_steps = 20;

  available_tools = new ToolCollection(new Terminate());

  static async create(): Promise<Manus> {
    // stubbing MCP initialization
    return new Manus();
  }

  async cleanup() {
    // no-op for now
  }
}