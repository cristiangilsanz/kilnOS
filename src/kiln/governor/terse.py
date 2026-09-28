from __future__ import annotations
import re

PROTECTED_CONTENT_TYPES = {"spec", "plan", "review", "security", "code", "diff"}

FILLER_PATTERNS = [
    re.compile(r"(?i)\bI would be very happy to assist you with this task\.\s*"),
    re.compile(r"(?i)\bCertainly,?\s*here are my findings:?\s*"),
    re.compile(r"(?i)\bLet me take a look at the codebase and start working on it right away!?\s*"),
    re.compile(r"(?i)\bSure thing!?:?\s*"),
    re.compile(r"(?i)\bAs an AI language model,?\s*"),
    re.compile(r"(?i)\bI hope this helps!?\s*"),
    re.compile(r"(?i)\bPlease let me know if you need anything else!?\s*"),
]

def compress_reasoning_chatter(text: str, content_type: str = "chatter") -> str:
    """Compresses conversational filler while never touching protected content types."""
    if content_type.lower() in PROTECTED_CONTENT_TYPES:
        return text

    compressed = text
    for pat in FILLER_PATTERNS:
        compressed = pat.sub("", compressed)

    # Clean up double spaces or orphan newlines
    compressed = re.sub(r" {2,}", " ", compressed).strip()
    return compressed
