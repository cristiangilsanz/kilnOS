import pytest
from pathlib import Path
from kiln.graph.mcp_bridge import CodeGraphBridge

def test_mcp_bridge_local_fallback(tmp_path):
    py_file = tmp_path / "payment.py"
    py_file.write_text("""class PaymentGateway:
    def charge(self, amount: int) -> bool:
        return amount > 0
""", encoding="utf-8")

    # Bridge initialized with no remote MCP server URL -> falls back to local AST
    bridge = CodeGraphBridge(root_dir=tmp_path, mcp_server_cmd=None)
    assert bridge.is_remote_active is False

    sym = bridge.find_symbol("PaymentGateway")
    assert sym is not None
    assert sym.name == "PaymentGateway"
    assert sym.kind == "class"

    charge_method = bridge.find_symbol("charge")
    assert charge_method is not None
    assert charge_method.kind == "method"

def test_mcp_bridge_read_file_guard(tmp_path):
    py_file = tmp_path / "test_read.py"
    py_file.write_text("DATA = 123\n", encoding="utf-8")

    bridge = CodeGraphBridge(root_dir=tmp_path)
    
    # Must reject edit if not yet read
    assert bridge.can_edit_file(py_file) is False

    # Simulate reading file
    bridge.record_file_read(py_file)
    assert bridge.can_edit_file(py_file) is True
