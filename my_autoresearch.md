PROJECT NAME: my_autoresearch

META-INSTRUCTIONS:

<Read it all before acting. Ask about anything unclear, contradictory or
 underspecified — before starting and mid-build. Ask in the question widget
 (AskUserQuestion): related questions batched, concrete options, your
 recommendation first. Plain text only if the widget isn't available.>

<Don't expand scope. Anything not listed here is a proposal, including changes
 to this file — propose it, don't do it.>

<Prefer doing over describing: run the code, write the files, test it.>

<Always in scope, no proposal needed: when it goes on GitHub, a README that is
 easy to read at a glance — a line on what it is, then clear visuals
 (screenshots, a diagram or a chart), then links. Everything else goes in
 linked files: docs/INSTRUCTIONS.md (setup, run, use),
 docs/SYSTEM-DESIGN.md (see below) and docs/FILE-STRUCTURE.md (what's where). If what you're
 building is an application rather than a script, also a small unobtrusive feedback tab, and a settings
 button or tab (⌘, on the Mac) that gathers its preferences in one place.>

<If what you're building is an application, build it as a Mac app first; the
 website comes after, as its own step.>

<Name things the way a person would say them — "Goal Tracker", not
 goal_tracker — for the app, its windows, titles, files people open, repo
 descriptions and README headings. When you create the GitHub repo, name it
 with no "_" or "-": one word or joined words, e.g. GoalTracker.>

<Always in scope: a system design doc in the codebase, docs/SYSTEM-DESIGN.md,
 kept current as the build changes. Cover the architecture (with a Mermaid
 diagram), each component's job, the main flows, where data lives, the key
 design decisions and their trade-offs, how it's tested, and known limits.>

<Finish by listing every deliverable: path, what it is, how to check it works.>

<Git rules (no Claude attribution, never commit .claude/) are in
 ~/.claude/CLAUDE.md and apply on their own — nothing to repeat here.>

<Keep the changelog at the bottom current.>

CONTEXT:

autoresearch (a la karpathy), but my version

DELIVERABLES:

autoresearch module

OPEN QUESTIONS / ASSUMPTIONS:

Answered by you (2026-10-06):
- Target: generic. Any git repo, a list of editable files, and a command that prints a metric.
- Agent: headless Claude Code (`claude -p`), using your existing login.
- Hardware: this Mac. It turned out to be an Intel i9 with no MPS, so the example is
  CPU-only NumPy. The tool itself never touches devices; hardware is the target's business.
- Form: Python CLI (not an app, so no Mac app, settings or feedback tab). GitHub repo MyAutoresearch.

Decided without asking:
- The agent gets file tools only (Read, Edit, Write, Glob, Grep) and no shell. The harness
  commits, runs, keeps or reverts. Each experiment is a fresh `claude -p` call with the
  history in the prompt.
- Keep a change only if it strictly improves the metric (optional `min_improvement`). Editing a
  non-editable file or creating a file rejects the whole experiment.
- Results live in `.autoresearch/<tag>/` (ignored locally via .git/info/exclude); kept changes
  are commits on branch `autoresearch/<tag>`; runs resume by tag.
- Shipped one small example (examples/tiny-mlp, 10 s per experiment) to test and demo with.
- Python 3.11+ managed with uv; matplotlib for the progress chart.
- The GitHub repo is private (you can make it public in its settings).

CHANGELOG:

- 2026-10-06 — created
- 2026-09-15 — added meta-instruction: built-out applications include a small feedback tab
- 2026-09-15 — added meta-instruction: no "Claude" attribution in commits, PRs, or branches
- 2026-09-16 — added meta-instruction: always include a README when adding to GitHub
- 2026-09-16 — changed meta-instruction: ask clarifying questions in the question widget
- 2026-09-17 — added meta-instructions: Claude never a contributor; never commit .claude/
- 2026-09-26 — compressed the meta-instructions and every field prompt; git rules moved to the global instruction file
- 2026-09-27 — added meta-instruction: applications are built as a Mac app first, then a website
- 2026-09-28 — folded inputs, instructions, constraints, deliverables and done criteria into one free-form CONTEXT
- 2026-09-28 — changed meta-instruction: a README on GitHub always includes a visual
- 2026-09-28 — added meta-instruction: name things like a person would, never snake_case
- 2026-09-28 — changed meta-instruction: README leads with visuals; instructions live in a linked guide
- 2026-09-28 — changed meta-instruction: README is visuals and links; details in docs/INSTRUCTIONS.md and docs/FILE-STRUCTURE.md
- 2026-09-29 — changed meta-instruction: GitHub repo names have no "_" or "-"
- 2026-10-02 — added a DELIVERABLES field after CONTEXT
- 2026-10-02 — added meta-instruction: every project has a system design doc at docs/SYSTEM-DESIGN.md
- 2026-10-05 — added meta-instruction: applications include a settings button or tab
- 2026-10-06 — built v0.1: generic autoresearch CLI (Claude Code agent), Tiny MLP example, tests, docs
