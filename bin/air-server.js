#!/usr/bin/env node
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const backendDir = path.resolve(__dirname, "../backend");

console.log("Starting AI Gateway Pro Server (air-server)...");

// Spawn the Python process running the server
const child = spawn(".venv\\Scripts\\python.exe", ["run.py"], {
  cwd: backendDir,
  stdio: "inherit",
  shell: true
});

child.on("close", (code) => {
  process.exit(code);
});
