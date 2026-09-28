import os
from pathlib import Path

def test_repo_structure():
    root = Path(__file__).resolve().parent.parent
    expected_dirs = [
        root / ".kiln",
        root / ".kiln" / "skills",
        root / ".kiln" / "agents",
        root / ".kiln" / "hooks",
        root / ".kiln" / "templates",
        root / ".kiln" / "graph" / "nodes",
        root / "standards",
        root / "work",
        root / "scripts",
        root / "evals",
        root / "adapters",
    ]
    for d in expected_dirs:
        assert d.exists() and d.is_dir(), f"Expected directory missing: {d}"

def test_agents_md_token_budget():
    root = Path(__file__).resolve().parent.parent
    agents_md = root / "AGENTS.md"
    assert agents_md.exists(), "AGENTS.md must exist at root"
    lines = agents_md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 80, f"AGENTS.md exceeds 80 lines: {len(lines)}"

def test_standards_index():
    root = Path(__file__).resolve().parent.parent
    index_file = root / "standards" / "index.yml"
    assert index_file.exists(), "standards/index.yml must exist"
    tdd_std = root / "standards" / "tdd.md"
    resilience_std = root / "standards" / "resilience.md"
    assert tdd_std.exists(), "standards/tdd.md must exist"
    assert resilience_std.exists(), "standards/resilience.md must exist"
