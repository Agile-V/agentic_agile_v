"""
Component Index

Manages approved components, alternative parts, and datasheet references.
Integrates with Understand Anything for datasheet parsing if available.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DatasheetExtract:
    """Key information extracted from a component datasheet."""

    component: str
    part_number: str
    manufacturer: str
    datasheet_url: str

    # Pin information
    pins: list[dict[str, Any]] = field(default_factory=list)

    # Electrical characteristics
    voltage_min: float | None = None
    voltage_max: float | None = None
    voltage_typ: float | None = None
    current_max: float | None = None
    power_max: float | None = None

    # Typical application
    typical_application_circuit: str | None = None
    recommended_layout: str | None = None

    # Additional specs
    package: str | None = None
    temperature_min: float | None = None
    temperature_max: float | None = None

    # Metadata
    extracted_date: str | None = None
    confidence: str | None = "manual"  # manual, auto-high, auto-medium, auto-low

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DatasheetExtract":
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
    preferred_vendor: str | None = None
    stock_url: str | None = None
    lifecycle_status: str = "active"  # active, nrnd, obsolete

    # Specifications
    package: str | None = None
    datasheet_url: str | None = None
    datasheet_extract: DatasheetExtract | None = None

    # Alternatives
    alternates: list[str] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)

    # Approval status
    approved: bool = False
    approved_by: str | None = None
    approved_date: str | None = None
    restrictions: list[str] = field(default_factory=list)

    # Metadata
    notes: str | None = None
    created: str | None = None
    updated: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        if self.datasheet_extract:
            d["datasheet_extract"] = self.datasheet_extract.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentEntry":
        """Create from dictionary."""
        if "datasheet_extract" in data and data["datasheet_extract"]:
            data["datasheet_extract"] = DatasheetExtract.from_dict(data["datasheet_extract"])
        return cls(**data)


class ComponentIndex:
    """Index of approved and known components."""

    def __init__(self, index_file: Path | None = None):
        """
        Initialize component index.

        Args:
            index_file: Path to component index JSON file
        """
        self.index_file = index_file
        self.components: dict[str, ComponentEntry] = {}

        if index_file and index_file.exists():
            self.load(index_file)

    def add_component(self, component: ComponentEntry) -> None:
        """Add component to index."""
        self.components[component.id] = component

    def get_component(self, component_id: str) -> ComponentEntry | None:
        """Get component by ID."""
        return self.components.get(component_id)

    def find_by_part_number(self, part_number: str) -> ComponentEntry | None:
        """Find component by part number."""
        for comp in self.components.values():
            if comp.part_number == part_number:
                return comp
        return None

    def find_by_category(self, category: str) -> list[ComponentEntry]:
        """Find all components in a category."""
        return [c for c in self.components.values() if c.category == category]

    def find_approved(self) -> list[ComponentEntry]:
        """Find all approved components."""
        return [c for c in self.components.values() if c.approved]

    def find_available(self) -> list[ComponentEntry]:
        """Find all available components."""
        return [c for c in self.components.values() if c.available]

    def get_alternates(self, component_id: str) -> list[ComponentEntry]:
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

    def save(self, filepath: Path | None = None) -> None:
        """Save index to JSON file."""
        if filepath is None:
            filepath = self.index_file

        if filepath is None:
            raise ValueError("No filepath specified")

        data = {
            "version": "1.0",
            "components": {comp_id: comp.to_dict() for comp_id, comp in self.components.items()},
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: Path) -> None:
        """Load index from JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        self.components = {}
        for comp_id, comp_data in data.get("components", {}).items():
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

    def generate_bom_template(self, approved_only: bool = True) -> list[dict[str, Any]]:
        """Generate BOM template with approved components."""
        components = self.find_approved() if approved_only else list(self.components.values())

        bom = []
        for comp in components:
            bom.append(
                {
                    "Part Number": comp.part_number,
                    "Manufacturer": comp.manufacturer,
                    "Description": comp.description,
                    "Package": comp.package,
                    "Category": comp.category,
                    "Preferred Vendor": comp.preferred_vendor,
                    "Datasheet": comp.datasheet_url,
                }
            )

        return bom


# Helper functions for common component creation


def create_resistor_entry(
    part_number: str,
    value: str,
    package: str = "0603",
    tolerance: str = "1%",
    power: str = "0.1W",
    approved: bool = False,
) -> ComponentEntry:
    """Create resistor component entry."""
    return ComponentEntry(
        id=f"resistor_{value}_{package}".replace(".", "p"),
        part_number=part_number,
        manufacturer="Generic",
        description=f"Resistor {value} {tolerance} {power} {package}",
        category="resistor",
        package=package,
        approved=approved,
    )


def create_capacitor_entry(
    part_number: str,
    value: str,
    voltage: str,
    package: str = "0603",
    dielectric: str = "X7R",
    approved: bool = False,
) -> ComponentEntry:
    """Create capacitor component entry."""
    return ComponentEntry(
        id=f"capacitor_{value}_{voltage}_{package}".replace(".", "p"),
        part_number=part_number,
        manufacturer="Generic",
        description=f"Capacitor {value} {voltage} {dielectric} {package}",
        category="capacitor",
        package=package,
        approved=approved,
    )


def create_ic_entry(
    part_number: str,
    manufacturer: str,
    description: str,
    package: str,
    datasheet_url: str,
    approved: bool = False,
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
        approved=approved,
    )


# Integration with Understand Anything (if available)


def extract_datasheet_info(datasheet_path: Path, part_number: str) -> DatasheetExtract | None:
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


def auto_populate_from_datasheet(component: ComponentEntry, datasheet_path: Path) -> ComponentEntry:
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
