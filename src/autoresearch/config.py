"""Loads and validates autoresearch.toml, the per-project experiment setup."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "autoresearch.toml"


class ConfigError(Exception):
    pass


@dataclass
class AgentConfig:
    model: str = ""  # empty: Claude Code's default model
    max_budget_usd: float = 0.0  # per experiment; 0 means no cap
    timeout: int = 900  # seconds the agent gets to make its change
    extra_args: list[str] = field(default_factory=list)


@dataclass
class Config:
    root: Path
    editable: list[str]
    command: str
    metric: str
    goal: str = "minimize"
    timeout: int = 600
    program: str = "program.md"
    metric_regex: str = ""
    min_improvement: float = 0.0
    history: int = 30  # past experiments shown to the agent
    agent: AgentConfig = field(default_factory=AgentConfig)

    @property
    def pattern(self) -> re.Pattern[str]:
        if self.metric_regex:
            return re.compile(self.metric_regex, re.MULTILINE)
        number = r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
        return re.compile(rf"^\s*{re.escape(self.metric)}\s*[:=]\s*{number}", re.MULTILINE)

    def better(self, new: float, best: float) -> bool:
        if self.goal == "minimize":
            return new < best - self.min_improvement
        return new > best + self.min_improvement

    def program_text(self) -> str:
        path = self.root / self.program
        return path.read_text() if path.exists() else ""


def load(root: Path) -> Config:
    root = root.resolve()
    path = root / CONFIG_NAME
    if not path.exists():
        raise ConfigError(f"No {CONFIG_NAME} in {root}. Run `autoresearch init` first.")
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e

    agent = AgentConfig(**data.pop("agent", {}))
    for key in ("editable", "command", "metric"):
        if key not in data:
            raise ConfigError(f"{CONFIG_NAME} is missing `{key}`.")
    try:
        cfg = Config(root=root, agent=agent, **data)
    except TypeError as e:
        raise ConfigError(f"{CONFIG_NAME}: {e}") from e

    if cfg.goal not in ("minimize", "maximize"):
        raise ConfigError("`goal` must be \"minimize\" or \"maximize\".")
    if not cfg.editable:
        raise ConfigError("`editable` must list at least one file.")
    for rel in cfg.editable:
        if not (root / rel).is_file():
            raise ConfigError(f"Editable file not found: {rel}")
    if cfg.metric_regex and cfg.pattern.groups < 1:
        raise ConfigError("`metric_regex` needs one capture group for the number.")
    return cfg
