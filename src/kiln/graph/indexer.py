import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from kiln.graph.schema import validate_node_file

def estimate_tokens(text: str) -> int:
    """Estimates token count for a text snippet."""
    if not text:
        return 0
    # Standard rule of thumb: ~4 characters per token
    return max(1, len(text) // 4)

def init_db(conn: sqlite3.Connection) -> None:
    """Initializes tables in the SQLite index."""
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        confidence REAL NOT NULL,
        created TEXT NOT NULL,
        valid_from TEXT,
        valid_to TEXT,
        supersedes TEXT,
        body_summary TEXT,
        file_path TEXT NOT NULL,
        token_count INTEGER NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS edges (
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        type TEXT NOT NULL,
        valid_from TEXT,
        valid_to TEXT,
        PRIMARY KEY (source_id, target_id, type)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        node_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        PRIMARY KEY (node_id, file_path)
    );
    """)
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS fts_nodes USING fts5(
        id UNINDEXED,
        title,
        body_summary
    );
    """)
    conn.commit()

def compile_graph_index(nodes_dir: Path, db_path: Path) -> int:
    """Compiles markdown nodes in nodes_dir into SQLite db_path."""
    nodes_dir = Path(nodes_dir)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    init_db(conn)
    cur = conn.cursor()

    count = 0
    if nodes_dir.exists():
        for md_file in sorted(nodes_dir.glob("*.md")):
            try:
                node = validate_node_file(md_file)
            except Exception:
                continue

            # First non-header non-empty line of body as summary
            lines = [l.strip() for l in node.body.splitlines() if l.strip() and not l.strip().startswith("#")]
            summary = lines[0] if lines else node.title
            if len(summary) > 120:
                summary = summary[:117] + "..."

            token_count = estimate_tokens(node.body) + estimate_tokens(node.title)

            cur.execute("""
            INSERT INTO nodes (
                id, type, title, status, confidence, created,
                valid_from, valid_to, supersedes, body_summary, file_path, token_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node.id, node.type, node.title, node.status, node.confidence,
                node.created, node.valid_from, node.valid_to, node.supersedes,
                summary, str(md_file), token_count
            ))

            for edge in node.edges:
                cur.execute("""
                INSERT OR REPLACE INTO edges (source_id, target_id, type, valid_from, valid_to)
                VALUES (?, ?, ?, ?, ?)
                """, (node.id, edge.target, edge.type, edge.valid_from, edge.valid_to))

            for ev in node.evidence:
                cur.execute("""
                INSERT OR REPLACE INTO evidence (node_id, file_path, sha256)
                VALUES (?, ?, ?)
                """, (node.id, ev.file, ev.sha256))

            cur.execute("""
            INSERT INTO fts_nodes (id, title, body_summary)
            VALUES (?, ?, ?)
            """, (node.id, node.title, summary))

            count += 1

    conn.commit()
    conn.close()
    return count

def query_node_by_id(db_path: Path, node_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves node summary from SQLite index."""
    if not Path(db_path).exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
