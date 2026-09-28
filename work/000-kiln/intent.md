# Task 000-kiln: Intent

## Objective
Design and implement **Kiln OS**, a resilient, token-minimizing operating system for AI coding agents covering the complete software engineering lifecycle. Provide a single canonical portable bundle (`.kiln/`) that targets Claude Code, Codex, OpenCode, and Antigravity through deterministic generated adapters and strict hooks.

## Scope & Decisions
* **Runtime**: Python 3.11+ (standard library + lightweight CLI dependencies, cross-platform on Windows/macOS/Linux).
* **Compiled Graph Storage**: SQLite (`.kiln/graph/index.db`) as a disposable, derived, rebuildable query cache over git-native markdown node files and `events.jsonl`.
* **Rigor Tier**: **Standard** (1 design approval checkpoint, automated TDD verification, committed artifact chain).
* **Target Harness Sequence**: Claude Code as primary target for Milestone 1, with Antigravity compatibility maintained in parallel; Codex and OpenCode adapters delivered in Milestone 2.
* **Core Components**:
  1. **Lifecycle Artifact Chain**: `work/<id>/{intent,spec,plan,review}.md` and `state.yml`.
  2. **Memory OS**:
     - Graph A (Code graph): Tree-sitter MCP/AST navigation index (read raw files before edit).
     - Graph B (Knowledge graph): Git-native markdown nodes (`.kiln/graph/nodes/*.md`) with temporal valid-time frontmatter (`valid_from`, `valid_to`, `supersedes`) + append-only `.kiln/graph/events.jsonl`.
     - 5-Tier Memory Hierarchy (L0 hot `<=300` tokens, L1 working context pack, L2 warm index, L3 cold bodies, L4 raw logs).
     - Deterministic non-LLM retrieval: `kiln pack <id> --budget N` and `kiln node <id>`.
  3. **Token Governor**: Budgeting, context caching discipline, terse reasoning rules, CLI output filtering, and token linting in CI.
  4. **Resilience & Safety**: Zero-loss index reconstruction (`kiln doctor`), untrusted memory data quarantine (prompt injection defense), and deterministic fail-closed safety hooks.

## Non-Goals
* Proprietary IDE extensions or heavy background daemons.
* Hosted SaaS dependencies or mandatory external graph databases.
* Reimplementing native harness plan mode (Kiln layers tier gates and committed artifacts on top).
* Unverified marketing or token reduction claims without reproducible local evals.

## Success Criteria
* Clean `kiln doctor` passing all schema and index validation checks.
* Deterministic index rebuild from flat files matches prior queries identically.
* Context pack generated within token budget with measurable savings.
* Enforced gate hooks preventing unauthorized progression or policy violations.
