import pytest
from pathlib import Path
from kiln.hooks.gates import (
    check_secrets_gate,
    check_protected_branch_gate,
    check_tests_touched_gate,
    check_prod_gate,
    run_helper_hook
)
from kiln.hooks.state_runner import resume_task, load_state, save_state

def test_secret_gate_fail_closed(tmp_path):
    safe_file = tmp_path / "safe.py"
    safe_file.write_text("API_ENDPOINT = 'https://api.example.com'\n", encoding="utf-8")
    assert check_secrets_gate([safe_file]) is True

    leaky_file = tmp_path / "leaky.py"
    leaky_file.write_text("KEY = 'sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz'\n", encoding="utf-8")
    assert check_secrets_gate([leaky_file]) is False

def test_protected_branch_gate():
    # Attempting to commit/push to 'main' without approval should be blocked
    assert check_protected_branch_gate("main", is_approved=False) is False
    assert check_protected_branch_gate("main", is_approved=True) is True
    assert check_protected_branch_gate("feat/feature-branch", is_approved=False) is True

def test_tests_touched_gate():
    # Production code changed without tests changed
    touched_only_src = ["src/module.py", "src/core.py"]
    assert check_tests_touched_gate(touched_only_src) is False

    # Production code + tests changed
    touched_with_tests = ["src/module.py", "tests/test_module.py"]
    assert check_tests_touched_gate(touched_with_tests) is True

    # Docs only changed
    touched_docs = ["docs/readme.md"]
    assert check_tests_touched_gate(touched_docs) is True

def test_prod_gate():
    state = {
        "tier": "critical",
        "stage": "release",
        "checkpoints": [{"name": "human_prod_approval", "status": "approved"}]
    }
    assert check_prod_gate(state) is True

    unapproved_state = {
        "tier": "critical",
        "stage": "release",
        "checkpoints": [{"name": "human_prod_approval", "status": "pending"}]
    }
    assert check_prod_gate(unapproved_state) is False

def test_helper_hook_fail_open():
    def failing_helper():
        raise RuntimeError("Network timeout during cache warmup")

    # Helper hook should catch exception and return True (fail open)
    success = run_helper_hook("cache_warmup", failing_helper)
    assert success is True

def test_state_runner_and_resume(tmp_path):
    work_dir = tmp_path / "work" / "task-42"
    work_dir.mkdir(parents=True)
    state_file = work_dir / "state.yml"
    state_file.write_text("""id: task-42
title: "Build Feature"
tier: standard
stage: build
checkpoints:
  - name: design_plan_approval
    status: approved
tokens:
  budget: 50000
  spent: 1200
""", encoding="utf-8")

    loaded = load_state(work_dir)
    assert loaded["id"] == "task-42"
    assert loaded["stage"] == "build"

    resumed_summary = resume_task(tmp_path, "task-42")
    assert "task-42" in resumed_summary
    assert "Stage:** build" in resumed_summary
