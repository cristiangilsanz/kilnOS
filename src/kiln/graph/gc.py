from __future__ import annotations
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from kiln.graph.schema import parse_frontmatter
from kiln.graph.indexer import compile_graph_index

def run_graph_gc(root_dir: Path) -> Dict[str, Any]:
    """Compacts the knowledge graph: archives superseded nodes and vacuums SQLite index."""
    root_dir = Path(root_dir)
    nodes_dir = root_dir / ".kiln" / "graph" / "nodes"
    archive_dir = root_dir / ".kiln" / "graph" / "archive"
    index_db = root_dir / ".kiln" / "graph" / "index.db"

    if not nodes_dir.exists():
        return {"archived_nodes": 0, "vacuumed": False}

    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_count = 0
    now = datetime.now(timezone.utc)

    for md_file in list(nodes_dir.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            data, body = parse_frontmatter(content)
            status = data.get("status", "")
            valid_to = data.get("valid_to")

            should_archive = (status == "superseded")
            if valid_to:
                try:
                    vt_dt = datetime.fromisoformat(str(valid_to).replace("Z", "+00:00"))
                    if vt_dt < now:
                        should_archive = True
                except Exception:
                    pass

            if should_archive:
                dest = archive_dir / md_file.name
                shutil.move(str(md_file), str(dest))
                archived_count += 1
        except Exception:
            continue

    # Recompile active index
    compile_graph_index(nodes_dir, index_db)

    # Vacuum SQLite database to reclaim disk pages
    vacuumed = False
    if index_db.exists():
        try:
            conn = sqlite3.connect(index_db)
            conn.execute("VACUUM")
            conn.close()
            vacuumed = True
        except Exception:
            pass

    return {
        "archived_nodes": archived_count,
        "vacuumed": vacuumed
    }
