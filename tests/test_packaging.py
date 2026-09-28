import json
import subprocess
from pathlib import Path

def test_package_json_validity():
    root = Path(__file__).resolve().parent.parent
    pkg_json = root / "package.json"
    assert pkg_json.exists(), "package.json must exist"
    data = json.loads(pkg_json.read_text(encoding="utf-8"))
    assert data["name"] == "kiln-os"
    assert "kiln" in data["bin"]
    assert "kiln-os" in data["bin"]

    bin_script = root / "bin" / "kiln.js"
    assert bin_script.exists(), "bin/kiln.js must exist"

def test_npx_runner_execution():
    root = Path(__file__).resolve().parent.parent
    bin_script = root / "bin" / "kiln.js"
    res = subprocess.run(
        ["node", str(bin_script), "doctor"],
        cwd=str(root),
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "Kiln Doctor" in res.stdout
