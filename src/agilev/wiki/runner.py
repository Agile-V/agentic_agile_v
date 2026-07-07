"""Subprocess wrapper around the external `openwiki` CLI.

`openwiki` (https://github.com/langchain-ai/openwiki) is an npm-installed,
LLM-backed CLI that is not part of the `agilev` package. This module never
imports or vendors it; it only knows how to invoke it as a subprocess and
capture output, so unit tests can inject a fake `run_fn` and never spawn a
real process or make network/API calls.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from agilev.wiki import constants
from agilev.wiki.errors import WikiRunnerError

RunFn = Callable[..., subprocess.CompletedProcess]


@dataclass
class RunResult:
    """Result of invoking the `openwiki` CLI."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    log_path: Path | None = None

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class OpenWikiRunner:
    """Invokes the external `openwiki` binary and captures its output."""

    def __init__(
        self,
        repo_root: Path,
        binary: str = "openwiki",
        run_fn: RunFn | None = None,
    ):
        """Initialize the runner.

        Args:
            repo_root: Repository root directory (cwd for the subprocess).
            binary: Name/path of the `openwiki` executable.
            run_fn: Callable matching `subprocess.run`'s signature. Defaults
                to `subprocess.run`; tests should inject a fake.
        """
        self.repo_root = repo_root
        self.binary = binary
        self._run_fn: RunFn = run_fn or subprocess.run

    def is_available(self) -> bool:
        """Return True if the `openwiki` binary is resolvable on PATH."""
        return shutil.which(self.binary) is not None

    def init(self, extra_args: list[str] | None = None) -> RunResult:
        """Run `openwiki --init`."""
        return self._run(["--init", *(extra_args or [])], log_name="init")

    def update(self, extra_args: list[str] | None = None) -> RunResult:
        """Run `openwiki --update`."""
        return self._run(["--update", *(extra_args or [])], log_name="update")

    def prompt(self, prompt_text: str, extra_args: list[str] | None = None) -> RunResult:
        """Run `openwiki -p "<prompt_text>"` (one-shot, non-interactive)."""
        return self._run(["-p", prompt_text, *(extra_args or [])], log_name="prompt")

    def _run(self, args: list[str], log_name: str) -> RunResult:
        if not self.is_available():
            raise WikiRunnerError(
                f"'{self.binary}' was not found on PATH. Install it with "
                "'npm install -g openwiki', or see docs/integrations/openwiki.md."
            )

        command = [self.binary, *args]
        completed = self._run_fn(
            command,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        log_path = self._write_log(log_name, command, completed)

        return RunResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            log_path=log_path,
        )

    def _write_log(
        self, log_name: str, command: list[str], completed: subprocess.CompletedProcess
    ) -> Path:
        logs_dir = self.repo_root / constants.STATE_DIR / constants.LOGS_DIRNAME
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        log_path = logs_dir / f"{timestamp}-{log_name}.log"

        content = (
            f"$ {' '.join(command)}\n"
            f"exit_code: {completed.returncode}\n"
            f"--- stdout ---\n{completed.stdout or ''}\n"
            f"--- stderr ---\n{completed.stderr or ''}\n"
        )
        log_path.write_text(content, encoding="utf-8")
        return log_path
