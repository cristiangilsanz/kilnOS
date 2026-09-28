"""Kiln Task Pipeline and Lifecycle Module."""

from kiln.pipeline.task_creator import create_task, classify_tier
from kiln.pipeline.lifecycle import validate_stage_transition, install_git_hooks
from kiln.pipeline.discover import discover_codebase_conventions
from kiln.pipeline.interviewer import generate_clarifying_questions, apply_interview_answers
from kiln.pipeline.gardener import run_gardener_maintenance
from kiln.pipeline.incident import incident_to_intent
from kiln.pipeline.release import prepare_release

__all__ = [
    "create_task",
    "classify_tier",
    "validate_stage_transition",
    "install_git_hooks",
    "discover_codebase_conventions",
    "generate_clarifying_questions",
    "apply_interview_answers",
    "run_gardener_maintenance",
    "incident_to_intent",
    "prepare_release",
]
