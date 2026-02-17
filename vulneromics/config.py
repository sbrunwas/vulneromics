"""Configuration constants for the vulneromics Streamlit app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_REGION_COLUMN_CANDIDATES = (
    "parcellation_substructure",
    "parcellation_structure",
    "structure_acronym",
    "brain_region",
)

DEFAULT_CLASS_COLUMN_CANDIDATES = (
    "class",
    "cell_class",
    "supertype",
)

DEFAULT_COORD_COLUMN_CANDIDATES = (
    ("x", "y", "z"),
    ("x_ccf", "y_ccf", "z_ccf"),
    ("ccf_x", "ccf_y", "ccf_z"),
)

DEFAULT_CELL_ID_CANDIDATES = ("cell_label", "cell_id", "cell")

DEFAULT_RECEPTOR_PANEL = [
    "Adra1a",
    "Adra1b",
    "Adra2a",
    "Adrb1",
    "Adrb2",
    "Chrm1",
    "Chrm2",
    "Chrm3",
    "Chrna4",
    "Chrna7",
]


@dataclass(slots=True)
class AppPaths:
    """Simple file path container for dataset locations."""

    metadata: Path
    expression: Path | None = None

    @classmethod
    def from_strings(cls, metadata: str, expression: str | None = None) -> "AppPaths":
        return cls(metadata=Path(metadata), expression=Path(expression) if expression else None)
