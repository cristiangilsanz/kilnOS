import hashlib
import json
import sqlite3
from pathlib import Path
from kiln.cli import main
from kiln.graph.indexer import compile_graph_index

def test_cli_remember(tmp_path, monkeypatch):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    events_file = tmp_path / ".kiln" / "graph" / "events.jsonl"
    db_file = tmp_path / ".kiln" / "graph" / "index.db"

    monkeypatch.chdir(tmp_path)

    # Invoke remember via CLI
    ret = main([
        "remember",
        "--id", "std-code-style",
        "--type", "standard",
        "--title", "Python PEP8 Guidelines",
        "--body", "Always use 4 spaces for indentation sk-ant-secret1234567890abcdef."
    ])
    assert ret == 0

    node_file = nodes_dir / "std-code-style.md"
    assert node_file.exists()
    content = node_file.read_text(encoding="utf-8")
    assert "sk-ant-" not in content
    assert "[REDACTED_SECRET]" in content
    assert "Always use 4 spaces" in content

    # Check event log
    assert events_file.exists()
    events = events_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(events) == 1
    assert json.loads(events[0])["node_id"] == "std-code-style"

def test_cli_doctor_rebuild_corrupt_index(tmp_path, monkeypatch):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    db_file = tmp_path / ".kiln" / "graph" / "index.db"

    # Create a node
    (nodes_dir / "dec-001.md").write_text("""---
id: dec-001
type: decision
title: Use Postgres
status: accepted
confidence: 0.9
created: "2026-09-28T16:00:00Z"
source: "agent"
edges: []
---
Postgres is our primary database.
""", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    # Index is missing, doctor should detect and rebuild it
    ret = main(["doctor"])
    assert ret == 0
    assert db_file.exists()

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM nodes WHERE id = 'dec-001'")
    row = cur.fetchone()
    assert row is not None
    assert row[1] == "Use Postgres"
    conn.close()

def test_cli_doctor_stale_detection(tmp_path, monkeypatch):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    evidence_file = tmp_path / "src" / "main.py"
    evidence_file.parent.mkdir(parents=True)
    evidence_file.write_text("print('hello world')\n", encoding="utf-8")

    initial_hash = hashlib.sha256(evidence_file.read_bytes()).hexdigest()

    # Create node with evidence
    (nodes_dir / "dec-main.md").write_text(f"""---
id: dec-main
type: decision
title: Main Entrypoint
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "agent"
evidence:
  - file: "src/main.py"
    sha256: "{initial_hash}"
edges: []
---
Main entrypoint implementation.
""", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    compile_graph_index(nodes_dir, tmp_path / ".kiln" / "graph" / "index.db")

    # Tamper with evidence file
    evidence_file.write_text("print('modified world')\n", encoding="utf-8")

    # Doctor should report stale evidence node
    ret = main(["doctor"])
    # Doctor flags issue with exit code 1 or warning
    assert ret == 1

def test_cli_lint_tokens(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    # Over budget AGENTS.md (> 80 lines)
    (tmp_path / "AGENTS.md").write_text("\n".join([f"line {i}" for i in range(85)]), encoding="utf-8")
    
    ret = main(["lint-tokens"])
    assert ret == 1

    # Fix AGENTS.md
    (tmp_path / "AGENTS.md").write_text("# Valid AGENTS.md\nSmall content\n", encoding="utf-8")
    ret = main(["lint-tokens"])
    assert ret == 0
