import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as TOML from "toml";

export type LLMSettings = {
  model: string;
  base_url: string;
  api_key: string;
  max_tokens?: number;
  max_input_tokens?: number | null;
  temperature?: number;
  api_type?: string;
  api_version?: string;
};

export type AppConfig = {
  llm: Record<string, LLMSettings>;
};

function getProjectRoot(): string {
  const __dirname = dirname(fileURLToPath(import.meta.url));
  // src/ -> project root assumed at parent
  return resolve(__dirname, "..");
}

const PROJECT_ROOT = getProjectRoot();

function loadRawConfig(): any {
  const cfg = resolve(PROJECT_ROOT, "config", "config.toml");
  const example = resolve(PROJECT_ROOT, "config", "config.example.toml");
  const path = existsSync(cfg) ? cfg : example;
  if (!existsSync(path)) throw new Error("No configuration file found in config directory");
  const raw = readFileSync(path, "utf-8");
  return TOML.parse(raw);
}

function buildConfig(): AppConfig {
  const raw = loadRawConfig();
  const base = raw.llm ?? {};
  const overrides: Record<string, any> = Object.fromEntries(
    Object.entries(base).filter(([_, v]) => typeof v === "object")
  );
  const defaultSettings: LLMSettings = {
    model: base.model,
    base_url: base.base_url,
    api_key: base.api_key,
    max_tokens: base.max_tokens ?? 4096,
    max_input_tokens: base.max_input_tokens ?? null,
    temperature: base.temperature ?? 1.0,
    api_type: base.api_type ?? "",
    api_version: base.api_version ?? "",
  };

  return {
    llm: {
      default: defaultSettings,
      ...Object.fromEntries(
        Object.entries(overrides).map(([name, ov]) => [name, { ...defaultSettings, ...ov }])
      ),
    },
  };
}

export const config = {
  get llm() {
    return appConfig.llm;
  },
  get root_path() {
    return PROJECT_ROOT;
  },
  get workspace_root() {
    return resolve(PROJECT_ROOT, "workspace");
  },
};

const appConfig = buildConfig();