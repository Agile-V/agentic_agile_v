"""
Tests for system contract validation.
"""

from pathlib import Path


def test_system_contract_schema_exists():
    """Test that system contract schema exists."""
    schema_path = Path(__file__).parent.parent.parent / "schemas" / "system_contract.schema.json"
    assert schema_path.exists(), f"Schema not found: {schema_path}"


def test_hardware_firmware_contract_schema_exists():
    """Test that hardware-firmware contract schema exists."""
    schema_path = (
        Path(__file__).parent.parent.parent
        / "schemas"
        / "hardware_firmware_contract.schema.json"
    )
    assert schema_path.exists(), f"Schema not found: {schema_path}"


def test_firmware_software_contract_schema_exists():
    """Test that firmware-software contract schema exists."""
    schema_path = (
        Path(__file__).parent.parent.parent
        / "schemas"
        / "firmware_software_contract.schema.json"
    )
    assert schema_path.exists(), f"Schema not found: {schema_path}"


def test_firmware_evidence_bundle_schema_exists():
    """Test that firmware evidence bundle schema exists."""
    schema_path = (
        Path(__file__).parent.parent.parent / "schemas" / "firmware_evidence_bundle.schema.json"
    )
    assert schema_path.exists(), f"Schema not found: {schema_path}"


def test_system_contract_template_exists():
    """Test that system contract template exists."""
    template_path = (
        Path(__file__).parent.parent.parent / "templates" / "embedded" / "system_contract.yaml"
    )
    assert template_path.exists(), f"Template not found: {template_path}"


def test_hardware_firmware_contract_template_exists():
    """Test that hardware-firmware contract template exists."""
    template_path = (
        Path(__file__).parent.parent.parent
        / "templates"
        / "embedded"
        / "hardware_firmware_contract.yaml"
    )
    assert template_path.exists(), f"Template not found: {template_path}"


def test_firmware_software_contract_template_exists():
    """Test that firmware-software contract template exists."""
    template_path = (
        Path(__file__).parent.parent.parent
        / "templates"
        / "embedded"
        / "firmware_software_contract.yaml"
    )
    assert template_path.exists(), f"Template not found: {template_path}"


def test_firmware_evidence_bundle_template_exists():
    """Test that firmware evidence bundle template exists."""
    template_path = (
        Path(__file__).parent.parent.parent
        / "templates"
        / "embedded"
        / "firmware_evidence_bundle.json"
    )
    assert template_path.exists(), f"Template not found: {template_path}"
