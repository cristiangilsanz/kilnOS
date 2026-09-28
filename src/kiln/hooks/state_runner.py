from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from kiln.retrieval.packer import pack_context

def load_state(work_dir: Path) -> Dict[str, Any]:
    """Loads work/<id>/state.yml."""
    work_dir = Path(work_dir)
    state_file = work_dir / "state.yml"
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found at {state_file}")
    content = state_file.read_text(encoding="utf-8")
    return yaml.safe_load(content) or {}

def save_state(work_dir: Path, state_dict: Dict[str, Any]) -> None:
    """Saves work/<id>/state.yml."""
    work_dir = Path(work_dir)
    state_file = work_dir / "state.yml"
    state_file.write_text(yaml.dump(state_dict, sort_keys=False), encoding="utf-8")

def resume_task(root_dir: Path, work_id: str, budget_tokens: int = 1500) -> str:
    """Restores task context without re-reading the entire repository."""
    root_dir = Path(root_dir)
    work_dir = root_dir / "work" / work_id
    state = load_state(work_dir)

    lines = [
        f"# Resuming Kiln Task: [{work_id}] {state.get('title', '')}",
        f"- **Tier:** {state.get('tier', 'standard')}",
        f"- **Stage:** {state.get('stage', 'discover')}",
        f"- **Tokens spent:** {state.get('tokens', {}).get('spent', 0)} / {state.get('tokens', {}).get('budget', 0)}",
        "## Checkpoint Statuses:"
    ]

    for cp in state.get("checkpoints", []):
        lines.append(f"  - {cp.get('name')}: {cp.get('status')}")

    db_path = root_dir / ".kiln" / "graph" / "index.db"
    if db_path.exists():
        pack = pack_context(db_path, [work_id], budget_tokens=budget_tokens)
        lines.append("\n" + pack.to_markdown())

    return "\n".join(lines)
