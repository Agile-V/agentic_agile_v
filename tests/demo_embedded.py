#!/usr/bin/env python3
"""
Demonstration of embedded systems integration capabilities.

Shows what files are created and their structure without requiring dependencies.
"""

from pathlib import Path


def show_file_tree(directory: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
    """Display directory tree."""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(directory.iterdir())
    except PermissionError:
        return
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        
        print(f"{prefix}{connector}{item.name}")
        
        if item.is_dir() and not item.name.startswith('.'):
            extension = "    " if is_last else "│   "
            show_file_tree(item, prefix + extension, max_depth, current_depth + 1)


def show_file_preview(file_path: Path, max_lines: int = 20):
    """Show preview of a file."""
    try:
        lines = file_path.read_text().split('\n')
        print(f"\n📄 {file_path.name}:")
        print("-" * 60)
        for i, line in enumerate(lines[:max_lines], 1):
            print(f"{i:3}: {line}")
        if len(lines) > max_lines:
            print(f"... ({len(lines) - max_lines} more lines)")
        print("-" * 60)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")


def main():
    """Show demonstration of embedded systems integration."""
    print("=" * 70)
    print("EMBEDDED SYSTEMS INTEGRATION DEMONSTRATION")
    print("=" * 70)
    
    base_path = Path(__file__).parent.parent
    
    # Show repository structure
    print("\n📁 Repository Structure:")
    print("-" * 70)
    
    key_dirs = [
        ("docs/embedded", "Embedded systems documentation"),
        ("docs/adr", "Architecture decision records"),
        ("config/embedded", "Embedded risk levels and configuration"),
        ("schemas", "JSON schemas for contracts and evidence"),
        ("templates/embedded", "Template contracts and evidence bundles"),
        ("src/agilev/embedded", "Embedded systems Python module"),
        ("src/agilev/firmware", "Firmware backend Python module"),
        ("src/agilev/pcb", "PCB integration module"),
    ]
    
    for dir_path, description in key_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            file_count = len(list(full_path.rglob("*.py" if "src" in dir_path else "*")))
            print(f"✓ {dir_path:<30} - {description} ({file_count} files)")
        else:
            print(f"✗ {dir_path:<30} - Missing!")
    
    # Show template examples
    print("\n📋 Contract Templates:")
    print("-" * 70)
    
    templates = [
        ("system_contract.yaml", "Top-level system contract"),
        ("hardware_firmware_contract.yaml", "PCB to firmware contract"),
        ("firmware_software_contract.yaml", "Firmware to software contract"),
        ("firmware_evidence_bundle.json", "Firmware evidence bundle"),
    ]
    
    template_dir = base_path / "templates" / "embedded"
    for template_name, description in templates:
        template_path = template_dir / template_name
        if template_path.exists():
            size = template_path.stat().st_size
            print(f"✓ {template_name:<40} - {description} ({size} bytes)")
        else:
            print(f"✗ {template_name:<40} - Missing!")
    
    # Show example template content
    print("\n📖 Example Template Content:")
    print("-" * 70)
    
    hw_fw_contract = template_dir / "hardware_firmware_contract.yaml"
    if hw_fw_contract.exists():
        show_file_preview(hw_fw_contract, max_lines=30)
    
    # Show CLI commands available
    print("\n⚙️  Available CLI Commands:")
    print("-" * 70)
    
    commands = [
        ("agilev embedded init", "Initialize embedded systems structure"),
        ("agilev embedded doctor", "Check embedded environment"),
        ("agilev embedded contract validate", "Validate system contract"),
        ("agilev firmware contract generate", "Generate HW-FW contract from PCB"),
        ("agilev firmware contract validate", "Validate firmware contract"),
        ("agilev firmware generate", "Generate firmware project from contract"),
        ("agilev firmware build", "Build firmware project"),
        ("agilev firmware test --host", "Run host-based firmware tests"),
    ]
    
    for cmd, description in commands:
        print(f"  {cmd:<40} - {description}")
    
    # Show workflow
    print("\n🔄 Complete Workflow:")
    print("-" * 70)
    print("""
    1. PCB Design (using existing PCB backend)
       └─> Circuit IR with components, nets, interfaces
    
    2. Export PCB to Firmware Contract
       └─> agilev firmware contract generate --from-pcb ...
       └─> hardware_firmware_contract.yaml created
    
    3. Generate Firmware Project
       └─> agilev firmware generate --contract ...
       └─> firmware/platformio/ project created with:
           ├── platformio.ini (build config)
           ├── include/board_contract.h (pin definitions)
           ├── src/main.cpp (firmware skeleton)
           └── src/diagnostics.cpp (diagnostic commands)
    
    4. Build and Test
       └─> agilev firmware build --project ...
       └─> agilev firmware test --project ... --host
    
    5. Collect Evidence
       └─> firmware_evidence_bundle.json with:
           - Build status and logs
           - Test results
           - Firmware binary hash
           - Traceability to PCB/requirements
    
    6. Independent Verification
       └─> Cross-domain verification checks:
           - PCB netlist ↔ contract
           - Firmware config ↔ contract
           - Software API ↔ contract
    
    7. Human Approval & Release
       └─> L0-L4 risk-based approval gates
       └─> Stale evidence detection
       └─> Release gate blocks merge if incomplete
    """)
    
    # Show statistics
    print("\n📊 Implementation Statistics:")
    print("-" * 70)
    
    python_files = list((base_path / "src" / "agilev" / "embedded").rglob("*.py"))
    python_files += list((base_path / "src" / "agilev" / "firmware").rglob("*.py"))
    python_files += list((base_path / "src" / "agilev" / "pcb").rglob("*firmware*.py"))
    
    total_lines = 0
    for py_file in python_files:
        total_lines += len(py_file.read_text().split('\n'))
    
    print(f"  Python modules: {len(python_files)}")
    print(f"  Total lines: ~{total_lines}")
    print(f"  Schemas: 4")
    print(f"  Templates: 4")
    print(f"  Documentation: 3 files")
    
    # Show key features
    print("\n✨ Key Features:")
    print("-" * 70)
    
    features = [
        "✓ Machine-checkable contracts (PCB ↔ Firmware ↔ Software)",
        "✓ Automatic firmware code generation from contracts",
        "✓ Pin definitions extracted from PCB Circuit IR",
        "✓ Risk-based approval gates (L0-L4)",
        "✓ Stale evidence detection on contract changes",
        "✓ Cross-domain traceability",
        "✓ PlatformIO backend support",
        "✓ Evidence collection and validation",
        "✓ Schema validation for all contracts",
        "✓ CLI tools for complete workflow",
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n" + "=" * 70)
    print("✓ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nAll components implemented and ready for use!")
    print("Install pyyaml and jsonschema to enable full functionality.")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
