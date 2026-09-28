import pytest
from pathlib import Path
from kiln.cli import main
from kiln.pipeline.task_creator import classify_tier, create_task

def test_tier_classification():
    assert classify_tier("fix typo in readme") == "spark"
    assert classify_tier("update documentation for quickstart") == "spark"
    assert classify_tier("implement user profile api endpoint") == "standard"
    assert classify_tier("refactor caching layer") == "standard"
    assert classify_tier("add payment stripe integration") == "critical"
    assert classify_tier("database migration and auth overhaul") == "critical"

def test_create_task(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".kiln").mkdir()

    work_id, work_dir = create_task(
        root_dir=tmp_path,
        idea="Implement redis session caching",
        tier_override="standard"
    )

    assert work_id.startswith("000-") or work_id.startswith("001-")
    assert work_dir.exists()
    assert (work_dir / "intent.md").exists()
    assert (work_dir / "state.yml").exists()

    intent_content = (work_dir / "intent.md").read_text(encoding="utf-8")
    assert "redis session caching" in intent_content
    assert "Tier:** standard" in intent_content

    state_content = (work_dir / "state.yml").read_text(encoding="utf-8")
    assert "standard" in state_content
    assert "design_plan_approval" in state_content
