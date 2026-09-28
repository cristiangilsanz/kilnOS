# Task 000-kiln: Implementation Plan

Derived from: `work/000-kiln/spec.md`

## Overview
This plan breaks the realization of Kiln OS into four verifiable milestones. Each task follows Test-Driven Development (TDD) with concrete verification commands.

---

## Milestone 1: Core Engine, Memory OS & Primary Harnesses (M1)

### Task 1.1: Project Skeleton & Token-Compliant Base Assets
- **Actions**:
  - Initialize directory layout: `.kiln/`, `standards/`, `work/000-kiln/`, `scripts/`, `evals/`, `adapters/`.
  - Create initial root `AGENTS.md` (budget <= 80 lines) pointing to `.kiln/`.
  - Create base `standards/index.yml` and core standard templates (`tdd.md`, `resilience.md`).
- **Verification Command**:
  ```bash
  python -m pytest tests/test_skeleton.py -v
  ```

### Task 1.2: Knowledge Graph (Graph B) Core & Storage Engine
- **Actions**:
  - Implement node schema validator in `kiln.graph.schema` (validating frontmatter, status, confidence, timestamps, temporal edges).
  - Implement append-only event logging in `kiln.graph.events`.
  - Implement SQLite index compiler in `kiln.graph.indexer` (`index.db` with nodes, edges, evidence, and FTS5 search).
  - Implement secret redaction filter for incoming memory notes.
- **Verification Command**:
  ```bash
  python -m pytest tests/test_graph_engine.py -v
  ```

### Task 1.3: Deterministic Retrieval Engine (`kiln pack` & `kiln node`)
- **Actions**:
  - Implement decayed BFS / Personalized PageRank traversal in `kiln.retrieval.pagerank`.
  - Implement token-weighted scoring formula:
    $$\text{Score} = \frac{\text{Relevance} \times \text{Recency} \times \text{Confidence} \times \text{StatusWeight}}{\text{TokenCost}}$$
  - Implement budget packing algorithm respecting max token limits ($N$).
  - Implement full node expansion in `kiln node <id>`.
- **Verification Command**:
  ```bash
  python -m pytest tests/test_retrieval.py -v
  ```

### Task 1.4: CLI Tools & Self-Healing Diagnostics (`doctor`, `remember`, `lint-tokens`)
- **Actions**:
  - Implement `kiln remember` CLI command with schema enforcement, secret redaction, and event logging.
  - Implement `kiln doctor` CLI command: verifies graph integrity, flags orphan edges, detects stale nodes via SHA256 hashes, and rebuilds missing SQLite index from flat files.
  - Implement `kiln lint-tokens` CLI: enforces `<=80` lines on `AGENTS.md`, `<=40` words on skill descriptions, `<=40` lines on templates.
- **Verification Command**:
  ```bash
  python -m pytest tests/test_cli_doctor.py -v
  ```

### Task 1.5: Claude Code & Antigravity Primary Adapters
- **Actions**:
  - Define canonical `.kiln/skills/` definitions.
  - Implement generator for Claude Code (`CLAUDE.md`, `.claude/skills/`) and Antigravity (`AGENTS.md`, `.agent/skills/`).
  - Verify prompt cache stability (byte-stable bootstrap headers).
- **Verification Command**:
  ```bash
  python -m pytest tests/test_adapters_primary.py -v
  ```

---

## Milestone 2: Multi-Harness Adapters & Portability (M2)

### Task 2.1: Codex & OpenCode Adapters
- **Actions**:
  - Implement generator for Codex instruction prompts and OpenCode/Cursor `.cursorrules` / agent specs.
  - Implement `kiln build-adapters` ensuring no adapter is hand-written and no instruction is injected twice.
  - Add drift detection to `kiln doctor` (verifying generated adapters match `.kiln/` canonical sources).
- **Verification Command**:
  ```bash
  python -m pytest tests/test_adapters_multi.py -v
  ```

---

## Milestone 3: Hooks, Safety Gates, Token Governor & Evals (M3)

### Task 3.1: Deterministic Lifecycle Hook Gates
- **Actions**:
  - Implement safety gates (fail closed): protected branch blocks, secret detector, tests-not-edited barrier, production deployment gate.
  - Implement helper hooks (fail open): output formatting, cache warmup.
  - Implement state machine runner (`work/<id>/state.yml`, `kiln resume <work-id>`).
- **Verification Command**:
  ```bash
  python -m pytest tests/test_hooks_and_gates.py -v
  ```

### Task 3.2: Token Governor & Telemetry
- **Actions**:
  - Implement output filtering processor (compressing repetitive build/test output while retaining failures).
  - Implement terse chatter rules engine for conversational reasoning.
  - Implement `kiln audit` usage telemetry tracker modeled after `ccusage`.
- **Verification Command**:
  ```bash
  python -m pytest tests/test_token_governor.py -v
  ```

### Task 3.3: Evaluation Harness (Retrieval & Token A/B)
- **Actions**:
  - Implement golden question retrieval evaluation suite in `evals/memory_retrieval/`.
  - Implement token A/B benchmark suite comparing standard vs Kiln-governed task runs.
- **Verification Command**:
  ```bash
  python -m pytest tests/test_evals.py -v
  ```

---

## Milestone 4: Code-Graph Integration & Loop Closers (M4)

### Task 4.1: Graph A (Code Graph) & Navigation Bridges
- **Actions**:
  - Implement Tree-sitter MCP client wrapper and local AST fallback parser in `kiln.graph.code_graph`.
  - Bridge knowledge nodes to code symbols (`requirement -> symbol/file`).
  - Enforce raw file read invariant before modification.
- **Verification Command**:
  ```bash
  python -m pytest tests/test_code_graph.py -v
  ```

### Task 4.2: Closed Loop Automation & Maintenance
- **Actions**:
  - Implement Incident-to-Intent pipeline (`kiln incident`).
  - Implement gardener background scan: marks nodes stale upon evidence file modification, merges duplicates, prunes superseded nodes.
  - Implement CLI packaging and installation documentation (`docs/install.md`).
- **Verification Command**:
  ```bash
  python -m pytest tests/test_gardener_and_pipeline.py -v
  ```
