from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
import yaml

from kiln.graph.events import EventLogger
from kiln.graph.indexer import compile_graph_index

def prepare_release(
    root_dir: Path,
    version: str,
    summary: str
) -> Tuple[Path, Path]:
    """Generates release knowledge node and updates root CHANGELOG.md from graph nodes."""
    root_dir = Path(root_dir)
    nodes_dir = root_dir / ".kiln" / "graph" / "nodes"
    events_file = root_dir / ".kiln" / "graph" / "events.jsonl"
    nodes_dir.mkdir(parents=True, exist_ok=True)

    created_iso = datetime.now(timezone.utc).isoformat()
    rel_id = f"rel-{version.lstrip('v')}"

    # 1. Author Release Node in Graph B
    rel_frontmatter = {
        "id": rel_id,
        "type": "release",
        "title": f"Release {version}",
        "status": "accepted",
        "confidence": 1.0,
        "created": created_iso,
        "source": "release-pipeline",
        "evidence": [],
        "valid_from": created_iso,
        "valid_to": None,
        "supersedes": None,
        "edges": []
    }

    rel_body = f"""# Release {version}

## Overview
{summary}

## Rehearsed Rollback Procedure
```bash
git checkout tags/{version}^
python scripts/kiln doctor
```
"""
    rel_node_path = nodes_dir / f"{rel_id}.md"
    rel_node_path.write_text(f"---\n{yaml.dump(rel_frontmatter, sort_keys=False)}---\n{rel_body}", encoding="utf-8")

    # 2. Update CHANGELOG.md
    changelog_path = root_dir / "CHANGELOG.md"
    existing_changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else "# Changelog\n\n"
    
    release_entry = f"""## [{version}] - {created_iso[:10]}
{summary}

"""
    updated_changelog = existing_changelog.replace("# Changelog\n\n", f"# Changelog\n\n{release_entry}", 1)
    changelog_path.write_text(updated_changelog, encoding="utf-8")

    # 3. Log event & recompile index
    logger = EventLogger(events_file)
    logger.log_event("release_published", rel_id, {"version": version, "summary": summary})
    compile_graph_index(nodes_dir, root_dir / ".kiln" / "graph" / "index.db")

    return rel_node_path, changelog_path
