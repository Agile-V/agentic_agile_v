"""
Component Index

Manages approved components, alternative parts, and datasheet references.
Integrates with Understand Anything for datasheet parsing if available.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any
import json


@dataclass
class DatasheetExtract:
    """Key information extracted from a component datasheet."""
    component: str
    part_number: str
    manufacturer: str
    datasheet_url: str
    
    # Pin information
    pins: List[Dict[str, Any]] = field(default_factory=list)
    
    # Electrical characteristics
    voltage_min: Optional[float] = None
    voltage_max: Optional[float] = None
    voltage_typ: Optional[float] = None
    current_max: Optional[float] = None
    power_max: Optional[float] = None
    
    # Typical application
    typical_application_circuit: Optional[str] = None
    recommended_layout: Optional[str] = None
    
    # Additional specs
    package: Optional[str] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    
    # Metadata
    extracted_date: Optional[str] = None
    confidence: Optional[str] = "manual"  # manual, auto-high, auto-medium, auto-low
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasheetExtract':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ComponentEntry:
    """Entry in component index."""
    id: str  # Internal ID
    part_number: str
    manufacturer: str
    description: str
    category: str  # resistor, capacitor, ic, sensor, etc.
    
    # Availability
    available: bool = True
    preferred_vendor: Optional[str] = None
    stock_url: Optional[str] = None
    lifecycle_status: str = "active"  # active, nrnd, obsolete
    
    # Specifications
    package: Optional[str] = None
    datasheet_url: Optional[str] = None
    datasheet_extract: Optional[DatasheetExtract] = None
    
    # Alternatives
    alternates: List[str] = field(default_factory=list)
    compatible_with: List[str] = field(default_factory=list)
    
    # Approval status
    approved: bool = False
    approved_by: Optional[str] = None
    approved_date: Optional[str] = None
    restrictions: List[str] = field(default_factory=list)
    
    # Metadata
    notes: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        if self.datasheet_extract:
            d['datasheet_extract'] = self.datasheet_extract.to_dict()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentEntry':
        """Create from dictionary."""
        if 'datasheet_extract' in data and data['datasheet_extract']:
            data['datasheet_extract'] = DatasheetExtract.from_dict(data['datasheet_extract'])
        return cls(**data)


class ComponentIndex:
    """Index of approved and known components."""
    
    def __init__(self, index_file: Optional[Path] = None):
        """
        Initialize component index.
        
        Args:
            index_file: Path to component index JSON file
        """
        self.index_file = index_file
        self.components: Dict[str, ComponentEntry] = {}
        
        if index_file and index_file.exists():
            self.load(index_file)
    
    def add_component(self, component: ComponentEntry) -> None:
        """Add component to index."""
        self.components[component.id] = component
    
    def get_component(self, component_id: str) -> Optional[ComponentEntry]:
        """Get component by ID."""
        return self.components.get(component_id)
    
    def find_by_part_number(self, part_number: str) -> Optional[ComponentEntry]:
        """Find component by part number."""
        for comp in self.components.values():
            if comp.part_number == part_number:
                return comp
        return None
    
    def find_by_category(self, category: str) -> List[ComponentEntry]:
        """Find all components in a category."""
        return [c for c in self.components.values() if c.category == category]
    
    def find_approved(self) -> List[ComponentEntry]:
        """Find all approved components."""
        return [c for c in self.components.values() if c.approved]
    
    def find_available(self) -> List[ComponentEntry]:
        """Find all available components."""
        return [c for c in self.components.values() if c.available]
    
    def get_alternates(self, component_id: str) -> List[ComponentEntry]:
        """Get alternate components."""
        comp = self.get_component(component_id)
        if not comp:
            return []
        
        alternates = []
        for alt_id in comp.alternates:
            alt = self.get_component(alt_id)
            if alt:
                alternates.append(alt)
        
        return alternates
    
    def save(self, filepath: Optional[Path] = None) -> None:
        """Save index to JSON file."""
        if filepath is None:
            filepath = self.index_file
        
        if filepath is None:
            raise ValueError("No filepath specified")
        
        data = {
            'version': '1.0',
            'components': {
                comp_id: comp.to_dict()
                for comp_id, comp in self.components.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: Path) -> None:
        """Load index from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        
        self.components = {}
        for comp_id, comp_data in data.get('components', {}).items():
            self.components[comp_id] = ComponentEntry.from_dict(comp_data)
        
        self.index_file = filepath
    
    def import_kicad_library(self, library_path: Path) -> int:
        """
        Import components from KiCad library.
        
        Returns number of components imported.
        
        Note: This is a placeholder. Actual implementation would parse
        KiCad library formats (.kicad_sym, .lib, etc.)
        """
        # Placeholder for KiCad library import
        # Would parse .kicad_sym or .lib files
        return 0
    
    def generate_bom_template(self, approved_only: bool = True) -> List[Dict[str, Any]]:
        """Generate BOM template with approved components."""
        components = self.find_approved() if approved_only else list(self.components.values())
        
        bom = []
        for comp in components:
            bom.append({
                'Part Number': comp.part_number,
                'Manufacturer': comp.manufacturer,
                'Description': comp.description,
                'Package': comp.package,
                'Category': comp.category,
                'Preferred Vendor': comp.preferred_vendor,
                'Datasheet': comp.datasheet_url
            })
        
        return bom


# Helper functions for common component creation

def create_resistor_entry(
    part_number: str,
    value: str,
    package: str = "0603",
    tolerance: str = "1%",
    power: str = "0.1W",
    approved: bool = False
) -> ComponentEntry:
    """Create resistor component entry."""
    return ComponentEntry(
        id=f"resistor_{value}_{package}".replace(".", "p"),
        part_number=part_number,
        manufacturer="Generic",
        description=f"Resistor {value} {tolerance} {power} {package}",
        category="resistor",
        package=package,
        approved=approved
    )


def create_capacitor_entry(
    part_number: str,
    value: str,
    voltage: str,
    package: str = "0603",
    dielectric: str = "X7R",
    approved: bool = False
) -> ComponentEntry:
    """Create capacitor component entry."""
    return ComponentEntry(
        id=f"capacitor_{value}_{voltage}_{package}".replace(".", "p"),
        part_number=part_number,
        manufacturer="Generic",
        description=f"Capacitor {value} {voltage} {dielectric} {package}",
        category="capacitor",
        package=package,
        approved=approved
    )


def create_ic_entry(
    part_number: str,
    manufacturer: str,
    description: str,
    package: str,
    datasheet_url: str,
    approved: bool = False
) -> ComponentEntry:
    """Create IC component entry."""
    return ComponentEntry(
        id=f"ic_{part_number}".lower().replace("-", "_"),
        part_number=part_number,
        manufacturer=manufacturer,
        description=description,
        category="ic",
        package=package,
        datasheet_url=datasheet_url,
        approved=approved
    )


# Integration with Understand Anything (if available)

def extract_datasheet_info(
    datasheet_path: Path,
    part_number: str
) -> Optional[DatasheetExtract]:
    """
    Extract information from datasheet using Understand Anything.
    
    This is a placeholder. Real implementation would:
    1. Check if Understand Anything is available
    2. Send datasheet for parsing
    3. Extract key specifications
    4. Return structured data
    
    Returns None if extraction fails or UA not available.
    """
    # Placeholder - would integrate with Understand Anything
    return None


def auto_populate_from_datasheet(
    component: ComponentEntry,
    datasheet_path: Path
) -> ComponentEntry:
    """
    Automatically populate component details from datasheet.
    
    Uses Understand Anything if available, falls back to manual entry.
    """
    extract = extract_datasheet_info(datasheet_path, component.part_number)
    
    if extract:
        component.datasheet_extract = extract
        # Update component fields from extract
        if extract.package:
            component.package = extract.package
    
    return component
