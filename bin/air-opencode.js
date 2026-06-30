#!/usr/bin/env node
import { spawn } from "child_process";

console.log("Launching OpenCode via AI Gateway Pro (air-opencode)...");

// Setup the OpenAI environment variables to redirect OpenCode requests to the gateway
const env = {
  ...process.env,
  OPENAI_BASE_URL: "http://localhost:8080/v1",
  OPENAI_API_KEY: "sk-ant-aigateway-pro-rotation-key"
};

// Forward any arguments passed to the CLI command
const args = process.argv.slice(2);

const child = spawn("opencode", args, {
  stdio: "inherit",
  shell: true,
  env
});

child.on("close", (code) => {
  process.exit(code);
});
