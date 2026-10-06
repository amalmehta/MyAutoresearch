"""The agent that proposes and makes one change per experiment.

ClaudeCodeAgent runs headless Claude Code (`claude -p`). Anything with the same
`propose(prompt, cwd)` method works, which is how the tests drive the loop.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import AgentConfig, Config
from .results import Row

TOOLS = "Read,Edit,Write,Glob,Grep"  # file tools only: the harness runs experiments, not the agent


@dataclass
class AgentResult:
    description: str
    cost_usd: float = 0.0
    error: str = ""


class Agent(Protocol):
    def propose(self, prompt: str, cwd: Path) -> AgentResult: ...


class ClaudeCodeAgent:
    def __init__(self, cfg: AgentConfig, executable: str = "claude"):
        self.cfg = cfg
        self.executable = executable

    def command(self, prompt: str) -> list[str]:
        cmd = [self.executable, "-p", prompt, "--output-format", "json",
               "--tools", TOOLS, "--permission-mode", "acceptEdits", "--no-session-persistence"]
        if self.cfg.model:
            cmd += ["--model", self.cfg.model]
        if self.cfg.max_budget_usd > 0:
            cmd += ["--max-budget-usd", str(self.cfg.max_budget_usd)]
        return cmd + list(self.cfg.extra_args)

    def propose(self, prompt: str, cwd: Path) -> AgentResult:
        try:
            p = subprocess.run(self.command(prompt), cwd=cwd, capture_output=True, text=True,
                               timeout=self.cfg.timeout)
        except FileNotFoundError:
            return AgentResult("", error=f"`{self.executable}` not found. Install Claude Code.")
        except OSError as e:
            return AgentResult("", error=f"could not start `{self.executable}`: {e}")
        except subprocess.TimeoutExpired:
            return AgentResult("", error=f"agent took longer than {self.cfg.timeout}s")
        try:
            out = json.loads(p.stdout)
        except json.JSONDecodeError:
            return AgentResult("", error=(p.stderr or p.stdout).strip()[-500:] or f"exit {p.returncode}")
        text = out.get("result") or ""
        cost = float(out.get("total_cost_usd") or 0.0)
        if out.get("is_error") or p.returncode != 0:
            return AgentResult("", cost, error=text.strip()[-500:] or f"exit {p.returncode}")
        return AgentResult(extract_description(text), cost)


def extract_description(text: str) -> str:
    m = re.findall(r"^\s*DESCRIPTION:\s*(.+)$", text, re.MULTILINE)
    if m:
        return m[-1].strip()
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    return lines[-1][:200] if lines else "(no description)"


def build_prompt(cfg: Config, rows: list[Row], best: Row, last_failure: str = "") -> str:
    direction = "lower" if cfg.goal == "minimize" else "higher"
    files = "\n".join(f"- {f}" for f in cfg.editable)
    recent = rows[-cfg.history:]
    history = "\n".join(
        f"| {r.n} | {r.metric or '-'} | {r.status} | {r.description} |" for r in recent
    )
    program = cfg.program_text().strip() or "(no research program given: use your judgement)"
    parts = [
        "You are running one experiment in an automated research loop.",
        f"Goal: make `{cfg.metric}` {direction}. The current best is {best.metric} (experiment {best.n}).",
        "",
        "## Research program (from the human)",
        program,
        "",
        "## Files you may edit",
        files,
        "Do not create, edit or delete any other file. Changes elsewhere get the experiment rejected.",
        "",
        "## Past experiments (most recent last)",
        "| # | " + cfg.metric + " | status | description |",
        "|---|---|---|---|",
        history,
        "",
        "Statuses: keep = improved and kept; discard = no better, reverted; crash/timeout = failed, reverted;",
        "rejected = touched a file it may not edit; no-change = nothing was edited.",
        "The files are at the current best version. Discarded ideas are gone from the code.",
    ]
    if last_failure:
        parts += ["", "## Output of the last failed run (tail)", "```", last_failure, "```"]
    parts += [
        "",
        "## Your task",
        "Read the editable files, then make ONE focused change you expect to improve the metric.",
        "Prefer ideas not yet tried; learn from what was kept and discarded. Simpler is better at equal metric.",
        f"Do not run anything: the harness runs `{cfg.command}` after you finish, with a "
        f"{cfg.timeout}s limit.",
        "End your reply with a single line: DESCRIPTION: <what you changed, under 15 words>",
    ]
    return "\n".join(parts)
