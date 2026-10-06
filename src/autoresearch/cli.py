"""Command line: autoresearch init | run | report."""

from __future__ import annotations

import argparse
import shutil
import sys
from importlib import resources
from pathlib import Path

from . import config, report, results
from .agent import ClaudeCodeAgent
from .git import GitError
from .loop import LoopError, default_tag, research


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name in (config.CONFIG_NAME, "program.md"):
        dest = root / name
        if dest.exists():
            print(f"exists, left alone: {dest}")
            continue
        with resources.as_file(resources.files("autoresearch") / "templates" / name) as src:
            shutil.copy(src, dest)
        print(f"wrote {dest}")
    print("Edit both files, commit them, then run `autoresearch run`.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = config.load(Path(args.dir))
    tag = args.tag or default_tag()
    rows = research(cfg, ClaudeCodeAgent(cfg.agent, args.claude), tag, args.experiments)
    _report(cfg, tag, rows)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    cfg = config.load(Path(args.dir))
    tag = args.tag or _latest_tag(cfg.root)
    if not tag:
        print("No runs yet.")
        return 1
    rows = results.read(results.run_dir(cfg.root, tag) / "results.tsv")
    _report(cfg, tag, rows, Path(args.out) if args.out else None)
    return 0


def _report(cfg: config.Config, tag: str, rows: list[results.Row], out: Path | None = None) -> None:
    print("\n" + report.summary(rows, cfg.goal, cfg.metric))
    if rows:
        png = report.chart(rows, cfg.goal, cfg.metric, out or results.run_dir(cfg.root, tag) / "progress.png")
        print(f"\nChart: {png}")


def _latest_tag(root: Path) -> str:
    runs = [p for p in (root / ".autoresearch").glob("*/results.tsv")]
    return max(runs, key=lambda p: p.stat().st_mtime).parent.name if runs else ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="autoresearch",
                                description="An agent edits your code, runs your benchmark, "
                                            "and keeps only what improves the metric.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="write autoresearch.toml and program.md templates")
    s.add_argument("dir", nargs="?", default=".")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("run", help="run the research loop")
    s.add_argument("--dir", default=".", help="project folder with autoresearch.toml")
    s.add_argument("--tag", help="run name; the branch is autoresearch/<tag> (default: today, e.g. oct06)")
    s.add_argument("-n", "--experiments", type=int, default=0, help="stop after N experiments (default: run until Ctrl-C)")
    s.add_argument("--claude", default="claude", help="path to the Claude Code executable")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("report", help="summarise a run and draw progress.png")
    s.add_argument("--dir", default=".")
    s.add_argument("--tag", help="run to report (default: the most recent)")
    s.add_argument("--out", help="where to write the chart")
    s.set_defaults(fn=cmd_report)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except (config.ConfigError, LoopError, GitError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
