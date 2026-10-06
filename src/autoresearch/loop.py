"""The research loop: propose a change, run the experiment, keep it only if the metric improves."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable

from . import results
from .agent import Agent, build_prompt
from .config import Config
from .git import GitError, Repo
from .runner import run_experiment


class LoopError(Exception):
    pass


MAX_AGENT_ERRORS = 3  # in a row; stops a loop whose agent can't run at all


def default_tag() -> str:
    return date.today().strftime("%b%d").lower()  # e.g. oct06, like the original


def research(cfg: Config, agent: Agent, tag: str, max_experiments: int = 0,
             log: Callable[[str], None] = print) -> list[results.Row]:
    """Run experiments on branch autoresearch/<tag>. max_experiments=0 runs until interrupted."""
    repo = Repo(cfg.root)
    if not repo.is_repo():
        raise LoopError(f"{cfg.root} is not inside a git repository. Run `git init` and commit first.")
    try:
        repo.head()
    except GitError:
        raise LoopError("The repository has no commits yet. Commit your files first.")
    repo.exclude(".autoresearch/")

    tsv = results.run_dir(cfg.root, tag) / "results.tsv"
    logs = tsv.parent / "logs"
    rows = results.read(tsv)
    branch = f"autoresearch/{tag}"

    if repo.dirty():
        raise LoopError("Uncommitted changes to tracked files. Commit or stash them first.")
    if repo.branch() != branch:
        repo.checkout(branch, create=not repo.branch_exists(branch))
    log(f"Branch {branch}, results in {tsv.relative_to(cfg.root)}")

    best = results.best(rows, cfg.goal)
    if best is None:
        log(f"Running the baseline: {cfg.command}")
        r = run_experiment(cfg, logs / "0.log")
        if r.status != "ok":
            raise LoopError(f"The baseline run failed ({r.status}). See {logs / '0.log'}:\n{r.log_tail}")
        best = results.Row(0, repo.short(), f"{r.metric:g}", "baseline", f"{r.seconds:.1f}", "0", "baseline")
        results.append(tsv, best)
        rows.append(best)
        log(f"  baseline {cfg.metric} = {best.metric}")
    else:
        repo.reset_hard(best.commit)
        log(f"Resuming from experiment {best.n}: {cfg.metric} = {best.metric}")

    n = rows[-1].n + 1
    last_failure = ""
    agent_errors = 0
    done = 0
    editable = set(cfg.editable)
    before = repo.untracked()

    try:
        while not max_experiments or done < max_experiments:
            before = repo.untracked()
            log(f"[{n}] agent is making a change…")
            res = agent.propose(build_prompt(cfg, rows, best, last_failure), cfg.root)
            changed = repo.modified()
            created = repo.untracked() - before
            metric, seconds, commit = "", "", ""
            last_failure = ""

            if res.error:
                status, desc = "agent-error", res.error.splitlines()[0][:200]
                agent_errors += 1
            elif created or changed - editable:
                status, desc = "rejected", f"edited {', '.join(sorted(created | (changed - editable)))}"
            elif not changed:
                status, desc = "no-change", res.description
            else:
                desc = res.description
                repo.commit(sorted(changed), f"autoresearch {n}: {desc}")
                commit = repo.short()
                log(f"[{n}] {desc}\n[{n}] running: {cfg.command}")
                r = run_experiment(cfg, logs / f"{n}.log")
                seconds = f"{r.seconds:.1f}"
                if r.status != "ok":
                    status, last_failure = r.status, r.log_tail
                else:
                    metric = f"{r.metric:g}"
                    status = "keep" if cfg.better(r.metric, best.value) else "discard"

            if status != "agent-error":
                agent_errors = 0
            row = results.Row(n, commit, metric, status, seconds, f"{res.cost_usd:.4f}", desc)
            if status == "keep":
                best = row
            else:
                _revert(repo, best.commit, created)
            results.append(tsv, row)
            rows.append(row)
            log(f"[{n}] {status:<11} {cfg.metric}={metric or '-':<10} best={best.metric}")
            n += 1
            done += 1
            if agent_errors >= MAX_AGENT_ERRORS:
                raise LoopError(f"The agent failed {agent_errors} times in a row. Last error: {desc}")
    except KeyboardInterrupt:
        log("\nInterrupted. Restoring the best version.")
        _revert(repo, best.commit, repo.untracked() - before)
    return rows


def _revert(repo: Repo, commit: str, created: set[str]) -> None:
    repo.reset_hard(commit)
    for rel in created:
        (repo.root / rel).unlink(missing_ok=True)
