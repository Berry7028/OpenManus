import { BaseAgent } from "../agent/base";

export abstract class BaseFlow<A extends BaseAgent = BaseAgent> {
  agents: Record<string, A>;
  tools?: any[];
  primary_agent_key?: string;

  constructor(agents: A | A[] | Record<string, A>, init?: { primary_agent_key?: string }) {
    let agents_dict: Record<string, A>;
    if (agents instanceof BaseAgent || (agents as any)?.run) {
      agents_dict = { default: agents as A };
    } else if (Array.isArray(agents)) {
      agents_dict = Object.fromEntries(agents.map((a, i) => [`agent_${i}`, a]));
    } else {
      agents_dict = agents as Record<string, A>;
    }
    this.agents = agents_dict;
    this.primary_agent_key = init?.primary_agent_key ?? Object.keys(agents_dict)[0];
  }

  get primary_agent(): A | undefined {
    return this.primary_agent_key ? this.agents[this.primary_agent_key] : undefined;
  }

  get_agent(key: string): A | undefined {
    return this.agents[key];
  }

  add_agent(key: string, agent: A) {
    this.agents[key] = agent;
  }

  abstract execute(input_text: string): Promise<string>;
}