import { BaseFlow } from "./base";
import { BaseAgent } from "../agent/base";
import { LLM } from "../llm";
import { Message } from "../schema";
import { PlanningTool, PlanStepStatus } from "../tool/planning";

export class PlanningFlow extends BaseFlow {
  llm: LLM;
  planning_tool: PlanningTool;
  executor_keys: string[] = [];
  active_plan_id: string;
  current_step_index: number | null = null;

  constructor(agents: Record<string, BaseAgent> | BaseAgent | BaseAgent[], init?: { executors?: string[]; plan_id?: string; planning_tool?: PlanningTool }) {
    super(agents);
    this.llm = new LLM();
    this.planning_tool = init?.planning_tool ?? new PlanningTool();
    this.executor_keys = init?.executors ?? Object.keys(this.agents);
    this.active_plan_id = init?.plan_id ?? `plan_${Date.now()}`;
  }

  get_executor(step_type?: string): BaseAgent {
    if (step_type && this.agents[step_type]) return this.agents[step_type];
    for (const key of this.executor_keys) if (this.agents[key]) return this.agents[key];
    return this.primary_agent!;
  }

  async execute(input_text: string): Promise<string> {
    if (!this.primary_agent) throw new Error("No primary agent available");
    if (input_text) await this.create_initial_plan(input_text);

    let result = "";
    while (true) {
      const { index, info } = await this.get_current_step_info();
      this.current_step_index = index;
      if (index == null) {
        result += await this.finalize_plan();
        break;
      }
      const executor = this.get_executor(info?.type);
      const step_result = await this.execute_step(executor, info!);
      result += step_result + "\n";
    }
    return result;
  }

  private async create_initial_plan(request: string): Promise<void> {
    const system = Message.system_message(
      "You are a planning assistant. Create a concise, actionable plan with clear steps. Focus on key milestones rather than detailed sub-steps. Optimize for clarity and efficiency."
    );

    const response = await this.llm.ask_tool({
      messages: [Message.user_message(`Create a reasonable plan with clear steps to accomplish the task: ${request}`)],
      system_msgs: [system],
      tools: [this.planning_tool.toParam()],
      tool_choice: "auto",
    });

    if (response.tool_calls?.length) {
      for (const call of response.tool_calls) {
        if (call.function.name === "planning") {
          let args: any = {};
          try {
            args = JSON.parse(call.function.arguments || "{}");
          } catch {}
          args.plan_id = this.active_plan_id;
          await this.planning_tool.execute(args);
          return;
        }
      }
    }

    await this.planning_tool.execute({
      command: "create",
      plan_id: this.active_plan_id,
      title: `Plan for: ${request.slice(0, 50)}${request.length > 50 ? "..." : ""}`,
      steps: ["Analyze request", "Execute task", "Verify results"],
    });
  }

  private async get_current_step_info(): Promise<{ index: number | null; info: { text: string; type?: string } | null }> {
    const plan = this.planning_tool.plans[this.active_plan_id];
    if (!plan) return { index: null, info: null };

    for (let i = 0; i < plan.steps.length; i++) {
      const status = plan.step_statuses[i] ?? "not_started";
      if (status === "not_started" || status === "in_progress") {
        const text = plan.steps[i];
        const typeMatch = /\[([A-Z_]+)\]/.exec(text);
        const type = typeMatch ? typeMatch[1].toLowerCase() : undefined;
        try {
          await this.planning_tool.execute({ command: "mark_step", plan_id: this.active_plan_id, step_index: i, step_status: "in_progress" });
        } catch {}
        return { index: i, info: { text, type } };
      }
    }
    return { index: null, info: null };
  }

  private async execute_step(executor: BaseAgent, step_info: { text: string; type?: string }): Promise<string> {
    const plan_text = await this.get_plan_text();
    const prompt = `
CURRENT PLAN STATUS:
${plan_text}

YOUR CURRENT TASK:
You are now working on step ${this.current_step_index}: "${step_info.text}"

Please only execute this current step using the appropriate tools. When you're done, provide a summary of what you accomplished.`.trim();

    try {
      const step_result = await executor.run(prompt);
      await this.mark_step_completed();
      return step_result;
    } catch (e: any) {
      return `Error executing step ${this.current_step_index}: ${e?.message ?? String(e)}`;
    }
  }

  private async mark_step_completed(): Promise<void> {
    if (this.current_step_index == null) return;
    try {
      await this.planning_tool.execute({ command: "mark_step", plan_id: this.active_plan_id, step_index: this.current_step_index, step_status: "completed" });
    } catch {
      const plan = this.planning_tool.plans[this.active_plan_id];
      if (!plan) return;
      while (plan.step_statuses.length <= this.current_step_index) plan.step_statuses.push("not_started");
      plan.step_statuses[this.current_step_index] = "completed";
    }
  }

  private async get_plan_text(): Promise<string> {
    const res = await this.planning_tool.execute({ command: "get", plan_id: this.active_plan_id });
    return String(res.output ?? res.toString());
  }

  private async finalize_plan(): Promise<string> {
    const plan_text = await this.get_plan_text();
    const response = await this.llm.ask({
      messages: [Message.user_message(`The plan has been completed. Here is the final plan status:\n\n${plan_text}\n\nPlease provide a summary of what was accomplished and any final thoughts.`)],
      system_msgs: [Message.system_message("You are a planning assistant. Your task is to summarize the completed plan.")],
    });
    return `Plan completed:\n\n${response}`;
  }
}