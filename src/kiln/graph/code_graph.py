from __future__ import annotations
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

@dataclass
class Symbol:
    name: str
    kind: str  # "class", "function", "method"
    line_number: int
    file_path: str
    docstring: Optional[str] = None

class CodeGraphIndex:
    """Disposable, rebuildable in-memory AST index for Code Graph (Graph A)."""
    def __init__(self):
        self.symbols: Dict[str, Symbol] = {}
        self.by_file: Dict[str, List[Symbol]] = {}

    def add_file_symbols(self, file_path: str, symbols: List[Symbol]) -> None:
        self.by_file[file_path] = symbols
        for sym in symbols:
            self.symbols[sym.name] = sym

    def find_symbol(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def symbols_in_file(self, file_path: str) -> List[Symbol]:
        return self.by_file.get(file_path, [])

def parse_python_ast(file_path: Path) -> List[Symbol]:
    """Extracts symbols from a Python file using the native AST parser."""
    file_path = Path(file_path)
    if not file_path.exists() or not file_path.is_file():
        return []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return []

    symbols: List[Symbol] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            symbols.append(Symbol(
                name=node.name,
                kind="class",
                line_number=node.lineno,
                file_path=str(file_path),
                docstring=doc
            ))
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_doc = ast.get_docstring(item)
                    symbols.append(Symbol(
                        name=item.name,
                        kind="method",
                        line_number=item.lineno,
                        file_path=str(file_path),
                        docstring=m_doc
                    ))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            symbols.append(Symbol(
                name=node.name,
                kind="function",
                line_number=node.lineno,
                file_path=str(file_path),
                docstring=doc
            ))

    return symbols

def bridge_knowledge_to_code(node_id: str, symbol_name: str, file_path: str) -> Dict[str, Any]:
    """Constructs a bidirectional bridge linking Graph B knowledge to Graph A code symbols."""
    return {
        "node_id": node_id,
        "target_symbol": symbol_name,
        "file_path": file_path,
        "type": "bridges_to"
    }

def verify_file_read_invariant(target_file: Path, session_reads: Set[str]) -> bool:
    """Invariant enforcement: Agents must ALWAYS read the actual file before editing."""
    target_abs = str(Path(target_file).resolve())
    if target_abs not in session_reads:
        print(f"[Invariant Breach] Attempted modification of {target_file} without prior read in current session.")
        return False
    return True
