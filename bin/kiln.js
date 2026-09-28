#!/usr/bin/env node

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

function findPython() {
  const candidates = process.platform === "win32"
    ? ["python", "py", "python3"]
    : ["python3", "python"];

  for (const cmd of candidates) {
    const res = spawnSync(cmd, ["--version"], { stdio: "ignore" });
    if (res.status === 0) {
      return cmd;
    }
  }
  return null;
}

const pythonCmd = findPython();
if (!pythonCmd) {
  console.error("[Kiln OS Error] Python 3.10+ is required to run Kiln OS, but no Python executable was found on PATH.");
  console.error("Please install Python from https://www.python.org/ or via your system package manager.");
  process.exit(1);
}

const rootDir = path.resolve(__dirname, "..");
const localScript = path.join(rootDir, "scripts", "kiln");
const userArgs = process.argv.slice(2);

let runArgs;
if (fs.existsSync(localScript)) {
  runArgs = [localScript, ...userArgs];
} else {
  runArgs = ["-m", "kiln.cli", ...userArgs];
}

const env = { ...process.env, PYTHONPATH: path.join(rootDir, "src") + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : "") };

const child = spawnSync(pythonCmd, runArgs, {
  stdio: "inherit",
  env: env
});

process.exit(child.status !== null ? child.status : 0);
