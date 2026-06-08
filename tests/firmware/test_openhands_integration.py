"""
Tests for firmware OpenHands integration.
"""

from pathlib import Path


def test_firmware_hooks_exist():
    """Test that firmware hooks exist and are executable."""
    hooks_dir = Path(__file__).parent.parent.parent / ".openhands" / "hooks"

    required_hooks = [
        "enforce_hardware_firmware_contract.sh",
        "validate_firmware_scope.sh",
        "require_firmware_tests.sh",
        "collect_firmware_evidence.sh",
    ]

    for hook_name in required_hooks:
        hook_path = hooks_dir / hook_name
        assert hook_path.exists(), f"Hook not found: {hook_name}"
        # Check if executable (on Unix systems)
        if hook_path.exists():
            import stat

            st = hook_path.stat()
            is_executable = bool(st.st_mode & stat.S_IXUSR)
            assert is_executable, f"Hook not executable: {hook_name}"


def test_firmware_builder_module_exists():
    """Test that firmware builder module exists."""
    module_path = (
        Path(__file__).parent.parent.parent / "src" / "agilev" / "openhands" / "firmware_builder.py"
    )
    assert module_path.exists(), f"Module not found: {module_path}"


def test_firmware_evidence_adapter_exists():
    """Test that firmware evidence adapter exists."""
    module_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "agilev"
        / "openhands"
        / "firmware_evidence_adapter.py"
    )
    assert module_path.exists(), f"Module not found: {module_path}"


def test_hooks_json_updated():
    """Test that hooks.json includes firmware hooks."""
    hooks_json = Path(__file__).parent.parent.parent / ".openhands" / "hooks.json"
    assert hooks_json.exists(), "hooks.json not found"

    import json

    with open(hooks_json) as f:
        config = json.load(f)

    # Check that firmware hooks are referenced
    all_hooks = []
    for hook_type in config.values():
        if isinstance(hook_type, list):
            for entry in hook_type:
                if "hooks" in entry:
                    all_hooks.extend([h["command"] for h in entry["hooks"]])

    firmware_hooks = [h for h in all_hooks if "firmware" in h]
    assert len(firmware_hooks) >= 3, (
        f"Expected at least 3 firmware hooks, found {len(firmware_hooks)}"
    )
