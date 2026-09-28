# Kiln OS: Installation & Quickstart

Kiln OS is a portable, resilient, token-minimizing operating system for AI coding agents.

## 1. Prerequisites
- Python 3.10+ (Standard library + `pyyaml`)
- Git

## 2. Installation
To install Kiln OS CLI locally or in your project:
```bash
git clone https://github.com/cristiangilsanz/kilnOS.git
cd kilnOS
pip install -e .
```
Or directly use `scripts/kiln` (`scripts/kiln.bat` on Windows).

## 3. Harness Integration
Generate adapters for your active coding agent:
```bash
kiln build-adapters
```
* **Claude Code**: Uses generated `CLAUDE.md` and `.claude/skills/`.
* **Antigravity**: Uses `AGENTS.md` and `.agent/skills/`.
* **OpenAI Codex**: Uses `.codex/instructions.md`.
* **OpenCode / Cursor**: Uses `.cursorrules`.

## 4. Key Commands
* `kiln pack <work-id> --budget <N>`: Deterministic L1 context pack.
* `kiln node <id>`: Expand full knowledge node details.
* `kiln remember --id <id> --type <type> --title "<title>"`: Store knowledge node.
* `kiln doctor`: Check integrity, rebuild index, and flag stale evidence.
* `kiln resume <work-id>`: Restore task state after `/clear` or `/compact`.
* `kiln lint-tokens`: Enforce line and word budgets across agent files.
* `kiln audit <work-id>`: Report token spend telemetry.
