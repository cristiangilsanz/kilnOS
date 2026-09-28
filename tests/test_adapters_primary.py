import pytest
from pathlib import Path
from kiln.adapters.primary import generate_claude_adapter, generate_antigravity_adapter

@pytest.fixture
def mock_kiln_dir(tmp_path):
    skills_dir = tmp_path / ".kiln" / "skills"
    pack_skill = skills_dir / "kiln-pack"
    pack_skill.mkdir(parents=True)
    (pack_skill / "SKILL.md").write_text("""---
name: kiln-pack
description: Retrieve relevant task context from Kiln Graph memory within token budget.
---
# Kiln Pack Skill
Run `kiln pack <work-id> --budget <tokens>`.
""", encoding="utf-8")

    remember_skill = skills_dir / "kiln-remember"
    remember_skill.mkdir(parents=True)
    (remember_skill / "SKILL.md").write_text("""---
name: kiln-remember
description: Store durable knowledge node into Kiln Graph memory.
---
# Kiln Remember Skill
Run `kiln remember --id <id> --type <type> --title <title>`.
""", encoding="utf-8")

    return tmp_path

def test_generate_claude_code_adapter(mock_kiln_dir):
    out_dir = mock_kiln_dir / ".claude"
    claude_md_path = mock_kiln_dir / "CLAUDE.md"

    generate_claude_adapter(mock_kiln_dir, claude_md_path, out_dir)

    assert claude_md_path.exists()
    claude_content = claude_md_path.read_text(encoding="utf-8")
    assert "Kiln OS" in claude_content
    # Must be token budget compliant
    assert len(claude_content.splitlines()) <= 80

    skills_out = out_dir / "skills"
    assert (skills_out / "kiln-pack" / "SKILL.md").exists()
    assert (skills_out / "kiln-remember" / "SKILL.md").exists()

def test_generate_antigravity_adapter(mock_kiln_dir):
    out_skills_dir = mock_kiln_dir / ".agent" / "skills"
    agents_md_path = mock_kiln_dir / "AGENTS.md"

    generate_antigravity_adapter(mock_kiln_dir, agents_md_path, out_skills_dir)

    assert agents_md_path.exists()
    agents_content = agents_md_path.read_text(encoding="utf-8")
    assert "Kiln OS" in agents_content
    assert len(agents_content.splitlines()) <= 80

    assert (out_skills_dir / "kiln-pack" / "SKILL.md").exists()
    assert (out_skills_dir / "kiln-remember" / "SKILL.md").exists()
