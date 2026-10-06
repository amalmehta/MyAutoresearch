"""Summarises a run: a text table and a progress chart (progress.png)."""

from __future__ import annotations

from pathlib import Path

from .results import Row, best

KEPT = "#2a78d6"  # categorical slot 1 (blue): kept experiments and the running best
OTHER = "#a3a29c"  # recessive gray: discarded
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e8e7e3"


def summary(rows: list[Row], goal: str, metric: str) -> str:
    if not rows:
        return "No experiments yet."
    b = best(rows, goal)
    base = rows[0]
    counts: dict[str, int] = {}
    for r in rows[1:]:
        counts[r.status] = counts.get(r.status, 0) + 1
    cost = sum(float(r.cost_usd or 0) for r in rows)
    lines = [
        f"{len(rows) - 1} experiments · " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())),
        f"baseline {metric} = {base.metric}  →  best {b.metric} (experiment {b.n}, commit {b.commit})",
        f"agent cost ${cost:.2f}",
        "",
        "Kept changes:",
    ]
    lines += [f"  {r.n:>4}  {r.metric:<10} {r.description}" for r in rows if r.status == "keep"] or ["  none yet"]
    return "\n".join(lines)


def chart(rows: list[Row], goal: str, metric: str, out: Path, title: str = "") -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    fig.patch.set_facecolor("white")
    pts = [r for r in rows if r.value is not None]
    disc = [r for r in pts if r.status == "discard"]
    kept = [r for r in pts if r.status in ("baseline", "keep")]

    ax.scatter([r.n for r in disc], [r.value for r in disc], s=22, color=OTHER, label="Discarded",
               zorder=2, linewidths=0)
    # Running best as a step line through every experiment.
    xs, ys, cur = [], [], None
    for r in rows:
        if r.status in ("baseline", "keep") and r.value is not None:
            cur = r.value
        if cur is not None:
            xs.append(r.n)
            ys.append(cur)
    ax.step(xs, ys, where="post", color=KEPT, linewidth=2, label="Best so far", zorder=3)
    ax.scatter([r.n for r in kept], [r.value for r in kept], s=46, color=KEPT, edgecolors="white",
               linewidths=1.5, label="Kept", zorder=4)
    # Label kept changes on the side of the point away from the step line; flip left near the right edge.
    last = rows[-1].n or 1
    for r in kept[1:]:
        right = r.n / last > 0.7
        ax.annotate(_short(r.description), (r.n, r.value), xytext=(-8 if right else 8, 8 if goal == "minimize" else -14),
                    textcoords="offset points", fontsize=7, color=MUTED, ha="right" if right else "left")

    failed = sum(1 for r in rows if r.status in ("crash", "timeout"))
    skipped = sum(1 for r in rows if r.status in ("rejected", "no-change", "agent-error"))
    b = best(rows, goal)
    ax.set_title(title or f"{len(rows) - 1} experiments · {len(kept) - 1} kept · {metric}: "
                 f"{rows[0].metric} → {b.metric}", loc="left", fontsize=11, color=INK)
    if failed or skipped:
        ax.text(1.0, 1.02, f"not plotted: {failed} crashed, {skipped} skipped", transform=ax.transAxes,
                ha="right", fontsize=8, color=MUTED)
    ax.set_xlabel("Experiment", color=MUTED, fontsize=9)
    ax.set_ylabel(f"{metric} ({'lower' if goal == 'minimize' else 'higher'} is better)", color=MUTED, fontsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.legend(frameon=False, fontsize=8, loc="upper right" if goal == "minimize" else "lower right",
              labelcolor=INK)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def _short(text: str, n: int = 32) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"
