import pytest
from kiln.pipeline.interviewer import generate_clarifying_questions, apply_interview_answers

def test_generate_interview_questions():
    questions = generate_clarifying_questions("Add authentication service")
    assert len(questions) <= 5
    assert len(questions) >= 2
    for q in questions:
        assert "question" in q
        assert "options" in q
        assert len(q["options"]) >= 2

def test_apply_interview_answers():
    answers = [
        {"question": "What is the primary interface?", "selected": "REST API"},
        {"question": "What is the rigor tier?", "selected": "Critical"}
    ]
    enriched = apply_interview_answers("Add authentication service", answers)
    assert enriched["tier"] == "critical"
    assert "REST API" in enriched["clarifications"]
