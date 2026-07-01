#!/usr/bin/env node
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function getGatewayUrl() {
  const envPath = path.resolve(__dirname, "../backend/.env");
  let host = "127.0.0.1";
  let port = "8080";
  let prefix = "/v1";

  if (fs.existsSync(envPath)) {
    try {
      const envContent = fs.readFileSync(envPath, "utf-8");
      const lines = envContent.split(/\r?\n/);
      for (const line of lines) {
        const cleanLine = line.trim();
        if (!cleanLine || cleanLine.startsWith("#")) continue;
        const index = cleanLine.indexOf("=");
        if (index > 0) {
          const key = cleanLine.substring(0, index).trim();
          const val = cleanLine.substring(index + 1).trim();
          if (key === "HOST") host = val;
          if (key === "PORT") port = val;
          if (key === "GATEWAY_PREFIX") prefix = val;
        }
      }
    } catch (e) {
      // Fallback to defaults
    }
  }
  return `http://${host}:${port}${prefix}`;
}

const gatewayUrl = getGatewayUrl();
console.log(`Launching OpenCode via AI Gateway Pro (air-opencode)... (Routing requests to: ${gatewayUrl})`);

// Setup the OpenAI environment variables to redirect OpenCode requests to the gateway
const env = {
  ...process.env,
  OPENAI_BASE_URL: gatewayUrl,
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
