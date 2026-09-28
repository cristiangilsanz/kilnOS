from __future__ import annotations
from typing import Any, Dict, List

def generate_clarifying_questions(idea: str) -> List[Dict[str, Any]]:
    """Generates <=5 structured multiple-choice questions to shape underspecified task ideas."""
    idea_lower = idea.lower()

    questions = [
        {
            "question": f"What is the primary interface or deliverable for '{idea}'?",
            "options": [
                "CLI tool / Command line interface",
                "Internal backend service / REST API",
                "Library module / Reusable Python package",
                "Web frontend / User interface"
            ]
        },
        {
            "question": "What is the desired error handling & resilience policy?",
            "options": [
                "Fail-closed (Strict safety: block execution on errors)",
                "Fail-open with retry budget and fallback defaults",
                "Raise informative exceptions to caller"
            ]
        },
        {
            "question": "What rigor tier should govern this task?",
            "options": [
                "Standard (Recommended: 1 design approval gate before code)",
                "Spark (Fast-track: 0 checkpoints, fully automated)",
                "Critical (2 checkpoints + human diff review before merge)"
            ]
        }
    ]

    if "auth" in idea_lower or "security" in idea_lower:
        questions.append({
            "question": "Which authentication mechanism is preferred?",
            "options": [
                "JWT Bearer tokens with HMAC-SHA256",
                "Session cookies with Redis cache",
                "API Keys with secret hashing"
            ]
        })
    elif "database" in idea_lower or "data" in idea_lower or "store" in idea_lower:
        questions.append({
            "question": "Which persistence layer is targeted?",
            "options": [
                "SQLite embedded local transactions",
                "PostgreSQL client",
                "In-memory dictionary with disk snapshots"
            ]
        })

    return questions[:5]

def apply_interview_answers(idea: str, answers: List[Dict[str, str]]) -> Dict[str, Any]:
    """Combines original idea and interview selections into an enriched intent specification."""
    tier = "standard"
    clarifications = []

    for ans in answers:
        sel = ans.get("selected", "")
        q = ans.get("question", "")
        clarifications.append(f"- **{q}**: {sel}")
        if "Critical" in sel or "critical" in sel:
            tier = "critical"
        elif "Spark" in sel or "spark" in sel:
            tier = "spark"

    return {
        "idea": idea,
        "tier": tier,
        "clarifications": "\n".join(clarifications)
    }
