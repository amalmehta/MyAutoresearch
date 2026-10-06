# File Structure

```
MyAutoresearch/
├── README.md                     What it is, the chart, links
├── my_autoresearch.md            The project spec this was built from
├── pyproject.toml                Package, dependencies, `autoresearch` command
├── src/autoresearch/
│   ├── cli.py                    autoresearch init | run | report
│   ├── loop.py                   The research loop: keep, discard, revert
│   ├── agent.py                  Prompt + headless Claude Code (claude -p)
│   ├── runner.py                 Runs one experiment, reads the metric
│   ├── config.py                 Reads and checks autoresearch.toml
│   ├── git.py                    The git commands the loop uses
│   ├── results.py                results.tsv read/append, best row
│   ├── report.py                 Text summary and progress.png
│   └── templates/                Files written by `autoresearch init`
│       ├── autoresearch.toml
│       └── program.md
├── examples/tiny-mlp/            A 10-second NumPy example to try it on
│   ├── prepare.py                Fixed data, time budget, evaluation
│   ├── train.py                  The file the agent edits
│   ├── program.md                Research directions
│   └── autoresearch.toml
├── tests/
│   ├── conftest.py               Throwaway git project + scripted fake agent
│   ├── test_loop.py              Loop behaviour end to end
│   └── test_parts.py             Config, metric parsing, Claude adapter, report, CLI
└── docs/
    ├── INSTRUCTIONS.md           Setup, run, use
    ├── SYSTEM-DESIGN.md          Architecture, flows, decisions, limits
    ├── FILE-STRUCTURE.md         This file
    └── images/progress.png       Chart from a real run on the example
```

In a project you run it on:

```
your-project/
├── autoresearch.toml             Your setup (commit it)
├── program.md                    Your research directions (commit it)
└── .autoresearch/<tag>/          Created by runs; ignored by git locally
    ├── results.tsv               One row per experiment
    ├── logs/<n>.log              Command output per experiment
    └── progress.png              Chart from `autoresearch report`
```
