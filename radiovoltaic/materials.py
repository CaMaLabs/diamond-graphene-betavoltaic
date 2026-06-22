from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "config" / "materials.yaml"
_NUMERIC = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


@dataclass(frozen=True)
class Source:
    name: str
    mean_beta_energy_keV: float
    max_beta_energy_keV: float
    half_life_years: float
    default_activity_Bq_cm2: float
    description: str


@dataclass(frozen=True)
class MaterialDatabase:
    raw: dict[str, Any]

    @property
    def sources(self) -> dict[str, Source]:
        return {
            name: Source(name=name, **props)
            for name, props in self.raw["sources"].items()
        }

    @property
    def diamond(self) -> dict[str, float]:
        return self.raw["materials"]["diamond"]

    @property
    def graphene(self) -> dict[str, float]:
        return self.raw["materials"]["graphene"]

    @property
    def ferrites(self) -> dict[str, dict[str, float]]:
        return self.raw["materials"]["ferrites"]


def load_materials(path: Path | str = DEFAULT_DB) -> MaterialDatabase:
    with Path(path).open("r", encoding="utf-8") as handle:
        return MaterialDatabase(_normalize_numbers(yaml.safe_load(handle)))


def _normalize_numbers(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_numbers(item) for item in value]
    if isinstance(value, str) and _NUMERIC.match(value):
        return float(value)
    return value
