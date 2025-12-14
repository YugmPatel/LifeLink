"""
LifeLink: Instant Emergency, Instant Response

A LangGraph-based multi-agent orchestration system for emergency department coordination.
"""

from lifelink.graph import build_lifelink_graph, run_lifelink_case
from lifelink.state import LifeLinkState

__all__ = [
    "build_lifelink_graph",
    "run_lifelink_case",
    "LifeLinkState",
]

__version__ = "1.0.0"
