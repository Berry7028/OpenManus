import { BaseTool, ToolResult } from "./base";

export type PlanStepStatus = "not_started" | "in_progress" | "completed" | "blocked";

export interface PlanData {
  title: string;
  steps: string[];
  step_statuses: PlanStepStatus[];
  step_notes: string[];
}

export class PlanningTool extends BaseTool {
  name = "planning";
  description = "Create and manage a simple plan with steps and statuses";
  parameters = {
    type: "object",
    properties: {
      command: { type: "string", enum: ["create", "get", "mark_step"] },
      plan_id: { type: "string" },
      title: { type: "string" },
      steps: { type: "array", items: { type: "string" } },
      step_index: { type: "number" },
      step_status: { type: "string", enum: ["not_started", "in_progress", "completed", "blocked"] },
    },
    required: ["command", "plan_id"],
  } as const;

  plans: Record<string, PlanData> = {};

  async execute(args?: Record<string, any>): Promise<ToolResult> {
    const { command, plan_id } = args ?? {};
    if (!command || !plan_id) return new ToolResult({ error: "Missing command or plan_id" });

    switch (command) {
      case "create": {
        const title = (args?.title as string) ?? `Plan ${plan_id}`;
        const steps: string[] = Array.isArray(args?.steps) ? args!.steps : [];
        this.plans[plan_id] = {
          title,
          steps,
          step_statuses: steps.map(() => "not_started"),
          step_notes: steps.map(() => ""),
        };
        return new ToolResult({ output: `Plan '${title}' created with ${steps.length} steps` });
      }
      case "get": {
        const plan = this.plans[plan_id];
        if (!plan) return new ToolResult({ error: `Plan ${plan_id} not found` });
        return new ToolResult({ output: this.renderPlan(plan_id, plan) });
      }
      case "mark_step": {
        const plan = this.plans[plan_id];
        if (!plan) return new ToolResult({ error: `Plan ${plan_id} not found` });
        const idx = Number(args?.step_index);
        const status = args?.step_status as PlanStepStatus;
        if (!(idx >= 0 && idx < plan.steps.length)) return new ToolResult({ error: `Invalid step index ${idx}` });
        plan.step_statuses[idx] = status ?? plan.step_statuses[idx];
        return new ToolResult({ output: `Step ${idx} -> ${plan.step_statuses[idx]}` });
      }
      default:
        return new ToolResult({ error: `Unknown command ${command}` });
    }
  }

  private renderPlan(plan_id: string, plan: PlanData): string {
    const statusMark: Record<PlanStepStatus, string> = {
      completed: "[✓]",
      in_progress: "[→]",
      blocked: "[!]",
      not_started: "[ ]",
    };
    const completed = plan.step_statuses.filter((s) => s === "completed").length;
    const total = plan.steps.length;
    const progress = total ? ((completed / total) * 100).toFixed(1) : "0.0";
    let text = `Plan: ${plan.title} (ID: ${plan_id})\n\n`;
    text += `Progress: ${completed}/${total} steps completed (${progress}%)\n\n`;
    text += `Steps:\n`;
    plan.steps.forEach((s, i) => {
      const mark = statusMark[plan.step_statuses[i] ?? "not_started"];
      text += `${i}. ${mark} ${s}\n`;
      const note = plan.step_notes[i];
      if (note) text += `   Notes: ${note}\n`;
    });
    return text;
  }
}