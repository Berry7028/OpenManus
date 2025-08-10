import { BaseAgent } from "./base";

export abstract class ReActAgent extends BaseAgent {
  abstract think(): Promise<boolean>;
  abstract act(): Promise<string>;

  protected async step(): Promise<string> {
    const should_act = await this.think();
    if (!should_act) return "Thinking complete - no action needed";
    return this.act();
  }
}