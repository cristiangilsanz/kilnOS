import pytest
import os
from pathlib import Path
from kiln.pipeline.lifecycle import (
    load_template,
    validate_stage_transition,
    install_git_hooks
)
from kiln.hooks.state_runner import load_state, save_state

def test_templates_budget_and_content():
    root = Path(__file__).resolve().parent.parent
    templates_dir = root / ".kiln" / "templates"
    
    expected_templates = ["intent.md", "spec.md", "plan.md", "review.md", "release.md"]
    for t_name in expected_templates:
        t_path = templates_dir / t_name
        assert t_path.exists(), f"Template missing: {t_name}"
        lines = t_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 40, f"Template {t_name} exceeds 40 lines: {len(lines)}"

def test_stage_transitions():
    state = {
        "tier": "standard",
        "stage": "plan",
        "checkpoints": [{"name": "design_plan_approval", "status": "approved"}]
    }
    # With approved checkpoint, can transition to build
    assert validate_stage_transition(state, "build") is True

    # With pending checkpoint, cannot transition to build
    pending_state = {
        "tier": "standard",
        "stage": "plan",
        "checkpoints": [{"name": "design_plan_approval", "status": "pending"}]
    }
    assert validate_stage_transition(pending_state, "build") is False

def test_spark_tier_zero_checkpoints():
    spark_state = {
        "tier": "spark",
        "stage": "plan",
        "checkpoints": []
    }
    # Spark tier has 0 checkpoints, transitions directly
    assert validate_stage_transition(spark_state, "build") is True
    assert validate_stage_transition(spark_state, "review") is True

def test_install_git_hooks(tmp_path):
    git_dir = tmp_path / ".git"
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True)

    installed = install_git_hooks(tmp_path)
    assert installed is True
    assert (hooks_dir / "pre-commit").exists()
    assert (hooks_dir / "pre-push").exists()
