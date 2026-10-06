"""My Autoresearch: an agent edits your code, runs your benchmark, and keeps only what improves the metric."""

from .agent import AgentResult, ClaudeCodeAgent
from .config import Config, load
from .loop import research

__all__ = ["AgentResult", "ClaudeCodeAgent", "Config", "load", "research"]
__version__ = "0.1.0"
