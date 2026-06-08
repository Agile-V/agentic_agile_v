"""
PCB to firmware export utilities.

Exports hardware-firmware contract data from PCB circuit IR.
"""

from typing import Any

from agilev.pcb.circuit_ir import Circuit, Component, Interface, Pin


class PCBFirmwareExporter:
    """Exports PCB circuit data to firmware contract format."""

    def __init__(self, circuit: Circuit):
        """Initialize exporter with circuit.

        Args:
            circuit: Circuit IR instance
        """
        self.circuit = circuit

    def export_hardware_firmware_contract(
        self,
        contract_id: str,
        board_name: str,
        pcb_revision: str,
        pcb_task_id: str,
        pcb_candidate_id: str,
    ) -> dict[str, Any]:
        """Export hardware-firmware contract from circuit.

        Args:
            contract_id: Contract identifier (e.g., HFC-001)
            board_name: Board name
            pcb_revision: PCB revision (e.g., rev_a)
            pcb_task_id: Source PCB task ID
            pcb_candidate_id: Source PCB candidate ID

        Returns:
            Hardware-firmware contract dictionary
        """
        contract = {
            "contract_id": contract_id,
            "board": board_name,
            "pcb_revision": pcb_revision,
            "source_pcb_task": pcb_task_id,
            "source_pcb_candidate": pcb_candidate_id,
        }

        # Export MCU
        mcu = self._export_mcu()
        if mcu:
            contract["mcu"] = mcu

        # Export interfaces
        interfaces = self._export_interfaces()
        if interfaces:
            contract["interfaces"] = interfaces

        # Export power
        power = self._export_power()
        if power:
            contract["power"] = power

        return contract

    def _export_mcu(self) -> dict[str, Any] | None:
        """Export MCU configuration.

        Returns:
            MCU configuration dictionary or None
        """
        # Find MCU component
        mcu_component = None
        for comp in self.circuit.components.values():
            # Look for component with MCU or microcontroller in name/type
            if "mcu" in comp.id.lower() or "mcu" in comp.part_number.lower():
                mcu_component = comp
                break

        if not mcu_component:
            return None

        mcu = {
            "part_number": mcu_component.part_number,
            "package": mcu_component.package,
        }

        # Try to determine voltage domain from power nets
        vdd_net = None
        for pin in mcu_component.pins.values():
            if "vdd" in pin.name.lower() or "vcc" in pin.name.lower():
                vdd_net = self.circuit.nets.get(pin.net_id)
                break

        if vdd_net:
            # Try to find associated power domain
            for pd in self.circuit.power_domains.values():
                if vdd_net.id in [n.id for n in pd.nets]:
                    mcu["voltage_domain"] = pd.name
                    break

        return mcu

    def _export_interfaces(self) -> dict[str, Any]:
        """Export interface configurations (I2C, SPI, UART, ADC, GPIO).

        Returns:
            Interfaces dictionary
        """
        interfaces: dict[str, Any] = {}

        # Export I2C interfaces
        i2c_interfaces = self._export_i2c()
        if i2c_interfaces:
            interfaces["i2c"] = i2c_interfaces

        # Export SPI interfaces
        spi_interfaces = self._export_spi()
        if spi_interfaces:
            interfaces["spi"] = spi_interfaces

        # Export UART interfaces
        uart_interfaces = self._export_uart()
        if uart_interfaces:
            interfaces["uart"] = uart_interfaces

        # Export ADC channels
        adc_channels = self._export_adc()
        if adc_channels:
            interfaces["adc"] = adc_channels

        # Export GPIO pins
        gpio_pins = self._export_gpio()
        if gpio_pins:
            interfaces["gpio"] = gpio_pins

        return interfaces

    def _export_i2c(self) -> list[dict[str, Any]]:
        """Export I2C interfaces.

        Returns:
            List of I2C interface dictionaries
        """
        i2c_list = []

        # Find I2C interfaces in circuit
        for interface in self.circuit.interfaces.values():
            if interface.type == "i2c":
                i2c_dict = {
                    "id": interface.id,
                }

                # Find SDA and SCL pins
                for signal_name, net_id in interface.signals.items():
                    net = self.circuit.nets.get(net_id)
                    if not net:
                        continue

                    # Find MCU pin connected to this net
                    mcu_pin = self._find_mcu_pin_on_net(net_id)
                    if mcu_pin:
                        pin_config = {
                            "mcu_pin": mcu_pin.name,
                            "net": net.name,
                        }

                        if "sda" in signal_name.lower():
                            i2c_dict["sda"] = pin_config
                        elif "scl" in signal_name.lower():
                            i2c_dict["scl"] = pin_config

                # Find devices on this bus
                devices = []
                for comp in self.circuit.components.values():
                    # Check if component is connected to I2C nets
                    if self._is_component_on_i2c_bus(comp, interface):
                        device = {
                            "name": comp.id,
                            "part_number": comp.part_number,
                        }
                        # TODO: Extract I2C address from component properties
                        devices.append(device)

                if devices:
                    i2c_dict["devices"] = devices

                i2c_list.append(i2c_dict)

        return i2c_list

    def _export_spi(self) -> list[dict[str, Any]]:
        """Export SPI interfaces.

        Returns:
            List of SPI interface dictionaries
        """
        spi_list = []

        for interface in self.circuit.interfaces.values():
            if interface.type == "spi":
                spi_dict = {
                    "id": interface.id,
                }

                # Map signals to pins
                for signal_name, net_id in interface.signals.items():
                    mcu_pin = self._find_mcu_pin_on_net(net_id)
                    net = self.circuit.nets.get(net_id)

                    if mcu_pin and net:
                        pin_config = {
                            "mcu_pin": mcu_pin.name,
                            "net": net.name,
                        }

                        if "sck" in signal_name.lower() or "clk" in signal_name.lower():
                            spi_dict["sck"] = pin_config
                        elif "miso" in signal_name.lower():
                            spi_dict["miso"] = pin_config
                        elif "mosi" in signal_name.lower():
                            spi_dict["mosi"] = pin_config

                spi_list.append(spi_dict)

        return spi_list

    def _export_uart(self) -> list[dict[str, Any]]:
        """Export UART interfaces.

        Returns:
            List of UART interface dictionaries
        """
        uart_list = []

        for interface in self.circuit.interfaces.values():
            if interface.type == "uart":
                uart_dict = {
                    "id": interface.id,
                }

                for signal_name, net_id in interface.signals.items():
                    mcu_pin = self._find_mcu_pin_on_net(net_id)
                    net = self.circuit.nets.get(net_id)

                    if mcu_pin and net:
                        pin_config = {
                            "mcu_pin": mcu_pin.name,
                            "net": net.name,
                        }

                        if "tx" in signal_name.lower():
                            uart_dict["tx"] = pin_config
                        elif "rx" in signal_name.lower():
                            uart_dict["rx"] = pin_config

                uart_list.append(uart_dict)

        return uart_list

    def _export_adc(self) -> list[dict[str, Any]]:
        """Export ADC channels.

        Returns:
            List of ADC channel dictionaries
        """
        # TODO: Implement ADC export based on circuit IR
        return []

    def _export_gpio(self) -> list[dict[str, Any]]:
        """Export GPIO pins.

        Returns:
            List of GPIO pin dictionaries
        """
        # TODO: Implement GPIO export based on circuit IR
        return []

    def _export_power(self) -> dict[str, Any]:
        """Export power configuration.

        Returns:
            Power configuration dictionary
        """
        power = {}

        # Export power rails
        rails = []
        for pd in self.circuit.power_domains.values():
            rail = {
                "name": pd.name,
                "nominal_v": pd.nominal_voltage,
            }

            if pd.min_voltage is not None:
                rail["min_v"] = pd.min_voltage
            if pd.max_voltage is not None:
                rail["max_v"] = pd.max_voltage

            # Calculate tolerance if min/max are set
            if pd.min_voltage and pd.max_voltage:
                tolerance = ((pd.max_voltage - pd.min_voltage) / (2 * pd.nominal_voltage)) * 100
                rail["tolerance_percent"] = round(tolerance, 1)

            rails.append(rail)

        if rails:
            power["rails"] = rails

        return power

    def _find_mcu_pin_on_net(self, net_id: str) -> Pin | None:
        """Find MCU pin connected to a net.

        Args:
            net_id: Net identifier

        Returns:
            Pin instance or None
        """
        for comp in self.circuit.components.values():
            if "mcu" in comp.id.lower() or "mcu" in comp.part_number.lower():
                for pin in comp.pins.values():
                    if pin.net_id == net_id:
                        return pin
        return None

    def _is_component_on_i2c_bus(self, component: Component, i2c_interface: Interface) -> bool:
        """Check if component is connected to I2C bus.

        Args:
            component: Component to check
            i2c_interface: I2C interface

        Returns:
            True if component is on the bus
        """
        # Get I2C net IDs
        i2c_nets = set(i2c_interface.signals.values())

        # Check if any component pins are on I2C nets
        for pin in component.pins.values():
            if pin.net_id in i2c_nets:
                return True

        return False
