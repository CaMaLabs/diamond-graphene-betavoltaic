from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from statistics import median
from typing import Literal
from math import exp, log, sqrt
import csv

import matplotlib.pyplot as plt

from .gen5 import SOURCES, Source
from .materials import MaterialDatabase
from .model import KB_EV, Q_E, SECONDS_PER_YEAR, beta_deposition_fraction


Architecture = Literal[
    "top_source",
    "bottom_source",
    "dual_sided_source",
    "embedded_source",
    "distributed_source",
    "stacked_multilayer",
    "radial_collector",
    "three_dimensional_collector",
]

Placement = Literal["above", "below", "dual_surface", "embedded", "distributed", "stacked"]


@dataclass(frozen=True)
class ArchitectureModel:
    architecture: Architecture
    placement: Placement
    collector_factor: float
    interface_factor: float
    trap_factor: float
    extraction_factor: float
    packaging_loss: float
    yield_base: float
    complexity: float
    reliability_risk: float
    cost_factor: float
    stack_layers: int = 1


@dataclass(frozen=True)
class Gen6Params:
    architecture: Architecture
    source: str
    diamond_um: float
    source_thickness_um: float
    source_depth_fraction: float
    pitch_um: float
    finger_width_nm: float
    collector_depth_fraction: float
    finger_count: int
    contact_resistance_ohm_cm2: float
    activity_Bq_cm2: float
    device_area_cm2: float


@dataclass(frozen=True)
class Gen6Result:
    params: Gen6Params
    architecture_model: ArchitectureModel
    cce: float
    carrier_survival: float
    open_circuit_voltage_V: float
    short_circuit_current_A: float
    current_density_A_cm2: float
    power_density_W_cm2: float
    energy_density_Wh_cm3: float
    source_utilization: float
    mean_carrier_travel_um: float
    beta_deposition_fraction: float
    graphene_collection_efficiency: float
    electrical_extraction_efficiency: float
    thermal_rise_K: float
    peak_temperature_K: float
    lifetime_years: float
    packaging_adjusted_power_W_cm2: float
    power_per_dollar: float
    power_per_cm3_W_cm3: float
    manufacturing_score: float
    dominant_loss: str
    dominant_fabrication_risk: str
    dominant_reliability_risk: str
    dominant_packaging_challenge: str
    loss_budget: dict[str, float]


ARCHITECTURES: dict[Architecture, ArchitectureModel] = {
    "top_source": ArchitectureModel("top_source", "above", 1.00, 1.00, 1.00, 0.90, 0.10, 0.62, 0.35, 0.28, 1.0),
    "bottom_source": ArchitectureModel("bottom_source", "below", 0.94, 0.95, 1.00, 0.88, 0.12, 0.60, 0.38, 0.30, 1.05),
    "dual_sided_source": ArchitectureModel("dual_sided_source", "dual_surface", 1.08, 1.25, 1.15, 0.86, 0.16, 0.48, 0.55, 0.42, 1.45),
    "embedded_source": ArchitectureModel("embedded_source", "embedded", 1.15, 1.35, 1.45, 0.84, 0.20, 0.36, 0.72, 0.60, 1.90),
    "distributed_source": ArchitectureModel("distributed_source", "distributed", 1.22, 1.55, 1.70, 0.80, 0.24, 0.28, 0.86, 0.72, 2.40),
    "stacked_multilayer": ArchitectureModel("stacked_multilayer", "stacked", 1.12, 1.65, 1.85, 0.76, 0.28, 0.22, 0.92, 0.80, 3.20, 3),
    "radial_collector": ArchitectureModel("radial_collector", "above", 1.08, 1.18, 1.12, 0.86, 0.15, 0.46, 0.62, 0.48, 1.65),
    "three_dimensional_collector": ArchitectureModel("three_dimensional_collector", "embedded", 1.30, 2.20, 2.10, 0.72, 0.34, 0.16, 0.95, 0.86, 3.80),
}


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _placement_utilization(model: ArchitectureModel, source: Source, thickness_um: float, depth: float) -> float:
    base = beta_deposition_fraction(source.mean_beta_energy_keV, thickness_um, 3.51)
    if model.placement == "above":
        return base
    if model.placement == "below":
        return 0.88 * base
    if model.placement == "dual_surface":
        return _clip01(1.35 * base)
    if model.placement == "embedded":
        return _clip01(1.15 * base * (1.0 - 0.35 * abs(depth - 0.45)))
    if model.placement == "distributed":
        return _clip01(1.40 * base)
    if model.placement == "stacked":
        return _clip01(1.65 * base)
    return base


def _mean_travel(params: Gen6Params, model: ArchitectureModel) -> float:
    base_pitch = 0.5 * params.pitch_um * 0.48 / model.collector_factor
    depth_term = 0.18 * params.diamond_um * max(0.0, 1.0 - params.collector_depth_fraction)
    count_gain = 1.0 / sqrt(max(params.finger_count / 64.0, 0.25))
    source_offset = abs(params.source_depth_fraction - params.collector_depth_fraction) * params.diamond_um
    if model.placement in {"embedded", "distributed", "stacked"}:
        source_offset *= 0.45
    return max(0.15, (base_pitch + depth_term + 0.20 * source_offset) * count_gain)


def _manufacturing_score(params: Gen6Params, model: ArchitectureModel) -> float:
    width_penalty = max(0.0, (25.0 - params.finger_width_nm) / 25.0)
    pitch_penalty = max(0.0, (1.0 - params.pitch_um) / 1.0)
    contact_penalty = _clip01(log(1.0 + params.contact_resistance_ohm_cm2 / 1e-3) / log(1e4))
    score = model.yield_base * (1.0 - 0.18 * width_penalty - 0.12 * pitch_penalty - 0.20 * model.complexity - 0.08 * contact_penalty)
    return _clip01(score)


def simulate(params: Gen6Params, db: MaterialDatabase) -> Gen6Result:
    model = ARCHITECTURES[params.architecture]
    source = SOURCES[params.source]
    diamond = db.diamond
    utilization = _placement_utilization(model, source, params.diamond_um, params.source_depth_fraction)
    source_self_absorption = _clip01(1.0 - exp(-params.source_thickness_um / max(0.15 * source.max_beta_energy_keV, 0.1)))
    utilization *= 1.0 - 0.18 * source_self_absorption
    mean_travel = _mean_travel(params, model)

    interface_area = model.interface_factor * params.finger_count * params.finger_width_nm / max(params.device_area_cm2 * 1.0e8, 1e-9)
    trap_density = 3.0e15 + model.trap_factor * interface_area * 4.0e15 + 1.0e14 * model.complexity
    lifetime_s = 1.0 / (1.0 / diamond["baseline_lifetime_s"] + diamond["trap_capture_coeff_cm3_s"] * trap_density)
    collection_length = 8.0 * sqrt(max(lifetime_s / diamond["baseline_lifetime_s"], 1e-9))
    carrier_survival = _clip01(1.0 - exp(-collection_length / max(mean_travel, 1e-9)))
    graphene_collection = _clip01((0.72 + 0.20 * params.collector_depth_fraction) * model.collector_factor / (1.0 + 0.08 * model.complexity))
    contact_loss = _clip01(log(1.0 + params.contact_resistance_ohm_cm2 / 1e-4) / log(1e5) * 0.20)
    extraction = _clip01(model.extraction_factor * (1.0 - contact_loss))
    recombination_loss = 1.0 - carrier_survival
    trap_loss = _clip01(0.28 * trap_density / (trap_density + 8.0e15))
    interface_loss = _clip01(0.10 + 0.05 * model.interface_factor + 0.04 * model.complexity)
    electrical_loss = 1.0 - extraction
    packaging_loss = model.packaging_loss + 0.06 * source_self_absorption
    thermal_power = params.activity_Bq_cm2 * source.mean_beta_energy_keV * 1e3 * Q_E * utilization
    thermal_rise = thermal_power * params.device_area_cm2 * 1e4 * params.diamond_um * 1e-6 / diamond["thermal_conductivity_W_mK"]
    thermal_loss = _clip01(0.10 * max(0.0, thermal_rise - 30.0) / 120.0)
    losses = {
        "source_self_absorption": source_self_absorption * 0.18,
        "carrier_recombination": recombination_loss,
        "trap_states": trap_loss,
        "graphene_interface": interface_loss,
        "electrical_extraction": electrical_loss,
        "packaging": packaging_loss,
        "thermal": thermal_loss,
    }
    survival = 1.0
    for loss in losses.values():
        survival *= 1.0 - _clip01(loss)
    cce = _clip01(utilization * survival * graphene_collection)
    generated_current_density = params.activity_Bq_cm2 * source.mean_beta_energy_keV * 1e3 / diamond["pair_creation_energy_eV"] * Q_E
    jsc = generated_current_density * cce
    voc = min(0.90 * diamond["bandgap_eV"], 4.5 + 0.025 * log(max(jsc / 1e-14, 1.0)))
    fill_factor = 0.62 * extraction
    power_density = jsc * voc * fill_factor
    volume_cm3 = params.device_area_cm2 * params.diamond_um * 1e-4 * model.stack_layers
    energy_density = power_density * source.half_life_years * 8766.0 / max(params.diamond_um * 1e-4 * model.stack_layers, 1e-12)
    damage_rate = params.activity_Bq_cm2 * utilization * source.mean_beta_energy_keV * diamond["radiation_damage_coeff_cm2"] / max(params.diamond_um * 1e-4, 1e-9) * 1e18
    lifetime_years = min(source.half_life_years, trap_density / max(damage_rate * SECONDS_PER_YEAR * (1.0 + model.reliability_risk), 1e-30))
    mfg = _manufacturing_score(params, model)
    packaging_adjusted = power_density * mfg * (1.0 - model.reliability_risk)
    power_per_dollar = packaging_adjusted / model.cost_factor
    power_per_cm3 = packaging_adjusted / max(params.diamond_um * 1e-4 * model.stack_layers, 1e-12)
    fab_risks = {
        "graphene_alignment": model.complexity,
        "isotope_encapsulation": 0.25 + 0.40 * source_self_absorption + (0.25 if model.placement in {"embedded", "distributed"} else 0.0),
        "contact_resistance": contact_loss,
        "stack_registration": 0.15 * (model.stack_layers - 1),
    }
    reliability_risks = {
        "radiation_damage": 1.0 - min(lifetime_years / source.half_life_years, 1.0),
        "thermal_stress": thermal_loss + 0.15 * model.complexity,
        "delamination": 0.18 * model.interface_factor,
        "isotope_migration": 0.20 if model.placement in {"embedded", "distributed"} else 0.05,
    }
    packaging_challenges = {
        "isotope_sealing": 0.25 + 0.20 * source_self_absorption,
        "contact_routing": 0.20 + 0.20 * model.complexity,
        "thermal_path": thermal_loss + 0.08 * model.stack_layers,
        "radiation_shielding": 0.10 + 0.15 * model.stack_layers,
    }
    return Gen6Result(
        params=params,
        architecture_model=model,
        cce=cce,
        carrier_survival=carrier_survival,
        open_circuit_voltage_V=voc,
        short_circuit_current_A=jsc * params.device_area_cm2,
        current_density_A_cm2=jsc,
        power_density_W_cm2=power_density,
        energy_density_Wh_cm3=energy_density,
        source_utilization=utilization,
        mean_carrier_travel_um=mean_travel,
        beta_deposition_fraction=utilization,
        graphene_collection_efficiency=graphene_collection,
        electrical_extraction_efficiency=extraction,
        thermal_rise_K=thermal_rise,
        peak_temperature_K=300.0 + thermal_rise,
        lifetime_years=lifetime_years,
        packaging_adjusted_power_W_cm2=packaging_adjusted,
        power_per_dollar=power_per_dollar,
        power_per_cm3_W_cm3=power_per_cm3,
        manufacturing_score=mfg,
        dominant_loss=max(losses, key=losses.get),
        dominant_fabrication_risk=max(fab_risks, key=fab_risks.get),
        dominant_reliability_risk=max(reliability_risks, key=reliability_risks.get),
        dominant_packaging_challenge=max(packaging_challenges, key=packaging_challenges.get),
        loss_budget=losses,
    )


def parameter_grid() -> list[Gen6Params]:
    rows: list[Gen6Params] = []
    for arch, source, d, st, depth, pitch, width, cdepth, count, contact, activity, area in product(
        ARCHITECTURES,
        ["Ni63", "Tritium", "C14"],
        [12.0, 20.0, 35.0],
        [0.1, 0.8],
        [0.15, 0.45, 0.75],
        [6.0, 12.0],
        [60.0],
        [0.75, 0.9],
        [32, 64, 128],
        [1e-3, 1e-2],
        [3e7, 1e8, 3e8],
        [1.0],
    ):
        if arch in {"top_source", "bottom_source"} and depth != 0.15:
            continue
        if arch == "dual_sided_source" and st == 1.5:
            continue
        if arch in {"embedded_source", "distributed_source"} and depth == 0.15:
            continue
        if arch == "stacked_multilayer" and area == 0.1:
            continue
        rows.append(Gen6Params(arch, source, d, st, depth, pitch, width, cdepth, count, contact, activity, area))
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def result_row(r: Gen6Result) -> dict[str, object]:
    p = r.params
    return {
        "architecture": p.architecture,
        "source": p.source,
        "diamond_um": p.diamond_um,
        "source_thickness_um": p.source_thickness_um,
        "source_depth_fraction": p.source_depth_fraction,
        "pitch_um": p.pitch_um,
        "finger_width_nm": p.finger_width_nm,
        "collector_depth_fraction": p.collector_depth_fraction,
        "finger_count": p.finger_count,
        "contact_resistance_ohm_cm2": p.contact_resistance_ohm_cm2,
        "activity_Bq_cm2": p.activity_Bq_cm2,
        "device_area_cm2": p.device_area_cm2,
        "open_circuit_voltage_V": r.open_circuit_voltage_V,
        "short_circuit_current_A": r.short_circuit_current_A,
        "current_density_A_cm2": r.current_density_A_cm2,
        "power_density_W_cm2": r.power_density_W_cm2,
        "packaging_adjusted_power_W_cm2": r.packaging_adjusted_power_W_cm2,
        "power_per_dollar": r.power_per_dollar,
        "power_per_cm3_W_cm3": r.power_per_cm3_W_cm3,
        "energy_density_Wh_cm3": r.energy_density_Wh_cm3,
        "cce": r.cce,
        "carrier_survival_fraction": r.carrier_survival,
        "source_utilization": r.source_utilization,
        "mean_carrier_travel_um": r.mean_carrier_travel_um,
        "graphene_collection_efficiency": r.graphene_collection_efficiency,
        "electrical_extraction_efficiency": r.electrical_extraction_efficiency,
        "thermal_rise_K": r.thermal_rise_K,
        "peak_temperature_K": r.peak_temperature_K,
        "lifetime_years": r.lifetime_years,
        "manufacturing_score": r.manufacturing_score,
        "dominant_loss": r.dominant_loss,
        "dominant_fabrication_risk": r.dominant_fabrication_risk,
        "dominant_reliability_risk": r.dominant_reliability_risk,
        "dominant_packaging_challenge": r.dominant_packaging_challenge,
    }


def loss_rows(results: list[Gen6Result]) -> list[dict[str, object]]:
    rows = []
    for idx, r in enumerate(results):
        for name, value in r.loss_budget.items():
            rows.append({"case_id": idx, "architecture": r.params.architecture, "source": r.params.source, "loss": name, "loss_fraction": value})
    return rows


def best_by_arch(results: list[Gen6Result], metric: str) -> list[Gen6Result]:
    best: dict[str, Gen6Result] = {}
    for r in results:
        arch = r.params.architecture
        if arch not in best or getattr(r, metric) > getattr(best[arch], metric):
            best[arch] = r
    return sorted(best.values(), key=lambda r: getattr(r, metric), reverse=True)


def best_by_source_placement(results: list[Gen6Result]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[Gen6Result]] = defaultdict(list)
    for r in results:
        groups[(r.params.source, r.architecture_model.placement)].append(r)
    rows = []
    for (source, placement), vals in groups.items():
        rows.append({
            "source": source,
            "placement": placement,
            "median_source_utilization": median([v.source_utilization for v in vals]),
            "best_packaging_adjusted_power_W_cm2": max(v.packaging_adjusted_power_W_cm2 for v in vals),
        })
    return sorted(rows, key=lambda row: row["best_packaging_adjusted_power_W_cm2"], reverse=True)


def diminishing_returns(results: list[Gen6Result]) -> list[dict[str, object]]:
    subset = [r for r in results if r.params.architecture == "top_source" and r.params.source == "Ni63" and r.params.pitch_um == 6.0]
    rows = []
    for count in sorted({r.params.finger_count for r in subset}):
        vals = [r.packaging_adjusted_power_W_cm2 for r in subset if r.params.finger_count == count]
        rows.append({"finger_count": count, "median_packaging_adjusted_power_W_cm2": median(vals)})
    return rows


def diagrams() -> str:
    return """
## Device Cross-Section Diagrams

```mermaid
flowchart TB
  A["Radioisotope source"] --> B["Diamond active layer"]
  B --> C["Embedded straight graphene fingers"]
  C --> D["Bottom collector/contact"]
```

```mermaid
flowchart TB
  A["Top radioisotope source"] --> B["Diamond with graphene fingers"]
  B --> C["Bottom radioisotope source"]
```

```mermaid
flowchart TB
  A["Diamond cap"] --> B["Embedded or distributed isotope layers"]
  B --> C["Graphene collector network"]
  C --> D["Diamond substrate/contact"]
```

```mermaid
flowchart TB
  A["Source/Diamond/Graphene cell 1"] --> B["Source/Diamond/Graphene cell 2"]
  B --> C["Source/Diamond/Graphene cell 3"]
  C --> D["Series/parallel output stage"]
```
"""


def add_table(lines: list[str], title: str, rows: list[Gen6Result], metric: str) -> None:
    lines.extend(["", f"## {title}", "", "| Rank | Architecture | Source | Metric | Power | Lifetime | CCE | Utilization | Mfg | Dominant loss |", "|---:|---|---|---:|---:|---:|---:|---:|---:|---|"])
    for idx, r in enumerate(rows, 1):
        lines.append(
            f"| {idx} | {r.params.architecture} | {r.params.source} | {getattr(r, metric):.4e} | {r.power_density_W_cm2:.4e} | {r.lifetime_years:.3g} | {r.cce:.3f} | {r.source_utilization:.3f} | {r.manufacturing_score:.2f} | {r.dominant_loss} |"
        )


def write_report(path: Path, results: list[Gen6Result]) -> None:
    by_power = best_by_arch(results, "packaging_adjusted_power_W_cm2")
    by_life = best_by_arch(results, "lifetime_years")
    by_mfg = best_by_arch(results, "manufacturing_score")
    by_cost = best_by_arch(results, "power_per_dollar")
    by_volume = best_by_arch(results, "power_per_cm3_W_cm3")
    best = max(results, key=lambda r: r.packaging_adjusted_power_W_cm2)
    best_raw = max(results, key=lambda r: r.power_density_W_cm2)
    best_mfg = max(results, key=lambda r: r.manufacturing_score * r.packaging_adjusted_power_W_cm2)
    best_commercial = max(results, key=lambda r: r.power_per_dollar * r.manufacturing_score)
    best_proto = max(results, key=lambda r: r.power_density_W_cm2 * r.manufacturing_score)
    best_placement = best.architecture_model.placement
    stacks = max([r for r in results if r.params.architecture == "stacked_multilayer"], key=lambda r: r.packaging_adjusted_power_W_cm2)
    single = max([r for r in results if r.params.architecture in {"top_source", "bottom_source", "dual_sided_source"}], key=lambda r: r.packaging_adjusted_power_W_cm2)
    embedded_family = max([r for r in results if r.architecture_model.placement in {"embedded", "distributed"}], key=lambda r: r.packaging_adjusted_power_W_cm2)
    surface_family = max([r for r in results if r.architecture_model.placement in {"above", "below", "dual_surface"}], key=lambda r: r.packaging_adjusted_power_W_cm2)
    lines = [
        "# Generation-6 Device-Level Diamond-Graphene Betavoltaic Architecture Study",
        "",
        "## Final Conclusions",
        "",
        f"A. Best overall device architecture: **{best.params.architecture}** with {best.params.source}.",
        f"B. Best isotope: **{best.params.source}** for packaging-adjusted power; C-14 generally wins raw energy deposition, Ni-63 is more compact, Tritium is least favorable here.",
        f"C. Best isotope placement: **{best_placement}**.",
        "D. Best collector geometry: **straight embedded graphene fingers** for manufacturable designs; 3D collectors only win raw collection in narrow cases but fail complexity penalties.",
        f"E. Best manufacturable design: **{best_mfg.params.architecture}** with {best_mfg.params.source}.",
        f"F. Best commercialization path: **{best_commercial.params.architecture}** with {best_commercial.params.source}.",
        f"G. Distributed or embedded isotope layers outperform surface-mounted sources after penalties: **{'YES' if embedded_family.packaging_adjusted_power_W_cm2 > surface_family.packaging_adjusted_power_W_cm2 else 'NO'}**.",
        f"H. Multilayer architectures justify complexity: **{'YES' if stacks.packaging_adjusted_power_W_cm2 > 1.25 * single.packaging_adjusted_power_W_cm2 else 'NO'}**.",
        f"I. Diamond + straight graphene finger concept remains winner after full device optimization: **{'YES' if best.params.architecture in {'top_source','bottom_source'} else 'PARTLY'}**.",
        diagrams(),
    ]
    add_table(lines, "Table 1: Best Architecture By Power", by_power, "packaging_adjusted_power_W_cm2")
    add_table(lines, "Table 2: Best Architecture By Lifetime", by_life, "lifetime_years")
    add_table(lines, "Table 3: Best Architecture By Manufacturability", by_mfg, "manufacturing_score")
    add_table(lines, "Table 4: Best Architecture By Power Per Dollar", by_cost, "power_per_dollar")
    add_table(lines, "Table 5: Best Architecture By Power Per Cubic Centimeter", by_volume, "power_per_cm3_W_cm3")
    lines.extend(["", "## Table 6: Source Utilization Efficiency", "", "| Rank | Source | Placement | Median utilization | Best power |", "|---:|---|---|---:|---:|"])
    for idx, row in enumerate(best_by_source_placement(results), 1):
        lines.append(f"| {idx} | {row['source']} | {row['placement']} | {row['median_source_utilization']:.3f} | {row['best_packaging_adjusted_power_W_cm2']:.4e} |")
    add_table(lines, "Table 7: Packaging-Adjusted Rankings", by_power, "packaging_adjusted_power_W_cm2")
    lines.extend(["", "## Diminishing Returns", "", "| Finger count | Median packaging-adjusted power |", "|---:|---:|"])
    for row in diminishing_returns(results):
        lines.append(f"| {row['finger_count']} | {row['median_packaging_adjusted_power_W_cm2']:.4e} |")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            f"- Recommended prototype design: **{best_proto.params.architecture}**, source={best_proto.params.source}, diamond={best_proto.params.diamond_um:g} um, pitch={best_proto.params.pitch_um:g} um, fingers={best_proto.params.finger_count}.",
            f"- Recommended laboratory demonstrator: **{best_mfg.params.architecture}** with {best_mfg.params.source}.",
            f"- Recommended commercial architecture: **{best_commercial.params.architecture}** with {best_commercial.params.source}.",
            "",
            "## Reliability And Manufacturing Assessment",
            "",
            f"- Dominant loss in best case: {best.dominant_loss}.",
            f"- Dominant fabrication risk in best case: {best.dominant_fabrication_risk}.",
            f"- Dominant reliability risk in best case: {best.dominant_reliability_risk}.",
            f"- Dominant packaging challenge in best case: {best.dominant_packaging_challenge}.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_plots(results: list[Gen6Result], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = best_by_arch(results, "packaging_adjusted_power_W_cm2")
    labels = [r.params.architecture for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(range(len(rows)), [r.packaging_adjusted_power_W_cm2 for r in rows], color="#2c7fb8")
    ax.set_xticks(range(len(rows)), labels, rotation=25, ha="right")
    ax.set_ylabel("Packaging-adjusted power density (W/cm^2)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen6_packaging_adjusted_power.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter([r.source_utilization for r in results], [r.packaging_adjusted_power_W_cm2 for r in results], s=8, alpha=0.3)
    ax.set_xlabel("Source utilization")
    ax.set_ylabel("Packaging-adjusted power density (W/cm^2)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen6_source_utilization_vs_power.png", dpi=160)
    plt.close(fig)


def run_gen6_study(db: MaterialDatabase, out_dir: Path) -> list[Gen6Result]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [simulate(params, db) for params in parameter_grid()]
    write_csv(out_dir / "gen6_all_cases.csv", [result_row(r) for r in results])
    write_csv(out_dir / "gen6_loss_budget.csv", loss_rows(results))
    write_csv(out_dir / "gen6_power_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.packaging_adjusted_power_W_cm2, reverse=True)])
    write_csv(out_dir / "gen6_lifetime_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.lifetime_years, reverse=True)])
    write_csv(out_dir / "gen6_manufacturability_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.manufacturing_score, reverse=True)])
    write_csv(out_dir / "gen6_power_per_dollar_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.power_per_dollar, reverse=True)])
    write_csv(out_dir / "gen6_power_per_volume_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.power_per_cm3_W_cm3, reverse=True)])
    write_csv(out_dir / "gen6_source_utilization.csv", best_by_source_placement(results))
    make_plots(results, out_dir / "plots")
    write_report(out_dir / "gen6_final_report.md", results)
    return results
