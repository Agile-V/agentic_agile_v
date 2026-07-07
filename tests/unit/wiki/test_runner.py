"""Tests for agilev.wiki.runner."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agilev.wiki.errors import WikiRunnerError
from agilev.wiki.runner import OpenWikiRunner


class _FakeCompleted:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_is_available_false_when_binary_missing(tmp_path: Path) -> None:
    runner = OpenWikiRunner(tmp_path, binary="definitely-not-a-real-binary-xyz")
    assert runner.is_available() is False


def test_run_raises_when_binary_missing(tmp_path: Path) -> None:
    runner = OpenWikiRunner(tmp_path, binary="definitely-not-a-real-binary-xyz")
    with pytest.raises(WikiRunnerError):
        runner.update()


def test_update_invokes_injected_run_fn_and_writes_log(tmp_path: Path) -> None:
    calls = []

    def fake_run(command, cwd, capture_output, text, check):  # noqa: ARG001
        calls.append(command)
        return _FakeCompleted(returncode=0, stdout="ok", stderr="")

    runner = OpenWikiRunner(tmp_path, binary="echo", run_fn=fake_run)
    result = runner.update()

    assert result.ok is True
    assert calls == [["echo", "--update"]]
    assert result.log_path is not None
    assert result.log_path.exists()
    assert "ok" in result.log_path.read_text(encoding="utf-8")


def test_init_and_prompt_build_expected_commands(tmp_path: Path) -> None:
    calls = []

    def fake_run(command, **kwargs):  # noqa: ARG001
        calls.append(command)
        return _FakeCompleted(returncode=0)

    runner = OpenWikiRunner(tmp_path, binary="echo", run_fn=fake_run)
    runner.init()
    runner.prompt("summarize this repo")

    assert calls[0] == ["echo", "--init"]
    assert calls[1] == ["echo", "-p", "summarize this repo"]


def test_run_result_ok_false_on_nonzero_exit(tmp_path: Path) -> None:
    def fake_run(command, **kwargs):  # noqa: ARG001
        return _FakeCompleted(returncode=1, stderr="boom")

    runner = OpenWikiRunner(tmp_path, binary="echo", run_fn=fake_run)
    result = runner.update()

    assert result.ok is False
    assert "boom" in result.stderr


def test_default_run_fn_is_subprocess_run(tmp_path: Path) -> None:
    runner = OpenWikiRunner(tmp_path, binary="echo")
    assert runner._run_fn is subprocess.run
