#!/usr/bin/env node
import { spawn } from "child_process";

console.log("Launching Claude Code via AI Gateway Pro (air-claude)...");

// Setup the Anthropic base URL and credentials variables to intercept requests
const env = {
  ...process.env,
  ANTHROPIC_BASE_URL: "http://localhost:8080/v1",
  ANTHROPIC_API_KEY: "sk-ant-aigateway-pro-rotation-key"
};

// Forward any arguments passed to the CLI command
const args = process.argv.slice(2);

const child = spawn("claude", args, {
  stdio: "inherit",
  shell: true,
  env
});

child.on("close", (code) => {
  process.exit(code);
});
