"""
LifeLink API Package
FastAPI backend with LangGraph multi-agent orchestration
"""

__version__ = "1.0.0"
__author__ = "LifeLink Team"
__description__ = "LifeLink - Instant Emergency, Instant Response API"

from .main import app, socket_app

__all__ = ["app", "socket_app"]