import { BaseTool, ToolFailure, ToolResult } from "./base";

export class ToolCollection {
  private tools: BaseTool[];
  tool_map: Record<string, BaseTool>;

  constructor(...tools: BaseTool[]) {
    this.tools = tools;
    this.tool_map = Object.fromEntries(tools.map((t) => [t.name, t]));
  }

  toParams(): any[] {
    return this.tools.map((t) => t.toParam());
  }

  add_tools(...tools: BaseTool[]) {
    for (const tool of tools) {
      if (!this.tool_map[tool.name]) {
        this.tools.push(tool);
        this.tool_map[tool.name] = tool;
      }
    }
    return this;
  }

  async execute(name: string, tool_input: Record<string, unknown> = {}): Promise<ToolResult> {
    const tool = this.tool_map[name];
    if (!tool) return new ToolFailure({ error: `Tool ${name} is invalid` });
    try {
      return await tool.call(tool_input);
    } catch (e: any) {
      return new ToolFailure({ error: e?.message ?? String(e) });
    }
  }
}