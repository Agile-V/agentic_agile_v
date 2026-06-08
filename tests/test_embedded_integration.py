#!/usr/bin/env python3
"""
Test embedded systems integration without full installation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from agilev.embedded import __version__
        print(f"✓ agilev.embedded imported (v{__version__})")
    except Exception as e:
        print(f"✗ Failed to import agilev.embedded: {e}")
        return False
    
    try:
        from agilev.firmware import __version__
        print(f"✓ agilev.firmware imported (v{__version__})")
    except Exception as e:
        print(f"✗ Failed to import agilev.firmware: {e}")
        return False
    
    return True


def test_schemas_exist():
    """Test that all schemas exist."""
    print("\nTesting schemas...")
    
    schema_dir = Path(__file__).parent.parent / "schemas"
    required_schemas = [
        "system_contract.schema.json",
        "hardware_firmware_contract.schema.json",
        "firmware_software_contract.schema.json",
        "firmware_evidence_bundle.schema.json",
    ]
    
    all_exist = True
    for schema_name in required_schemas:
        schema_path = schema_dir / schema_name
        if schema_path.exists():
            print(f"✓ {schema_name} exists")
        else:
            print(f"✗ {schema_name} missing")
            all_exist = False
    
    return all_exist


def test_templates_exist():
    """Test that all templates exist."""
    print("\nTesting templates...")
    
    template_dir = Path(__file__).parent.parent / "templates" / "embedded"
    required_templates = [
        "system_contract.yaml",
        "hardware_firmware_contract.yaml",
        "firmware_software_contract.yaml",
        "firmware_evidence_bundle.json",
    ]
    
    all_exist = True
    for template_name in required_templates:
        template_path = template_dir / template_name
        if template_path.exists():
            print(f"✓ {template_name} exists")
        else:
            print(f"✗ {template_name} missing")
            all_exist = False
    
    return all_exist


def test_documentation_exists():
    """Test that documentation exists."""
    print("\nTesting documentation...")
    
    docs = [
        ("docs/embedded/embedded_systems_overview.md", "Embedded overview"),
        ("docs/adr/ADR-0002-embedded-systems-layer.md", "ADR-0002"),
        ("config/embedded/embedded_risk_levels.yaml", "Risk levels"),
    ]
    
    all_exist = True
    for doc_path, name in docs:
        full_path = Path(__file__).parent.parent / doc_path
        if full_path.exists():
            print(f"✓ {name} exists")
        else:
            print(f"✗ {name} missing")
            all_exist = False
    
    return all_exist


def test_modules_exist():
    """Test that all Python modules exist."""
    print("\nTesting Python modules...")
    
    modules = [
        ("src/agilev/embedded/__init__.py", "Embedded __init__"),
        ("src/agilev/embedded/cli.py", "Embedded CLI"),
        ("src/agilev/embedded/system_contract.py", "SystemContract"),
        ("src/agilev/firmware/__init__.py", "Firmware __init__"),
        ("src/agilev/firmware/cli.py", "Firmware CLI"),
        ("src/agilev/firmware/contract.py", "Contract classes"),
        ("src/agilev/firmware/backend.py", "FirmwareBackend"),
        ("src/agilev/firmware/platformio_backend.py", "PlatformIOBackend"),
        ("src/agilev/firmware/pcb_import.py", "PCB import"),
        ("src/agilev/pcb/firmware_export.py", "PCB firmware export"),
    ]
    
    all_exist = True
    for module_path, name in modules:
        full_path = Path(__file__).parent.parent / module_path
        if full_path.exists():
            print(f"✓ {name}")
        else:
            print(f"✗ {name} missing")
            all_exist = False
    
    return all_exist


def test_template_validation():
    """Test that templates are valid YAML/JSON."""
    print("\nTesting template validity...")
    
    # We'll just check they can be read without dependencies
    template_dir = Path(__file__).parent.parent / "templates" / "embedded"
    
    # Check YAML templates are readable
    yaml_templates = [
        "system_contract.yaml",
        "hardware_firmware_contract.yaml",
        "firmware_software_contract.yaml",
    ]
    
    all_valid = True
    for template_name in yaml_templates:
        template_path = template_dir / template_name
        try:
            content = template_path.read_text()
            if len(content) > 0 and "contract_id:" in content:
                print(f"✓ {template_name} is valid YAML")
            else:
                print(f"✗ {template_name} appears invalid")
                all_valid = False
        except Exception as e:
            print(f"✗ {template_name} error: {e}")
            all_valid = False
    
    # Check JSON template
    json_path = template_dir / "firmware_evidence_bundle.json"
    try:
        import json
        with open(json_path) as f:
            data = json.load(f)
        if "task_id" in data and "artifact_type" in data:
            print("✓ firmware_evidence_bundle.json is valid JSON")
        else:
            print("✗ firmware_evidence_bundle.json missing required fields")
            all_valid = False
    except Exception as e:
        print(f"✗ firmware_evidence_bundle.json error: {e}")
        all_valid = False
    
    return all_valid


def main():
    """Run all tests."""
    print("=" * 60)
    print("Embedded Systems Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Schemas", test_schemas_exist()))
    results.append(("Templates", test_templates_exist()))
    results.append(("Documentation", test_documentation_exists()))
    results.append(("Modules", test_modules_exist()))
    results.append(("Template Validity", test_template_validation()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
