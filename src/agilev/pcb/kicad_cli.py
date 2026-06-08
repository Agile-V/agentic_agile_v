"""
KiCad CLI Integration

Provides Python wrappers around kicad-cli commands for:
- ERC (Electrical Rule Check)
- Netlist export
- BOM export
- PDF export
- DRC (Design Rule Check)
- Gerber export

Requires KiCad 8.0+ with kicad-cli installed.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


@dataclass
class ERCResult:
    """Result from Electrical Rule Check."""
    success: bool
    errors: int
    warnings: int
    output: str
    exit_code: int


@dataclass
class DRCResult:
    """Result from Design Rule Check."""
    success: bool
    errors: int
    warnings: int
    unconnected: int
    output: str
    exit_code: int


class KiCadCLI:
    """Wrapper for kicad-cli commands."""
    
    def __init__(self, kicad_cli_path: str = "kicad-cli"):
        """
        Initialize KiCad CLI wrapper.
        
        Args:
            kicad_cli_path: Path to kicad-cli executable
        """
        self.kicad_cli = kicad_cli_path
        self._verify_installation()
    
    def _verify_installation(self):
        """Verify kicad-cli is installed and accessible."""
        try:
            result = subprocess.run(
                [self.kicad_cli, "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError(f"kicad-cli not working: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                f"kicad-cli not found at '{self.kicad_cli}'. "
                "Please install KiCad 8.0+ or specify correct path."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("kicad-cli version check timed out")
    
    def run_erc(
        self,
        schematic_path: Path,
        output_path: Optional[Path] = None
    ) -> ERCResult:
        """
        Run Electrical Rule Check on schematic.
        
        Args:
            schematic_path: Path to .kicad_sch file
            output_path: Path for ERC report (optional)
            
        Returns:
            ERCResult with errors, warnings, and output
        """
        if not schematic_path.exists():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        
        cmd = [self.kicad_cli, "sch", "erc"]
        
        if output_path:
            cmd.extend(["--output", str(output_path)])
        
        cmd.append(str(schematic_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse ERC output to count errors and warnings
        output = result.stdout + result.stderr
        errors = self._count_pattern(output, "Error:")
        warnings = self._count_pattern(output, "Warning:")
        
        return ERCResult(
            success=(result.returncode == 0 and errors == 0),
            errors=errors,
            warnings=warnings,
            output=output,
            exit_code=result.returncode
        )
    
    def export_netlist(
        self,
        schematic_path: Path,
        output_path: Path,
        format: str = "kicad"
    ) -> bool:
        """
        Export netlist from schematic.
        
        Args:
            schematic_path: Path to .kicad_sch file
            output_path: Path for netlist output
            format: Netlist format (kicad, orcadpcb2, cadstar, spice, etc.)
            
        Returns:
            True if export succeeded
        """
        if not schematic_path.exists():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        
        cmd = [
            self.kicad_cli, "sch", "export", "netlist",
            "--format", format,
            "--output", str(output_path),
            str(schematic_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    def export_bom(
        self,
        schematic_path: Path,
        output_path: Path,
        format: str = "csv",
        fields: Optional[List[str]] = None
    ) -> bool:
        """
        Export Bill of Materials.
        
        Args:
            schematic_path: Path to .kicad_sch file
            output_path: Path for BOM output
            format: BOM format (csv, xml, etc.)
            fields: List of fields to include
            
        Returns:
            True if export succeeded
        """
        if not schematic_path.exists():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        
        # Default fields if not specified
        if fields is None:
            fields = ["Reference", "Value", "Footprint", "Datasheet", "Description"]
        
        cmd = [
            self.kicad_cli, "sch", "export", "bom",
            "--format", format,
            "--output", str(output_path),
            "--fields", ",".join(fields),
            str(schematic_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    def export_pdf(
        self,
        schematic_path: Path,
        output_path: Path,
        black_and_white: bool = False
    ) -> bool:
        """
        Export schematic to PDF.
        
        Args:
            schematic_path: Path to .kicad_sch file
            output_path: Path for PDF output
            black_and_white: Export in black and white
            
        Returns:
            True if export succeeded
        """
        if not schematic_path.exists():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        
        cmd = [
            self.kicad_cli, "sch", "export", "pdf",
            "--output", str(output_path)
        ]
        
        if black_and_white:
            cmd.append("--black-and-white")
        
        cmd.append(str(schematic_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    def export_svg(
        self,
        schematic_path: Path,
        output_dir: Path,
        black_and_white: bool = False
    ) -> bool:
        """
        Export schematic to SVG.
        
        Args:
            schematic_path: Path to .kicad_sch file
            output_dir: Directory for SVG output
            black_and_white: Export in black and white
            
        Returns:
            True if export succeeded
        """
        if not schematic_path.exists():
            raise FileNotFoundError(f"Schematic not found: {schematic_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.kicad_cli, "sch", "export", "svg",
            "--output", str(output_dir)
        ]
        
        if black_and_white:
            cmd.append("--black-and-white")
        
        cmd.append(str(schematic_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    def run_drc(
        self,
        pcb_path: Path,
        output_path: Optional[Path] = None
    ) -> DRCResult:
        """
        Run Design Rule Check on PCB layout.
        
        Args:
            pcb_path: Path to .kicad_pcb file
            output_path: Path for DRC report (optional)
            
        Returns:
            DRCResult with errors, warnings, and output
        """
        if not pcb_path.exists():
            raise FileNotFoundError(f"PCB file not found: {pcb_path}")
        
        cmd = [self.kicad_cli, "pcb", "drc"]
        
        if output_path:
            cmd.extend(["--output", str(output_path)])
        
        cmd.append(str(pcb_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse DRC output
        output = result.stdout + result.stderr
        errors = self._count_pattern(output, "Error:")
        warnings = self._count_pattern(output, "Warning:")
        unconnected = self._count_pattern(output, "Unconnected")
        
        return DRCResult(
            success=(result.returncode == 0 and errors == 0 and unconnected == 0),
            errors=errors,
            warnings=warnings,
            unconnected=unconnected,
            output=output,
            exit_code=result.returncode
        )
    
    def export_gerbers(
        self,
        pcb_path: Path,
        output_dir: Path,
        layers: Optional[List[str]] = None
    ) -> bool:
        """
        Export Gerber files for manufacturing.
        
        Args:
            pcb_path: Path to .kicad_pcb file
            output_dir: Directory for Gerber output
            layers: Specific layers to export (None = all)
            
        Returns:
            True if export succeeded
        """
        if not pcb_path.exists():
            raise FileNotFoundError(f"PCB file not found: {pcb_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.kicad_cli, "pcb", "export", "gerbers",
            "--output", str(output_dir)
        ]
        
        if layers:
            cmd.extend(["--layers", ",".join(layers)])
        
        cmd.append(str(pcb_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    def export_drill(
        self,
        pcb_path: Path,
        output_dir: Path,
        format: str = "excellon"
    ) -> bool:
        """
        Export drill files.
        
        Args:
            pcb_path: Path to .kicad_pcb file
            output_dir: Directory for drill file output
            format: Drill format (excellon, gerber)
            
        Returns:
            True if export succeeded
        """
        if not pcb_path.exists():
            raise FileNotFoundError(f"PCB file not found: {pcb_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.kicad_cli, "pcb", "export", "drill",
            "--format", format,
            "--output", str(output_dir),
            str(pcb_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return result.returncode == 0
    
    def _count_pattern(self, text: str, pattern: str) -> int:
        """Count occurrences of pattern in text."""
        return text.count(pattern)


# Convenience functions

def validate_schematic(schematic_path: Path) -> Dict[str, Any]:
    """
    Run all schematic validations.
    
    Returns dictionary with validation results.
    """
    kicad = KiCadCLI()
    
    results = {
        'schematic': str(schematic_path),
        'erc': None,
        'netlist': None,
        'bom': None,
        'pdf': None
    }
    
    # Run ERC
    try:
        erc_result = kicad.run_erc(schematic_path)
        results['erc'] = {
            'success': erc_result.success,
            'errors': erc_result.errors,
            'warnings': erc_result.warnings,
            'exit_code': erc_result.exit_code
        }
    except Exception as e:
        results['erc'] = {'error': str(e)}
    
    # Export netlist
    try:
        netlist_path = schematic_path.parent / "netlist.net"
        success = kicad.export_netlist(schematic_path, netlist_path)
        results['netlist'] = {
            'success': success,
            'path': str(netlist_path) if success else None
        }
    except Exception as e:
        results['netlist'] = {'error': str(e)}
    
    # Export BOM
    try:
        bom_path = schematic_path.parent / "bom.csv"
        success = kicad.export_bom(schematic_path, bom_path)
        results['bom'] = {
            'success': success,
            'path': str(bom_path) if success else None
        }
    except Exception as e:
        results['bom'] = {'error': str(e)}
    
    # Export PDF
    try:
        pdf_path = schematic_path.parent / "schematic.pdf"
        success = kicad.export_pdf(schematic_path, pdf_path)
        results['pdf'] = {
            'success': success,
            'path': str(pdf_path) if success else None
        }
    except Exception as e:
        results['pdf'] = {'error': str(e)}
    
    return results
