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


Geometry = Literal[
    "baseline",
    "straight_fingers",
    "interdigitated_combs",
    "honeycomb_mesh",
    "radial_spokes",
    "fractal_tree",
    "multilayer_3d_mesh",
    "random_percolating_nanoribbons",
]


@dataclass(frozen=True)
class Gen3Params:
    geometry: Geometry
    source: str = "Ni63"
    diamond_um: float = 20.0
    pitch_um: float = 4.0
    ribbon_width_nm: float = 50.0
    graphene_layers: int = 1
    network_depth_fraction: float = 0.75
    electric_field_V_cm: float = 5.0e4
    temperature_K: float = 300.0
    surface_recombination_cm_s: float = 1.0e3
    interface_trap_density_cm2: float = 1.0e11
    trap_density_cm3: float = 1.0e14
    activity_Bq_cm2: float | None = None
    load_resistance_ohm_cm2: float = 1.0e8


@dataclass(frozen=True)
class GeometrySpec:
    geometry: Geometry
    path_factor: float
    interface_multiplier: float
    trap_multiplier: float
    collection_connectivity: float
    sheet_resistance_multiplier: float
    manufacturability_base: float
    manufacturability_slope: float
    departure_rank: int


@dataclass(frozen=True)
class Gen3Result:
    params: Gen3Params
    mean_carrier_travel_um: float
    graphene_interface_area_ratio: float
    added_trap_density_cm3: float
    interface_loss_fraction: float
    trap_penalty_fraction: float
    carrier_survival_fraction: float
    collection_efficiency: float
    current_density_A_cm2: float
    voltage_V: float
    power_density_W_cm2: float
    lifetime_years: float
    manufacturability_score: float
    geometry_departure_score: float
    net_power_ratio_vs_baseline: float
    loss_budget: dict[str, float]


GEOMETRIES: dict[Geometry, GeometrySpec] = {
    "baseline": GeometrySpec("baseline", 1.0, 0.0, 0.0, 1.0, 1.0, 0.98, 0.0, 0),
    "straight_fingers": GeometrySpec("straight_fingers", 0.48, 1.00, 0.85, 0.78, 1.18, 0.82, 0.10, 1),
    "interdigitated_combs": GeometrySpec("interdigitated_combs", 0.36, 1.35, 1.05, 0.88, 1.05, 0.72, 0.13, 2),
    "radial_spokes": GeometrySpec("radial_spokes", 0.42, 1.20, 0.95, 0.82, 1.16, 0.70, 0.15, 3),
    "honeycomb_mesh": GeometrySpec("honeycomb_mesh", 0.28, 1.85, 1.30, 0.94, 0.92, 0.55, 0.18, 4),
    "fractal_tree": GeometrySpec("fractal_tree", 0.24, 2.15, 1.45, 0.91, 0.98, 0.43, 0.22, 5),
    "random_percolating_nanoribbons": GeometrySpec(
        "random_percolating_nanoribbons", 0.30, 2.80, 1.85, 0.74, 1.45, 0.48, 0.20, 6
    ),
    "multilayer_3d_mesh": GeometrySpec("multilayer_3d_mesh", 0.16, 3.30, 2.20, 0.98, 0.75, 0.30, 0.25, 7),
}


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _coverage_fraction(params: Gen3Params, spec: GeometrySpec) -> float:
    if params.geometry == "baseline":
        return 0.0
    width_um = params.ribbon_width_nm * 1e-3
    raw = spec.interface_multiplier * width_um / max(params.pitch_um, width_um)
    raw *= sqrt(max(params.graphene_layers, 1))
    return _clip01(raw)


def _interface_area_ratio(params: Gen3Params, spec: GeometrySpec) -> float:
    if params.geometry == "baseline":
        return 0.0
    width_um = params.ribbon_width_nm * 1e-3
    sidewall = 2.0 * params.network_depth_fraction * params.diamond_um / max(params.pitch_um, width_um)
    basal = width_um / max(params.pitch_um, width_um)
    return max(0.0, spec.interface_multiplier * (sidewall + basal) * max(params.graphene_layers, 1) ** 0.65)


def _mean_travel_um(params: Gen3Params, spec: GeometrySpec, interface_area_ratio: float) -> float:
    if params.geometry == "baseline":
        return 0.50 * params.diamond_um
    nearest_collector = 0.5 * params.pitch_um * spec.path_factor
    vertical_term = 0.20 * params.diamond_um * max(0.0, 1.0 - params.network_depth_fraction)
    crowding_penalty = 1.0 + 0.025 * max(0.0, interface_area_ratio - 4.0)
    return max(0.05, (nearest_collector + vertical_term) * crowding_penalty)


def _manufacturability(params: Gen3Params, spec: GeometrySpec, interface_area_ratio: float) -> float:
    if params.geometry == "baseline":
        return spec.manufacturability_base
    width_penalty = max(0.0, (35.0 - params.ribbon_width_nm) / 35.0)
    pitch_penalty = max(0.0, (1.0 - params.pitch_um) / 1.0)
    layer_penalty = max(0, params.graphene_layers - 1) * 0.07
    area_penalty = spec.manufacturability_slope * min(interface_area_ratio / 10.0, 2.0)
    return _clip01(spec.manufacturability_base - width_penalty * 0.20 - pitch_penalty * 0.12 - layer_penalty - area_penalty)


def simulate_gen3(params: Gen3Params, db: MaterialDatabase, baseline_power: float | None = None) -> Gen3Result:
    spec = GEOMETRIES[params.geometry]
    source = db.sources[params.source]
    diamond = db.diamond
    graphene = db.graphene
    activity = params.activity_Bq_cm2 or source.default_activity_Bq_cm2
    dep_frac = beta_deposition_fraction(source.mean_beta_energy_keV, params.diamond_um, diamond["density_g_cm3"])
    generated_current = activity * source.mean_beta_energy_keV * 1e3 * dep_frac / diamond["pair_creation_energy_eV"] * Q_E

    interface_area_ratio = _interface_area_ratio(params, spec)
    coverage = _coverage_fraction(params, spec)
    mean_travel_um = _mean_travel_um(params, spec, interface_area_ratio)

    base_traps = params.trap_density_cm3
    areal_trap_to_volume = params.interface_trap_density_cm2 * interface_area_ratio / max(params.diamond_um * 1e-4, 1e-12)
    added_traps = spec.trap_multiplier * areal_trap_to_volume * 0.035
    graphene_bulk_traps = coverage * 2.0e15 * 0.10
    gen2_trap_floor = 3.0e15
    effective_traps = base_traps + gen2_trap_floor + added_traps + graphene_bulk_traps

    damage_rate = (
        activity
        * dep_frac
        * source.mean_beta_energy_keV
        * diamond["radiation_damage_coeff_cm2"]
        / max(params.diamond_um * 1e-4, 1e-9)
        * 1e18
        * (1.0 - 0.18 * coverage)
    )
    carrier_lifetime_s = 1.0 / (
        1.0 / diamond["baseline_lifetime_s"]
        + diamond["trap_capture_coeff_cm3_s"] * effective_traps
        + 1e3 * exp(-(diamond["bandgap_eV"] / 2.0) / (KB_EV * params.temperature_K))
    )
    effective_collection_um = (
        8.0
        * sqrt(max(carrier_lifetime_s / diamond["baseline_lifetime_s"], 1e-9))
        * (max(params.electric_field_V_cm, 1.0) / 5.0e4) ** 0.20
    )
    carrier_survival = _clip01(1.0 - exp(-effective_collection_um / max(mean_travel_um, 1e-12)))

    interface_trap_loss = 0.18 * added_traps / (added_traps + 8.0e15)
    surface_loss_arg = params.surface_recombination_cm_s * carrier_lifetime_s * interface_area_ratio / max(params.diamond_um * 1e-4, 1e-12)
    surface_recombination_loss = 0.22 * surface_loss_arg / (1.0 + surface_loss_arg)
    graphene_contact_loss = 0.08 * log(1.0 + graphene["sheet_resistance_ohm_sq"] * spec.sheet_resistance_multiplier / 500.0) / log(10.0)
    collector_interface_floor = 0.18
    internal_area_loss = interface_trap_loss + surface_recombination_loss + graphene_contact_loss * coverage
    interface_loss = _clip01(max(collector_interface_floor * (1.0 - 0.55 * coverage), 0.08) + internal_area_loss)
    trap_penalty = _clip01(0.28 * effective_traps / (effective_traps + 8.0e15))
    geometry_occlusion = _clip01(0.08 * coverage + 0.015 * max(0.0, interface_area_ratio - 8.0))
    manufacturability_risk_loss = _clip01(0.05 * (1.0 - _manufacturability(params, spec, interface_area_ratio)))
    connectivity_gain = 1.0 + 0.28 * coverage * spec.collection_connectivity

    survival_terms = {
        "carrier_travel_recombination": 1.0 - carrier_survival,
        "graphene_diamond_interface": interface_loss,
        "trap_area_penalty": trap_penalty,
        "geometric_occlusion": geometry_occlusion,
        "manufacturing_risk_proxy": manufacturability_risk_loss,
    }
    total_survival = 1.0
    for loss in survival_terms.values():
        total_survival *= 1.0 - _clip01(loss)
    cce = _clip01(dep_frac * total_survival * connectivity_gain)
    current = generated_current * cce / max(dep_frac, 1e-12)
    voltage = min(0.92 * diamond["bandgap_eV"], current * params.load_resistance_ohm_cm2)
    power = current * voltage

    threshold = max(effective_traps, 1.0e12)
    lifetime_years = min(source.half_life_years, threshold / max(damage_rate * SECONDS_PER_YEAR, 1e-30))
    manufacturability = _manufacturability(params, spec, interface_area_ratio)
    departure = spec.departure_rank + coverage + 0.08 * max(0, params.graphene_layers - 1) + 0.02 * interface_area_ratio

    return Gen3Result(
        params=params,
        mean_carrier_travel_um=mean_travel_um,
        graphene_interface_area_ratio=interface_area_ratio,
        added_trap_density_cm3=added_traps + graphene_bulk_traps,
        interface_loss_fraction=interface_loss,
        trap_penalty_fraction=trap_penalty,
        carrier_survival_fraction=carrier_survival,
        collection_efficiency=cce,
        current_density_A_cm2=current,
        voltage_V=voltage,
        power_density_W_cm2=power,
        lifetime_years=lifetime_years,
        manufacturability_score=manufacturability,
        geometry_departure_score=departure,
        net_power_ratio_vs_baseline=power / max(baseline_power or power, 1e-30),
        loss_budget=survival_terms,
    )


def gen3_params(preset: str = "focused") -> list[Gen3Params]:
    if preset == "smoke":
        diamonds = [20.0]
        pitches = [2.0, 6.0]
        widths = [25.0, 100.0]
        layers = [1, 2]
        depths = [0.75]
    else:
        diamonds = [8.0, 12.0, 20.0]
        pitches = [0.75, 1.5, 3.0, 6.0, 12.0]
        widths = [15.0, 30.0, 60.0, 120.0]
        layers = [1, 2, 4]
        depths = [0.35, 0.65, 0.9]
    rows = [Gen3Params("baseline", diamond_um=d) for d in diamonds]
    for geometry in GEOMETRIES:
        if geometry == "baseline":
            continue
        for d, pitch, width, layer, depth in product(diamonds, pitches, widths, layers, depths):
            rows.append(
                Gen3Params(
                    geometry=geometry,
                    diamond_um=d,
                    pitch_um=pitch,
                    ribbon_width_nm=width,
                    graphene_layers=layer,
                    network_depth_fraction=depth,
                )
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def result_row(result: Gen3Result) -> dict[str, object]:
    p = result.params
    return {
        "geometry": p.geometry,
        "source": p.source,
        "diamond_um": p.diamond_um,
        "pitch_um": p.pitch_um,
        "ribbon_width_nm": p.ribbon_width_nm,
        "graphene_layers": p.graphene_layers,
        "network_depth_fraction": p.network_depth_fraction,
        "mean_carrier_travel_um": result.mean_carrier_travel_um,
        "graphene_interface_area_ratio": result.graphene_interface_area_ratio,
        "added_trap_density_cm3": result.added_trap_density_cm3,
        "interface_loss_fraction": result.interface_loss_fraction,
        "trap_penalty_fraction": result.trap_penalty_fraction,
        "carrier_survival_fraction": result.carrier_survival_fraction,
        "collection_efficiency": result.collection_efficiency,
        "current_density_A_cm2": result.current_density_A_cm2,
        "voltage_V": result.voltage_V,
        "power_density_W_cm2": result.power_density_W_cm2,
        "net_power_ratio_vs_baseline": result.net_power_ratio_vs_baseline,
        "lifetime_years": result.lifetime_years,
        "manufacturability_score": result.manufacturability_score,
        "geometry_departure_score": result.geometry_departure_score,
        "dominant_loss": max(result.loss_budget, key=result.loss_budget.get),
        "dominant_loss_fraction": max(result.loss_budget.values()),
    }


def loss_rows(results: list[Gen3Result]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id, result in enumerate(results):
        for name, value in result.loss_budget.items():
            rows.append(
                {
                    "case_id": case_id,
                    "geometry": result.params.geometry,
                    "loss_channel": name,
                    "loss_fraction": value,
                }
            )
    return rows


def median_by_geometry(results: list[Gen3Result], attr: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in results:
        grouped[result.params.geometry].append(float(getattr(result, attr)))
    return {geometry: median(values) for geometry, values in grouped.items()}


def ranking_rows(results: list[Gen3Result]) -> list[dict[str, object]]:
    med_power = median_by_geometry(results, "power_density_W_cm2")
    med_cce = median_by_geometry(results, "collection_efficiency")
    med_iface = median_by_geometry(results, "interface_loss_fraction")
    med_trap = median_by_geometry(results, "trap_penalty_fraction")
    med_survival = median_by_geometry(results, "carrier_survival_fraction")
    med_life = median_by_geometry(results, "lifetime_years")
    med_mfg = median_by_geometry(results, "manufacturability_score")
    baseline = med_power["baseline"]
    rows = []
    for geometry in med_power:
        rows.append(
            {
                "geometry": geometry,
                "median_power_W_cm2": med_power[geometry],
                "median_power_ratio_vs_baseline": med_power[geometry] / max(baseline, 1e-30),
                "median_cce": med_cce[geometry],
                "median_carrier_survival": med_survival[geometry],
                "median_interface_loss": med_iface[geometry],
                "median_trap_penalty": med_trap[geometry],
                "median_lifetime_years": med_life[geometry],
                "median_manufacturability_score": med_mfg[geometry],
            }
        )
    rows.sort(key=lambda row: float(row["median_power_W_cm2"]), reverse=True)
    return rows


def best_results(results: list[Gen3Result], n: int = 15) -> list[Gen3Result]:
    return sorted(
        results,
        key=lambda r: (
            r.power_density_W_cm2,
            r.manufacturability_score,
            -r.graphene_interface_area_ratio,
        ),
        reverse=True,
    )[:n]


def smallest_2x_departure(results: list[Gen3Result]) -> Gen3Result | None:
    candidates = [
        r
        for r in results
        if r.params.geometry != "baseline"
        and r.net_power_ratio_vs_baseline >= 2.0
        and r.manufacturability_score >= 0.35
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda r: (
            r.geometry_departure_score,
            r.graphene_interface_area_ratio,
            -r.power_density_W_cm2,
        ),
    )


def write_report(path: Path, results: list[Gen3Result], rankings: list[dict[str, object]]) -> None:
    best = best_results(results, 1)[0]
    smallest = smallest_2x_departure(results)
    lines = [
        "# Generation-3 Embedded Graphene Collector Geometry Optimization",
        "",
        "## Conclusion",
        "",
        f"Best net-power geometry: **{best.params.geometry}** with power {best.power_density_W_cm2:.4e} W/cm^2, CCE {best.collection_efficiency:.3f}, interface loss {best.interface_loss_fraction:.3f}, trap penalty {best.trap_penalty_fraction:.3f}, and manufacturability score {best.manufacturability_score:.2f}.",
    ]
    if smallest:
        p = smallest.params
        lines.append(
            f"Smallest geometry departure beating baseline by at least 2x: **{p.geometry}**, pitch {p.pitch_um:g} um, width {p.ribbon_width_nm:g} nm, layers {p.graphene_layers}, depth fraction {p.network_depth_fraction:g}; ratio {smallest.net_power_ratio_vs_baseline:.2f}x, manufacturability {smallest.manufacturability_score:.2f}."
        )
    else:
        lines.append("No geometry with manufacturability score >= 0.35 beat baseline by at least 2x.")
    lines.extend(
        [
            "",
            "## Architecture Ranking",
            "",
            "| Rank | Geometry | Median power (W/cm^2) | Ratio vs baseline | Median CCE | Carrier survival | Interface loss | Trap penalty | Lifetime (yr) | Manufacturability |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for idx, row in enumerate(rankings, 1):
        lines.append(
            f"| {idx} | {row['geometry']} | {float(row['median_power_W_cm2']):.4e} | {float(row['median_power_ratio_vs_baseline']):.2f} | {float(row['median_cce']):.4g} | {float(row['median_carrier_survival']):.3f} | {float(row['median_interface_loss']):.3f} | {float(row['median_trap_penalty']):.3f} | {float(row['median_lifetime_years']):.3g} | {float(row['median_manufacturability_score']):.2f} |"
        )
    lines.extend(["", "## Best Individual Geometries", ""])
    for idx, result in enumerate(best_results(results), 1):
        p = result.params
        lines.append(
            f"{idx}. {p.geometry}: pitch={p.pitch_um:g} um, width={p.ribbon_width_nm:g} nm, layers={p.graphene_layers}, depth={p.network_depth_fraction:g}, diamond={p.diamond_um:g} um; power={result.power_density_W_cm2:.4e} W/cm^2, ratio={result.net_power_ratio_vs_baseline:.2f}x, CCE={result.collection_efficiency:.3f}, travel={result.mean_carrier_travel_um:.3g} um, area ratio={result.graphene_interface_area_ratio:.2f}, traps={result.added_trap_density_cm3:.3e} cm^-3, manufacturability={result.manufacturability_score:.2f}."
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Straight fingers are the conservative minimum-change geometry; they improve travel distance with the lowest added interface area.",
            "- Interdigitated combs and radial spokes add more collection reach but pay more interface and fabrication penalty.",
            "- Honeycomb, fractal/tree, random nanoribbon, and multilayer 3D meshes can reduce travel distance strongly, but interface/trap area and manufacturability penalties decide whether the gain survives.",
            "- The optimization criterion is net electrical power after added graphene/diamond interface, interface traps, geometric occlusion, and manufacturability-risk penalties.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_plots(results: list[Gen3Result], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in results:
        grouped[result.params.geometry].append(result.power_density_W_cm2)
    labels = sorted(grouped)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.boxplot([grouped[label] for label in labels], labels=labels, showfliers=False)
    ax.set_yscale("log")
    ax.set_ylabel("Net power density (W/cm^2)")
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen3_power_by_geometry.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for geometry in labels:
        subset = [r for r in results if r.params.geometry == geometry]
        ax.scatter(
            [r.graphene_interface_area_ratio for r in subset],
            [r.power_density_W_cm2 for r in subset],
            s=9,
            alpha=0.35,
            label=geometry,
        )
    ax.set_yscale("log")
    ax.set_xlabel("Graphene/diamond interface area ratio")
    ax.set_ylabel("Net power density (W/cm^2)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out_dir / "gen3_interface_area_vs_power.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for geometry in labels:
        subset = [r for r in results if r.params.geometry == geometry]
        ax.scatter(
            [r.mean_carrier_travel_um for r in subset],
            [r.collection_efficiency for r in subset],
            s=9,
            alpha=0.35,
            label=geometry,
        )
    ax.set_xlabel("Mean carrier travel distance (um)")
    ax.set_ylabel("Charge collection efficiency")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out_dir / "gen3_travel_distance_vs_cce.png", dpi=160)
    plt.close(fig)


def run_gen3_study(db: MaterialDatabase, out_dir: Path, preset: str = "focused") -> list[Gen3Result]:
    out_dir.mkdir(parents=True, exist_ok=True)
    params = gen3_params(preset)
    raw_results = [simulate_gen3(p, db) for p in params]
    baseline_by_thickness = {
        r.params.diamond_um: r.power_density_W_cm2
        for r in raw_results
        if r.params.geometry == "baseline"
    }
    results = [
        simulate_gen3(p, db, baseline_by_thickness.get(p.diamond_um))
        for p in params
    ]
    rankings = ranking_rows(results)
    write_csv(out_dir / "gen3_summary.csv", [result_row(r) for r in results])
    write_csv(out_dir / "gen3_loss_budget.csv", loss_rows(results))
    write_csv(out_dir / "gen3_geometry_rankings.csv", rankings)
    make_plots(results, out_dir / "plots")
    write_report(out_dir / "gen3_final_report.md", results, rankings)
    return results
