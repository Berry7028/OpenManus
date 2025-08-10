import { Manus } from "./agent/manus";
import { logger } from "./logger";

function parseArgs(): { prompt?: string } {
  const idx = process.argv.indexOf("--prompt");
  if (idx >= 0 && process.argv[idx + 1]) return { prompt: process.argv[idx + 1] };
  return {};
}

async function main() {
  const args = parseArgs();
  const agent = await Manus.create();
  try {
    const prompt = args.prompt ?? (await new Promise<string>((resolve) => {
      process.stdout.write("Enter your prompt: ");
      process.stdin.once("data", (d) => resolve(String(d).trim()));
    }));

    if (!prompt || !prompt.trim()) {
      logger.warn("Empty prompt provided.");
      return;
    }

    logger.warn("Processing your request...");
    await agent.run(prompt);
    logger.info("Request processing completed.");
  } catch (e) {
    logger.error(`Error: ${e instanceof Error ? e.message : String(e)}`);
  } finally {
    if ((agent as any).cleanup) await (agent as any).cleanup();
  }
}

main().catch((e) => {
  logger.error(`Fatal: ${e instanceof Error ? e.message : String(e)}`);
  process.exit(1);
});