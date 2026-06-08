#!/usr/bin/env python3
"""
Real-world PCB example: LED blinker circuit with ESP32

This demonstrates:
1. Creating a complete circuit in Circuit IR
2. Validating power domains
3. Validating power budget
4. Generating validation report
5. Saving to JSON
"""

import sys

sys.path.insert(0, 'src')

from pathlib import Path

from agilev.pcb.circuit_ir import CircuitIR, Component, Net, NetType, Pin, PinType, PowerDomain
from agilev.pcb.validators import generate_validation_report, validate_circuit


def create_led_blinker_circuit():
    """Create an ESP32-based LED blinker circuit."""
    
    # Initialize circuit
    circuit = CircuitIR(
        name="led_blinker",
        description="ESP32-C3 LED Blinker with USB-C Power",
        version="1.0"
    )
    
    print("🔧 Creating LED Blinker Circuit...")
    
    # Define power domain (3.3V from USB)
    vcc_3v3 = PowerDomain(
        name="VCC_3V3",
        voltage_nominal=3.3,
        voltage_min=3.0,
        voltage_max=3.6,
        current_max=0.5,  # 500mA from USB
        nets=["VCC_3V3"],
        source_component="U2"  # LDO regulator
    )
    circuit.add_power_domain(vcc_3v3)
    print("  ✅ Added 3.3V power domain")
    
    # Add ESP32-C3 module
    esp32 = Component(
        id="U1",
        type="mcu",
        value="ESP32-C3-MINI-1-N4",
        package="SMD-53",
        manufacturer="Espressif",
        part_number="ESP32-C3-MINI-1-N4",
        power_domain="VCC_3V3",
        power_consumption=0.35,  # 350mA max
        pins=[
            Pin(number="1", name="GND", type=PinType.GROUND, electrical_type="ground"),
            Pin(number="2", name="3V3", type=PinType.POWER, electrical_type="power_input"),
            Pin(number="8", name="GPIO0", type=PinType.BIDIRECTIONAL, electrical_type="bidirectional"),
            Pin(number="9", name="GPIO1", type=PinType.BIDIRECTIONAL, electrical_type="bidirectional"),
        ]
    )
    circuit.add_component(esp32)
    print("  ✅ Added ESP32-C3 module")
    
    # Add LDO regulator (5V USB → 3.3V)
    ldo = Component(
        id="U2",
        type="regulator",
        value="AP2112K-3.3",
        package="SOT-23-5",
        manufacturer="Diodes Inc",
        part_number="AP2112K-3.3TRG1",
        current_rating=0.6,  # 600mA output
        pins=[
            Pin(number="1", name="VIN", type=PinType.POWER, electrical_type="power_input"),
            Pin(number="2", name="GND", type=PinType.GROUND, electrical_type="ground"),
            Pin(number="3", name="EN", type=PinType.INPUT, electrical_type="input"),
            Pin(number="5", name="VOUT", type=PinType.POWER, electrical_type="power_output"),
        ]
    )
    circuit.add_component(ldo)
    print("  ✅ Added 3.3V LDO regulator")
    
    # Add status LED
    led1 = Component(
        id="D1",
        type="led",
        value="Red",
        package="0603",
        manufacturer="Wurth",
        part_number="150060RS75000",
        pins=[
            Pin(number="1", name="A", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="K", type=PinType.PASSIVE, electrical_type="passive"),
        ]
    )
    circuit.add_component(led1)
    print("  ✅ Added status LED")
    
    # Add current limiting resistor for LED
    r1 = Component(
        id="R1",
        type="resistor",
        value="330R",
        package="0603",
        tolerance="1%",
        power_rating=0.1,
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
        ]
    )
    circuit.add_component(r1)
    print("  ✅ Added LED resistor")
    
    # Add decoupling capacitors
    c1 = Component(
        id="C1",
        type="capacitor",
        value="100nF",
        package="0603",
        voltage_rating=50,
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
        ]
    )
    circuit.add_component(c1)
    
    c2 = Component(
        id="C2",
        type="capacitor",
        value="10uF",
        package="0805",
        voltage_rating=16,
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
        ]
    )
    circuit.add_component(c2)
    print("  ✅ Added decoupling capacitors")
    
    # Create nets
    # Power nets
    vcc_net = Net(
        name="VCC_3V3",
        type=NetType.POWER,
        voltage=3.3,
        connections=[
            ("U1", "2"),   # ESP32 VCC
            ("U2", "5"),   # LDO output
            ("C1", "1"),   # Cap 1
            ("C2", "1"),   # Cap 2
        ]
    )
    circuit.add_net(vcc_net)
    
    gnd_net = Net(
        name="GND",
        type=NetType.GROUND,
        voltage=0.0,
        connections=[
            ("U1", "1"),   # ESP32 GND
            ("U2", "2"),   # LDO GND
            ("C1", "2"),   # Cap 1
            ("C2", "2"),   # Cap 2
            ("D1", "2"),   # LED cathode
        ]
    )
    circuit.add_net(gnd_net)
    
    # GPIO signal to LED
    gpio0_net = Net(
        name="GPIO0_LED",
        type=NetType.SIGNAL,
        connections=[
            ("U1", "8"),   # ESP32 GPIO0
            ("R1", "1"),   # Resistor
        ]
    )
    circuit.add_net(gpio0_net)
    
    led_anode_net = Net(
        name="LED_ANODE",
        type=NetType.SIGNAL,
        connections=[
            ("R1", "2"),   # Resistor
            ("D1", "1"),   # LED anode
        ]
    )
    circuit.add_net(led_anode_net)
    
    print("  ✅ Added all nets (4 nets, 13 connections)")
    
    return circuit


def main():
    """Create and validate the circuit."""
    
    print("=" * 60)
    print("LED Blinker Circuit Example")
    print("=" * 60)
    print()
    
    # Create circuit
    circuit = create_led_blinker_circuit()
    
    print()
    print("📊 Circuit Statistics:")
    stats = circuit.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Validate connections
    print()
    print("🔍 Validating Connections...")
    errors = circuit.validate_connections()
    
    if errors:
        print("  ❌ Validation errors found:")
        for error in errors:
            print(f"    - {error}")
        return 1
    else:
        print("  ✅ All connections valid")
    
    # Run semantic validators
    print()
    print("🔍 Running Semantic Validators...")
    results = validate_circuit(circuit)
    
    # Generate report
    report = generate_validation_report(results)
    print()
    print(report)
    
    # Save circuit
    output_file = Path("examples/pcb/led_blinker_circuit.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    circuit.save(output_file)
    
    print()
    print(f"💾 Circuit saved to: {output_file}")
    
    # Verify we can load it back
    loaded = CircuitIR.load(output_file)
    print(f"✅ Verified: Loaded circuit '{loaded.name}' with {len(loaded.components)} components")
    
    print()
    print("=" * 60)
    print("✅ SUCCESS: Complete LED blinker circuit created and validated!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review circuit JSON: examples/pcb/led_blinker_circuit.json")
    print("  2. Create KiCad schematic using this as reference")
    print("  3. Run: agilev pcb validate --task <task-id>")
    print("  4. Generate evidence bundle for manufacturing approval")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
