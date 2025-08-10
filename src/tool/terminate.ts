import { BaseTool, ToolResult } from "./base";

export class Terminate extends BaseTool {
  name = "terminate";
  description = "Finish the current task when you are done";
  parameters = {
    type: "object",
    properties: {
      reason: { type: "string", description: "Brief reason for finishing" },
    },
  };

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    const reason = typeof args?.reason === "string" ? args?.reason : "Task finished";
    return new ToolResult({ output: `Terminated: ${reason}` });
  }
}