"""
Tests for PlatformIO backend.
"""

from pathlib import Path


def test_platformio_backend_exists():
    """Test that PlatformIO backend module exists."""
    backend_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "agilev"
        / "firmware"
        / "platformio_backend.py"
    )
    assert backend_path.exists(), f"Backend not found: {backend_path}"


def test_firmware_backend_base_exists():
    """Test that firmware backend base class exists."""
    backend_path = (
        Path(__file__).parent.parent.parent / "src" / "agilev" / "firmware" / "backend.py"
    )
    assert backend_path.exists(), f"Backend base not found: {backend_path}"


def test_pcb_firmware_export_exists():
    """Test that PCB firmware export module exists."""
    export_path = (
        Path(__file__).parent.parent.parent / "src" / "agilev" / "pcb" / "firmware_export.py"
    )
    assert export_path.exists(), f"Export module not found: {export_path}"


def test_firmware_pcb_import_exists():
    """Test that firmware PCB import module exists."""
    import_path = (
        Path(__file__).parent.parent.parent / "src" / "agilev" / "firmware" / "pcb_import.py"
    )
    assert import_path.exists(), f"Import module not found: {import_path}"
