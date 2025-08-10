import { Manus } from "./agent/manus";
import { PlanningFlow } from "./flow/planning";
import { logger } from "./logger";

function promptInput(): Promise<string> {
  return new Promise((resolve) => {
    process.stdout.write("Enter your prompt: ");
    process.stdin.once("data", (d) => resolve(String(d).trim()));
  });
}

async function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  return await Promise.race([
    p,
    new Promise<T>((_, rej) => setTimeout(() => rej(new Error("Timeout")), ms)),
  ]);
}

async function run_flow() {
  const agents = { manus: await Manus.create() };
  try {
    const prompt = await promptInput();
    if (!prompt || !prompt.trim()) {
      logger.warn("Empty prompt provided.");
      return;
    }

    const flow = new PlanningFlow(agents);
    logger.warn("Processing your request...");

    try {
      const start = Date.now();
      const result = await withTimeout(flow.execute(prompt), 60 * 60 * 1000);
      const elapsed = (Date.now() - start) / 1000;
      logger.info(`Request processed in ${elapsed.toFixed(2)} seconds`);
      logger.info(result);
    } catch (e: any) {
      if (e?.message === "Timeout") {
        logger.error("Request processing timed out after 1 hour");
        logger.info("Operation terminated due to timeout. Please try a simpler request.");
      } else {
        logger.error(`Error: ${e?.message ?? String(e)}`);
      }
    }
  } catch {
    logger.info("Operation cancelled by user.");
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  run_flow().catch((e) => {
    logger.error(`Fatal: ${e instanceof Error ? e.message : String(e)}`);
    process.exit(1);
  });
}