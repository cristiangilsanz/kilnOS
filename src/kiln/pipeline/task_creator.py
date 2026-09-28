from __future__ import annotations
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
import yaml

CRITICAL_KEYWORDS = {
    "auth", "security", "payment", "stripe", "crypto",
    "migration", "prod", "production", "rbac", "secret", "billing"
}

SPARK_KEYWORDS = {
    "typo", "doc", "docs", "documentation", "cosmetic",
    "cleanup", "comment", "formatting", "quickfix", "readme"
}

def classify_tier(idea: str) -> str:
    """Classifies task rigor tier into spark (0 gates), standard (1 gate), or critical (2 gates)."""
    text = idea.lower()
    words = set(re.findall(r"\w+", text))

    if any(k in words or k in text for k in CRITICAL_KEYWORDS):
        return "critical"
    if any(k in words or k in text for k in SPARK_KEYWORDS):
        return "spark"
    return "standard"

def slugify(text: str) -> str:
    """Converts a phrase into a clean URL-friendly slug."""
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", text)[:40]

def create_task(
    root_dir: Path,
    idea: str,
    tier_override: Optional[str] = None
) -> Tuple[str, Path]:
    """Initializes a new task artifact chain in work/<id>/."""
    root_dir = Path(root_dir)
    work_base = root_dir / "work"
    work_base.mkdir(parents=True, exist_ok=True)

    tier = tier_override.lower() if tier_override else classify_tier(idea)
    slug = slugify(idea)

    # Determine next numeric task index
    existing_dirs = [d.name for d in work_base.iterdir() if d.is_dir() and re.match(r"^\d{3}", d.name)]
    next_idx = len(existing_dirs)

    work_id = f"{next_idx:03d}-{slug}"
    work_dir = work_base / work_id
    work_dir.mkdir(parents=True, exist_ok=True)

    # Configure checkpoints based on tier
    if tier == "spark":
        checkpoints = []
    elif tier == "critical":
        checkpoints = [
            {"name": "design_plan_approval", "status": "pending", "approved_by": None},
            {"name": "pre_merge_review", "status": "pending", "approved_by": None},
            {"name": "human_diff_review", "status": "pending", "approved_by": None}
        ]
    else:  # standard
        checkpoints = [
            {"name": "design_plan_approval", "status": "pending", "approved_by": None}
        ]

    created_iso = datetime.now(timezone.utc).isoformat()

    intent_content = f"""# Task {work_id}: Intent

## Objective
{idea}

## Metadata
- **Tier:** {tier}
- **Stage:** discover
- **Created:** {created_iso}

## Checkpoints Required
{'- None (Spark fast-track)' if not checkpoints else chr(10).join([f"- {cp['name']} ({cp['status']})" for cp in checkpoints])}

## Acceptance Criteria
- [ ] Requirements and design specified
- [ ] TDD implementation with unit tests
- [ ] Review artifact with real execution evidence
"""
    (work_dir / "intent.md").write_text(intent_content, encoding="utf-8")

    state_dict = {
        "id": work_id,
        "title": idea,
        "tier": tier,
        "stage": "discover",
        "checkpoints": checkpoints,
        "tokens": {
            "budget": 50000 if tier == "spark" else 150000,
            "spent": 0
        },
        "artifacts": {
            "intent": f"work/{work_id}/intent.md",
            "spec": f"work/{work_id}/spec.md",
            "plan": f"work/{work_id}/plan.md",
            "review": f"work/{work_id}/review.md"
        }
    }
    (work_dir / "state.yml").write_text(yaml.dump(state_dict, sort_keys=False), encoding="utf-8")

    # Git commit if in a git repository
    try:
        subprocess.run(
            ["git", "add", f"work/{work_id}"],
            cwd=str(root_dir),
            capture_output=True,
            check=False
        )
        subprocess.run(
            ["git", "commit", "-m", f"docs({work_id}): initialize task intent and state"],
            cwd=str(root_dir),
            capture_output=True,
            check=False
        )
    except Exception:
        pass

    return work_id, work_dir
