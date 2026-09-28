import pytest
from pathlib import Path
from kiln.graph.gc import run_graph_gc
from kiln.graph.indexer import compile_graph_index

def test_graph_gc_archive_superseded(tmp_path):
    nodes_dir = tmp_path / ".kiln" / "graph" / "nodes"
    nodes_dir.mkdir(parents=True)
    archive_dir = tmp_path / ".kiln" / "graph" / "archive"
    db_path = tmp_path / ".kiln" / "graph" / "index.db"

    # Active node
    (nodes_dir / "dec-001.md").write_text("""---
id: dec-001
type: decision
title: Use Postgres
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "agent"
edges: []
---
Active decision.
""", encoding="utf-8")

    # Superseded node
    (nodes_dir / "dec-old.md").write_text("""---
id: dec-old
type: decision
title: Use MySQL
status: superseded
confidence: 0.8
created: "2025-01-01T00:00:00Z"
source: "agent"
edges: []
---
Old superseded decision.
""", encoding="utf-8")

    compile_graph_index(nodes_dir, db_path)

    stats = run_graph_gc(tmp_path)
    assert stats["archived_nodes"] == 1
    assert stats["vacuumed"] is True

    # Superseded file moved to archive
    assert not (nodes_dir / "dec-old.md").exists()
    assert (archive_dir / "dec-old.md").exists()

    # Active file remains
    assert (nodes_dir / "dec-001.md").exists()
