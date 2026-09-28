# Kiln OS: Research & Architectural Decisions

## 1. Foundation Synthesis & Decisions

* **Anthropic AI-Native SDLC Playbook (`claude.com/blog/the-ai-native-sdlc-playbook`)**:
  * *Distilled Pattern*: Strict artifact chaining (Idea → Intent → Spec → Plan → TDD → Review → Deploy) where each stage reads **only** the prior artifact; subagent-per-task isolation; human gates for production/architecture.
  * *Kiln Decision*: Adopt 3-tier gating (Spark, Standard, Critical) with committed markdown artifacts in `work/<id>/`. Enforce deterministic hook gates instead of relying on prompt compliance.
* **Superpowers (`obra/superpowers`)**:
  * *Distilled Pattern*: Systematic engineering discipline, TDD enforcement, disposable git worktrees per subagent, task-by-task commit cadence.
  * *Kiln Decision*: Kiln tasks build test-first inside isolated git worktrees; real shell command stdout is required as evidentiary proof before stage transitions.
* **Agent-OS v3 (`buildermethods/agent-os`)**:
  * *Distilled Pattern*: Decoupled codebase standards (`standards/*.md`) injected conditionally based on file paths and domain context.
  * *Kiln Decision*: Implement `standards/index.yml` routing. Max 5 standards injected per context pack via index pointers, not full prose embeds.
* **Token Governance Tools (`caveman`, `ponytail`, `ppgranger/token-saver`, `ccusage`)**:
  * *Distilled Pattern*:
    * `caveman`: Terseness compression (strips conversational pleasantries/filler, reports 60–75% output token reductions in isolated summaries).
    * `ponytail`: YAGNI behavioral decision ladder (reuse existing code → stdlib → native platform before writing new code; claims ~20–54% reduction).
    * `token-saver` (e.g. `ppgranger/token-saver`): Deterministic CLI output filtering (pruning test/build stdout noise).
    * `ccusage`: Usage telemetry and cache-hit tracking via local session logs.
  * *Kiln Decision*: Output terseness applied only to reasoning/chatter—**never** to specs, plans, security reviews, or diffs. Output filtering via deterministic hooks. Vendor benchmark numbers remain **[Unverified]** until Kiln's internal A/B evals reproduce token delta vs. task pass rate.
* **Graph Memory Systems (`hilyfux/knowledge-graph`, `DeusData/codebase-memory-mcp`, Temporal Graphs)**:
  * *Distilled Pattern*:
    * `hilyfux/knowledge-graph`: Git-native, append-first event log + markdown nodes without embeddings; snapshots survive `/compact` and `/clear`.
    * `DeusData/codebase-memory-mcp`: Tree-sitter AST symbol/call-graph exposed via MCP; vendor benchmarks report 83% vs 92% answer quality vs full file reads.
    * Temporal Graphs (e.g., Zep Graphiti / temporal edge intervals): Nodes have `valid_from`, `valid_to` timestamps and directional `supersedes` edges.
  * *Kiln Decision*:
    * **Graph A (Code Graph)**: Disposable, rebuildable AST index via Tree-sitter MCP (or local fallback). Used strictly for navigation; agents **must always** read the raw target file before editing. Vendor benchmark (83% vs 92%) marked **[Unverified]**.
    * **Graph B (Knowledge Graph)**: Git-native, authoritative markdown nodes (`.kiln/graph/nodes/*.md`) with frontmatter temporal validity (`valid_from`, `valid_to`, `supersedes`) + append-only `.kiln/graph/events.jsonl`.
    * **Retrieval**: Deterministic Personalized PageRank / Decayed BFS script (`kiln pack <id> --budget N`) scoring by relevance, recency, confidence, and status weight over token cost. No embeddings required by default.

---

## 2. Harness Compatibility Matrix

| Capability | Claude Code | OpenAI Codex / CLI | OpenCode / Cursor | Antigravity |
| :--- | :--- | :--- | :--- | :--- |
| **Instruction File** | `CLAUDE.md` (root / home) | `AGENTS.md` (root) | `.cursorrules` / `AGENTS.md` | `AGENTS.md` / `GEMINI.md` |
| **Skill Format** | `.claude/skills/*/SKILL.md` | *Unverified* (Function calls) | Custom / *Unverified* | Native `SKILL.md` (YAML frontmatter) |
| **Subagents** | Subagent tasks / processes | OpenAI Assistants/Swarm SDK | Multi-agent runtime (OpenDevin) | Native `invoke_subagent` / `define_subagent` |
| **Hooks** | Pre/Post tool event hooks | *Unverified* (Wrapper required)| Shell / Git integration | Workflow / Hook scripts & sidecars |
| **Plugins** | `/plugin` marketplace | Function calling tools | Extension ecosystem | Plugin directory architecture |
| **Plan Mode** | Native `/plan` command | Custom prompt / *Unverified* | Cursor Composer Planner | Native `/plan` & plan artifacts |
| **Per-Agent Model**| CLI flag / config per task | API model parameter | Selector per chat/agent | Explicit parameter (`inherit`, `flash`, `pro`)|
| **Prompt Caching** | Anthropic automatic cache | OpenAI prefix caching | Provider-dependent caching | Automatic context caching |
| **MCP Support** | Native (`claude.json`) | Adapter / *Unverified* | Native MCP Client | Native MCP Client |

*Note: Vendor benchmark claims and unconfirmed harness specs are categorized as [Unverified] pending Kiln automated test validation.*

---

## 3. Core Architectural Decisions

1. **Storage & Merge Strategy**: One file per knowledge node (`.kiln/graph/nodes/<id>.md`) + append-only `.kiln/graph/events.jsonl`. Index (`.kiln/graph/index.db` or `.json`) is derived, rebuildable, and gitignored.
2. **Memory Hierarchy**:
   * **L0 Hot** (`<=300` tokens): Byte-stable `AGENTS.md` + active task session state.
   * **L1 Working**: Active task context pack generated by `kiln pack <id>`.
   * **L2 Warm**: Compact graph index (ID, title, status, 1-line summary).
   * **L3 Cold**: Raw node bodies & ADRs (retrieved on-demand via `kiln node <id>`).
   * **L4 Raw**: Git log, transcripts, telemetry (grep/streamed only).
3. **Resilience & Prompt-Injection Defense**:
   * Rebuildable index from flat files on corruption (`kiln doctor`).
   * Memory nodes and tool returns are treated as untrusted data (wrapped in quarantine blocks, never evaluated as direct prompt instructions).
   * Hook gates fail closed on protected paths, secret patterns, and prod deployment boundaries.
4. **Token Governor Strategy**:
   * Measure with local telemetry (`ccusage` style).
   * Scoped reads only; avoid re-reads via content hashing.
   * Strict token budgets enforced in CI via `kiln lint-tokens`.
