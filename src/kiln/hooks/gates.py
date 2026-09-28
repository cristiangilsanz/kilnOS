from __future__ import annotations
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

from kiln.graph.schema import SECRET_PATTERNS

PROTECTED_BRANCHES = {"main", "master", "prod", "production"}

def check_secrets_gate(files: List[Path]) -> bool:
    """Fail-closed gate: Scans files for exposed API keys and credentials."""
    leak_found = False
    for f in files:
        f = Path(f)
        if not f.exists() or not f.is_file():
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for pat in SECRET_PATTERNS:
                if pat.search(content):
                    print(f"[Gate Blocked] Secret pattern detected in file: {f}")
                    leak_found = True
        except Exception as e:
            print(f"[Gate Blocked] Failed to read {f}: {e}")
            leak_found = True

    return not leak_found

def check_protected_branch_gate(branch_name: str, is_approved: bool = False) -> bool:
    """Fail-closed gate: Blocks unapproved direct mutations to protected branches."""
    if branch_name.strip() in PROTECTED_BRANCHES:
        if not is_approved:
            print(f"[Gate Blocked] Direct modifications to protected branch '{branch_name}' require prior review approval.")
            return False
    return True

def check_tests_touched_gate(touched_files: List[str]) -> bool:
    """Fail-closed gate: Ensures production code edits include test additions/updates."""
    has_src = any(f.startswith("src/") or "\\src\\" in f or "/src/" in f for f in touched_files)
    has_tests = any(f.startswith("tests/") or "\\tests\\" in f or "/tests/" in f for f in touched_files)

    if has_src and not has_tests:
        print("[Gate Blocked] TDD violation: Source code in src/ was modified without corresponding changes in tests/.")
        return False
    return True

def check_prod_gate(state_dict: Dict[str, Any]) -> bool:
    """Fail-closed gate: Enforces human signoff before deploying to production."""
    stage = state_dict.get("stage", "")
    tier = state_dict.get("tier", "standard")

    if stage == "release" or tier == "critical":
        checkpoints = state_dict.get("checkpoints", [])
        for cp in checkpoints:
            if cp.get("name") in {"human_prod_approval", "design_plan_approval", "pre_merge_review"}:
                if cp.get("status") != "approved":
                    print(f"[Gate Blocked] Checkpoint '{cp.get('name')}' is {cp.get('status')}. Human approval required.")
                    return False
    return True

def run_helper_hook(name: str, fn: Callable[[], Any]) -> bool:
    """Fail-open hook wrapper: Helper hooks log warnings on failure but do not break builds."""
    try:
        fn()
        return True
    except Exception as e:
        print(f"[Helper Hook Warning] Hook '{name}' encountered an error (failing open): {e}")
        return True
