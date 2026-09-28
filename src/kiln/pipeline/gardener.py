from __future__ import annotations
import hashlib
from pathlib import Path
from typing import List
import yaml

from kiln.graph.schema import parse_frontmatter
from kiln.graph.indexer import compile_graph_index

def run_gardener_maintenance(root_dir: Path) -> int:
    """Gardener maintenance process: detects stale nodes when evidence file SHA256 changes."""
    root_dir = Path(root_dir)
    nodes_dir = root_dir / ".kiln" / "graph" / "nodes"
    index_db = root_dir / ".kiln" / "graph" / "index.db"

    if not nodes_dir.exists():
        return 0

    stale_count = 0

    for node_file in nodes_dir.glob("*.md"):
        content = node_file.read_text(encoding="utf-8")
        try:
            data, body = parse_frontmatter(content)
        except Exception:
            continue

        evidence_list = data.get("evidence", []) or []
        node_stale = False

        for ev in evidence_list:
            file_rel = ev.get("file", "")
            expected_sha = ev.get("sha256", "")
            target_file = root_dir / file_rel

            if not target_file.exists():
                node_stale = True
                break

            actual_sha = hashlib.sha256(target_file.read_bytes()).hexdigest()
            if actual_sha != expected_sha:
                node_stale = True
                break

        if node_stale and data.get("status") != "stale":
            data["status"] = "stale"
            new_content = f"---\n{yaml.dump(data, sort_keys=False)}---\n{body}\n"
            node_file.write_text(new_content, encoding="utf-8")
            stale_count += 1

    # Rebuild index
    compile_graph_index(nodes_dir, index_db)
    return stale_count
