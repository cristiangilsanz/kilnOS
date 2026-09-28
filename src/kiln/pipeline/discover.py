from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List
import yaml

from kiln.graph.events import EventLogger
from kiln.graph.indexer import compile_graph_index

def discover_codebase_conventions(root_dir: Path) -> Dict[str, Any]:
    """Scans existing repository to discover language, frameworks, test runners, and conventions."""
    root_dir = Path(root_dir)
    conventions: Dict[str, Any] = {
        "primary_language": "unknown",
        "test_runner": "unknown",
        "linters": [],
        "frameworks": [],
        "directories": []
    }

    # 1. Detect Languages & Build Systems
    if (root_dir / "tsconfig.json").exists():
        conventions["primary_language"] = "typescript"
    elif (root_dir / "package.json").exists():
        conventions["primary_language"] = "javascript"
    elif (root_dir / "pyproject.toml").exists() or (root_dir / "setup.py").exists() or (root_dir / "requirements.txt").exists():
        conventions["primary_language"] = "python"
    elif (root_dir / "Cargo.toml").exists():
        conventions["primary_language"] = "rust"
    elif (root_dir / "go.mod").exists():
        conventions["primary_language"] = "go"

    # 2. Detect Package Dependencies & Test Runners
    if (root_dir / "package.json").exists():
        try:
            pkg = json.loads((root_dir / "package.json").read_text(encoding="utf-8"))
            scripts = pkg.get("scripts", {})
            dev_deps = pkg.get("devDependencies", {})
            deps = pkg.get("dependencies", {})

            if "vitest" in dev_deps or "vitest" in str(scripts):
                conventions["test_runner"] = "vitest"
            elif "jest" in dev_deps or "jest" in str(scripts):
                conventions["test_runner"] = "jest"

            if "eslint" in dev_deps:
                conventions["linters"].append("eslint")
            if "prettier" in dev_deps:
                conventions["linters"].append("prettier")
        except Exception:
            pass

    if (root_dir / "pyproject.toml").exists():
        try:
            content = (root_dir / "pyproject.toml").read_text(encoding="utf-8")
            if "pytest" in content:
                conventions["test_runner"] = "pytest"
            if "ruff" in content:
                conventions["linters"].append("ruff")
            if "fastapi" in content:
                conventions["frameworks"].append("fastapi")
            if "flask" in content:
                conventions["frameworks"].append("flask")
            if "django" in content:
                conventions["frameworks"].append("django")
        except Exception:
            pass

    # 3. Detect Directory Structure
    for common_dir in ["src", "lib", "tests", "docs", "scripts", "packages"]:
        if (root_dir / common_dir).exists() and (root_dir / common_dir).is_dir():
            conventions["directories"].append(common_dir)

    # 4. Auto-generate module knowledge nodes if .kiln/ exists
    nodes_dir = root_dir / ".kiln" / "graph" / "nodes"
    if nodes_dir.exists():
        mod_node = nodes_dir / "mod-architecture.md"
        if not mod_node.exists():
            mod_node.write_text(f"""---
id: mod-architecture
type: module
title: Core Architecture Conventions
status: accepted
confidence: 1.0
created: "2026-09-28T18:00:00Z"
source: "discover-conventions"
edges: []
---
# Discovered Conventions
- Primary Language: {conventions['primary_language']}
- Test Runner: {conventions['test_runner']}
- Linters: {', '.join(conventions['linters']) or 'none'}
- Key Directories: {', '.join(conventions['directories'])}
""", encoding="utf-8")
            compile_graph_index(nodes_dir, root_dir / ".kiln" / "graph" / "index.db")

    return conventions
