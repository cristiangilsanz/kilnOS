import pytest
from pathlib import Path
from evals.eval_retrieval import run_retrieval_eval
from evals.eval_token_ab import run_token_ab_eval
from kiln.graph.indexer import compile_graph_index

@pytest.fixture
def eval_graph_environment(tmp_path):
    nodes_dir = tmp_path / "nodes"
    nodes_dir.mkdir()

    (nodes_dir / "dec-db.md").write_text("""---
id: dec-db
type: decision
title: Use SQLite Database
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "agent"
edges:
  - target: req-storage
    type: satisfies
---
SQLite is chosen for zero-dependency local transactions.
""", encoding="utf-8")

    (nodes_dir / "req-storage.md").write_text("""---
id: req-storage
type: requirement
title: Local Storage Engine
status: accepted
confidence: 0.95
created: "2026-09-28T16:00:00Z"
source: "pm"
edges: []
---
Storage must be embedded and require no external daemon.
""", encoding="utf-8")

    (nodes_dir / "std-tdd.md").write_text("""---
id: std-tdd
type: standard
title: TDD Standards
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "team"
edges: []
---
Write tests before implementation code.
""", encoding="utf-8")

    db_path = tmp_path / "index.db"
    compile_graph_index(nodes_dir, db_path)
    return db_path

def test_retrieval_eval_precision_recall(eval_graph_environment):
    db_path = eval_graph_environment
    results = run_retrieval_eval(db_path)

    assert results["precision"] >= 0.75, f"Precision target not met: {results['precision']}"
    assert results["recall"] >= 0.75, f"Recall target not met: {results['recall']}"
    assert results["total_evals"] > 0

def test_token_ab_eval():
    ab_results = run_token_ab_eval()

    assert ab_results["tokens_baseline"] > ab_results["tokens_kiln"]
    assert ab_results["reduction_pct"] >= 20.0
    assert ab_results["lossless_preservation"] is True
