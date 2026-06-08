#!/usr/bin/env python3
"""Manual test script for PCB modules."""

import sys

sys.path.insert(0, 'src')

from agilev.pcb.circuit_ir import CircuitIR, Component, Net, NetType, Pin, PinType, PowerDomain
from agilev.pcb.component_index import (
    ComponentIndex,
    create_capacitor_entry,
    create_ic_entry,
    create_resistor_entry,
)
from agilev.pcb.validators import (
    PowerBudgetValidator,
    VoltageDomainValidator,
    generate_validation_report,
    validate_circuit,
)


def test_circuit_ir():
    """Test Circuit IR functionality."""
    print("\n=== Testing Circuit IR ===")
    
    # Create circuit
    circuit = CircuitIR("esp32_test", "ESP32 Test Circuit")
    print(f"✅ Created circuit: {circuit.name}")
    
    # Add power domain
    vcc = PowerDomain(
        name="VCC_3V3",
        voltage_nominal=3.3,
        voltage_min=3.0,
        voltage_max=3.6,
        current_max=1.0,
        nets=["VCC_3V3"]  # Include the net name we'll create
    )
    circuit.add_power_domain(vcc)
    print(f"✅ Added power domain: {vcc.name} ({vcc.voltage_nominal}V)")
    
    # Add components
    r1 = Component(
        id="R1",
        type="resistor",
        value="10k",
        package="0603",
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive")
        ]
    )
    circuit.add_component(r1)
    print(f"✅ Added component: {r1.id} ({r1.value})")
    
    c1 = Component(
        id="C1",
        type="capacitor",
        value="100nF",
        package="0603",
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive")
        ]
    )
    circuit.add_component(c1)
    print(f"✅ Added component: {c1.id} ({c1.value})")
    
    # Add nets
    vcc_net = Net(
        name="VCC_3V3",
        type=NetType.POWER,
        connections=[("R1", "1"), ("C1", "1")]
    )
    circuit.add_net(vcc_net)
    print(f"✅ Added net: {vcc_net.name} with {len(vcc_net.connections)} connections")
    
    gnd_net = Net(
        name="GND",
        type=NetType.GROUND,
        connections=[("R1", "2"), ("C1", "2")]
    )
    circuit.add_net(gnd_net)
    print(f"✅ Added net: {gnd_net.name} with {len(gnd_net.connections)} connections")
    
    # Validate connections
    errors = circuit.validate_connections()
    if errors:
        print(f"❌ Validation errors: {errors}")
        return False
    else:
        print("✅ Connection validation passed (0 errors)")
    
    # Test save/load
    import os
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        from pathlib import Path
        circuit.save(Path(temp_file))
        print(f"✅ Saved circuit to {temp_file}")
        
        loaded = CircuitIR.load(Path(temp_file))
        print(f"✅ Loaded circuit: {loaded.name}")
        
        assert loaded.name == circuit.name
        assert len(loaded.components) == len(circuit.components)
        assert len(loaded.nets) == len(circuit.nets)
        print("✅ Save/load verification passed")
        
    finally:
        os.unlink(temp_file)
    
    return True


def test_component_index():
    """Test component index."""
    print("\n=== Testing Component Index ===")
    
    index = ComponentIndex()
    print("✅ Created empty index")
    
    # Add components using helper functions
    r1 = create_resistor_entry("RC0603FR-0710KL", "10k", approved=True)
    index.add_component(r1)
    print(f"✅ Added resistor: {r1.part_number}")
    
    c1 = create_capacitor_entry("CL10B104KB8NNNC", "100nF", "50V", approved=True)
    index.add_component(c1)
    print(f"✅ Added capacitor: {c1.part_number}")
    
    ic1 = create_ic_entry(
        "ESP32-C3-MINI-1",
        "Espressif",
        "WiFi/BLE Module",
        "SMD-53",
        "https://espressif.com/...",
        approved=True
    )
    index.add_component(ic1)
    print(f"✅ Added IC: {ic1.part_number}")
    
    # Test searches
    found = index.find_by_part_number("RC0603FR-0710KL")
    assert found is not None
    assert found.part_number == "RC0603FR-0710KL"
    print(f"✅ Find by part number: {found.part_number}")
    
    resistors = index.find_by_category("resistor")
    print(f"✅ Find by category 'resistor': {len(resistors)} found")
    
    approved = index.find_approved()
    print(f"✅ Find approved: {len(approved)} found")
    
    # Test save/load
    import os
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        from pathlib import Path
        index.save(Path(temp_file))
        print(f"✅ Saved index to {temp_file}")
        
        loaded = ComponentIndex(Path(temp_file))
        print(f"✅ Loaded index: {len(loaded.components)} components")
        
        assert len(loaded.components) == len(index.components)
        print("✅ Save/load verification passed")
        
    finally:
        os.unlink(temp_file)
    
    return True


def test_validators():
    """Test validators."""
    print("\n=== Testing Validators ===")
    
    circuit = CircuitIR("validator_test", "Validator Test")
    
    # Add nets FIRST (before power domain references them)
    vcc_net = Net(
        name="VCC_3V3",
        type=NetType.POWER,
        connections=[]
    )
    circuit.add_net(vcc_net)
    
    # Add power domain
    vcc = PowerDomain(
        name="VCC_3V3",
        voltage_nominal=3.3,
        voltage_min=3.0,
        voltage_max=3.6,
        current_max=1.0,
        nets=["VCC_3V3"]
    )
    circuit.add_power_domain(vcc)
    
    # Add component with power consumption
    mcu = Component(
        id="U1",
        type="mcu",
        value="ESP32",
        package="QFN-48",
        power_domain="VCC_3V3",
        power_consumption=0.5
    )
    circuit.add_component(mcu)
    
    # Test voltage domain validator
    validator = VoltageDomainValidator()
    result = validator.validate(circuit)
    
    if result.passed:
        print("✅ VoltageDomainValidator: PASSED")
    else:
        print("❌ VoltageDomainValidator: FAILED")
        for error in result.errors:
            print(f"   Error: {error}")
        return False
    
    # Test power budget validator
    validator = PowerBudgetValidator()
    result = validator.validate(circuit)
    
    if result.passed:
        print("✅ PowerBudgetValidator: PASSED")
        if result.warnings:
            print(f"   Warnings: {len(result.warnings)}")
    else:
        print("❌ PowerBudgetValidator: FAILED")
        for error in result.errors:
            print(f"   Error: {error}")
        return False
    
    # Test validation report generation
    results = validate_circuit(circuit)
    report = generate_validation_report(results)
    
    assert "Validation Report" in report
    print(f"✅ Generated validation report ({len(report)} chars)")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("PCB Module Manual Testing")
    print("=" * 60)
    
    tests = [
        ("Circuit IR", test_circuit_ir),
        ("Component Index", test_component_index),
        ("Validators", test_validators),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name}: FAILED with exception")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
