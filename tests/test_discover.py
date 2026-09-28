import pytest
from pathlib import Path
from kiln.pipeline.discover import discover_codebase_conventions

def test_discover_python_pytest(tmp_path):
    # Simulate a Python repo with pytest and pyproject.toml
    (tmp_path / "pyproject.toml").write_text("""[project]
name = "demo-app"
dependencies = ["fastapi"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".kiln").mkdir()

    conventions = discover_codebase_conventions(tmp_path)
    assert conventions["primary_language"] == "python"
    assert conventions["test_runner"] == "pytest"
    assert "src" in conventions["directories"]
    assert "tests" in conventions["directories"]

def test_discover_typescript_repo(tmp_path):
    (tmp_path / "package.json").write_text("""{
  "name": "ts-app",
  "scripts": {
    "test": "vitest run"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "eslint": "^8.0.0"
  }
}""", encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".kiln").mkdir()

    conventions = discover_codebase_conventions(tmp_path)
    assert conventions["primary_language"] == "typescript"
    assert conventions["test_runner"] == "vitest"
    assert "eslint" in conventions["linters"]
