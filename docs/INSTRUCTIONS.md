# Instructions

## Setup

You need [uv](https://docs.astral.sh/uv/), git and [Claude Code](https://claude.com/claude-code)
(`claude` on your PATH, logged in).

```bash
git clone https://github.com/amalmehta/MyAutoresearch.git
cd MyAutoresearch
uv sync
```

Check it works:

```bash
uv run pytest
```

To have `autoresearch` available everywhere:

```bash
uv tool install .
```

## Try the example

The Tiny MLP example trains a small NumPy network for 10 seconds per experiment
on CPU. Copy it into its own git repository and start a short run:

```bash
cp -r examples/tiny-mlp ~/tiny-mlp && cd ~/tiny-mlp && git init -q && git add -A && git commit -qm "Tiny MLP"
autoresearch run -n 10
```

## Use it on your own project

1. In your project (a git repository), write the two setup files:

   ```bash
   autoresearch init
   ```

2. Edit `autoresearch.toml`:
   - `editable`: the files the agent may change. Keep the evaluation and data
     loading out of this list, so the agent can't change how it's judged.
   - `command`: runs one experiment and prints the metric as `name: value`
     (for example `val_loss: 0.123`). Give it a fixed budget (time or steps) so
     experiments are comparable.
   - `metric`, `goal` (`minimize` or `maximize`), `timeout`.
   - Optional: `metric_regex`, `min_improvement` (use it for noisy benchmarks),
     `history`, and under `[agent]`: `model`, `max_budget_usd`, `timeout`.

3. Write `program.md`: what the code does, ideas worth trying, and rules. The agent
   reads it before every experiment, and you can edit it between runs to steer.

4. Commit both files, then run:

   ```bash
   autoresearch run            # until Ctrl-C
   autoresearch run -n 20      # 20 experiments
   autoresearch run --tag adam # name the run; the branch is autoresearch/adam
   ```

   Run the same command again with the same tag to resume from the best result.
   The default tag is today's date, e.g. `oct06`.

## Read the results

```bash
autoresearch report                 # latest run
autoresearch report --tag adam
```

It prints the baseline, the best result, each kept change, and the agent cost,
then writes `.autoresearch/<tag>/progress.png`. Per-experiment details are in
`.autoresearch/<tag>/results.tsv`, and the command output is in `.autoresearch/<tag>/logs/`.

The branch `autoresearch/<tag>` holds only the kept changes, one commit each. To
use the result, merge that branch, or look at it with `git log autoresearch/<tag>`.

## Statuses

| Status | Meaning |
|---|---|
| baseline | Your starting code |
| keep | Better than the best so far; committed and kept |
| discard | Ran fine but wasn't better; reverted |
| crash | The command failed or printed no metric; reverted. Its output goes to the next prompt |
| timeout | Ran past `timeout`; killed and reverted |
| rejected | The agent touched a file outside `editable` or created a file; reverted |
| no-change | The agent edited nothing |
| agent-error | Claude Code failed (three in a row stops the run) |
