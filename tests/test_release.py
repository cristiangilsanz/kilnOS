import pytest
from pathlib import Path
from kiln.pipeline.release import prepare_release
from kiln.graph.indexer import compile_graph_index

def test_prepare_release_generation(tmp_path):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    events_file = tmp_path / ".kiln" / "graph" / "events.jsonl"
    db_path = tmp_path / ".kiln" / "graph" / "index.db"

    # Seed an intent and decision
    (nodes_dir / "dec-001.md").write_text("""---
id: dec-001
type: decision
title: Use SQLite
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "agent"
edges: []
---
SQLite decision.
""", encoding="utf-8")

    compile_graph_index(nodes_dir, db_path)

    rel_node_path, changelog_path = prepare_release(
        root_dir=tmp_path,
        version="v1.0.0",
        summary="Initial release of Kiln OS core engine"
    )

    assert rel_node_path.exists()
    assert changelog_path.exists()

    rel_content = rel_node_path.read_text(encoding="utf-8")
    assert "v1.0.0" in rel_content
    assert "type: release" in rel_content

    changelog_content = changelog_path.read_text(encoding="utf-8")
    assert "v1.0.0" in changelog_content
    assert "Initial release of Kiln OS core engine" in changelog_content
