import json
import os
import stat
import subprocess
import sys

import pytest
from conftest import FakeAgent, set_x

from autoresearch import cli, config, results
from autoresearch.agent import ClaudeCodeAgent, extract_description
from autoresearch.config import AgentConfig, ConfigError
from autoresearch.loop import research
from autoresearch.report import chart, summary
from autoresearch.runner import parse_metric


def test_parse_metric(project):
    cfg = config.load(project)
    assert parse_metric(cfg, "score: 1\nloss 3\nscore = 2.5e-3\n") == 0.0025
    assert parse_metric(cfg, "best_score: 4") is None
    assert parse_metric(cfg, "nothing") is None
    cfg.metric_regex = r"loss=(\d+\.\d+)"
    assert parse_metric(cfg, "step 1 loss=0.50\nstep 2 loss=0.25") == 0.25


@pytest.mark.parametrize("edit, message", [
    (lambda t: t.replace('metric = "score"\n', ""), "missing `metric`"),
    (lambda t: t.replace("minimize", "smaller"), "goal"),
    (lambda t: t.replace("params.txt", "nope.txt"), "not found"),
    (lambda t: t + "colour = 1\n", "colour"),
])
def test_config_errors(project, edit, message):
    path = project / "autoresearch.toml"
    path.write_text(edit(path.read_text()))
    with pytest.raises(ConfigError, match=message):
        config.load(project)


def fake_claude(tmp_path, body):
    # A sh wrapper: a shebang can't hold the interpreter path if it has spaces.
    (tmp_path / "claude.py").write_text(f"import json, sys\n{body}\n")
    exe = tmp_path / "claude"
    exe.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$0.py" "$@"\n')
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return str(exe)


def test_claude_agent_runs_cli_and_reads_json(project, tmp_path):
    exe = fake_claude(tmp_path, (
        "open('params.txt', 'w').write('3')\n"
        "json.dump({'argv': sys.argv[1:]}, open('../argv.json', 'w'))\n"
        "print(json.dumps({'result': 'Done.\\nDESCRIPTION: set x to 3', 'total_cost_usd': 0.12,"
        " 'is_error': False}))"))
    agent = ClaudeCodeAgent(AgentConfig(model="sonnet", max_budget_usd=0.5), exe)
    rows = research(config.load(project), agent, "c", 1, log=lambda s: None)
    assert rows[-1].status == "keep" and rows[-1].description == "set x to 3"
    assert rows[-1].cost_usd == "0.1200"
    argv = json.load(open(project.parent / "argv.json"))["argv"]
    assert argv[0] == "-p"
    assert argv[argv.index("--tools") + 1] == "Read,Edit,Write,Glob,Grep"
    assert argv[argv.index("--model") + 1] == "sonnet"
    assert argv[argv.index("--max-budget-usd") + 1] == "0.5"


def test_claude_agent_errors(project, tmp_path):
    cfg = AgentConfig()
    assert "not found" in ClaudeCodeAgent(cfg, str(tmp_path / "missing")).propose("hi", project).error
    exe = fake_claude(tmp_path, "print(json.dumps({'result': 'Credit balance too low', 'is_error': True}))")
    assert ClaudeCodeAgent(cfg, exe).propose("hi", project).error == "Credit balance too low"
    exe = fake_claude(tmp_path, "sys.exit('not json')")
    assert "not json" in ClaudeCodeAgent(cfg, exe).propose("hi", project).error


def test_extract_description():
    assert extract_description("blah\nDESCRIPTION: use Adam\n") == "use Adam"
    assert extract_description("I switched to Adam.") == "I switched to Adam."


def test_report_and_cli(project, capsys):
    research(config.load(project), FakeAgent([set_x(2), set_x(1), set_x(3)]), "r", 3, log=lambda s: None)
    rows = results.read(project / ".autoresearch/r/results.tsv")
    text = summary(rows, "minimize", "score")
    assert "3 experiments" in text and "best 0" in text and "set x to 3" in text
    png = chart(rows, "minimize", "score", project.parent / "p.png")
    assert png.read_bytes()[:4] == b"\x89PNG"

    assert cli.main(["report", "--dir", str(project), "--out", str(project.parent / "q.png")]) == 0
    assert (project.parent / "q.png").exists()
    assert cli.main(["run", "--dir", str(project.parent)]) == 1
    assert "No autoresearch.toml" in capsys.readouterr().err


def test_init_writes_templates(tmp_path):
    assert cli.main(["init", str(tmp_path / "new")]) == 0
    assert (tmp_path / "new/autoresearch.toml").exists()
    assert (tmp_path / "new/program.md").exists()


def test_console_script_installed():
    bin_dir = os.path.dirname(sys.executable)
    out = subprocess.run([os.path.join(bin_dir, "autoresearch"), "--help"], capture_output=True, text=True)
    assert "init" in out.stdout and "report" in out.stdout

