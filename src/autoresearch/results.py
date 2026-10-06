"""The results log: one tab-separated row per experiment, in .autoresearch/<tag>/results.tsv."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, fields
from pathlib import Path

# Statuses: baseline, keep, discard, crash, timeout, rejected (touched a file it may
# not edit), no-change (agent changed nothing), agent-error.


@dataclass
class Row:
    n: int
    commit: str
    metric: str  # blank when there is no number
    status: str
    seconds: str
    cost_usd: str
    description: str

    @property
    def value(self) -> float | None:
        return float(self.metric) if self.metric else None


COLUMNS = [f.name for f in fields(Row)]


def run_dir(root: Path, tag: str) -> Path:
    return root / ".autoresearch" / tag


def read(path: Path) -> list[Row]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        rows = []
        for r in csv.DictReader(f, delimiter="\t"):
            d = {k: r.get(k) or "" for k in COLUMNS}
            d["n"] = int(d["n"])
            rows.append(Row(**d))
        return rows


def append(path: Path, row: Row) -> None:
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t")
        if new:
            w.writeheader()
        clean = {k: str(v).replace("\t", " ").replace("\n", " ") for k, v in asdict(row).items()}
        w.writerow(clean)


def best(rows: list[Row], goal: str) -> Row | None:
    kept = [r for r in rows if r.status in ("baseline", "keep") and r.value is not None]
    if not kept:
        return None
    pick = min if goal == "minimize" else max
    return pick(kept, key=lambda r: r.value)
