import express from "express";
import cors from "cors";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Manus } from "./agent/manus";
import { PlanningFlow } from "./flow/planning";
import { ToolCollection } from "./tool/toolCollection";
import { PythonExecute } from "./tool/python_execute";
import { WebSearch } from "./tool/web_search";
import { StrReplaceEditor } from "./tool/str_replace_editor";
import { AskHuman } from "./tool/ask_human";
import { Bash } from "./tool/bash";
import { Terminate } from "./tool/terminate";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function buildServer() {
  const app = express();
  app.use(cors());
  app.use(express.json({ limit: "2mb" }));

  const tools = new ToolCollection(
    new PythonExecute(),
    new WebSearch(),
    new StrReplaceEditor(),
    new AskHuman(),
    new Bash(),
    new Terminate()
  );

  // APIs
  app.get("/api/tools", (req, res) => {
    const list = Object.values(tools.tool_map).map((t) => t.toParam().function);
    res.json(list);
  });

  app.post("/api/tool", async (req, res) => {
    try {
      const { name, args } = req.body ?? {};
      if (!name) return res.status(400).json({ error: "name required" });
      const result = await tools.execute(String(name), args ?? {});
      res.json({ output: result.output ?? null, error: result.error ?? null, base64_image: result.base64_image ?? null });
    } catch (e: any) {
      res.status(500).json({ error: e?.message ?? String(e) });
    }
  });

  app.post("/api/run", async (req, res) => {
    try {
      const { prompt } = req.body ?? {};
      if (!prompt || !String(prompt).trim()) return res.status(400).json({ error: "prompt required" });
      const agent = await Manus.create();
      const result = await agent.run(String(prompt));
      await agent.cleanup?.();
      res.json({ result });
    } catch (e: any) {
      res.status(500).json({ error: e?.message ?? String(e) });
    }
  });

  app.post("/api/flow", async (req, res) => {
    try {
      const { prompt } = req.body ?? {};
      if (!prompt || !String(prompt).trim()) return res.status(400).json({ error: "prompt required" });
      const agents = { manus: await Manus.create() };
      const flow = new PlanningFlow(agents);
      const result = await flow.execute(String(prompt));
      res.json({ result });
    } catch (e: any) {
      res.status(500).json({ error: e?.message ?? String(e) });
    }
  });

  // Static frontend
  const publicDir = path.resolve(__dirname, "../public");
  app.use(express.static(publicDir));

  // Fallback to index
  app.get("*", (req, res) => {
    res.sendFile(path.join(publicDir, "index.html"));
  });

  const port = Number(process.env.PORT ?? 3000);
  return new Promise<void>((resolve) => {
    app.listen(port, () => {
      // eslint-disable-next-line no-console
      console.log(`Server listening on http://localhost:${port}`);
      resolve();
    });
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  buildServer();
}