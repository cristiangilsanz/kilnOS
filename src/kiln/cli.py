from __future__ import annotations
import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import yaml

from kiln.graph.schema import (
    VALID_TYPES, VALID_STATUSES, redact_secrets, validate_node_file
)
from kiln.graph.events import EventLogger
from kiln.graph.indexer import compile_graph_index, query_node_by_id
from kiln.retrieval.packer import pack_context, expand_node

from kiln.adapters.multi import build_all_adapters, check_adapter_drift
from kiln.hooks.state_runner import resume_task

def get_kiln_paths(base_dir: Optional[Path] = None) -> tuple[Path, Path, Path, Path]:
    base = base_dir or Path.cwd()
    kiln_dir = base / ".kiln"
    nodes_dir = kiln_dir / "graph" / "nodes"
    events_file = kiln_dir / "graph" / "events.jsonl"
    index_db = kiln_dir / "graph" / "index.db"
    return base, nodes_dir, events_file, index_db

def cmd_remember(args: argparse.Namespace) -> int:
    base, nodes_dir, events_file, index_db = get_kiln_paths()
    nodes_dir.mkdir(parents=True, exist_ok=True)

    node_id = args.id
    node_type = args.type
    title = redact_secrets(args.title)
    body = redact_secrets(args.body or "")
    status = args.status
    confidence = float(args.confidence)

    if node_type not in VALID_TYPES:
        print(f"[Error] Invalid type '{node_type}'. Valid types: {sorted(VALID_TYPES)}")
        return 1
    if status not in VALID_STATUSES:
        print(f"[Error] Invalid status '{status}'. Valid statuses: {sorted(VALID_STATUSES)}")
        return 1

    created_iso = datetime.now(timezone.utc).isoformat()

    frontmatter = {
        "id": node_id,
        "type": node_type,
        "title": title,
        "status": status,
        "confidence": confidence,
        "created": created_iso,
        "source": "cli-remember",
        "evidence": [],
        "valid_from": created_iso,
        "valid_to": None,
        "supersedes": None,
        "edges": []
    }

    node_content = f"---\n{yaml.dump(frontmatter, sort_keys=False)}---\n{body}\n"
    node_path = nodes_dir / f"{node_id}.md"
    node_path.write_text(node_content, encoding="utf-8")

    # Log event
    logger = EventLogger(events_file)
    logger.log_event("node_created", node_id, {"title": title, "type": node_type}, actor="cli")

    # Refresh index
    compile_graph_index(nodes_dir, index_db)
    print(f"[Success] Remembered node '{node_id}' in {node_path}")
    return 0

def cmd_doctor(args: argparse.Namespace) -> int:
    base, nodes_dir, events_file, index_db = get_kiln_paths()
    issues_found = False

    print("[Kiln Doctor] Running system diagnostics...")

    # 1. Directory checks
    if not nodes_dir.exists():
        print(f"[*] Nodes directory missing: creating {nodes_dir}")
        nodes_dir.mkdir(parents=True, exist_ok=True)

    # 2. Index existence & integrity
    if not index_db.exists():
        print(f"[!] Index database missing at {index_db}. Rebuilding from flat files...")
        count = compile_graph_index(nodes_dir, index_db)
        print(f"[+] Rebuilt index with {count} nodes.")
    else:
        try:
            # Check SQLite readability
            import sqlite3
            conn = sqlite3.connect(index_db)
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM nodes")
            count = cur.fetchone()[0]
            conn.close()
            print(f"[+] SQLite index healthy ({count} indexed nodes).")
        except Exception as e:
            print(f"[!] Index corrupt: {e}. Rebuilding...")
            compile_graph_index(nodes_dir, index_db)

    # 3. Schema & Evidence Validation
    node_ids = set()
    node_files = list(nodes_dir.glob("*.md")) if nodes_dir.exists() else []
    all_nodes = []

    for nf in node_files:
        try:
            node = validate_node_file(nf)
            node_ids.add(node.id)
            all_nodes.append((nf, node))
        except Exception as e:
            print(f"[Error] Schema violation in {nf.name}: {e}")
            issues_found = True

    # 4. Check for orphan edges & stale evidence
    for nf, node in all_nodes:
        # Check edges
        for edge in node.edges:
            if edge.target not in node_ids:
                print(f"[Warning] Orphan edge in {node.id} -> target '{edge.target}' does not exist.")

        # Check evidence
        for ev in node.evidence:
            ev_file = base / ev.file
            if not ev_file.exists():
                print(f"[Error] Stale evidence in {node.id}: File {ev.file} does not exist.")
                issues_found = True
            else:
                curr_hash = hashlib.sha256(ev_file.read_bytes()).hexdigest()
                if curr_hash != ev.sha256:
                    print(f"[Error] Stale evidence in {node.id}: SHA256 mismatch for {ev.file}.")
                    issues_found = True

    # 5. Check adapter drift (only if adapters exist or repo initialized)
    if (base / ".kiln").exists():
        drifted = check_adapter_drift(base)
        for d in drifted:
            print(f"[Warning] Adapter drift detected in {d}. Run 'kiln build-adapters' to resync.")

    if issues_found:
        print("[Kiln Doctor] Issues detected!")
        return 1
    else:
        print("[Kiln Doctor] All checks passed cleanly.")
        return 0

def cmd_build_adapters(args: argparse.Namespace) -> int:
    base, _, _, _ = get_kiln_paths()
    print("[Kiln Adapters] Generating harness adapters from canonical .kiln/ source...")
    build_all_adapters(base)
    print("[Kiln Adapters] Adapters generated for Claude Code, Antigravity, Codex, and OpenCode.")
    return 0

def cmd_pack(args: argparse.Namespace) -> int:
    base, nodes_dir, events_file, index_db = get_kiln_paths()
    if not index_db.exists():
        compile_graph_index(nodes_dir, index_db)

    seed_ids = [args.work_id]
    pack = pack_context(index_db, seed_ids, budget_tokens=args.budget)
    print(pack.to_markdown())
    print(f"\n<!-- Total Tokens: {pack.total_tokens} / Budget: {args.budget} -->")
    return 0

def cmd_node(args: argparse.Namespace) -> int:
    base, nodes_dir, events_file, index_db = get_kiln_paths()
    expanded = expand_node(nodes_dir, args.node_id)
    if not expanded:
        print(f"[Error] Node '{args.node_id}' not found.")
        return 1
    print(f"# [{expanded['id']}] {expanded['title']}")
    print(f"**Type:** {expanded['type']} | **Status:** {expanded['status']} | **Confidence:** {expanded['confidence']}")
    print(f"**Created:** {expanded['created']} | **Source:** {expanded['source']}\n")
    print("## Body\n")
    print(expanded["body"])
    return 0

def cmd_lint_tokens(args: argparse.Namespace) -> int:
    base = Path.cwd()
    failed = False

    # 1. AGENTS.md <= 80 lines
    agents_md = base / "AGENTS.md"
    if agents_md.exists():
        line_count = len(agents_md.read_text(encoding="utf-8").splitlines())
        if line_count > 80:
            print(f"[Lint Error] AGENTS.md exceeds 80 lines: found {line_count} lines.")
            failed = True
        else:
            print(f"[Lint OK] AGENTS.md line count: {line_count}/80")

    # 2. Skill descriptions <= 40 words
    skills_dir = base / ".kiln" / "skills"
    if skills_dir.exists():
        for skill_md in skills_dir.glob("*/SKILL.md"):
            try:
                content = skill_md.read_text(encoding="utf-8")
                # Parse frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        fm = yaml.safe_load(parts[1]) or {}
                        desc = fm.get("description", "")
                        words = len(desc.split())
                        if words > 40:
                            print(f"[Lint Error] Skill {skill_md.parent.name} description exceeds 40 words: {words}")
                            failed = True
            except Exception:
                pass

    # 3. Templates <= 40 lines
    templates_dir = base / ".kiln" / "templates"
    if templates_dir.exists():
        for tmpl in templates_dir.glob("*.md"):
            lines = len(tmpl.read_text(encoding="utf-8").splitlines())
            if lines > 40:
                print(f"[Lint Error] Template {tmpl.name} exceeds 40 lines: {lines}")
                failed = True

    return 1 if failed else 0

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="kiln", description="Kiln OS Agent CLI")
    subparsers = parser.add_subparsers(dest="command")

    # remember
    p_remember = subparsers.add_parser("remember", help="Record knowledge node")
    p_remember.add_argument("--id", required=True, help="Node ID (e.g. dec-001)")
    p_remember.add_argument("--type", required=True, help="Node type")
    p_remember.add_argument("--title", required=True, help="Short title")
    p_remember.add_argument("--body", default="", help="Markdown body")
    p_remember.add_argument("--status", default="accepted", help="Status")
    p_remember.add_argument("--confidence", default=1.0, type=float, help="Confidence (0.0-1.0)")

    # doctor
    subparsers.add_parser("doctor", help="Check and repair system health")

    # pack
    p_pack = subparsers.add_parser("pack", help="Generate L1 context pack")
    p_pack.add_argument("work_id", help="Work task ID or seed ID")
    p_pack.add_argument("--budget", type=int, default=1500, help="Max token budget")

    # node
    p_node = subparsers.add_parser("node", help="Expand node by ID")
    p_node.add_argument("node_id", help="Node ID")

    # lint-tokens
    subparsers.add_parser("lint-tokens", help="Check token budgets across files")

    # build-adapters
    subparsers.add_parser("build-adapters", help="Generate harness adapters from .kiln/")

    # resume
    p_resume = subparsers.add_parser("resume", help="Resume task from work/<id>/state.yml")
    p_resume.add_argument("work_id", help="Work task ID")
    p_resume.add_argument("--budget", type=int, default=1500, help="Max context pack budget")

    # audit
    p_audit = subparsers.add_parser("audit", help="Report token telemetry audit for task")
    p_audit.add_argument("work_id", help="Work task ID")

    # init
    subparsers.add_parser("init", help="Initialize .kiln workspace and adapters")

    # create
    p_create = subparsers.add_parser("create", help="Create new task from idea")
    p_create.add_argument("idea", help="Task idea or objective")
    p_create.add_argument("--tier", choices=["spark", "standard", "critical"], default=None, help="Rigor tier override")

    # install-hooks
    subparsers.add_parser("install-hooks", help="Install git safety hooks into .git/hooks/")

    # gate
    p_gate = subparsers.add_parser("gate", help="Validate stage transition against tier checkpoints")
    p_gate.add_argument("work_id", help="Work task ID")
    p_gate.add_argument("target_stage", help="Target stage (e.g. build, review, release)")

    # incident
    p_inc = subparsers.add_parser("incident", help="Record incident and spawn remediation intent")
    p_inc.add_argument("--id", required=True, help="Incident ID (e.g. inc-001)")
    p_inc.add_argument("--title", required=True, help="Incident title")
    p_inc.add_argument("--cause", required=True, help="Root cause explanation")
    p_inc.add_argument("--resolution", required=True, help="Remediation resolution")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    from kiln.governor.audit import calculate_session_audit
    from kiln.pipeline.incident import incident_to_intent
    from kiln.pipeline.task_creator import create_task
    from kiln.pipeline.lifecycle import install_git_hooks, validate_stage_transition
    from kiln.hooks.state_runner import load_state, save_state

    def handle_create(a):
        wid, wdir = create_task(Path.cwd(), a.idea, tier_override=a.tier)
        print(f"[Kiln Task] Created task {wid} in {wdir}")
        print(f"  Artifact: {wdir / 'intent.md'}")
        print(f"  State:    {wdir / 'state.yml'}")
        return 0

    def handle_gate(a):
        work_dir = Path.cwd() / "work" / a.work_id
        if not work_dir.exists():
            print(f"[Error] Task directory {work_dir} not found.")
            return 1
        state = load_state(work_dir)
        allowed = validate_stage_transition(state, a.target_stage)
        if not allowed:
            print(f"[Gate Blocked] Transition to '{a.target_stage}' blocked by pending checkpoints in tier '{state.get('tier')}'.")
            return 1
        state["stage"] = a.target_stage
        save_state(work_dir, state)
        print(f"[Gate Approved] Task {a.work_id} transitioned to stage '{a.target_stage}'.")
        return 0

    commands = {
        "init": lambda a: cmd_build_adapters(a),
        "create": handle_create,
        "install-hooks": lambda a: (install_git_hooks(Path.cwd()) and print("[Success] Git safety hooks installed into .git/hooks/") or 0) and 0 or 0,
        "gate": handle_gate,
        "remember": cmd_remember,
        "doctor": cmd_doctor,
        "pack": cmd_pack,
        "node": cmd_node,
        "lint-tokens": cmd_lint_tokens,
        "build-adapters": cmd_build_adapters,
        "resume": lambda a: print(resume_task(Path.cwd(), a.work_id, budget_tokens=a.budget)) or 0,
        "incident": lambda a: (
            incident_to_intent(Path.cwd(), a.id, a.title, a.cause, a.resolution),
            print(f"[Success] Incident {a.id} recorded and remediation intent created in work/{a.id}-fix/intent.md")
        ) and 0 or 0,
        "audit": lambda a: (
            lambda res: (
                print(f"[Kiln Token Audit] Task: {res['task_id']}"),
                print(f"  Prompt Tokens:     {res['total_prompt']}"),
                print(f"  Cached Tokens:     {res['total_cached']}"),
                print(f"  Completion Tokens: {res['total_completion']}"),
                print(f"  Net Billable:      {res['net_billable']}"),
                print(f"  Telemetry Records: {res['records']}")
            )
        )(calculate_session_audit(Path.cwd() / ".kiln" / "audit.jsonl", a.work_id)) and 0 or 0
    }
    return commands[args.command](args)

if __name__ == "__main__":
    sys.exit(main())
