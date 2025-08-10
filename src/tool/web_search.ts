import { BaseTool, ToolResult } from "./base";
import https from "node:https";

function fetch(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    https
      .get(url, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(data));
      })
      .on("error", reject);
  });
}

export class WebSearch extends BaseTool {
  name = "web_search";
  description = "Search the web using DuckDuckGo and return top results";
  parameters = {
    type: "object",
    properties: {
      query: { type: "string" },
      num: { type: "number", default: 5 },
    },
    required: ["query"],
  } as const;

  async execute(args?: Record<string, unknown>): Promise<ToolResult> {
    const q = encodeURIComponent(String(args?.query ?? ""));
    const num = Number(args?.num ?? 5);
    if (!q) return new ToolResult({ error: "Query is required" });
    try {
      const html = await fetch(`https://duckduckgo.com/html/?q=${q}`);
      const links = Array.from(html.matchAll(/<a[^>]*class=\"result__a\"[^>]*href=\"([^\"]+)\"/g)).slice(0, num).map((m) => m[1]);
      return new ToolResult({ output: links.join("\n") || "(no results)" });
    } catch (e: any) {
      return new ToolResult({ error: e?.message ?? String(e) });
    }
  }
}