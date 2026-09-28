import hashlib
from pathlib import Path
import pytest
import yaml

from kiln.pipeline.incident import incident_to_intent
from kiln.pipeline.gardener import run_gardener_maintenance
from kiln.graph.indexer import compile_graph_index, query_node_by_id

def test_incident_to_intent_pipeline(tmp_path):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    events_file = tmp_path / ".kiln" / "graph" / "events.jsonl"
    work_dir = tmp_path / "work"

    intent_path, node_path = incident_to_intent(
        root_dir=tmp_path,
        incident_id="inc-101",
        title="Production Connection Pool Exhaustion",
        cause="Database connection pool size too small under peak load",
        resolution="Scale max connections and add connection keepalive"
    )

    assert node_path.exists()
    assert intent_path.exists()

    node_content = node_path.read_text(encoding="utf-8")
    assert "inc-101" in node_content
    assert "type: incident" in node_content

    intent_content = intent_path.read_text(encoding="utf-8")
    assert "inc-101" in intent_content
    assert "Production Connection Pool Exhaustion" in intent_content

def test_gardener_stale_detection_and_rebuild(tmp_path):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    db_path = tmp_path / ".kiln" / "graph" / "index.db"

    ev_file = tmp_path / "src" / "db.py"
    ev_file.parent.mkdir(parents=True)
    ev_file.write_text("POOL_SIZE = 10\n", encoding="utf-8")
    ev_hash = hashlib.sha256(ev_file.read_bytes()).hexdigest()

    # Node starts accepted
    node_file = nodes_dir / "dec-pool.md"
    node_file.write_text(f"""---
id: dec-pool
type: decision
title: Connection Pool Settings
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "agent"
evidence:
  - file: "src/db.py"
    sha256: "{ev_hash}"
edges: []
---
Connection pool is set to 10.
""", encoding="utf-8")

    compile_graph_index(nodes_dir, db_path)

    # Change evidence file
    ev_file.write_text("POOL_SIZE = 50\n", encoding="utf-8")

    # Run gardener
    stale_count = run_gardener_maintenance(tmp_path)
    assert stale_count == 1

    # Check that node file was marked stale
    updated_node_content = node_file.read_text(encoding="utf-8")
    assert "status: stale" in updated_node_content

    # Index was rebuilt and reflects stale status
    row = query_node_by_id(db_path, "dec-pool")
    assert row is not None
    assert row["status"] == "stale"
