from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

VALID_TYPES = {
    "intent", "requirement", "spec", "decision",
    "standard", "module", "test", "lesson", "incident", "release"
}

VALID_STATUSES = {"proposed", "accepted", "superseded", "stale"}

VALID_EDGE_TYPES = {
    "derives_from", "satisfies", "constrains", "verified_by",
    "touches", "supersedes", "caused_by", "learned_from"
}

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"),                  # Anthropic / OpenAI keys
    re.compile(r"AKIA[0-9A-Z]{16}"),                       # AWS Access Key ID
    re.compile(r"gh[pousr]-[a-zA-Z0-9]{36}"),              # GitHub Tokens
    re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),      # Bearer tokens
    re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----"),
]

def redact_secrets(text: str) -> str:
    """Redacts known secret patterns from text."""
    redacted = text
    for pat in SECRET_PATTERNS:
        redacted = pat.sub("[REDACTED_SECRET]", redacted)
    return redacted

@dataclass
class KnowledgeEdge:
    target: str
    type: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None

@dataclass
class EvidenceItem:
    file: str
    sha256: str

@dataclass
class KnowledgeNode:
    id: str
    type: str
    title: str
    status: str
    confidence: float
    created: str
    source: str
    body: str
    evidence: List[EvidenceItem] = field(default_factory=list)
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    supersedes: Optional[str] = None
    edges: List[KnowledgeEdge] = field(default_factory=list)

def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Extracts YAML frontmatter and body from markdown content."""
    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
    match = pattern.match(content.strip())
    if not match:
        raise ValueError("Invalid markdown file: missing YAML frontmatter delimiters (---)")
    fm_raw, body = match.groups()
    data = yaml.safe_load(fm_raw) or {}
    return data, body.strip()

def validate_node_dict(data: Dict[str, Any], body: str = "") -> KnowledgeNode:
    """Validates raw dictionary data against Knowledge Node specifications."""
    node_id = data.get("id")
    if not node_id or not isinstance(node_id, str):
        raise ValueError("Node must have a non-empty string 'id'")

    node_type = data.get("type")
    if node_type not in VALID_TYPES:
        raise ValueError(f"Invalid type '{node_type}'. Must be one of {sorted(VALID_TYPES)}")

    status = data.get("status", "proposed")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}")

    title = data.get("title", "")
    if not title:
        raise ValueError("Node must have a non-empty 'title'")

    confidence = float(data.get("confidence", 1.0))
    if not (0.0 <= confidence <= 1.0):
        raise ValueError("Confidence must be between 0.0 and 1.0")

    created = str(data.get("created", ""))
    source = str(data.get("source", "agent"))

    evidence_list = []
    for ev in data.get("evidence", []) or []:
        evidence_list.append(EvidenceItem(
            file=ev.get("file", ""),
            sha256=ev.get("sha256", "")
        ))

    edges_list = []
    for edge in data.get("edges", []) or []:
        edge_type = edge.get("type", "touches")
        if edge_type not in VALID_EDGE_TYPES:
            raise ValueError(f"Invalid edge type '{edge_type}'. Must be one of {sorted(VALID_EDGE_TYPES)}")
        edges_list.append(KnowledgeEdge(
            target=str(edge.get("target", "")),
            type=edge_type,
            valid_from=edge.get("valid_from"),
            valid_to=edge.get("valid_to")
        ))

    return KnowledgeNode(
        id=node_id,
        type=node_type,
        title=title,
        status=status,
        confidence=confidence,
        created=created,
        source=source,
        body=redact_secrets(body),
        evidence=evidence_list,
        valid_from=data.get("valid_from"),
        valid_to=data.get("valid_to"),
        supersedes=data.get("supersedes"),
        edges=edges_list,
    )

def validate_node_file(file_path: Path) -> KnowledgeNode:
    """Reads and validates a knowledge node file."""
    content = file_path.read_text(encoding="utf-8")
    data, body = parse_frontmatter(content)
    return validate_node_dict(data, body)
