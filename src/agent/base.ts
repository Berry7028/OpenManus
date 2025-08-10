import { logger } from "../logger";
import { AgentState, Message, Role } from "../schema";
import { LLM } from "../llm";

export abstract class BaseAgent {
  name!: string;
  description?: string;

  system_prompt?: string;
  next_step_prompt?: string;

  llm: LLM;
  memory = { messages: [] as Message[] };
  state: AgentState = "IDLE";

  max_steps = 10;
  current_step = 0;
  duplicate_threshold = 2;

  constructor(init?: Partial<BaseAgent>) {
    this.llm = init?.llm ?? new LLM();
    this.system_prompt = init?.system_prompt;
    this.next_step_prompt = init?.next_step_prompt;
  }

  update_memory(role: Role, content: string, base64_image?: string | null, extra?: Partial<Message>) {
    const map: Record<Role, (c: string, b?: string | null) => Message> = {
      user: (c: string, b?: string | null) => Message.user_message(c, b),
      system: (c: string) => Message.system_message(c),
      assistant: (c: string, b?: string | null) => Message.assistant_message(c, b),
      tool: (c: string, b?: string | null) => Message.tool_message(c, extra?.name ?? "tool", extra?.tool_call_id ?? "", b ?? null),
    } as any;
    const msg = map[role](content, base64_image ?? null);
    this.memory.messages.push(msg);
  }

  async run(request?: string): Promise<string> {
    if (this.state !== "IDLE") throw new Error(`Cannot run agent from state: ${this.state}`);
    if (request) this.update_memory("user", request);

    const results: string[] = [];
    this.state = "RUNNING";
    try {
      while (this.current_step < this.max_steps) {
        this.current_step += 1;
        logger.info(`Executing step ${this.current_step}/${this.max_steps}`);
        const step_result = await this.step();
        if (this.is_stuck()) this.handle_stuck_state();
        results.push(`Step ${this.current_step}: ${step_result}`);
        if ((this as any).state === "FINISHED") break;
      }

      if (this.current_step >= this.max_steps) {
        this.current_step = 0;
        this.state = "IDLE";
        results.push(`Terminated: Reached max steps (${this.max_steps})`);
      }
    } finally {
      // no-op cleanup hook here; specific agents can override
    }

    return results.length ? results.join("\n") : "No steps executed";
  }

  protected handle_stuck_state() {
    const stuck_prompt = "Observed duplicate responses. Consider new strategies and avoid repeating ineffective paths already attempted.";
    this.next_step_prompt = `${stuck_prompt}\n${this.next_step_prompt ?? ""}`;
    logger.warn(`Agent detected stuck state. Added prompt: ${stuck_prompt}`);
  }

  protected is_stuck(): boolean {
    if (this.memory.messages.length < 2) return false;
    const last = this.memory.messages[this.memory.messages.length - 1]!;
    if (!last.content) return false;
    let duplicate_count = 0;
    for (let i = this.memory.messages.length - 2; i >= 0; i--) {
      const msg = this.memory.messages[i]!;
      if (msg.role === "assistant" && msg.content === last.content) duplicate_count++;
    }
    return duplicate_count >= this.duplicate_threshold;
  }

  get messages(): Message[] {
    return this.memory.messages;
  }
  set messages(value: Message[]) {
    this.memory.messages = value;
  }

  protected abstract step(): Promise<string>;
}