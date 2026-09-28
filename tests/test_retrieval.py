import pytest
from pathlib import Path
from kiln.graph.indexer import compile_graph_index
from kiln.retrieval.packer import pack_context, expand_node

@pytest.fixture
def populated_graph(tmp_path):
    nodes_dir = tmp_path / "nodes"
    nodes_dir.mkdir()

    # Seed task node
    (nodes_dir / "task-001.md").write_text("""---
id: task-001
type: intent
title: Implement Payment Gateway
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "human"
edges:
  - target: req-pay
    type: derives_from
  - target: std-sec
    type: constrains
---
Payment gateway integration task intent.
""", encoding="utf-8")

    # Linked requirement
    (nodes_dir / "req-pay.md").write_text("""---
id: req-pay
type: requirement
title: Stripe API v2 Support
status: accepted
confidence: 0.95
created: "2026-09-28T16:10:00Z"
source: "pm"
edges:
  - target: dec-stripe
    type: satisfies
---
Must support credit card tokenization and idempotency keys.
""", encoding="utf-8")

    # Linked decision
    (nodes_dir / "dec-stripe.md").write_text("""---
id: dec-stripe
type: decision
title: Use Stripe Python SDK
status: accepted
confidence: 0.9
created: "2026-09-28T16:20:00Z"
source: "tech-lead"
edges: []
---
Stripe official SDK handles retries and backoff.
""", encoding="utf-8")

    # Linked standard
    (nodes_dir / "std-sec.md").write_text("""---
id: std-sec
type: standard
title: PCI Compliance Standards
status: accepted
confidence: 1.0
created: "2026-09-28T16:00:00Z"
source: "sec-team"
edges: []
---
Never log raw credit card numbers or secret tokens.
""", encoding="utf-8")

    # Superseded older decision
    (nodes_dir / "dec-paypal.md").write_text("""---
id: dec-paypal
type: decision
title: Use PayPal SDK
status: superseded
confidence: 0.8
created: "2025-01-01T00:00:00Z"
source: "old-team"
supersedes: null
edges: []
---
Old PayPal SDK implementation details.
""", encoding="utf-8")

    # Unrelated node
    (nodes_dir / "dec-unrelated.md").write_text("""---
id: dec-unrelated
type: decision
title: Video Transcoder Setup
status: accepted
confidence: 0.7
created: "2026-01-01T00:00:00Z"
source: "media-team"
edges: []
---
FFmpeg video streaming configurations.
""", encoding="utf-8")

    db_path = tmp_path / "index.db"
    compile_graph_index(nodes_dir, db_path)
    return nodes_dir, db_path

def test_retrieval_pack_budget(populated_graph):
    nodes_dir, db_path = populated_graph

    # Pack context with budget 200 tokens
    pack = pack_context(
        db_path=db_path,
        seed_node_ids=["task-001"],
        budget_tokens=200
    )

    assert pack.total_tokens <= 200
    node_ids = [n["id"] for n in pack.packed_nodes]
    # task-001 and its direct connections should be prioritized
    assert "task-001" in node_ids
    assert "req-pay" in node_ids or "std-sec" in node_ids
    # superseded node must NOT be in the pack
    assert "dec-paypal" not in node_ids
    # unrelated node should not be in the pack
    assert "dec-unrelated" not in node_ids

def test_expand_node(populated_graph):
    nodes_dir, db_path = populated_graph
    expanded = expand_node(nodes_dir, "dec-stripe")
    assert expanded is not None
    assert expanded["id"] == "dec-stripe"
    assert "Stripe official SDK" in expanded["body"]
