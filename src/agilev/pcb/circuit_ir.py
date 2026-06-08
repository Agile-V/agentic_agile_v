"""
Circuit Intermediate Representation (IR)

This module defines the core data structures for representing PCB schematics
in a format that is:
- Easy for AI agents to generate and manipulate
- Validatable against schemas
- Convertible to KiCad formats
- Independent of specific EDA tool formats

The IR is inspired by pcbGPT but adapted for Agile-V's evidence-based workflow.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PinType(Enum):
    """Electronic pin types."""
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER = "power"
    GROUND = "ground"
    NO_CONNECT = "no_connect"
    PASSIVE = "passive"


class NetType(Enum):
    """Types of electrical nets."""
    SIGNAL = "signal"
    POWER = "power"
    GROUND = "ground"
    CLOCK = "clock"
    RESET = "reset"
    ANALOG = "analog"


@dataclass
class Pin:
    """Represents a component pin."""
    number: str  # Pin number (e.g., "1", "A5")
    name: str  # Pin name (e.g., "VCC", "SCL", "GPIO0")
    type: PinType
    electrical_type: str  # From datasheet (input, output, power, etc.)
    
    # Optional attributes
    voltage: float | None = None  # Operating voltage
    current_max: float | None = None  # Maximum current (mA)
    description: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = {
            'number': self.number,
            'name': self.name,
            'type': self.type.value,
            'electrical_type': self.electrical_type
        }
        if self.voltage is not None:
            d['voltage'] = self.voltage
        if self.current_max is not None:
            d['current_max'] = self.current_max
        if self.description:
            d['description'] = self.description
        return d


@dataclass
class Component:
    """Represents an electronic component."""
    id: str  # Unique ID (e.g., "U1", "C1", "R1")
    type: str  # Component type (resistor, capacitor, IC, etc.)
    value: str | None = None  # Value (e.g., "10k", "100nF", "STM32F4")
    package: str | None = None  # Package (e.g., "0603", "SOIC-8", "QFN-32")
    manufacturer: str | None = None
    part_number: str | None = None
    datasheet_url: str | None = None
    description: str | None = None
    
    # Pins
    pins: list[Pin] = field(default_factory=list)
    
    # Power information (for validation)
    power_domain: str | None = None  # Which power domain this component uses
    power_consumption: float | None = None  # Power consumption in Watts
    
    # Attributes
    voltage_rating: float | None = None
    current_rating: float | None = None
    power_rating: float | None = None
    tolerance: str | None = None
    temperature_coefficient: str | None = None
    
    # Metadata
    footprint: str | None = None
    symbol: str | None = None
    alternate_parts: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = {
            'id': self.id,
            'type': self.type,
            'pins': [p.to_dict() for p in self.pins]
        }
        
        # Add optional fields if present
        optional_fields = [
            'value', 'package', 'manufacturer', 'part_number', 
            'datasheet_url', 'description', 'voltage_rating',
            'current_rating', 'power_rating', 'tolerance',
            'temperature_coefficient', 'footprint', 'symbol',
            'power_domain', 'power_consumption'
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                d[field_name] = value
        
        if self.alternate_parts:
            d['alternate_parts'] = self.alternate_parts
        
        return d
    
    def get_pin_by_name(self, name: str) -> Pin | None:
        """Get pin by name."""
        for pin in self.pins:
            if pin.name == name:
                return pin
        return None
    
    def get_pin_by_number(self, number: str) -> Pin | None:
        """Get pin by number."""
        for pin in self.pins:
            if pin.number == number:
                return pin
        return None


@dataclass
class Net:
    """Represents an electrical net (connection between pins)."""
    name: str  # Net name (e.g., "VCC", "GND", "SCL", "NET_001")
    type: NetType
    
    # Connected pins (list of tuples: (component_id, pin_number))
    connections: list[tuple[str, str]] = field(default_factory=list)
    
    # Net attributes
    voltage: float | None = None  # Operating voltage
    description: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = {
            'name': self.name,
            'type': self.type.value,
            'connections': [{'component': c, 'pin': p} for c, p in self.connections]
        }
        if self.voltage is not None:
            d['voltage'] = self.voltage
        if self.description:
            d['description'] = self.description
        return d
    
    def add_connection(self, component_id: str, pin_number: str):
        """Add a connection to this net."""
        self.connections.append((component_id, pin_number))


@dataclass
class PowerDomain:
    """Represents a voltage domain in the circuit."""
    name: str  # Domain name (e.g., "VCC_3V3", "5V", "1V8_CORE")
    voltage_nominal: float  # Nominal voltage (V)
    voltage_min: float  # Minimum voltage (V)
    voltage_max: float  # Maximum voltage (V)
    current_max: float  # Maximum current (A)
    
    # Connected nets
    nets: list[str] = field(default_factory=list)  # Net names in this domain
    
    # Optional source information
    source_component: str | None = None  # Component providing this voltage
    source_pin: str | None = None  # Pin providing voltage
    
    # Optional regulation specs
    tolerance_percent: float | None = None
    ripple_max_mv: float | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = {
            'name': self.name,
            'voltage_nominal': self.voltage_nominal,
            'voltage_min': self.voltage_min,
            'voltage_max': self.voltage_max,
            'current_max': self.current_max,
            'nets': self.nets
        }
        if self.source_component:
            d['source_component'] = self.source_component
        if self.source_pin:
            d['source_pin'] = self.source_pin
        if self.tolerance_percent is not None:
            d['tolerance_percent'] = self.tolerance_percent
        if self.ripple_max_mv is not None:
            d['ripple_max_mv'] = self.ripple_max_mv
        return d


@dataclass
class Interface:
    """Represents a communication or electrical interface."""
    name: str  # Interface name (e.g., "I2C1", "SPI_FLASH", "USB")
    type: str  # Interface type (i2c, spi, uart, usb, etc.)
    
    # Signals (net names)
    signals: dict[str, str] = field(default_factory=dict)
    # e.g., {"SCL": "I2C1_SCL", "SDA": "I2C1_SDA"}
    
    # Attributes
    voltage: float | None = None
    frequency: float | None = None  # Hz or bps
    description: str | None = None
    
    # Components using this interface
    master: str | None = None  # Component ID
    slaves: list[str] = field(default_factory=list)  # Component IDs
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = {
            'name': self.name,
            'type': self.type,
            'signals': self.signals
        }
        if self.voltage is not None:
            d['voltage'] = self.voltage
        if self.frequency is not None:
            d['frequency'] = self.frequency
        if self.description:
            d['description'] = self.description
        if self.master:
            d['master'] = self.master
        if self.slaves:
            d['slaves'] = self.slaves
        return d


@dataclass
class CircuitIR:
    """
    Circuit Intermediate Representation.
    
    This is the main data structure representing a complete PCB schematic.
    """
    # Metadata
    name: str
    version: str = "1.0"
    description: str = ""
    task_id: str | None = None
    candidate_id: str | None = None
    
    # Design elements
    components: list[Component] = field(default_factory=list)
    nets: list[Net] = field(default_factory=list)
    power_domains: list[PowerDomain] = field(default_factory=list)
    interfaces: list[Interface] = field(default_factory=list)
    
    # Design metadata
    created: str | None = None
    modified: str | None = None
    author: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert entire circuit to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'task_id': self.task_id,
            'candidate_id': self.candidate_id,
            'components': [c.to_dict() for c in self.components],
            'nets': [n.to_dict() for n in self.nets],
            'power_domains': [pd.to_dict() for pd in self.power_domains],
            'interfaces': [i.to_dict() for i in self.interfaces],
            'created': self.created,
            'modified': self.modified,
            'author': self.author
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, filepath: Path):
        """Save to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'CircuitIR':
        """Create CircuitIR from dictionary."""
        circuit = cls(
            name=data['name'],
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            task_id=data.get('task_id'),
            candidate_id=data.get('candidate_id'),
            created=data.get('created'),
            modified=data.get('modified'),
            author=data.get('author')
        )
        
        # Parse components
        for comp_data in data.get('components', []):
            pins = [
                Pin(
                    number=p['number'],
                    name=p['name'],
                    type=PinType(p['type']),
                    electrical_type=p['electrical_type'],
                    voltage=p.get('voltage'),
                    current_max=p.get('current_max'),
                    description=p.get('description')
                )
                for p in comp_data.get('pins', [])
            ]
            
            component = Component(
                id=comp_data['id'],
                type=comp_data['type'],
                value=comp_data.get('value'),
                package=comp_data.get('package'),
                manufacturer=comp_data.get('manufacturer'),
                part_number=comp_data.get('part_number'),
                datasheet_url=comp_data.get('datasheet_url'),
                description=comp_data.get('description'),
                pins=pins,
                voltage_rating=comp_data.get('voltage_rating'),
                current_rating=comp_data.get('current_rating'),
                power_rating=comp_data.get('power_rating'),
                tolerance=comp_data.get('tolerance'),
                temperature_coefficient=comp_data.get('temperature_coefficient'),
                footprint=comp_data.get('footprint'),
                symbol=comp_data.get('symbol'),
                alternate_parts=comp_data.get('alternate_parts', [])
            )
            circuit.components.append(component)
        
        # Parse nets
        for net_data in data.get('nets', []):
            connections = [
                (conn['component'], conn['pin'])
                for conn in net_data.get('connections', [])
            ]
            net = Net(
                name=net_data['name'],
                type=NetType(net_data['type']),
                connections=connections,
                voltage=net_data.get('voltage'),
                description=net_data.get('description')
            )
            circuit.nets.append(net)
        
        # Parse power domains
        for pd_data in data.get('power_domains', []):
            pd = PowerDomain(
                name=pd_data['name'],
                voltage_nominal=pd_data.get('voltage_nominal', pd_data.get('voltage', 3.3)),  # Support both old and new
                voltage_min=pd_data.get('voltage_min', 0),
                voltage_max=pd_data.get('voltage_max', 5.0),
                current_max=pd_data.get('current_max', 1.0),
                nets=pd_data.get('nets', []),
                source_component=pd_data.get('source_component'),
                source_pin=pd_data.get('source_pin'),
                tolerance_percent=pd_data.get('tolerance_percent'),
                ripple_max_mv=pd_data.get('ripple_max_mv')
            )
            circuit.power_domains.append(pd)
        
        # Parse interfaces
        for if_data in data.get('interfaces', []):
            interface = Interface(
                name=if_data['name'],
                type=if_data['type'],
                signals=if_data.get('signals', {}),
                voltage=if_data.get('voltage'),
                frequency=if_data.get('frequency'),
                description=if_data.get('description'),
                master=if_data.get('master'),
                slaves=if_data.get('slaves', [])
            )
            circuit.interfaces.append(interface)
        
        return circuit
    
    @classmethod
    def load(cls, filepath: Path) -> 'CircuitIR':
        """Load from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    # Add/modify methods
    
    def add_component(self, component: Component) -> None:
        """Add a component to the circuit."""
        self.components.append(component)
    
    def add_net(self, net: Net) -> None:
        """Add a net to the circuit."""
        self.nets.append(net)
    
    def add_power_domain(self, power_domain: PowerDomain) -> None:
        """Add a power domain to the circuit."""
        self.power_domains.append(power_domain)
    
    def add_interface(self, interface: Interface) -> None:
        """Add an interface to the circuit."""
        self.interfaces.append(interface)
    
    # Utility methods
    
    def get_component(self, component_id: str) -> Component | None:
        """Get component by ID."""
        for comp in self.components:
            if comp.id == component_id:
                return comp
        return None
    
    def get_net(self, net_name: str) -> Net | None:
        """Get net by name."""
        for net in self.nets:
            if net.name == net_name:
                return net
        return None
    
    def get_power_domain(self, domain_name: str) -> PowerDomain | None:
        """Get power domain by name."""
        for pd in self.power_domains:
            if pd.name == domain_name:
                return pd
        return None
    
    def validate_connections(self) -> list[str]:
        """
        Validate circuit connections.
        
        Returns list of validation errors.
        """
        errors = []
        
        # Check that all net connections reference valid components and pins
        for net in self.nets:
            for comp_id, pin_number in net.connections:
                comp = self.get_component(comp_id)
                if comp is None:
                    errors.append(f"Net '{net.name}' references non-existent component '{comp_id}'")
                else:
                    # Check if component has get_pin_by_number method
                    pin_found = False
                    for pin in comp.pins:
                        if pin.number == pin_number:
                            pin_found = True
                            break
                    if not pin_found:
                        errors.append(f"Net '{net.name}' references non-existent pin '{pin_number}' on component '{comp_id}'")
        
        # Check that power domains reference valid nets
        for pd in self.power_domains:
            for net_name in pd.nets:
                if not self.get_net(net_name):
                    errors.append(f"Power domain '{pd.name}' references non-existent net '{net_name}'")
        
        # Check that interfaces reference valid components and nets
        for interface in self.interfaces:
            if interface.master and not self.get_component(interface.master):
                errors.append(f"Interface '{interface.name}' references non-existent master '{interface.master}'")
            
            for slave_id in interface.slaves:
                if not self.get_component(slave_id):
                    errors.append(f"Interface '{interface.name}' references non-existent slave '{slave_id}'")
            
            for signal_name, net_name in interface.signals.items():
                if not self.get_net(net_name):
                    errors.append(f"Interface '{interface.name}' signal '{signal_name}' references non-existent net '{net_name}'")
        
        return errors
    
    def get_stats(self) -> dict[str, Any]:
        """Get circuit statistics."""
        return {
            'components': len(self.components),
            'nets': len(self.nets),
            'power_domains': len(self.power_domains),
            'interfaces': len(self.interfaces),
            'total_pins': sum(len(c.pins) for c in self.components),
            'total_connections': sum(len(n.connections) for n in self.nets)
        }


# Helper functions for creating common components

def create_resistor(ref: str, value: str, package: str = "0603") -> Component:
    """Create a resistor component."""
    return Component(
        id=ref,
        type="resistor",
        value=value,
        package=package,
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive")
        ]
    )


def create_capacitor(ref: str, value: str, package: str = "0603", voltage_rating: float = None) -> Component:
    """Create a capacitor component."""
    return Component(
        id=ref,
        type="capacitor",
        value=value,
        package=package,
        voltage_rating=voltage_rating,
        pins=[
            Pin(number="1", name="1", type=PinType.PASSIVE, electrical_type="passive"),
            Pin(number="2", name="2", type=PinType.PASSIVE, electrical_type="passive")
        ]
    )


def create_power_net(name: str, voltage: float) -> Net:
    """Create a power net."""
    return Net(name=name, type=NetType.POWER, voltage=voltage)


def create_ground_net(name: str = "GND") -> Net:
    """Create a ground net."""
    return Net(name=name, type=NetType.GROUND, voltage=0.0)
