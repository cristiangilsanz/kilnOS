from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from kiln.retrieval.packer import pack_context

GOLDEN_RETRIEVAL_DATASET = [
    {
        "query_desc": "Storage architecture and database decisions",
        "seeds": ["dec-db"],
        "expected_relevant": {"dec-db", "req-storage"},
        "budget": 500
    },
    {
        "query_desc": "Development lifecycle and TDD testing rules",
        "seeds": ["std-tdd"],
        "expected_relevant": {"std-tdd"},
        "budget": 500
    }
]

def run_retrieval_eval(db_path: Path) -> Dict[str, Any]:
    """Runs golden question evaluation against the compiled graph index."""
    total_precision = 0.0
    total_recall = 0.0
    count = len(GOLDEN_RETRIEVAL_DATASET)

    for item in GOLDEN_RETRIEVAL_DATASET:
        pack = pack_context(db_path, item["seeds"], budget_tokens=item["budget"])
        retrieved_ids = {n["id"] for n in pack.packed_nodes}
        expected_ids = item["expected_relevant"]

        true_positives = len(retrieved_ids.intersection(expected_ids))
        precision = true_positives / len(retrieved_ids) if retrieved_ids else 0.0
        recall = true_positives / len(expected_ids) if expected_ids else 0.0

        total_precision += precision
        total_recall += recall

    avg_precision = total_precision / count if count else 0.0
    avg_recall = total_recall / count if count else 0.0

    return {
        "precision": avg_precision,
        "recall": avg_recall,
        "total_evals": count,
    }
