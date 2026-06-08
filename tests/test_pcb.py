"""Tests for PCB development modules."""

from agilev.pcb.circuit_ir import (
    CircuitIR,
    Component,
    Interface,
    Net,
    NetType,
    Pin,
    PinType,
    PowerDomain,
)
from agilev.pcb.component_index import (
    ComponentEntry,
    ComponentIndex,
    create_capacitor_entry,
    create_resistor_entry,
)
from agilev.pcb.validators import (
    I2CInterfaceValidator,
    PowerBudgetValidator,
    VoltageDomainValidator,
)


class TestCircuitIR:
    """Test Circuit IR functionality."""

    def test_create_empty_circuit(self):
        """Test creating an empty circuit."""
        circuit = CircuitIR(name="test_circuit", description="Test Circuit")
        assert circuit.name == "test_circuit"
        assert circuit.description == "Test Circuit"
        assert len(circuit.components) == 0
        assert len(circuit.nets) == 0

    def test_add_component(self):
        """Test adding a component."""
        circuit = CircuitIR(name="test", description="Test")

        comp = Component(
            id="R1",
            type="resistor",
            value="10k",
            package="0603",
            pins=[
                Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
                Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
            ],
        )

        circuit.add_component(comp)
        assert len(circuit.components) == 1
        assert circuit.get_component("R1") == comp

    def test_add_net(self):
        """Test adding a net."""
        circuit = CircuitIR(name="test", description="Test")

        # Add components first
        r1 = Component(
            id="R1",
            type="resistor",
            value="10k",
            package="0603",
            pins=[
                Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
                Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
            ],
        )

        r2 = Component(
            id="R2",
            type="resistor",
            value="10k",
            package="0603",
            pins=[
                Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
                Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
            ],
        )

        circuit.add_component(r1)
        circuit.add_component(r2)

        # Add net connecting them
        net = Net(name="VCC", type=NetType.POWER, connections=[("R1", "1"), ("R2", "1")])

        circuit.add_net(net)
        assert len(circuit.nets) == 1
        assert circuit.get_net("VCC") == net

    def test_validate_connections_success(self):
        """Test connection validation with valid connections."""
        circuit = CircuitIR(name="test", description="Test")

        comp = Component(
            id="R1",
            type="resistor",
            value="10k",
            package="0603",
            pins=[
                Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
                Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
            ],
        )

        circuit.add_component(comp)

        net = Net(name="VCC", type=NetType.POWER, connections=[("R1", "1")])

        circuit.add_net(net)

        errors = circuit.validate_connections()
        assert len(errors) == 0

    def test_validate_connections_missing_component(self):
        """Test connection validation with missing component."""
        circuit = CircuitIR(name="test", description="Test")

        net = Net(name="VCC", type=NetType.POWER, connections=[("R1", "1")])

        circuit.add_net(net)

        errors = circuit.validate_connections()
        assert len(errors) == 1
        assert "R1" in errors[0]

    def test_validate_connections_missing_pin(self):
        """Test connection validation with missing pin."""
        circuit = CircuitIR(name="test", description="Test")

        comp = Component(
            id="R1",
            type="resistor",
            value="10k",
            package="0603",
            pins=[Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive")],
        )

        circuit.add_component(comp)

        net = Net(name="VCC", type=NetType.POWER, connections=[("R1", "99")])

        circuit.add_net(net)

        errors = circuit.validate_connections()
        assert len(errors) == 1
        assert "99" in errors[0]  # Pin number should be in error message

    def test_save_and_load(self, tmp_path):
        """Test saving and loading circuit IR."""
        circuit = CircuitIR(name="test", description="Test Circuit")

        comp = Component(
            id="R1",
            type="resistor",
            value="10k",
            package="0603",
            pins=[
                Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
                Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive"),
            ],
        )

        circuit.add_component(comp)

        # Save
        filepath = tmp_path / "circuit.json"
        circuit.save(filepath)

        assert filepath.exists()

        # Load
        loaded = CircuitIR.load(filepath)

        assert loaded.name == circuit.name
        assert loaded.description == circuit.description
        assert len(loaded.components) == 1
        assert loaded.get_component("R1") is not None
        assert loaded.get_component("R1").value == "10k"


class TestComponentIndex:
    """Test component index functionality."""

    def test_create_empty_index(self):
        """Test creating an empty component index."""
        index = ComponentIndex()
        assert len(index.components) == 0

    def test_add_component(self):
        """Test adding a component to index."""
        index = ComponentIndex()

        comp = ComponentEntry(
            id="resistor_10k",
            part_number="RC0603FR-0710KL",
            manufacturer="Yageo",
            description="Resistor 10K 1% 0.1W 0603",
            category="resistor",
            package="0603",
            approved=True,
        )

        index.add_component(comp)
        assert len(index.components) == 1
        assert index.get_component("resistor_10k") == comp

    def test_find_by_part_number(self):
        """Test finding component by part number."""
        index = ComponentIndex()

        comp = ComponentEntry(
            id="resistor_10k",
            part_number="RC0603FR-0710KL",
            manufacturer="Yageo",
            description="Resistor 10K 1% 0.1W 0603",
            category="resistor",
        )

        index.add_component(comp)

        found = index.find_by_part_number("RC0603FR-0710KL")
        assert found == comp

    def test_find_by_category(self):
        """Test finding components by category."""
        index = ComponentIndex()

        r1 = create_resistor_entry("R1", "10k", approved=True)
        r2 = create_resistor_entry("R2", "1k", approved=True)
        c1 = create_capacitor_entry("C1", "100n", "50V", approved=True)

        index.add_component(r1)
        index.add_component(r2)
        index.add_component(c1)

        resistors = index.find_by_category("resistor")
        assert len(resistors) == 2

        capacitors = index.find_by_category("capacitor")
        assert len(capacitors) == 1

    def test_find_approved(self):
        """Test finding approved components."""
        index = ComponentIndex()

        r1 = create_resistor_entry("R1", "10k", approved=True)
        r2 = create_resistor_entry("R2", "1k", approved=False)

        index.add_component(r1)
        index.add_component(r2)

        approved = index.find_approved()
        assert len(approved) == 1
        assert approved[0].id == r1.id

    def test_save_and_load(self, tmp_path):
        """Test saving and loading component index."""
        index = ComponentIndex()

        comp = create_resistor_entry("R1", "10k", approved=True)
        index.add_component(comp)

        # Save
        filepath = tmp_path / "index.json"
        index.save(filepath)

        assert filepath.exists()

        # Load
        loaded = ComponentIndex(filepath)

        assert len(loaded.components) == 1
        assert "resistor_10k_0603" in loaded.components


class TestValidators:
    """Test PCB validators."""

    def test_voltage_domain_validator_success(self):
        """Test voltage domain validator with valid design."""
        circuit = CircuitIR(name="test", description="Test")

        # Add VCC net
        vcc_net = Net(name="VCC", type=NetType.POWER)
        circuit.add_net(vcc_net)

        # Add power domain
        vcc = PowerDomain(
            name="VCC",
            voltage_nominal=3.3,
            voltage_min=3.0,
            voltage_max=3.6,
            current_max=1.0,
            nets=["VCC"],
        )

        circuit.add_power_domain(vcc)

        # Add components
        ldo = Component(
            id="U1", type="ic", value="LDO_3V3", package="SOT-23-5", power_domain="VCC", pins=[]
        )

        circuit.add_component(ldo)

        # Validate
        validator = VoltageDomainValidator()
        result = validator.validate(circuit)

        assert result.passed
        assert len(result.errors) == 0

    def test_voltage_domain_validator_missing_domain(self):
        """Test voltage domain validator with missing net."""
        circuit = CircuitIR(name="test", description="Test")

        # Add power domain that references non-existent net
        vcc = PowerDomain(
            name="VCC",
            voltage_nominal=3.3,
            voltage_min=3.0,
            voltage_max=3.6,
            current_max=1.0,
            nets=["VCC"],  # This net doesn't exist
        )

        circuit.add_power_domain(vcc)

        # Validate
        validator = VoltageDomainValidator()
        result = validator.validate(circuit)

        assert not result.passed
        assert len(result.errors) > 0

    def test_power_budget_validator(self):
        """Test power budget validator."""
        circuit = CircuitIR(name="test", description="Test")

        # Add power domain
        vcc = PowerDomain(
            name="VCC",
            voltage_nominal=3.3,
            voltage_min=3.0,
            voltage_max=3.6,
            current_max=1.0,  # 3.3W max
            nets=["VCC"],
        )

        circuit.add_power_domain(vcc)

        # Add components with high power consumption (> 80% of capacity)
        ic1 = Component(
            id="U1",
            type="ic",
            value="MCU",
            package="QFN-32",
            power_domain="VCC",
            power_consumption=1.5,  # Higher consumption
            pins=[],
        )

        ic2 = Component(
            id="U2",
            type="ic",
            value="Sensor",
            package="SOIC-8",
            power_domain="VCC",
            power_consumption=1.3,  # Higher consumption
            pins=[],
        )

        circuit.add_component(ic1)
        circuit.add_component(ic2)

        # Validate - total is 2.8W out of 3.3W max (85% utilization, < 20% margin)
        validator = PowerBudgetValidator()
        result = validator.validate(circuit)

        assert result.passed  # Not over budget
        assert len(result.errors) == 0
        # Should have warning about insufficient margin
        assert len(result.warnings) > 0

    def test_i2c_interface_validator(self):
        """Test I2C interface validator."""
        circuit = CircuitIR(name="test", description="Test")

        # Add I2C interface
        i2c = Interface(
            name="I2C0",
            type="i2c",
            signals={"SDA": "I2C0_SDA", "SCL": "I2C0_SCL"},
            voltage=3.3,
            frequency=400000,
        )

        circuit.add_interface(i2c)

        # Add master
        master = Component(
            id="U1",
            type="ic",
            value="MCU",
            package="QFN-32",
            pins=[
                Pin(
                    number="10",
                    name="SDA",
                    type=PinType.BIDIRECTIONAL,
                    electrical_type="bidirectional",
                ),
                Pin(number="11", name="SCL", type=PinType.OUTPUT, electrical_type="output"),
            ],
        )

        circuit.add_component(master)

        # Add nets
        circuit.add_net(Net(name="I2C0_SDA", type=NetType.SIGNAL, connections=[("U1", "10")]))
        circuit.add_net(Net(name="I2C0_SCL", type=NetType.SIGNAL, connections=[("U1", "11")]))

        # Validate
        validator = I2CInterfaceValidator()
        result = validator.validate(circuit, i2c)

        # Should warn about missing pullups
        assert len(result.warnings) > 0
