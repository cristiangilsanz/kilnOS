import pytest
from pathlib import Path
from kiln.governor.filter import filter_cli_output
from kiln.governor.terse import compress_reasoning_chatter
from kiln.governor.audit import log_token_usage, calculate_session_audit

def test_filter_cli_output_repetitive_passes():
    noisy_output = "\n".join([
        "Running tests...",
        "test_1.py: PASSED",
        "test_2.py: PASSED",
        "test_3.py: PASSED",
        "test_4.py: PASSED",
        "test_5.py: PASSED",
        "test_6.py: PASSED",
        "test_7.py: PASSED",
        "test_8.py: PASSED",
        "test_9.py: PASSED",
        "test_10.py: PASSED",
        "10 passed in 0.2s"
    ])
    filtered = filter_cli_output(noisy_output)
    # Filter should collapse consecutive passing lines
    assert "[... 10 passing tests collapsed ...]" in filtered or "passed" in filtered
    assert len(filtered) < len(noisy_output)

def test_filter_cli_output_retains_failures():
    failure_output = """
test_bad.py: FAILED
================== FAILURES ==================
AssertionError: expected 5 but got 3
at test_bad.py:12
"""
    filtered = filter_cli_output(failure_output)
    assert "AssertionError" in filtered
    assert "test_bad.py:12" in filtered

def test_terse_chatter_compression():
    wordy_thought = "I would be very happy to assist you with this task. Let me take a look at the codebase and start working on it right away! Certainly, here are my findings."
    compressed = compress_reasoning_chatter(wordy_thought)
    assert len(compressed) < len(wordy_thought)
    assert "happy to assist" not in compressed

def test_terse_chatter_never_compresses_protected_types():
    spec_content = "# Specification\nMust implement authentication and AES-256 encryption."
    assert compress_reasoning_chatter(spec_content, content_type="spec") == spec_content

    plan_content = "1. Write test in tests/test_auth.py\n2. Run pytest"
    assert compress_reasoning_chatter(plan_content, content_type="plan") == plan_content

    sec_content = "SECURITY WARNING: SQL injection vulnerability detected!"
    assert compress_reasoning_chatter(sec_content, content_type="security") == sec_content

def test_audit_telemetry(tmp_path):
    audit_file = tmp_path / "usage_audit.jsonl"
    log_token_usage(audit_file, "000-kiln", stage="build", prompt_tokens=150, completion_tokens=50, cached_tokens=100)
    log_token_usage(audit_file, "000-kiln", stage="test", prompt_tokens=200, completion_tokens=40, cached_tokens=150)

    summary = calculate_session_audit(audit_file, "000-kiln")
    assert summary["total_prompt"] == 350
    assert summary["total_completion"] == 90
    assert summary["total_cached"] == 250
    assert summary["net_billable"] == (350 - 250) + 90
