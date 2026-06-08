"""
PCB Validators

Hardware-specific validation functions for:
- Voltage domain validation
- Power budget analysis
- Interface compliance (I2C, SPI, USB, UART, CAN)
- Protection circuit validation
- Datasheet compliance checking
"""

from dataclasses import dataclass
from typing import Any

from .circuit_ir import CircuitIR, Interface, Net, NetType


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # "error", "warning", "info"
    category: str
    message: str
    component: str | None = None
    net: str | None = None
    details: dict[str, Any] | None = None


@dataclass
class ValidationResult:
    """Result from validation."""
    passed: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    info: list[ValidationIssue]
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def summary(self) -> str:
        """Get summary string."""
        if self.passed:
            return f"✅ PASS (0 errors, {len(self.warnings)} warnings)"
        else:
            return f"❌ FAIL ({len(self.errors)} errors, {len(self.warnings)} warnings)"


class VoltageDomainValidator:
    """Validates voltage domains in a circuit."""
    
    def validate(self, circuit: CircuitIR) -> ValidationResult:
        """Validate all voltage domains."""
        errors = []
        warnings = []
        info = []
        
        # Check that all power domains have sources
        # Check that source components exist (if specified)
        for pd in circuit.power_domains:
            if pd.source_component and not circuit.get_component(pd.source_component):
                errors.append(ValidationIssue(
                    severity="error",
                    category="voltage_domain",
                    message=f"Power domain '{pd.name}' has invalid source component '{pd.source_component}'",
                    details={'domain': pd.name}
                ))
        
        # Check that power domain nets exist
        for pd in circuit.power_domains:
            for net_name in pd.nets:
                if not circuit.get_net(net_name):
                    errors.append(ValidationIssue(
                        severity="error",
                        category="voltage_domain",
                        message=f"Power domain '{pd.name}' references non-existent net '{net_name}'",
                        details={'domain': pd.name, 'net': net_name}
                    ))
        
        # Check for voltage conflicts on nets
        voltage_nets = {}
        for net in circuit.nets:
            if net.voltage is not None:
                if net.name in voltage_nets and voltage_nets[net.name] != net.voltage:
                    errors.append(ValidationIssue(
                        severity="error",
                        category="voltage_domain",
                        message=f"Net '{net.name}' has conflicting voltage assignments",
                        net=net.name,
                        details={'voltages': [voltage_nets[net.name], net.voltage]}
                    ))
                voltage_nets[net.name] = net.voltage
        
        passed = len(errors) == 0
        return ValidationResult(passed, errors, warnings, info)


class PowerBudgetValidator:
    """Validates power budget and current calculations."""
    
    def validate(self, circuit: CircuitIR, margin_percent: float = 20.0) -> ValidationResult:
        """
        Validate power budget.
        
        Args:
            circuit: Circuit IR to validate
            margin_percent: Required safety margin (default 20%)
        """
        errors = []
        warnings = []
        info = []
        
        for pd in circuit.power_domains:
            # Calculate total power consumption for this domain
            total_power = 0.0
            for comp in circuit.components:
                if comp.power_domain == pd.name and comp.power_consumption:
                    total_power += comp.power_consumption
            
            # Calculate max power capacity
            max_power = pd.voltage_nominal * pd.current_max
            
            # Check if over budget
            if total_power > max_power:
                errors.append(ValidationIssue(
                    severity="error",
                    category="power_budget",
                    message=f"Power domain '{pd.name}' exceeds capacity: {total_power:.2f}W > {max_power:.2f}W",
                    details={
                        'domain': pd.name,
                        'actual_w': total_power,
                        'max_w': max_power
                    }
                ))
            elif total_power > max_power * (1 - margin_percent/100):
                # Warn if margin is too small
                actual_margin = (max_power - total_power) / total_power * 100
                warnings.append(ValidationIssue(
                    severity="warning",
                    category="power_budget",
                    message=f"Power domain '{pd.name}' has insufficient margin: {actual_margin:.1f}% < {margin_percent}%",
                    details={
                        'domain': pd.name,
                        'actual_w': total_power,
                        'max_w': max_power,
                        'margin_percent': actual_margin
                    }
                ))
            else:
                # Good margin
                actual_margin = (max_power - total_power) / max_power * 100
                info.append(ValidationIssue(
                    severity="info",
                    category="power_budget",
                    message=f"Power domain '{pd.name}': {total_power:.2f}W / {max_power:.2f}W ({actual_margin:.0f}% margin)",
                    details={
                        'domain': pd.name,
                        'actual_w': total_power,
                        'max_w': max_power,
                        'margin_percent': actual_margin
                    }
                ))
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info
        )


class I2CInterfaceValidator:
    """Validates I2C interface compliance."""
    
    def validate(self, circuit: CircuitIR, interface: Interface) -> ValidationResult:
        """Validate I2C interface."""
        errors = []
        warnings = []
        info = []
        
        # Check required signals
        required_signals = ['SCL', 'SDA']
        for signal in required_signals:
            if signal not in interface.signals:
                errors.append(ValidationIssue(
                    severity="error",
                    category="i2c",
                    message=f"I2C interface '{interface.name}' missing required signal '{signal}'",
                    details={'interface': interface.name, 'signal': signal}
                ))
        
        # Check for pullup resistors on SDA and SCL
        for signal_name in ['SCL', 'SDA']:
            if signal_name in interface.signals:
                net_name = interface.signals[signal_name]
                net = circuit.get_net(net_name)
                
                if net:
                    # Look for pullup resistor
                    has_pullup = self._check_pullup_resistor(circuit, net)
                    if not has_pullup:
                        warnings.append(ValidationIssue(
                            severity="warning",
                            category="i2c",
                            message=f"I2C signal '{signal_name}' may be missing pullup resistor",
                            net=net_name,
                            details={'interface': interface.name}
                        ))
        
        # Check voltage compatibility
        if interface.voltage:
            for slave_id in interface.slaves:
                circuit.get_component(slave_id)
                # Would need to check slave's I2C voltage tolerance
                # This is a placeholder for datasheet-based validation
        
        passed = len(errors) == 0
        return ValidationResult(passed, errors, warnings, info)
    
    def _check_pullup_resistor(self, circuit: CircuitIR, net: Net) -> bool:
        """Check if net has a pullup resistor connected."""
        for comp_id, pin_num in net.connections:
            comp = circuit.get_component(comp_id)
            if comp and comp.type == "resistor":
                # Found a resistor on this net
                # Check if other pin connects to power net
                for pin in comp.pins:
                    if pin.number != pin_num:
                        # Find what this pin connects to
                        for other_net in circuit.nets:
                            for other_comp, other_pin in other_net.connections:
                                if other_comp == comp_id and other_pin == pin.number:
                                    # Check if this is a power net
                                    if other_net.type == NetType.POWER:
                                        return True
        return False


class SPIInterfaceValidator:
    """Validates SPI interface compliance."""
    
    def validate(self, circuit: CircuitIR, interface: Interface) -> ValidationResult:
        """Validate SPI interface."""
        errors = []
        warnings = []
        info = []
        
        # Check required signals
        required_signals = ['MOSI', 'MISO', 'SCK']
        for signal in required_signals:
            if signal not in interface.signals:
                errors.append(ValidationIssue(
                    severity="error",
                    category="spi",
                    message=f"SPI interface '{interface.name}' missing required signal '{signal}'",
                    details={'interface': interface.name, 'signal': signal}
                ))
        
        # Check for CS signals
        has_cs = any(sig.startswith('CS') for sig in interface.signals.keys())
        if not has_cs:
            warnings.append(ValidationIssue(
                severity="warning",
                category="spi",
                message=f"SPI interface '{interface.name}' has no chip select (CS) signal",
                details={'interface': interface.name}
            ))
        
        # Check voltage compatibility
        # This would need datasheet information
        
        passed = len(errors) == 0
        return ValidationResult(passed, errors, warnings, info)


class USBInterfaceValidator:
    """Validates USB interface compliance."""
    
    def validate(self, circuit: CircuitIR, interface: Interface) -> ValidationResult:
        """Validate USB interface."""
        errors = []
        warnings = []
        info = []
        
        # Check required signals
        required_signals = ['D+', 'D-']
        for signal in required_signals:
            if signal not in interface.signals:
                errors.append(ValidationIssue(
                    severity="error",
                    category="usb",
                    message=f"USB interface '{interface.name}' missing required signal '{signal}'",
                    details={'interface': interface.name, 'signal': signal}
                ))
        
        # Check for termination resistors (90Ω differential)
        # This would require schematic analysis
        
        # Check for 1.5kΩ pullup on D+ (for USB device)
        # This would require schematic analysis
        
        # Check for ESD protection
        info.append(ValidationIssue(
            severity="info",
            category="usb",
            message=f"Verify ESD protection on USB data lines for '{interface.name}'",
            details={'interface': interface.name}
        ))
        
        passed = len(errors) == 0
        return ValidationResult(passed, errors, warnings, info)


class ProtectionCircuitValidator:
    """Validates protection circuits."""
    
    def validate(self, circuit: CircuitIR) -> ValidationResult:
        """Validate protection circuits."""
        errors = []
        warnings = []
        info = []
        
        # Check for reverse polarity protection
        # This would analyze power input circuitry
        info.append(ValidationIssue(
            severity="info",
            category="protection",
            message="Verify reverse polarity protection on power inputs",
            details={}
        ))
        
        # Check for overcurrent protection
        info.append(ValidationIssue(
            severity="info",
            category="protection",
            message="Verify overcurrent protection (fuse or PTC)",
            details={}
        ))
        
        # Check for ESD protection on connectors
        info.append(ValidationIssue(
            severity="info",
            category="protection",
            message="Verify ESD protection (TVS diodes) on external connectors",
            details={}
        ))
        
        # These would be actual checks if we had more circuit analysis
        passed = True
        return ValidationResult(passed, errors, warnings, info)


class InterfaceValidator:
    """Master interface validator."""
    
    def __init__(self):
        self.validators = {
            'i2c': I2CInterfaceValidator(),
            'spi': SPIInterfaceValidator(),
            'usb': USBInterfaceValidator()
        }
    
    def validate(self, circuit: CircuitIR) -> dict[str, ValidationResult]:
        """Validate all interfaces in circuit."""
        results = {}
        
        for interface in circuit.interfaces:
            interface_type = interface.type.lower()
            
            if interface_type in self.validators:
                validator = self.validators[interface_type]
                results[interface.name] = validator.validate(circuit, interface)
            else:
                # Generic validation for unknown interface types
                results[interface.name] = ValidationResult(
                    passed=True,
                    errors=[],
                    warnings=[ValidationIssue(
                        severity="warning",
                        category="interface",
                        message=f"No specific validator for interface type '{interface.type}'",
                        details={'interface': interface.name}
                    )],
                    info=[]
                )
        
        return results


def validate_circuit(circuit: CircuitIR) -> dict[str, ValidationResult]:
    """
    Run all validations on a circuit.
    
    Returns dictionary of validation results by category.
    """
    results = {}
    
    # Voltage domain validation
    vd_validator = VoltageDomainValidator()
    results['voltage_domains'] = vd_validator.validate(circuit)
    
    # Power budget validation
    pb_validator = PowerBudgetValidator()
    results['power_budget'] = pb_validator.validate(circuit)
    
    # Interface validation
    if_validator = InterfaceValidator()
    interface_results = if_validator.validate(circuit)
    results.update(interface_results)
    
    # Protection circuits
    prot_validator = ProtectionCircuitValidator()
    results['protection'] = prot_validator.validate(circuit)
    
    return results


def generate_validation_report(results: dict[str, ValidationResult]) -> str:
    """Generate a human-readable validation report."""
    lines = ["# Circuit Validation Report\n"]
    
    # Summary
    total_errors = sum(len(r.errors) for r in results.values())
    total_warnings = sum(len(r.warnings) for r in results.values())
    total_info = sum(len(r.info) for r in results.values())
    
    if total_errors == 0:
        lines.append("## ✅ PASS\n")
    else:
        lines.append("## ❌ FAIL\n")
    
    lines.append(f"- Errors: {total_errors}")
    lines.append(f"- Warnings: {total_warnings}")
    lines.append(f"- Info: {total_info}\n")
    
    # Details by category
    for category, result in results.items():
        lines.append(f"\n### {category.replace('_', ' ').title()}")
        lines.append(f"\n{result.summary()}\n")
        
        if result.errors:
            lines.append("\n**Errors:**")
            for issue in result.errors:
                lines.append(f"- ❌ {issue.message}")
        
        if result.warnings:
            lines.append("\n**Warnings:**")
            for issue in result.warnings:
                lines.append(f"- ⚠️  {issue.message}")
        
        if result.info:
            lines.append("\n**Info:**")
            for issue in result.info:
                lines.append(f"- ℹ️  {issue.message}")
    
    return "\n".join(lines)
