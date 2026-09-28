from __future__ import annotations
import re

PASS_PATTERN = re.compile(r"(?i)\b(?:passed|ok|\. PASSED)\b")
FAIL_PATTERN = re.compile(r"(?i)\b(?:failed|error|assertionerror|traceback|exception)\b")
SUMMARY_PATTERN = re.compile(r"(?i)^\s*=?\s*\d+\s+passed\b")

def filter_cli_output(output: str) -> str:
    """Filters noisy repetitive CLI output (e.g. dozens of passing tests) while preserving failures and summaries."""
    lines = output.splitlines()
    filtered_lines = []
    consecutive_passes = []

    def flush_passes():
        if not consecutive_passes:
            return
        if len(consecutive_passes) >= 4:
            filtered_lines.append(f"[... {len(consecutive_passes)} passing tests collapsed ...]")
        else:
            filtered_lines.extend(consecutive_passes)
        consecutive_passes.clear()

    for line in lines:
        is_summary = bool(SUMMARY_PATTERN.search(line))
        is_pass = bool(PASS_PATTERN.search(line)) and not bool(FAIL_PATTERN.search(line)) and not is_summary

        if is_pass:
            consecutive_passes.append(line)
        else:
            flush_passes()
            filtered_lines.append(line)

    flush_passes()
    return "\n".join(filtered_lines)
