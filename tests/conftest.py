import subprocess
import sys
from pathlib import Path

import pytest

from autoresearch.agent import AgentResult

# score.py reads params.txt and prints `score: (x - 3)^2`; special values crash or hang.
SCORE = """
import sys, time
v = open("params.txt").read().strip()
if v == "crash":
    sys.exit("boom")
if v == "hang":
    time.sleep(30)
print("noise: 123")
print(f"score: {(float(v) - 3) ** 2}")
"""


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


@pytest.fixture(autouse=True)
def git_identity(monkeypatch):
    for k, v in {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com"}.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    root.mkdir()
    (root / "params.txt").write_text("0\n")
    (root / "score.py").write_text(SCORE)
    (root / "program.md").write_text("Find the best x.\n")
    (root / "autoresearch.toml").write_text(
        'editable = ["params.txt"]\n'
        f'command = "\\"{sys.executable}\\" score.py"\n'
        'metric = "score"\n'
        'goal = "minimize"\n'
        "timeout = 5\n"
    )
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    return root


class FakeAgent:
    """Plays a script of actions; each is a function of the project root returning an AgentResult."""

    def __init__(self, actions):
        self.actions = list(actions)
        self.prompts: list[str] = []

    def propose(self, prompt, cwd):
        self.prompts.append(prompt)
        return self.actions.pop(0)(cwd)


def set_x(value, cost=0.01):
    def act(root: Path):
        (root / "params.txt").write_text(f"{value}\n")
        return AgentResult(f"set x to {value}", cost)
    return act


def write(rel, text="x"):
    def act(root: Path):
        (root / rel).write_text(text)
        return AgentResult(f"wrote {rel}")
    return act


def nothing(root: Path):
    return AgentResult("thought about it")


def fail(root: Path):
    return AgentResult("", error="rate limited")
