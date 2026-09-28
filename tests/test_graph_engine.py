import pytest
import sqlite3
import json
from pathlib import Path
from kiln.graph.schema import KnowledgeNode, validate_node_file, redact_secrets
from kiln.graph.events import EventLogger
from kiln.graph.indexer import compile_graph_index, query_node_by_id

def test_node_schema_validation(tmp_path):
    valid_yaml_content = """---
id: dec-001
type: decision
title: Use SQLite for Graph Cache
status: accepted
confidence: 0.95
created: "2026-09-28T16:00:00Z"
source: "architect"
evidence:
  - file: "work/000-kiln/intent.md"
    sha256: "abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd"
valid_from: "2026-09-28T16:00:00Z"
valid_to: null
supersedes: null
edges:
  - target: req-001
    type: satisfies
    valid_from: "2026-09-28T16:00:00Z"
    valid_to: null
---
# Context & Rationale
We chose SQLite because it allows zero-configuration transactional indexing.
"""
    node_file = tmp_path / "dec-001.md"
    node_file.write_text(valid_yaml_content, encoding="utf-8")

    node = validate_node_file(node_file)
    assert node.id == "dec-001"
    assert node.type == "decision"
    assert node.status == "accepted"
    assert len(node.edges) == 1
    assert node.edges[0].target == "req-001"
    assert "Context & Rationale" in node.body

def test_node_schema_invalid_status(tmp_path):
    invalid_yaml_content = """---
id: dec-002
type: decision
title: Bad Status
status: unknown_status
confidence: 0.95
created: "2026-09-28T16:00:00Z"
source: "architect"
---
Body content.
"""
    node_file = tmp_path / "dec-002.md"
    node_file.write_text(invalid_yaml_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid status"):
        validate_node_file(node_file)

def test_secret_redaction():
    text_with_secrets = "Here is my secret token: sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz and AWS AKIAIOSFODNN7EXAMPLE"
    redacted = redact_secrets(text_with_secrets)
    assert "sk-ant-" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "[REDACTED_SECRET]" in redacted

def test_event_logging(tmp_path):
    events_file = tmp_path / "events.jsonl"
    logger = EventLogger(events_file)
    logger.log_event("node_created", "dec-001", {"title": "Test Decision"}, actor="agent")
    
    assert events_file.exists()
    lines = events_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event"] == "node_created"
    assert event["node_id"] == "dec-001"
    assert event["actor"] == "agent"

def test_sqlite_indexing_and_fts(tmp_path):
    nodes_dir = tmp_path / "nodes"
    nodes_dir.mkdir()
    node1 = nodes_dir / "dec-001.md"
    node1.write_text("""---
id: dec-001
type: decision
title: SQLite Database
status: accepted
confidence: 0.9
created: "2026-09-28T16:00:00Z"
source: "agent"
edges: []
---
Body discussing sqlite database caching.
""", encoding="utf-8")

    node2 = nodes_dir / "std-001.md"
    node2.write_text("""---
id: std-001
type: standard
title: TDD Standards
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "human"
edges:
  - target: dec-001
    type: constrains
---
Body discussing red green refactor rules.
""", encoding="utf-8")

    db_path = tmp_path / "index.db"
    compile_graph_index(nodes_dir, db_path)

    assert db_path.exists()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM nodes")
    assert cur.fetchone()[0] == 2

    cur.execute("SELECT count(*) FROM edges")
    assert cur.fetchone()[0] == 1

    # FTS search test
    cur.execute("SELECT id FROM fts_nodes WHERE fts_nodes MATCH 'sqlite'")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "dec-001"
    conn.close()

    queried = query_node_by_id(db_path, "dec-001")
    assert queried is not None
    assert queried["title"] == "SQLite Database"
