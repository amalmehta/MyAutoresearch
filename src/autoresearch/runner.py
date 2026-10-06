"""Runs one experiment (the configured command) and reads the metric from its output."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .config import Config


@dataclass
class RunResult:
    metric: float | None
    status: str  # "ok", "crash" or "timeout"
    seconds: float
    log_tail: str


def parse_metric(cfg: Config, output: str) -> float | None:
    """The last value the command printed for the metric, or None."""
    matches = cfg.pattern.findall(output)
    if not matches:
        return None
    last = matches[-1]
    try:
        return float(last[0] if isinstance(last, tuple) else last)
    except ValueError:
        return None


def run_experiment(cfg: Config, log_path: Path) -> RunResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    with open(log_path, "w") as log:
        # Own process group, so a timeout kills the command and everything it spawned.
        proc = subprocess.Popen(
            cfg.command, shell=True, cwd=cfg.root, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            code = proc.wait(timeout=cfg.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            code = None
    seconds = time.monotonic() - start
    output = log_path.read_text(errors="replace")
    tail = "\n".join(output.splitlines()[-40:])

    if code is None:
        return RunResult(None, "timeout", seconds, tail)
    metric = parse_metric(cfg, output)
    if code != 0 or metric is None or metric != metric:  # metric != metric: NaN
        return RunResult(None, "crash", seconds, tail)
    return RunResult(metric, "ok", seconds, tail)
