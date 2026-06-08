"""
Software API adapter for firmware communication.

Generates Python API classes from firmware-software contracts.
"""

from pathlib import Path

import yaml


class FirmwareAPIGenerator:
    """Generates Python API from firmware-software contract."""

    def __init__(self, contract_path: Path):
        """Initialize generator.

        Args:
            contract_path: Path to firmware-software contract
        """
        self.contract_path = contract_path
        with open(contract_path) as f:
            self.contract = yaml.safe_load(f)

    def generate_api_class(self) -> str:
        """Generate Python API class.

        Returns:
            Python source code for API class
        """
        contract_id = self.contract["contract_id"]
        _transport = self.contract.get("transport", "usb_cdc_serial")  # noqa: F841
        commands = self.contract.get("commands", [])
        error_codes = self.contract.get("error_codes", [])

        # Generate class header
        lines = [
            '"""',
            f"Firmware API for {contract_id}.",
            "",
            "Auto-generated from firmware-software contract.",
            "DO NOT EDIT MANUALLY.",
            '"""',
            "",
            "import json",
            "import time",
            "from typing import Any, Optional",
            "",
            "import serial",
            "",
            "",
        ]

        # Generate error codes enum
        if error_codes:
            lines.extend([
                "class FirmwareError(Exception):",
                '    """Firmware error."""',
                "",
                "    def __init__(self, code: str, message: str):",
                "        self.code = code",
                "        self.message = message",
                '        super().__init__(f"{code}: {message}")',
                "",
                "",
            ])

        # Generate API class
        class_name = contract_id.replace("-", "_").upper() + "_API"
        lines.extend([
            f"class {class_name}:",
            f'    """Firmware API client for {contract_id}."""',
            "",
            "    def __init__(self, port: str, baudrate: int = 115200):",
            '        """Initialize API client.',
            "",
            "        Args:",
            "            port: Serial port (e.g., /dev/ttyUSB0, COM3)",
            "            baudrate: Serial baudrate",
            '        """',
            "        self.port = port",
            "        self.baudrate = baudrate",
            "        self.serial: Optional[serial.Serial] = None",
            "",
            "    def connect(self) -> None:",
            '        """Connect to firmware."""',
            "        if self.serial and self.serial.is_open:",
            "            return",
            "",
            "        self.serial = serial.Serial(",
            "            port=self.port,",
            "            baudrate=self.baudrate,",
            "            timeout=1.0,",
            "        )",
            "        time.sleep(0.1)  # Allow connection to stabilize",
            "",
            "    def disconnect(self) -> None:",
            '        """Disconnect from firmware."""',
            "        if self.serial:",
            "            self.serial.close()",
            "            self.serial = None",
            "",
            "    def _send_command(self, command: str, params: dict[str, Any] = None)",
            "    -> dict[str, Any]:",
            '        """Send command to firmware.',
            "",
            "        Args:",
            "            command: Command name",
            "            params: Command parameters",
            "",
            "        Returns:",
            "            Response dictionary",
            "",
            "        Raises:",
            "            FirmwareError: If firmware returns error",
            "            RuntimeError: If communication fails",
            '        """',
            "        if not self.serial or not self.serial.is_open:",
            '            raise RuntimeError("Not connected")',
            "",
            "        # Build request",
            "        request = {",
            '            "command": command,',
            "        }",
            "        if params:",
            '            request["params"] = params',
            "",
            "        # Send request",
            "        request_json = json.dumps(request) + '\\n'",
            "        self.serial.write(request_json.encode())",
            "",
            "        # Read response",
            "        response_line = self.serial.readline().decode().strip()",
            "        if not response_line:",
            '            raise RuntimeError("No response from firmware")',
            "",
            "        response = json.loads(response_line)",
            "",
            "        # Check for errors",
            '        if "error" in response:',
            '            raise FirmwareError(',
            '                code=response["error"].get("code", "UNKNOWN"),',
            '                message=response["error"].get("message", "Unknown error"),',
            "            )",
            "",
            "        return response",
            "",
        ])

        # Generate command methods
        for cmd in commands:
            cmd_name = cmd["name"]
            request_fields = cmd.get("request", {}).get("fields", {})
            response_fields = cmd.get("response", {}).get("fields", {})

            # Generate method signature
            params = []
            for field_name, field_spec in request_fields.items():
                field_type = self._python_type(field_spec.get("type", "any"))
                params.append(f"{field_name}: {field_type}")

            param_str = ", ".join(params) if params else ""
            if param_str:
                param_str = ", " + param_str

            lines.extend([
                f"    def {cmd_name}(self{param_str}) -> dict[str, Any]:",
                f'        """Execute {cmd_name} command.',
                "",
            ])

            # Add parameter docs
            if request_fields:
                lines.append("        Args:")
                for field_name, field_spec in request_fields.items():
                    field_desc = field_spec.get("description", field_name)
                    lines.append(f"            {field_name}: {field_desc}")
                lines.append("")

            # Add return docs
            lines.extend([
                "        Returns:",
                "            Response dictionary with fields:",
            ])
            for field_name, field_spec in response_fields.items():
                field_type = field_spec.get("type", "any")
                field_desc = field_spec.get("description", "")
                lines.append(f"                {field_name} ({field_type}): {field_desc}")

            lines.extend([
                '        """',
            ])

            # Generate method body
            if request_fields:
                lines.append("        params = {")
                for field_name in request_fields:
                    lines.append(f'            "{field_name}": {field_name},')
                lines.append("        }")
                lines.append(f'        return self._send_command("{cmd_name}", params)')
            else:
                lines.append(f'        return self._send_command("{cmd_name}")')

            lines.append("")

        # Add context manager support
        lines.extend([
            "    def __enter__(self):",
            "        self.connect()",
            "        return self",
            "",
            "    def __exit__(self, exc_type, exc_val, exc_tb):",
            "        self.disconnect()",
            "",
        ])

        return "\n".join(lines)

    def _python_type(self, schema_type: str) -> str:
        """Convert schema type to Python type hint.

        Args:
            schema_type: Schema type name

        Returns:
            Python type hint
        """
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }
        return type_map.get(schema_type, "Any")

    def save_api(self, output_path: Path) -> None:
        """Save generated API to file.

        Args:
            output_path: Output Python file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        api_code = self.generate_api_class()
        with open(output_path, "w") as f:
            f.write(api_code)
