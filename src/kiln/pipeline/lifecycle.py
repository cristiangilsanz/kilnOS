from __future__ import annotations
import os
import stat
from pathlib import Path
from typing import Any, Dict, Optional

PRE_COMMIT_HOOK_SCRIPT = """#!/usr/bin/env bash
# Kiln OS pre-commit hook
set -e

python scripts/kiln lint-tokens
python -c "
import sys, subprocess
from pathlib import Path
from kiln.hooks.gates import check_secrets_gate
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'], text=True).splitlines()
code_files = [Path(f) for f in staged if f.endswith('.py') and not f.startswith('tests/')]
if not check_secrets_gate(code_files):
    sys.exit(1)
"
"""

PRE_PUSH_HOOK_SCRIPT = """#!/usr/bin/env bash
# Kiln OS pre-push hook
set -e

current_branch=$(git rev-parse --abbrev-ref HEAD)
python -c "
import sys
from kiln.hooks.gates import check_protected_branch_gate
if not check_protected_branch_gate('${current_branch}', is_approved=True):
    sys.exit(1)
"
"""

def load_template(templates_dir: Path, template_name: str) -> str:
    """Loads a lifecycle artifact template from .kiln/templates/."""
    tmpl_path = Path(templates_dir) / template_name
    if not tmpl_path.exists():
        raise FileNotFoundError(f"Template {template_name} not found in {templates_dir}")
    return tmpl_path.read_text(encoding="utf-8")

def validate_stage_transition(state_dict: Dict[str, Any], target_stage: str) -> bool:
    """Enforces tier gating and checkpoint approval before stage transitions."""
    tier = state_dict.get("tier", "standard").lower()
    current_stage = state_dict.get("stage", "discover").lower()
    target_stage = target_stage.lower()

    # Spark tier: 0 checkpoints, fast-track through all stages
    if tier == "spark":
        return True

    checkpoints = state_dict.get("checkpoints", [])

    # Standard tier: 1 checkpoint before build
    if tier == "standard":
        if target_stage in {"build", "test"}:
            for cp in checkpoints:
                if cp.get("name") == "design_plan_approval":
                    return cp.get("status") == "approved"

    # Critical tier: Plan checkpoint before build, review before release
    if tier == "critical":
        if target_stage in {"build", "test"}:
            for cp in checkpoints:
                if cp.get("name") == "design_plan_approval":
                    if cp.get("status") != "approved":
                        return False
        elif target_stage in {"release", "deploy"}:
            for cp in checkpoints:
                if cp.get("status") != "approved":
                    return False

    return True

def install_git_hooks(root_dir: Path) -> bool:
    """Installs deterministic Kiln OS safety hooks into .git/hooks/."""
    root_dir = Path(root_dir)
    git_dir = root_dir / ".git"
    if not git_dir.exists():
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_commit_file = hooks_dir / "pre-commit"
    pre_commit_file.write_text(PRE_COMMIT_HOOK_SCRIPT.strip() + "\n", encoding="utf-8")
    try:
        # Make executable on Unix/Linux/macOS
        pre_commit_file.chmod(pre_commit_file.stat().st_mode | stat.S_IEXEC)
    except Exception:
        pass

    pre_push_file = hooks_dir / "pre-push"
    pre_push_file.write_text(PRE_PUSH_HOOK_SCRIPT.strip() + "\n", encoding="utf-8")
    try:
        pre_push_file.chmod(pre_push_file.stat().st_mode | stat.S_IEXEC)
    except Exception:
        pass

    return True
