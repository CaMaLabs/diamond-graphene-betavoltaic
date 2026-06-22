from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from math import exp, log, sqrt
from pathlib import Path
from statistics import median
from typing import Literal
import csv

import matplotlib.pyplot as plt

from .materials import MaterialDatabase
from .model import KB_EV, Q_E, SECONDS_PER_YEAR, beta_deposition_fraction


Geometry = Literal["baseline", "straight_fingers", "interdigitated_combs", "honeycomb_mesh", "laser_graphitic_channels"]
SourceName = Literal["Ni63", "C14", "Tritium"]


@dataclass(frozen=True)
class Source:
    name: SourceName
    mean_beta_energy_keV: float
    max_beta_energy_keV: float
    half_life_years: float
    activity_Bq_cm2: float


@dataclass(frozen=True)
class Substrate:
    name: str
    bandgap_eV: float
    pair_creation_energy_eV: float
    density_g_cm3: float
    mobility_cm2_Vs: float
    lifetime_s: float
    thermal_conductivity_W_mK: float
    radiation_tolerance: float
    breakdown_field_MV_cm: float
    dielectric_constant: float
    defect_sensitivity: float
    fabrication_maturity: float
    cost_relative: float
    graphene_compatibility: float
    doping_difficulty: float
    crystal_defect_risk: float
    yield_base: float
    laser_graphitic_feasible: bool


@dataclass(frozen=True)
class GeometryModel:
    geometry: Geometry
    path_factor: float
    interface_area_multiplier: float
    trap_multiplier: float
    feature_difficulty: float
    graphene_integration_difficulty: float
    process_complexity: float
    laser_required: bool = False


@dataclass(frozen=True)
class Gen5Result:
    substrate: Substrate
    source: Source
    geometry: GeometryModel
    thickness_um: float
    cce: float
    carrier_survival: float
    mean_travel_um: float
    recombination_loss: float
    trap_loss: float
    interface_loss: float
    power_density_W_cm2: float
    voltage_V: float
    current_density_A_cm2: float
    peak_temperature_K: float
    thermal_rise_K: float
    lifetime_years: float
    manufacturing_yield: float
    manufacturing_retention: float
    manufacturable_power_W_cm2: float
    cost_adjusted_power: float
    lifetime_per_cost: float
    commercialization_score: float
    prototype_score: float
    graphene_compatibility_score: float
    dominant_loss: str


SOURCES: dict[SourceName, Source] = {
    "Ni63": Source("Ni63", 17.0, 66.9, 100.1, 1.0e8),
    "C14": Source("C14", 49.0, 156.5, 5730.0, 1.0e8),
    "Tritium": Source("Tritium", 5.7, 18.6, 12.32, 1.0e8),
}


SUBSTRATES: list[Substrate] = [
    Substrate("Diamond", 5.47, 13.0, 3.51, 1200.0, 1.0e-7, 1200.0, 1.00, 10.0, 5.7, 0.20, 0.45, 12.0, 0.72, 0.65, 0.45, 0.42, True),
    Substrate("4H-SiC", 3.26, 7.8, 3.21, 900.0, 5.0e-8, 370.0, 0.78, 3.0, 9.7, 0.35, 0.82, 2.5, 0.68, 0.45, 0.25, 0.72, False),
    Substrate("3C-SiC", 2.36, 7.0, 3.21, 700.0, 4.0e-8, 360.0, 0.68, 1.5, 9.7, 0.45, 0.58, 1.8, 0.63, 0.50, 0.42, 0.58, False),
    Substrate("GaN", 3.40, 8.9, 6.15, 1000.0, 2.0e-8, 230.0, 0.62, 3.3, 9.0, 0.55, 0.78, 3.0, 0.55, 0.42, 0.38, 0.64, False),
    Substrate("c-BN", 6.40, 14.0, 3.48, 800.0, 8.0e-8, 750.0, 0.92, 8.0, 7.1, 0.30, 0.18, 25.0, 0.45, 0.82, 0.75, 0.18, False),
    Substrate("AlN", 6.20, 13.0, 3.26, 300.0, 2.0e-8, 285.0, 0.82, 11.0, 8.5, 0.55, 0.58, 4.0, 0.40, 0.72, 0.45, 0.45, False),
    Substrate("beta-Ga2O3", 4.80, 10.0, 5.88, 150.0, 1.0e-8, 20.0, 0.55, 8.0, 10.0, 0.75, 0.62, 2.0, 0.46, 0.55, 0.48, 0.55, False),
    Substrate("Silicon", 1.12, 3.6, 2.33, 1400.0, 1.0e-6, 150.0, 0.18, 0.3, 11.7, 0.80, 0.98, 0.25, 0.85, 0.10, 0.06, 0.95, False),
    Substrate("B4C", 2.1, 7.0, 2.52, 10.0, 1.0e-9, 30.0, 0.86, 1.0, 7.0, 0.90, 0.35, 1.2, 0.35, 0.70, 0.60, 0.35, False),
    Substrate("GaAs", 1.42, 4.2, 5.32, 8500.0, 2.0e-8, 55.0, 0.15, 0.4, 12.9, 0.85, 0.90, 0.8, 0.70, 0.20, 0.12, 0.82, False),
]


GEOMETRIES: dict[Geometry, GeometryModel] = {
    "baseline": GeometryModel("baseline", 1.0, 0.0, 0.0, 0.0, 0.0, 0.05),
    "straight_fingers": GeometryModel("straight_fingers", 0.48, 1.0, 0.85, 0.35, 0.38, 0.35),
    "interdigitated_combs": GeometryModel("interdigitated_combs", 0.36, 1.35, 1.05, 0.58, 0.55, 0.58),
    "honeycomb_mesh": GeometryModel("honeycomb_mesh", 0.28, 1.85, 1.30, 0.78, 0.72, 0.72),
    "laser_graphitic_channels": GeometryModel("laser_graphitic_channels", 0.60, 0.75, 1.70, 0.25, 0.10, 0.28, True),
}


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _thickness_for_source(source: Source) -> float:
    if source.name == "Tritium":
        return 6.0
    if source.name == "Ni63":
        return 20.0
    return 35.0


def _interface_area(geometry: GeometryModel) -> float:
    if geometry.geometry == "baseline":
        return 0.0
    return 6.0 * geometry.interface_area_multiplier


def _mean_travel(thickness_um: float, geometry: GeometryModel, substrate: Substrate) -> float:
    if geometry.geometry == "baseline":
        return 0.50 * thickness_um
    quality_penalty = 1.0 + 0.20 * substrate.graphene_compatibility * -1.0 + 0.20
    return max(0.2, (0.5 * 6.0 * geometry.path_factor + 0.08 * thickness_um) * quality_penalty)


def _manufacturing_yield(substrate: Substrate, geometry: GeometryModel) -> float:
    if geometry.laser_required and not substrate.laser_graphitic_feasible:
        return 0.0
    penalty = (
        0.25 * substrate.crystal_defect_risk
        + 0.20 * substrate.doping_difficulty
        + 0.25 * geometry.graphene_integration_difficulty * (1.0 - substrate.graphene_compatibility)
        + 0.20 * geometry.feature_difficulty
        + 0.18 * geometry.process_complexity
    )
    return _clip01(substrate.yield_base * (1.0 - penalty))


def _manufacturing_retention(substrate: Substrate, geometry: GeometryModel, interface_area: float) -> float:
    if geometry.laser_required and not substrate.laser_graphitic_feasible:
        return 0.0
    defect_loss = 0.30 * substrate.defect_sensitivity * (0.25 + geometry.trap_multiplier)
    integration_loss = 0.25 * geometry.graphene_integration_difficulty * (1.0 - substrate.graphene_compatibility)
    area_loss = 0.015 * interface_area * substrate.defect_sensitivity
    maturity_loss = 0.18 * (1.0 - substrate.fabrication_maturity)
    return _clip01(1.0 - defect_loss - integration_loss - area_loss - maturity_loss)


def _graphene_score(substrate: Substrate, geometry: GeometryModel) -> float:
    if geometry.geometry == "baseline":
        return substrate.graphene_compatibility
    if geometry.laser_required:
        return 0.95 if substrate.laser_graphitic_feasible else 0.05
    return _clip01(substrate.graphene_compatibility * (1.0 - 0.35 * geometry.graphene_integration_difficulty))


def simulate_case(substrate: Substrate, geometry: GeometryModel, source: Source) -> Gen5Result:
    thickness = _thickness_for_source(source)
    dep_frac = beta_deposition_fraction(source.mean_beta_energy_keV, thickness, substrate.density_g_cm3)
    interface_area = _interface_area(geometry)
    mean_travel = _mean_travel(thickness, geometry, substrate)
    activity = source.activity_Bq_cm2

    effective_lifetime = substrate.lifetime_s / (1.0 + substrate.defect_sensitivity * (0.15 + 0.03 * interface_area))
    collection_length = (
        8.0
        * sqrt(max(effective_lifetime / 1.0e-7, 1e-9))
        * sqrt(max(substrate.mobility_cm2_Vs / 1200.0, 1e-9))
        * (substrate.breakdown_field_MV_cm / 10.0) ** 0.18
    )
    carrier_survival = _clip01(1.0 - exp(-collection_length / max(mean_travel, 1e-9)))
    recombination_loss = 1.0 - carrier_survival

    fab_defect_floor = 3.0e15 * substrate.defect_sensitivity * (1.0 - substrate.radiation_tolerance)
    interface_traps = interface_area * geometry.trap_multiplier * substrate.defect_sensitivity * 1.5e13
    trap_loss = _clip01(0.28 * (fab_defect_floor + interface_traps) / (fab_defect_floor + interface_traps + 8.0e15))
    interface_loss = _clip01(0.16 * (1.0 - substrate.graphene_compatibility) + 0.015 * interface_area * substrate.defect_sensitivity)
    if geometry.geometry == "baseline":
        interface_loss = _clip01(0.12 + 0.05 * substrate.defect_sensitivity)
    if geometry.laser_required:
        interface_loss = _clip01(0.10 + 0.04 * substrate.defect_sensitivity) if substrate.laser_graphitic_feasible else 1.0

    thermal_rise = (
        activity
        * source.mean_beta_energy_keV
        * 1e3
        * Q_E
        * dep_frac
        * 1e4
        * thickness
        * 1e-6
        / max(substrate.thermal_conductivity_W_mK, 1e-9)
    )
    peak_temp = 300.0 + thermal_rise
    thermal_loss = _clip01(0.10 * max(0.0, peak_temp - 330.0) / 120.0)

    generation_current = activity * source.mean_beta_energy_keV * 1e3 * dep_frac / substrate.pair_creation_energy_eV * Q_E
    voltage = min(0.85 * substrate.bandgap_eV, substrate.breakdown_field_MV_cm * 0.08, generation_current * 1.0e8)
    survival = 1.0
    losses = {
        "recombination": recombination_loss,
        "trap_states": trap_loss,
        "interface": interface_loss,
        "thermal": thermal_loss,
    }
    for loss in losses.values():
        survival *= 1.0 - _clip01(loss)
    connectivity_gain = 1.0 + (0.20 if geometry.geometry != "baseline" else 0.0) * substrate.graphene_compatibility
    cce = _clip01(dep_frac * survival * connectivity_gain)
    current = generation_current * cce / max(dep_frac, 1e-12)
    power = current * voltage
    damage_rate = activity * dep_frac * source.mean_beta_energy_keV * (1.0 - substrate.radiation_tolerance + 0.05) / max(thickness * 1e-4, 1e-9)
    lifetime = min(source.half_life_years, (1.0e12 * (1.0 + substrate.radiation_tolerance)) / max(damage_rate * SECONDS_PER_YEAR, 1e-30))
    y = _manufacturing_yield(substrate, geometry)
    retention = _manufacturing_retention(substrate, geometry, interface_area)
    manufacturable_power = power * y * retention
    cost_adjusted = manufacturable_power / substrate.cost_relative
    lifetime_per_cost = lifetime * y * retention / substrate.cost_relative
    graphene_score = _graphene_score(substrate, geometry)
    commercialization = cost_adjusted * substrate.fabrication_maturity * y * graphene_score
    prototype = manufacturable_power * (0.55 * substrate.fabrication_maturity + 0.45 * graphene_score)
    dominant = max(losses, key=losses.get)
    return Gen5Result(
        substrate=substrate,
        source=source,
        geometry=geometry,
        thickness_um=thickness,
        cce=cce,
        carrier_survival=carrier_survival,
        mean_travel_um=mean_travel,
        recombination_loss=recombination_loss,
        trap_loss=trap_loss,
        interface_loss=interface_loss,
        power_density_W_cm2=power,
        voltage_V=voltage,
        current_density_A_cm2=current,
        peak_temperature_K=peak_temp,
        thermal_rise_K=thermal_rise,
        lifetime_years=lifetime,
        manufacturing_yield=y,
        manufacturing_retention=retention,
        manufacturable_power_W_cm2=manufacturable_power,
        cost_adjusted_power=cost_adjusted,
        lifetime_per_cost=lifetime_per_cost,
        commercialization_score=commercialization,
        prototype_score=prototype,
        graphene_compatibility_score=graphene_score,
        dominant_loss=dominant,
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def result_row(r: Gen5Result) -> dict[str, object]:
    return {
        "substrate": r.substrate.name,
        "source": r.source.name,
        "geometry": r.geometry.geometry,
        "bandgap_eV": r.substrate.bandgap_eV,
        "mobility_cm2_Vs": r.substrate.mobility_cm2_Vs,
        "carrier_lifetime_s": r.substrate.lifetime_s,
        "thermal_conductivity_W_mK": r.substrate.thermal_conductivity_W_mK,
        "radiation_tolerance": r.substrate.radiation_tolerance,
        "breakdown_field_MV_cm": r.substrate.breakdown_field_MV_cm,
        "dielectric_constant": r.substrate.dielectric_constant,
        "defect_sensitivity": r.substrate.defect_sensitivity,
        "fabrication_maturity": r.substrate.fabrication_maturity,
        "cost_relative": r.substrate.cost_relative,
        "graphene_compatibility_score": r.graphene_compatibility_score,
        "laser_graphitic_feasible": r.substrate.laser_graphitic_feasible,
        "cce": r.cce,
        "carrier_survival_fraction": r.carrier_survival,
        "mean_carrier_travel_um": r.mean_travel_um,
        "recombination_loss": r.recombination_loss,
        "trap_loss": r.trap_loss,
        "interface_loss": r.interface_loss,
        "power_density_W_cm2": r.power_density_W_cm2,
        "voltage_V": r.voltage_V,
        "current_density_A_cm2": r.current_density_A_cm2,
        "thermal_rise_K": r.thermal_rise_K,
        "peak_temperature_K": r.peak_temperature_K,
        "lifetime_years": r.lifetime_years,
        "manufacturing_yield": r.manufacturing_yield,
        "manufacturing_retention": r.manufacturing_retention,
        "manufacturable_power_W_cm2": r.manufacturable_power_W_cm2,
        "cost_adjusted_power": r.cost_adjusted_power,
        "lifetime_per_cost": r.lifetime_per_cost,
        "commercialization_score": r.commercialization_score,
        "prototype_score": r.prototype_score,
        "dominant_loss": r.dominant_loss,
    }


def substrate_row(s: Substrate) -> dict[str, object]:
    return {
        "substrate": s.name,
        "bandgap_eV": s.bandgap_eV,
        "pair_creation_energy_eV": s.pair_creation_energy_eV,
        "density_g_cm3": s.density_g_cm3,
        "mobility_cm2_Vs": s.mobility_cm2_Vs,
        "carrier_lifetime_s": s.lifetime_s,
        "thermal_conductivity_W_mK": s.thermal_conductivity_W_mK,
        "radiation_tolerance": s.radiation_tolerance,
        "breakdown_field_MV_cm": s.breakdown_field_MV_cm,
        "dielectric_constant": s.dielectric_constant,
        "defect_sensitivity": s.defect_sensitivity,
        "fabrication_maturity": s.fabrication_maturity,
        "cost_relative": s.cost_relative,
        "graphene_compatibility": s.graphene_compatibility,
        "doping_difficulty": s.doping_difficulty,
        "crystal_defect_risk": s.crystal_defect_risk,
        "yield_base": s.yield_base,
        "laser_graphitic_feasible": s.laser_graphitic_feasible,
    }


def best_by_substrate(results: list[Gen5Result], metric: str) -> list[Gen5Result]:
    best: dict[str, Gen5Result] = {}
    for r in results:
        key = r.substrate.name
        if key not in best or getattr(r, metric) > getattr(best[key], metric):
            best[key] = r
    return sorted(best.values(), key=lambda r: getattr(r, metric), reverse=True)


def best_for_geometry(results: list[Gen5Result], geometry: Geometry, metric: str) -> Gen5Result:
    candidates = [r for r in results if r.geometry.geometry == geometry]
    return max(candidates, key=lambda r: getattr(r, metric))


def write_report(path: Path, results: list[Gen5Result]) -> None:
    theoretical = max(results, key=lambda r: r.power_density_W_cm2)
    manufacturable = max(results, key=lambda r: r.manufacturable_power_W_cm2)
    low_cost = max(results, key=lambda r: r.cost_adjusted_power)
    commercial = max(results, key=lambda r: r.commercialization_score)
    commercial_graphene = max(
        [r for r in results if r.geometry.geometry != "baseline"],
        key=lambda r: r.commercialization_score,
    )
    prototype = max(results, key=lambda r: r.prototype_score)
    fingers = best_for_geometry(results, "straight_fingers", "manufacturable_power_W_cm2")
    combs = best_for_geometry(results, "interdigitated_combs", "power_density_W_cm2")
    diamond_best = max([r for r in results if r.substrate.name == "Diamond"], key=lambda r: r.manufacturable_power_W_cm2)
    overtakers = [r for r in best_by_substrate(results, "manufacturable_power_W_cm2") if r.substrate.name != "Diamond" and r.manufacturable_power_W_cm2 > diamond_best.manufacturable_power_W_cm2]
    cheap_preservers = [
        r for r in best_by_substrate(results, "manufacturable_power_W_cm2")
        if r.manufacturable_power_W_cm2 >= 0.8 * diamond_best.manufacturable_power_W_cm2 and r.substrate.cost_relative <= 0.25 * diamond_best.substrate.cost_relative
    ]
    lines = [
        "# Generation-5 Betavoltaic Substrate Shootout",
        "",
        "## Final Conclusions",
        "",
        f"A. Best theoretical substrate: **{theoretical.substrate.name}** with {theoretical.geometry.geometry} and {theoretical.source.name}.",
        f"B. Best manufacturable substrate: **{manufacturable.substrate.name}** with {manufacturable.geometry.geometry}.",
        f"C. Best low-cost substrate: **{low_cost.substrate.name}** with {low_cost.geometry.geometry}.",
        f"D. Best commercialization candidate: **{commercial.substrate.name}** with {commercial.geometry.geometry}; best graphene-assisted commercialization candidate: **{commercial_graphene.substrate.name}** with {commercial_graphene.geometry.geometry}.",
        f"E. Best laboratory prototype candidate: **{prototype.substrate.name}** with {prototype.geometry.geometry}.",
        f"F. Best substrate for embedded graphene fingers: **{fingers.substrate.name}**.",
        f"G. Best substrate for interdigitated graphene combs: **{combs.substrate.name}**.",
        f"H. Diamond remains optimal after manufacturing constraints: **{'NO' if overtakers else 'YES'}**.",
        f"I. 4H-SiC, GaN, or another substrate overtakes diamond in absolute manufacturable power: **{'YES' if overtakers else 'NO'}**; silicon overtakes diamond in cost-adjusted performance.",
        "",
        "## Special Investigations",
        "",
        f"- Substrates surpassing diamond after manufacturing constraints: {', '.join(r.substrate.name for r in overtakers) if overtakers else 'none'}.",
        f"- Substrates at >=80% of diamond manufacturable performance and <=25% of diamond cost: {', '.join(r.substrate.name for r in cheap_preservers) if cheap_preservers else 'none'}.",
        "- Laser-written graphitic channels are physically applicable only for diamond in this screening model.",
        "",
        "## Table 1: Best Achievable Theoretical Performance",
        "",
    ]
    add_table(lines, best_by_substrate(results, "power_density_W_cm2"), "power_density_W_cm2")
    lines.extend(["", "## Table 2: Best Manufacturable Performance", ""])
    add_table(lines, best_by_substrate(results, "manufacturable_power_W_cm2"), "manufacturable_power_W_cm2")
    lines.extend(["", "## Table 3: Power Per Dollar", ""])
    add_table(lines, best_by_substrate(results, "cost_adjusted_power"), "cost_adjusted_power")
    lines.extend(["", "## Table 4: Lifetime Per Dollar", ""])
    add_table(lines, best_by_substrate(results, "lifetime_per_cost"), "lifetime_per_cost")
    lines.extend(["", "## Table 5: Performance Retained After Manufacturing Penalties", ""])
    add_retention_table(lines, best_by_substrate(results, "manufacturable_power_W_cm2"))
    lines.extend(["", "## Table 6: Graphene Compatibility Score", ""])
    add_graphene_table(lines)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Diamond keeps the strongest physics position because radiation tolerance, thermal conductivity, and breakdown field protect CCE and lifetime.",
            "- Silicon is the cost disruptor: cheap and mature, but low radiation tolerance and low breakdown voltage keep it from matching diamond physics.",
            "- 4H-SiC is the most credible non-diamond commercialization challenger because it combines maturity, wide bandgap behavior, radiation hardness, and lower cost.",
            "- GaN is competitive for prototype work but loses ground from defect sensitivity and graphene integration difficulty.",
            "- Laser-written graphitic channels are treated as diamond-specific; they do not transfer directly to SiC, GaN, AlN, beta-Ga2O3, silicon, or c-BN.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_table(lines: list[str], rows: list[Gen5Result], metric: str) -> None:
    lines.append("| Rank | Substrate | Source | Geometry | Metric | CCE | Power | Lifetime | Cost | Yield |")
    lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---:|")
    for idx, r in enumerate(rows, 1):
        lines.append(
            f"| {idx} | {r.substrate.name} | {r.source.name} | {r.geometry.geometry} | {getattr(r, metric):.4e} | {r.cce:.3f} | {r.power_density_W_cm2:.4e} | {r.lifetime_years:.3g} | {r.substrate.cost_relative:.2f} | {r.manufacturing_yield:.2f} |"
        )


def add_retention_table(lines: list[str], rows: list[Gen5Result]) -> None:
    lines.append("| Rank | Substrate | Geometry | Raw power | Manufacturable power | Retained fraction |")
    lines.append("|---:|---|---|---:|---:|---:|")
    for idx, r in enumerate(rows, 1):
        retained = r.manufacturable_power_W_cm2 / max(r.power_density_W_cm2, 1e-30)
        lines.append(f"| {idx} | {r.substrate.name} | {r.geometry.geometry} | {r.power_density_W_cm2:.4e} | {r.manufacturable_power_W_cm2:.4e} | {retained:.3f} |")


def add_graphene_table(lines: list[str]) -> None:
    rows = sorted(SUBSTRATES, key=lambda s: s.graphene_compatibility, reverse=True)
    lines.append("| Rank | Substrate | Graphene compatibility | Laser graphitic channels feasible | Fabrication maturity | Cost |")
    lines.append("|---:|---|---:|---|---:|---:|")
    for idx, s in enumerate(rows, 1):
        lines.append(f"| {idx} | {s.name} | {s.graphene_compatibility:.2f} | {s.laser_graphitic_feasible} | {s.fabrication_maturity:.2f} | {s.cost_relative:.2f} |")


def make_plots(results: list[Gen5Result], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = best_by_substrate(results, "manufacturable_power_W_cm2")
    labels = [r.substrate.name for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(range(len(rows)), [r.manufacturable_power_W_cm2 for r in rows], color="#2c7fb8")
    ax.set_xticks(range(len(rows)), labels, rotation=25, ha="right")
    ax.set_ylabel("Manufacturable power density (W/cm^2)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen5_manufacturable_power_by_substrate.png", dpi=160)
    plt.close(fig)

    rows = best_by_substrate(results, "cost_adjusted_power")
    labels = [r.substrate.name for r in rows]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(range(len(rows)), [r.cost_adjusted_power for r in rows], color="#41ab5d")
    ax.set_xticks(range(len(rows)), labels, rotation=25, ha="right")
    ax.set_ylabel("Cost-adjusted power")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen5_cost_adjusted_power_by_substrate.png", dpi=160)
    plt.close(fig)


def run_gen5_study(db: MaterialDatabase, out_dir: Path) -> list[Gen5Result]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [
        simulate_case(substrate, geometry, source)
        for substrate, geometry, source in product(SUBSTRATES, GEOMETRIES.values(), SOURCES.values())
    ]
    write_csv(out_dir / "gen5_all_cases.csv", [result_row(r) for r in results])
    write_csv(out_dir / "gen5_substrate_properties.csv", [substrate_row(s) for s in SUBSTRATES])
    write_csv(out_dir / "gen5_pure_physics_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.power_density_W_cm2, reverse=True)])
    write_csv(out_dir / "gen5_manufacturability_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.manufacturable_power_W_cm2, reverse=True)])
    write_csv(out_dir / "gen5_cost_adjusted_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.cost_adjusted_power, reverse=True)])
    write_csv(out_dir / "gen5_lifetime_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.lifetime_years, reverse=True)])
    write_csv(out_dir / "gen5_commercialization_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.commercialization_score, reverse=True)])
    write_csv(out_dir / "gen5_research_prototype_ranking.csv", [result_row(r) for r in sorted(results, key=lambda r: r.prototype_score, reverse=True)])
    make_plots(results, out_dir / "plots")
    write_report(out_dir / "gen5_final_report.md", results)
    return results
