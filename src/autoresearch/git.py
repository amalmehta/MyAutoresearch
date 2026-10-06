"""Thin wrapper over the git commands the loop needs."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    pass


class Repo:
    def __init__(self, root: Path):
        self.root = root

    def run(self, *args: str, check: bool = True) -> str:
        p = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        if check and p.returncode != 0:
            raise GitError(f"git {' '.join(args)}: {p.stderr.strip() or p.stdout.strip()}")
        return p.stdout

    def is_repo(self) -> bool:
        return self.run("rev-parse", "--is-inside-work-tree", check=False).strip() == "true"

    def head(self) -> str:
        return self.run("rev-parse", "HEAD").strip()

    def short(self, rev: str = "HEAD") -> str:
        return self.run("rev-parse", "--short", rev).strip()

    def branch(self) -> str:
        return self.run("rev-parse", "--abbrev-ref", "HEAD").strip()

    def branch_exists(self, name: str) -> bool:
        return bool(self.run("branch", "--list", name).strip())

    def checkout(self, name: str, create: bool = False) -> None:
        self.run("checkout", *(["-b"] if create else []), name)

    def modified(self) -> set[str]:
        """Tracked files changed against HEAD (staged or not)."""
        out = self.run("diff", "--name-only", "--relative", "HEAD")
        return {line for line in out.splitlines() if line}

    def dirty(self) -> bool:
        """Any uncommitted change to a tracked file, anywhere in the repo."""
        return bool(self.run("status", "--porcelain", "--untracked-files=no").strip())

    def untracked(self) -> set[str]:
        out = self.run("ls-files", "--others", "--exclude-standard")
        return {line for line in out.splitlines() if line}

    def diff(self, paths: list[str]) -> str:
        return self.run("diff", "HEAD", "--", *paths)

    def commit(self, paths: list[str], message: str) -> str:
        self.run("add", "--", *paths)
        self.run("commit", "-q", "-m", message)
        return self.head()

    def reset_hard(self, rev: str) -> None:
        self.run("reset", "-q", "--hard", rev)

    def exclude(self, pattern: str) -> None:
        """Ignore a path locally via .git/info/exclude (never committed)."""
        info = Path(self.run("rev-parse", "--git-path", "info/exclude").strip())
        if not info.is_absolute():
            info = self.root / info
        info.parent.mkdir(parents=True, exist_ok=True)
        lines = info.read_text().splitlines() if info.exists() else []
        if pattern not in lines:
            info.write_text("\n".join([*lines, pattern]) + "\n")
