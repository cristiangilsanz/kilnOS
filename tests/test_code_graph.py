import pytest
from pathlib import Path
from kiln.graph.code_graph import (
    CodeGraphIndex,
    parse_python_ast,
    bridge_knowledge_to_code,
    verify_file_read_invariant
)

def test_local_ast_symbol_extraction(tmp_path):
    py_file = tmp_path / "service.py"
    py_file.write_text("""import os
from typing import Optional

class UserService:
    def __init__(self, db_client):
        self.db = db_client

    def get_user(self, user_id: str) -> Optional[dict]:
        return self.db.find(user_id)

def authenticate(token: str) -> bool:
    return len(token) > 10
""", encoding="utf-8")

    index = CodeGraphIndex()
    symbols = parse_python_ast(py_file)
    index.add_file_symbols(str(py_file), symbols)

    found_classes = [s for s in symbols if s.kind == "class"]
    found_functions = [s for s in symbols if s.kind in ("function", "method")]

    assert len(found_classes) == 1
    assert found_classes[0].name == "UserService"

    func_names = [f.name for f in found_functions]
    assert "__init__" in func_names
    assert "get_user" in func_names
    assert "authenticate" in func_names

    queried = index.find_symbol("authenticate")
    assert queried is not None
    assert queried.file_path == str(py_file)

def test_bridge_knowledge_to_code():
    bridge = bridge_knowledge_to_code(
        node_id="req-auth",
        symbol_name="authenticate",
        file_path="src/service.py"
    )
    assert bridge["node_id"] == "req-auth"
    assert bridge["target_symbol"] == "authenticate"
    assert bridge["type"] == "bridges_to"

def test_read_file_before_edit_invariant(tmp_path):
    target_file = tmp_path / "target.py"
    target_file.write_text("INITIAL_CODE = True\n", encoding="utf-8")

    session_reads = set()

    # Attempting to edit without reading should fail invariant check
    assert verify_file_read_invariant(target_file, session_reads) is False

    # After reading the file:
    session_reads.add(str(target_file.resolve()))
    assert verify_file_read_invariant(target_file, session_reads) is True
