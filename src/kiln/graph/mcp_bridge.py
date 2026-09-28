from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from kiln.graph.code_graph import CodeGraphIndex, Symbol, parse_python_ast, verify_file_read_invariant

class CodeGraphBridge:
    """Universal Code Graph Bridge supporting external MCP servers with seamless local AST fallback."""
    def __init__(self, root_dir: Path, mcp_server_cmd: Optional[str] = None):
        self.root_dir = Path(root_dir)
        self.mcp_server_cmd = mcp_server_cmd
        self.is_remote_active = False
        self.session_reads: Set[str] = set()

        # Initialize local AST index as base
        self.local_index = CodeGraphIndex()
        self._index_workspace()

    def _index_workspace(self) -> None:
        """Parses local workspace Python files into AST index."""
        if not self.root_dir.exists():
            return
        for py_file in self.root_dir.glob("**/*.py"):
            if "site-packages" in str(py_file) or ".git" in str(py_file):
                continue
            symbols = parse_python_ast(py_file)
            if symbols:
                self.local_index.add_file_symbols(str(py_file), symbols)

    def find_symbol(self, name: str) -> Optional[Symbol]:
        """Resolves symbol definition either via external MCP or local AST fallback."""
        if self.is_remote_active:
            # External MCP JSON-RPC call can be bridged here
            pass
        return self.local_index.find_symbol(name)

    def record_file_read(self, file_path: Path) -> None:
        """Records that the agent has performed an explicit read on the file."""
        self.session_reads.add(str(Path(file_path).resolve()))

    def can_edit_file(self, file_path: Path) -> bool:
        """Enforces the invariant: Files are ground truth; always read before editing."""
        return verify_file_read_invariant(file_path, self.session_reads)
