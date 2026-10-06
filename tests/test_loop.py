import pytest
from conftest import FakeAgent, fail, git, nothing, set_x, write

from autoresearch import config, results
from autoresearch.loop import LoopError, research


def run(project, actions, tag="t", **kw):
    agent = FakeAgent(actions)
    rows = research(config.load(project), agent, tag, len(actions), log=lambda s: None, **kw)
    return rows, agent


def test_keeps_improvements_and_reverts_everything_else(project):
    rows, agent = run(project, [
        set_x(2),            # 1   -> keep
        set_x(1),            # 4   -> discard
        set_x("crash"),      #     -> crash
        write("score.py"),   #     -> rejected: not editable
        write("new.txt"),    #     -> rejected: new file
        nothing,             #     -> no-change
        set_x(3),            # 0   -> keep
        fail,                #     -> agent-error
    ])
    assert [r.status for r in rows] == [
        "baseline", "keep", "discard", "crash", "rejected", "rejected", "no-change", "keep", "agent-error"]
    assert [r.metric for r in rows[:3]] == ["9", "1", "4"]
    # Working tree ends at the best version, with nothing the agent wasn't allowed to leave behind.
    assert (project / "params.txt").read_text().strip() == "3"
    assert "print" in (project / "score.py").read_text()
    assert not (project / "new.txt").exists()
    assert git(project, "status", "--porcelain").strip() == ""
    # Only kept experiments remain in the branch history.
    log = git(project, "log", "--format=%s").splitlines()
    assert log == ["autoresearch 7: set x to 3", "autoresearch 1: set x to 2", "init"]
    assert git(project, "rev-parse", "--abbrev-ref", "HEAD").strip() == "autoresearch/t"
    # The log on disk matches, and the crash output reached the next prompt.
    assert results.read(project / ".autoresearch/t/results.tsv") == rows
    assert "boom" in agent.prompts[3]
    assert "| 2 | 4 | discard | set x to 1 |" in agent.prompts[3]


def test_timeout_is_reverted(project):
    cfg_path = project / "autoresearch.toml"
    cfg_path.write_text(cfg_path.read_text().replace("timeout = 5", "timeout = 1"))
    git(project, "commit", "-qam", "short timeout")
    rows, _ = run(project, [set_x("hang")])
    assert rows[-1].status == "timeout"
    assert (project / "params.txt").read_text().strip() == "0"


def test_resume_continues_from_best(project):
    run(project, [set_x(2), set_x(5)])
    rows, agent = run(project, [set_x(3)])
    assert [r.n for r in rows] == [0, 1, 2, 3]
    assert "current best is 1 (experiment 1)" in agent.prompts[0]
    assert rows[-1].status == "keep"


def test_untracked_files_present_before_are_left_alone(project):
    (project / "notes.txt").write_text("mine")
    run(project, [set_x(1), write("other.txt")])
    assert (project / "notes.txt").read_text() == "mine"
    assert not (project / "other.txt").exists()


def test_refuses_dirty_worktree(project):
    (project / "score.py").write_text("changed")
    with pytest.raises(LoopError, match="Uncommitted"):
        run(project, [set_x(1)])


def test_failed_baseline_stops(project):
    (project / "params.txt").write_text("crash\n")
    git(project, "commit", "-qam", "break")
    with pytest.raises(LoopError, match="baseline"):
        run(project, [set_x(1)])


def test_stops_after_repeated_agent_errors(project):
    with pytest.raises(LoopError, match="3 times"):
        run(project, [fail, fail, fail, set_x(3)])


def test_maximize_with_min_improvement(project):
    cfg_path = project / "autoresearch.toml"
    text = cfg_path.read_text().replace('"minimize"', '"maximize"') + "min_improvement = 2\n"
    cfg_path.write_text(text)
    git(project, "commit", "-qam", "maximize")
    rows, _ = run(project, [set_x(4), set_x(-1)])  # 9 -> 1 (worse), 9 -> 16 (better by 7)
    assert [r.status for r in rows] == ["baseline", "discard", "keep"]
