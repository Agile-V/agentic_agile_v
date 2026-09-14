"""Protocol-boundary checks for the local conformance command."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def command(tmp_path, *args, data=""):
    return subprocess.run(
        [sys.executable, "-m", "agilev.assurance", *args],
        input=data, text=True, capture_output=True, cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), timeout=10,
    )


def test_manifest_is_available_without_optional_validator(tmp_path):
    result = command(tmp_path, "--manifest")
    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    assert manifest["implementation"] == "agilev.assurance"
    assert manifest["deployment_mode"] == "local-conformance"


@pytest.mark.parametrize("data", ["{", '{"operation":"reuse","operation":"gate"}',
                                 '{"value":NaN}', "null", "[]"])
def test_invalid_protocol_input_is_rejected(tmp_path, data):
    context = tmp_path / "trusted.json"
    context.write_text("{}")
    result = command(tmp_path, "--trusted-context", str(context),
                     "--schemas", str(tmp_path), data=data)
    assert result.returncode == 1
    assert json.loads(result.stdout) == {
        "status": "rejected", "findings": [{"code": "INPUT_INVALID"}],
    }


def test_request_cannot_choose_trusted_context(tmp_path):
    result = command(tmp_path, data='{"trusted_context":"candidate.json"}')
    assert result.returncode == 2
    assert "--trusted-context" in result.stderr
