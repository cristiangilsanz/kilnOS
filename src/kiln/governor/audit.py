from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

def log_token_usage(
    audit_file: Path,
    task_id: str,
    stage: str,
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int = 0
) -> None:
    """Appends token usage telemetry record to audit log."""
    audit_file = Path(audit_file)
    audit_file.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "stage": stage,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_tokens": cached_tokens,
    }

    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def calculate_session_audit(audit_file: Path, task_id: str) -> Dict[str, Any]:
    """Aggregates session token spend and calculates net billable usage."""
    audit_file = Path(audit_file)
    if not audit_file.exists():
        return {
            "task_id": task_id,
            "total_prompt": 0,
            "total_completion": 0,
            "total_cached": 0,
            "net_billable": 0,
            "records": 0
        }

    total_prompt = 0
    total_completion = 0
    total_cached = 0
    records = 0

    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("task_id") == task_id:
                    total_prompt += rec.get("prompt_tokens", 0)
                    total_completion += rec.get("completion_tokens", 0)
                    total_cached += rec.get("cached_tokens", 0)
                    records += 1
            except Exception:
                continue

    net_billable = max(0, total_prompt - total_cached) + total_completion

    return {
        "task_id": task_id,
        "total_prompt": total_prompt,
        "total_completion": total_completion,
        "total_cached": total_cached,
        "net_billable": net_billable,
        "records": records
    }
