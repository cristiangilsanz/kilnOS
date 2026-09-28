"""Kiln OS: Resilient, token-minimizing operating system for AI coding agents."""

__version__ = "0.1.0"

from kiln.pipeline.task_creator import create_task, classify_tier
from kiln.pipeline.lifecycle import validate_stage_transition, install_git_hooks
from kiln.retrieval.packer import ContextPack, pack_context, expand_node
from kiln.graph.schema import KnowledgeNode, validate_node_file, redact_secrets
from kiln.graph.indexer import compile_graph_index, query_node_by_id
from kiln.governor.filter import filter_cli_output
from kiln.governor.terse import compress_reasoning_chatter
from kiln.adapters.multi import build_all_adapters

__all__ = [
    "__version__",
    "create_task",
    "classify_tier",
    "validate_stage_transition",
    "install_git_hooks",
    "ContextPack",
    "pack_context",
    "expand_node",
    "KnowledgeNode",
    "validate_node_file",
    "redact_secrets",
    "compile_graph_index",
    "query_node_by_id",
    "filter_cli_output",
    "compress_reasoning_chatter",
    "build_all_adapters",
]
