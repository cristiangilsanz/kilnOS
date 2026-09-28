from __future__ import annotations
from typing import Any, Dict
from kiln.governor.terse import compress_reasoning_chatter
from kiln.governor.filter import filter_cli_output
from kiln.graph.indexer import estimate_tokens

SAMPLE_BENCHMARK_PROMPTS = [
    "I would be very happy to assist you with this task. Let me take a look at the codebase and start working on it right away! Certainly, here are my findings: We should proceed with caution.",
    "Sure thing! I can help you implement this feature today. Please let me know if you need anything else! Here is the plan: execute steps 1 to 5.",
]

SAMPLE_CLI_LOG = "\n".join([
    "Running test suite...",
    "test_1.py: PASSED",
    "test_2.py: PASSED",
    "test_3.py: PASSED",
    "test_4.py: PASSED",
    "test_5.py: PASSED",
    "test_6.py: PASSED",
    "test_7.py: PASSED",
    "test_8.py: PASSED",
    "7 passed in 0.05s"
])

def run_token_ab_eval() -> Dict[str, Any]:
    """Compares baseline verbose execution tokens vs Kiln-governed execution."""
    raw_text = "\n".join(SAMPLE_BENCHMARK_PROMPTS) + "\n" + SAMPLE_CLI_LOG
    tokens_baseline = estimate_tokens(raw_text)

    # Kiln Token Governor applied:
    compressed_prompts = [compress_reasoning_chatter(p) for p in SAMPLE_BENCHMARK_PROMPTS]
    filtered_cli = filter_cli_output(SAMPLE_CLI_LOG)
    kiln_text = "\n".join(compressed_prompts) + "\n" + filtered_cli
    tokens_kiln = estimate_tokens(kiln_text)

    reduction = ((tokens_baseline - tokens_kiln) / tokens_baseline) * 100.0

    # Lossless verification: ensure key technical directives are intact
    lossless = ("proceed with caution" in kiln_text) and ("execute steps 1 to 5" in kiln_text)

    return {
        "tokens_baseline": tokens_baseline,
        "tokens_kiln": tokens_kiln,
        "reduction_pct": round(reduction, 2),
        "lossless_preservation": lossless
    }
