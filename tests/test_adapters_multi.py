import pytest
from pathlib import Path
from kiln.adapters.multi import (
    generate_codex_adapter,
    generate_opencode_adapter,
    build_all_adapters,
    check_adapter_drift
)

@pytest.fixture
def populated_kiln_workspace(tmp_path):
    # Setup .kiln directory
    skills_dir = tmp_path / ".kiln" / "skills" / "kiln-pack"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("""---
name: kiln-pack
description: Retrieve relevant task context.
---
# Pack
""", encoding="utf-8")

    (tmp_path / "AGENTS.md").write_text("# Base AGENTS.md\n", encoding="utf-8")
    return tmp_path

def test_codex_adapter(populated_kiln_workspace):
    codex_out = populated_kiln_workspace / ".codex"
    generate_codex_adapter(populated_kiln_workspace, codex_out)

    assert (codex_out / "instructions.md").exists()
    instructions = (codex_out / "instructions.md").read_text(encoding="utf-8")
    assert "Kiln OS" in instructions
    assert len(instructions.splitlines()) <= 80

def test_opencode_adapter(populated_kiln_workspace):
    cursorrules_file = populated_kiln_workspace / ".cursorrules"
    generate_opencode_adapter(populated_kiln_workspace, cursorrules_file)

    assert cursorrules_file.exists()
    rules = cursorrules_file.read_text(encoding="utf-8")
    assert "Kiln OS" in rules
    assert len(rules.splitlines()) <= 80

def test_build_all_adapters_and_drift_check(populated_kiln_workspace):
    # Initial build
    result = build_all_adapters(populated_kiln_workspace)
    assert result is True

    # Expected files generated
    assert (populated_kiln_workspace / "CLAUDE.md").exists()
    assert (populated_kiln_workspace / ".cursorrules").exists()
    assert (populated_kiln_workspace / ".claude" / "skills" / "kiln-pack" / "SKILL.md").exists()

    # Drift check should pass cleanly
    drift = check_adapter_drift(populated_kiln_workspace)
    assert len(drift) == 0

    # Tamper with an adapter file
    (populated_kiln_workspace / "CLAUDE.md").write_text("# Tampered content\n", encoding="utf-8")
    drift = check_adapter_drift(populated_kiln_workspace)
    assert "CLAUDE.md" in drift
