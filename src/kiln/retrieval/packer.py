from __future__ import annotations
import sqlite3
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from kiln.graph.schema import validate_node_file

@dataclass
class ContextPack:
    packed_nodes: List[Dict[str, Any]] = field(default_factory=list)
    total_tokens: int = 0

    def to_markdown(self) -> str:
        lines = ["# Kiln Context Pack (L1 Working Memory)", ""]
        for node in self.packed_nodes:
            lines.append(f"- **[{node['id']}]** ({node['type']}) {node['title']}: {node['body_summary']}")
        return "\n".join(lines)

def parse_iso_or_default(dt_str: str) -> datetime:
    try:
        # Handles 'Z' or standard ISO strings
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return datetime(2020, 1, 1, tzinfo=timezone.utc)

def pack_context(
    db_path: Path,
    seed_node_ids: List[str],
    budget_tokens: int = 1500,
    max_depth: int = 3,
    decay_factor: float = 0.85
) -> ContextPack:
    """Deterministic, token-weighted retrieval based on decayed BFS graph traversal."""
    db_path = Path(db_path)
    if not db_path.exists():
        return ContextPack()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Load all nodes into memory map
    cur.execute("SELECT * FROM nodes")
    nodes_map: Dict[str, Dict[str, Any]] = {row["id"]: dict(row) for row in cur.fetchall()}

    # Load all edges into adjacency list (bidirectional for traversal)
    cur.execute("SELECT source_id, target_id, type FROM edges")
    adj: Dict[str, List[str]] = {}
    for row in cur.fetchall():
        s, t = row["source_id"], row["target_id"]
        adj.setdefault(s, []).append(t)
        adj.setdefault(t, []).append(s)

    conn.close()

    # Decayed BFS from seeds
    relevance_scores: Dict[str, float] = {}
    queue = deque()
    for s_id in seed_node_ids:
        if s_id in nodes_map:
            relevance_scores[s_id] = 1.0
            queue.append((s_id, 0, 1.0))

    while queue:
        curr_id, depth, score = queue.popleft()
        if depth >= max_depth:
            continue
        next_score = score * decay_factor
        for neighbor in adj.get(curr_id, []):
            if neighbor not in relevance_scores or relevance_scores[neighbor] < next_score:
                relevance_scores[neighbor] = next_score
                queue.append((neighbor, depth + 1, next_score))

    status_weights = {
        "accepted": 1.0,
        "proposed": 0.7,
        "stale": 0.3,
        "superseded": 0.0,
    }

    now = datetime.now(timezone.utc)
    candidates: List[tuple[float, Dict[str, Any], int]] = []

    for node_id, relevance in relevance_scores.items():
        node = nodes_map.get(node_id)
        if not node:
            continue

        # Filter out superseded nodes
        if node["status"] == "superseded":
            continue

        # Filter out expired validity windows
        if node.get("valid_to"):
            valid_to_dt = parse_iso_or_default(node["valid_to"])
            if valid_to_dt < now:
                continue

        stat_weight = status_weights.get(node["status"], 0.5)
        conf = float(node.get("confidence") or 1.0)

        # Recency calculation (normalized between 0.5 and 1.0)
        created_dt = parse_iso_or_default(node.get("created") or "")
        age_days = max(0.0, (now - created_dt).total_seconds() / 86400.0)
        recency = 1.0 / (1.0 + (age_days / 365.0))

        # Token cost for this summary entry in the pack
        summary_text = f"- **[{node['id']}]** ({node['type']}) {node['title']}: {node['body_summary']}"
        token_cost = max(10, len(summary_text) // 4)

        final_score = (relevance * recency * conf * stat_weight) / max(1, token_cost)
        candidates.append((final_score, node, token_cost))

    # Sort descending by score
    candidates.sort(key=lambda x: x[0], reverse=True)

    packed: List[Dict[str, Any]] = []
    total_tokens = 0
    for _, node, cost in candidates:
        if total_tokens + cost <= budget_tokens:
            packed.append(node)
            total_tokens += cost
        else:
            break

    return ContextPack(packed_nodes=packed, total_tokens=total_tokens)

def expand_node(nodes_dir: Path, node_id: str) -> Optional[Dict[str, Any]]:
    """Expands a single node to full L3 markdown body and frontmatter."""
    nodes_dir = Path(nodes_dir)
    target_file = nodes_dir / f"{node_id}.md"
    if not target_file.exists():
        # Fallback search if id is not identical to filename
        matches = list(nodes_dir.glob(f"*{node_id}*.md"))
        if matches:
            target_file = matches[0]
        else:
            return None

    try:
        node = validate_node_file(target_file)
        return {
            "id": node.id,
            "type": node.type,
            "title": node.title,
            "status": node.status,
            "confidence": node.confidence,
            "created": node.created,
            "source": node.source,
            "body": node.body,
            "edges": [{"target": e.target, "type": e.type} for e in node.edges],
            "evidence": [{"file": ev.file, "sha256": ev.sha256} for ev in node.evidence],
        }
    except Exception:
        return None
