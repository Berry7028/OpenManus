export abstract class BaseTool {
  name!: string;
  description!: string;
  parameters?: Record<string, unknown>;

  abstract execute(args?: Record<string, unknown>): Promise<ToolResult>;

  async call(args?: Record<string, unknown>): Promise<ToolResult> {
    return this.execute(args ?? {});
  }

  toParam() {
    return {
      type: "function",
      function: {
        name: this.name,
        description: this.description,
        parameters: this.parameters ?? undefined,
      },
    };
  }
}

export class ToolResult {
  output?: string | unknown;
  error?: string | null;
  base64_image?: string | null;
  system?: string | null;

  constructor(init: Partial<ToolResult> = {}) {
    Object.assign(this, init);
  }

  toString() {
    return this.error ? `Error: ${this.error}` : String(this.output ?? "");
  }
}

export class ToolFailure extends ToolResult {}