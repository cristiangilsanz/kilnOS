from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
import yaml

from kiln.graph.events import EventLogger
from kiln.graph.indexer import compile_graph_index

def incident_to_intent(
    root_dir: Path,
    incident_id: str,
    title: str,
    cause: str,
    resolution: str
) -> Tuple[Path, Path]:
    """Closes the loop from production incident to tracked remediation intent artifact."""
    root_dir = Path(root_dir)
    nodes_dir = root_dir / ".kiln" / "graph" / "nodes"
    events_file = root_dir / ".kiln" / "graph" / "events.jsonl"
    nodes_dir.mkdir(parents=True, exist_ok=True)

    created_iso = datetime.now(timezone.utc).isoformat()
    fix_work_id = f"{incident_id}-fix"

    # 1. Author Incident Node
    node_frontmatter = {
        "id": incident_id,
        "type": "incident",
        "title": title,
        "status": "accepted",
        "confidence": 1.0,
        "created": created_iso,
        "source": "incident-pipeline",
        "evidence": [],
        "valid_from": created_iso,
        "valid_to": None,
        "supersedes": None,
        "edges": [
            {
                "target": fix_work_id,
                "type": "caused_by",
                "valid_from": created_iso,
                "valid_to": None
            }
        ]
    }

    node_body = f"""# Incident Summary: {title}

## Root Cause
{cause}

## Remediation Plan
{resolution}
"""
    node_file = nodes_dir / f"{incident_id}.md"
    node_file.write_text(f"---\n{yaml.dump(node_frontmatter, sort_keys=False)}---\n{node_body}", encoding="utf-8")

    # 2. Author Follow-up Intent Artifact
    work_dir = root_dir / "work" / fix_work_id
    work_dir.mkdir(parents=True, exist_ok=True)
    intent_file = work_dir / "intent.md"
    intent_file.write_text(f"""# Task {fix_work_id}: Intent

## Remediation for Incident [{incident_id}]: {title}

### Problem Statement
{cause}

### Required Outcome
{resolution}

### Constraints
- Enforce regression test proving the bug is prevented.
- Standard rigor tier: approval before code.
""", encoding="utf-8")

    # Log event & refresh index
    logger = EventLogger(events_file)
    logger.log_event("incident_recorded", incident_id, {"title": title, "fix_work_id": fix_work_id})
    compile_graph_index(nodes_dir, root_dir / ".kiln" / "graph" / "index.db")

    return intent_file, node_file
