from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from math import log
from pathlib import Path
from statistics import median
from typing import Literal
import csv

import matplotlib.pyplot as plt

from .gen3 import Gen3Params, Gen3Result, simulate_gen3
from .materials import MaterialDatabase


Architecture = Literal[
    "straight_graphene_fingers",
    "interdigitated_graphene_combs",
    "honeycomb_graphene_mesh",
    "radial_spoke_collectors",
    "fractal_tree_collectors",
    "multilayer_graphene_mesh",
    "graphene_diamond_composite",
    "laser_written_graphitic_channels",
    "graphene_coated_nanopore_channels",
    "vertical_graphitic_nanoribbons",
]


@dataclass(frozen=True)
class ManufacturingModel:
    architecture: Architecture
    gen3_geometry: str
    minimum_feature_nm: float
    alignment_tolerance_nm: float
    fabrication_yield: float
    fab_defect_density_cm3: float
    interface_roughness_nm: float
    relative_cost: float
    scalability: float
    process_maturity: float
    trl: int
    current_feasibility: str
    near_term_feasibility: str
    medium_term_feasibility: str
    delamination_risk: float
    cracking_risk: float
    thermal_stress_risk: float
    process_complexity: float
    performance_retention: float
    geometry_params: Gen3Params


@dataclass(frozen=True)
class Gen4Result:
    model: ManufacturingModel
    raw: Gen3Result
    charge_collection_efficiency: float
    mean_carrier_travel_um: float
    interface_area_ratio: float
    trap_state_generation_cm3: float
    fabrication_defect_density_cm3: float
    power_density_W_cm2: float
    lifetime_years: float
    yield_adjusted_power_W_cm2: float
    manufacturability_adjusted_power_W_cm2: float
    cost_adjusted_performance: float
    manufacturability_score: float
    risk_score: float
    dominant_failure_mechanism: str
    retained_performance_fraction: float
    graphene_net_benefit: bool


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def manufacturing_models() -> list[ManufacturingModel]:
    base = dict(source="Ni63", diamond_um=20.0, network_depth_fraction=0.9)
    return [
        ManufacturingModel(
            "straight_graphene_fingers",
            "straight_fingers",
            60.0,
            250.0,
            0.62,
            1.5e14,
            4.0,
            4.0,
            0.62,
            0.58,
            4,
            "Feasible as a small-area lithography and transfer stack.",
            "Feasible for repeatable lab devices.",
            "Plausible for wafer-scale if transfer/contact yield improves.",
            0.32,
            0.18,
            0.22,
            0.45,
            0.82,
            Gen3Params("straight_fingers", pitch_um=6.0, ribbon_width_nm=60.0, graphene_layers=1, **base),
        ),
        ManufacturingModel(
            "interdigitated_graphene_combs",
            "interdigitated_combs",
            80.0,
            120.0,
            0.42,
            3.0e14,
            5.5,
            7.0,
            0.42,
            0.42,
            3,
            "Feasible only as small proof-of-concept patterns.",
            "Possible with high-end lithography, low yield.",
            "Commercially plausible only with self-aligned patterning.",
            0.38,
            0.28,
            0.30,
            0.68,
            0.72,
            Gen3Params("interdigitated_combs", pitch_um=6.0, ribbon_width_nm=120.0, graphene_layers=1, **base),
        ),
        ManufacturingModel(
            "honeycomb_graphene_mesh",
            "honeycomb_mesh",
            120.0,
            100.0,
            0.30,
            4.0e14,
            7.0,
            9.0,
            0.30,
            0.30,
            2,
            "Marginal; complex etch/transfer alignment dominates.",
            "Possible as small-area demonstrator.",
            "Scale remains questionable without templated growth.",
            0.45,
            0.36,
            0.36,
            0.78,
            0.65,
            Gen3Params("honeycomb_mesh", pitch_um=6.0, ribbon_width_nm=120.0, graphene_layers=1, **base),
        ),
        ManufacturingModel(
            "radial_spoke_collectors",
            "radial_spokes",
            80.0,
            180.0,
            0.48,
            2.6e14,
            5.0,
            6.5,
            0.44,
            0.40,
            3,
            "Feasible in small devices; central contact crowding is risky.",
            "Likely feasible for laboratory radial cells.",
            "Scale-up depends on contact routing.",
            0.36,
            0.25,
            0.28,
            0.62,
            0.74,
            Gen3Params("radial_spokes", pitch_um=6.0, ribbon_width_nm=60.0, graphene_layers=1, **base),
        ),
        ManufacturingModel(
            "fractal_tree_collectors",
            "fractal_tree",
            60.0,
            80.0,
            0.22,
            5.0e14,
            8.0,
            11.0,
            0.18,
            0.22,
            2,
            "Not practical beyond demonstration patterns.",
            "Possible as a lithographic test coupon.",
            "Commercial route unlikely unless topology is simplified.",
            0.50,
            0.40,
            0.42,
            0.86,
            0.55,
            Gen3Params("fractal_tree", pitch_um=6.0, ribbon_width_nm=120.0, graphene_layers=1, **base),
        ),
        ManufacturingModel(
            "multilayer_graphene_mesh",
            "multilayer_3d_mesh",
            120.0,
            80.0,
            0.15,
            8.0e14,
            10.0,
            14.0,
            0.12,
            0.15,
            2,
            "Very low yield due to stacked alignment and buried interfaces.",
            "Possible only as a materials experiment.",
            "Commercialization unlikely without a new monolithic process.",
            0.58,
            0.52,
            0.55,
            0.92,
            0.45,
            Gen3Params("multilayer_3d_mesh", pitch_um=3.0, ribbon_width_nm=120.0, graphene_layers=4, **base),
        ),
        ManufacturingModel(
            "graphene_diamond_composite",
            "straight_fingers",
            500.0,
            1000.0,
            0.58,
            4.0e14,
            12.0,
            5.0,
            0.55,
            0.38,
            3,
            "Feasible as co-deposited or seeded composite, but transport is less controlled.",
            "Plausible for lab films with moderate reproducibility.",
            "Commercial path plausible if composite uniformity is solved.",
            0.20,
            0.30,
            0.34,
            0.55,
            0.58,
            Gen3Params("straight_fingers", pitch_um=12.0, ribbon_width_nm=500.0, graphene_layers=1, network_depth_fraction=0.65, source="Ni63", diamond_um=20.0),
        ),
        ManufacturingModel(
            "laser_written_graphitic_channels",
            "straight_fingers",
            800.0,
            1500.0,
            0.72,
            3.5e14,
            18.0,
            3.0,
            0.78,
            0.62,
            4,
            "Feasible today for graphitic paths in diamond.",
            "Strong laboratory path; geometry is coarser than transferred graphene.",
            "Best near-term scale-up candidate if damage annealing is controlled.",
            0.05,
            0.34,
            0.45,
            0.38,
            0.63,
            Gen3Params("straight_fingers", pitch_um=12.0, ribbon_width_nm=800.0, graphene_layers=1, network_depth_fraction=0.65, source="Ni63", diamond_um=20.0),
        ),
        ManufacturingModel(
            "graphene_coated_nanopore_channels",
            "multilayer_3d_mesh",
            50.0,
            60.0,
            0.18,
            7.0e14,
            15.0,
            13.0,
            0.18,
            0.18,
            2,
            "High risk; pore coating continuity and damage dominate.",
            "Possible as nanoscale coupon, not useful-area device.",
            "Scale unlikely without self-limiting conformal graphene growth.",
            0.62,
            0.58,
            0.50,
            0.90,
            0.48,
            Gen3Params("multilayer_3d_mesh", pitch_um=1.5, ribbon_width_nm=60.0, graphene_layers=4, **base),
        ),
        ManufacturingModel(
            "vertical_graphitic_nanoribbons",
            "straight_fingers",
            40.0,
            80.0,
            0.25,
            6.0e14,
            9.0,
            12.0,
            0.22,
            0.20,
            2,
            "Speculative; vertical alignment and contact continuity are unresolved.",
            "Possible as focused-area nanofabrication test.",
            "Commercial path uncertain without additive/self-assembled process.",
            0.42,
            0.46,
            0.48,
            0.84,
            0.52,
            Gen3Params("straight_fingers", pitch_um=1.5, ribbon_width_nm=60.0, graphene_layers=4, network_depth_fraction=0.9, source="Ni63", diamond_um=20.0),
        ),
    ]


def _feature_penalty(model: ManufacturingModel) -> float:
    if model.minimum_feature_nm >= 500.0:
        return 0.0
    return _clip01((80.0 - model.minimum_feature_nm) / 80.0 * 0.28)


def _alignment_penalty(model: ManufacturingModel) -> float:
    return _clip01((150.0 - model.alignment_tolerance_nm) / 150.0 * 0.18)


def manufacturability_score(model: ManufacturingModel) -> float:
    risks = (
        _feature_penalty(model)
        + _alignment_penalty(model)
        + 0.18 * model.delamination_risk
        + 0.18 * model.cracking_risk
        + 0.14 * model.thermal_stress_risk
        + 0.18 * model.process_complexity
    )
    base = (
        0.30 * model.fabrication_yield
        + 0.25 * model.scalability
        + 0.25 * model.process_maturity
        + 0.20 * (1.0 / max(model.relative_cost, 1.0))
    )
    return _clip01(base * (1.0 - risks))


def simulate_gen4(model: ManufacturingModel, db: MaterialDatabase, baseline_power: float) -> Gen4Result:
    raw = simulate_gen3(model.geometry_params, db, baseline_power)
    roughness_loss = _clip01(0.015 * model.interface_roughness_nm)
    fabrication_trap_loss = _clip01(0.22 * model.fab_defect_density_cm3 / (model.fab_defect_density_cm3 + 8.0e15))
    process_damage_loss = _clip01(roughness_loss + fabrication_trap_loss + 0.05 * model.cracking_risk + 0.04 * model.thermal_stress_risk)
    delamination_loss = _clip01(0.22 * model.delamination_risk)
    retained = _clip01(model.performance_retention * (1.0 - process_damage_loss) * (1.0 - delamination_loss))
    cce = raw.collection_efficiency * retained
    power = raw.power_density_W_cm2 * retained
    lifetime = raw.lifetime_years / (1.0 + model.fab_defect_density_cm3 / 4.0e14 + 2.0 * model.cracking_risk)
    y_power = power * model.fabrication_yield
    mfg = manufacturability_score(model)
    mfg_power = y_power * mfg
    cost_adjusted = mfg_power / model.relative_cost
    risks = {
        "feature_size": _feature_penalty(model),
        "alignment": _alignment_penalty(model),
        "low_yield": 1.0 - model.fabrication_yield,
        "fabrication_defects": fabrication_trap_loss,
        "interface_roughness": roughness_loss,
        "thermal_stress": model.thermal_stress_risk,
        "delamination": model.delamination_risk,
        "diamond_cracking": model.cracking_risk,
        "process_complexity": model.process_complexity,
        "cost": _clip01(log(model.relative_cost) / log(20.0)),
        "poor_scalability": 1.0 - model.scalability,
        "low_process_maturity": 1.0 - model.process_maturity,
    }
    dominant = max(risks, key=risks.get)
    return Gen4Result(
        model=model,
        raw=raw,
        charge_collection_efficiency=cce,
        mean_carrier_travel_um=raw.mean_carrier_travel_um,
        interface_area_ratio=raw.graphene_interface_area_ratio,
        trap_state_generation_cm3=raw.added_trap_density_cm3,
        fabrication_defect_density_cm3=model.fab_defect_density_cm3,
        power_density_W_cm2=power,
        lifetime_years=lifetime,
        yield_adjusted_power_W_cm2=y_power,
        manufacturability_adjusted_power_W_cm2=mfg_power,
        cost_adjusted_performance=cost_adjusted,
        manufacturability_score=mfg,
        risk_score=1.0 - mfg,
        dominant_failure_mechanism=dominant,
        retained_performance_fraction=retained,
        graphene_net_benefit=power > baseline_power,
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def result_row(result: Gen4Result) -> dict[str, object]:
    m = result.model
    return {
        "architecture": m.architecture,
        "gen3_geometry": m.gen3_geometry,
        "trl": m.trl,
        "minimum_feature_nm": m.minimum_feature_nm,
        "alignment_tolerance_nm": m.alignment_tolerance_nm,
        "fabrication_yield": m.fabrication_yield,
        "fab_defect_density_cm3": m.fab_defect_density_cm3,
        "interface_roughness_nm": m.interface_roughness_nm,
        "relative_cost": m.relative_cost,
        "scalability": m.scalability,
        "process_maturity": m.process_maturity,
        "charge_collection_efficiency": result.charge_collection_efficiency,
        "mean_carrier_travel_um": result.mean_carrier_travel_um,
        "interface_area_ratio": result.interface_area_ratio,
        "trap_state_generation_cm3": result.trap_state_generation_cm3,
        "fabrication_defect_density_cm3": result.fabrication_defect_density_cm3,
        "raw_power_density_W_cm2": result.raw.power_density_W_cm2,
        "retained_performance_fraction": result.retained_performance_fraction,
        "power_density_W_cm2": result.power_density_W_cm2,
        "lifetime_years": result.lifetime_years,
        "yield_adjusted_power_W_cm2": result.yield_adjusted_power_W_cm2,
        "manufacturability_adjusted_power_W_cm2": result.manufacturability_adjusted_power_W_cm2,
        "cost_adjusted_performance": result.cost_adjusted_performance,
        "manufacturability_score": result.manufacturability_score,
        "risk_score": result.risk_score,
        "dominant_failure_mechanism": result.dominant_failure_mechanism,
        "graphene_net_benefit": result.graphene_net_benefit,
        "current_feasibility": m.current_feasibility,
        "near_term_feasibility": m.near_term_feasibility,
        "medium_term_feasibility": m.medium_term_feasibility,
    }


def risk_rows(results: list[Gen4Result]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for result in results:
        m = result.model
        risks = {
            "unmanufacturable_feature_size": _feature_penalty(m),
            "unrealistic_alignment": _alignment_penalty(m),
            "low_fabrication_yield": 1.0 - m.fabrication_yield,
            "excessive_defect_creation": _clip01(m.fab_defect_density_cm3 / 1.0e15),
            "interface_roughness": _clip01(m.interface_roughness_nm / 20.0),
            "thermal_stress": m.thermal_stress_risk,
            "graphene_delamination": m.delamination_risk,
            "diamond_cracking": m.cracking_risk,
            "process_complexity": m.process_complexity,
            "high_cost": _clip01(log(m.relative_cost) / log(20.0)),
            "poor_scalability": 1.0 - m.scalability,
            "low_process_maturity": 1.0 - m.process_maturity,
        }
        for name, value in risks.items():
            rows.append({"architecture": m.architecture, "risk": name, "risk_score": value})
    return rows


def ranked(results: list[Gen4Result], key: str) -> list[Gen4Result]:
    return sorted(results, key=lambda r: float(getattr(r, key)), reverse=True)


def write_report(path: Path, results: list[Gen4Result], baseline_power: float) -> None:
    best_theory = max(results, key=lambda r: r.raw.power_density_W_cm2)
    best_mfg = max(results, key=lambda r: r.manufacturability_adjusted_power_W_cm2)
    best_cost = max(results, key=lambda r: r.cost_adjusted_performance)
    best_lab = max(results, key=lambda r: r.yield_adjusted_power_W_cm2 * r.model.process_maturity)
    commercial = max(results, key=lambda r: r.cost_adjusted_performance * r.model.scalability * r.model.fabrication_yield)
    laser = next(r for r in results if r.model.architecture == "laser_written_graphitic_channels")
    best_embedded = max(
        [r for r in results if r.model.architecture in {"straight_graphene_fingers", "interdigitated_graphene_combs", "radial_spoke_collectors"}],
        key=lambda r: r.manufacturability_adjusted_power_W_cm2,
    )
    laser_substitute = laser.manufacturability_adjusted_power_W_cm2 >= 0.70 * best_embedded.manufacturability_adjusted_power_W_cm2
    lines = [
        "# Generation-4 Manufacturability-Constrained Diamond-Graphene Radiovoltaic Study",
        "",
        "## Final Conclusion",
        "",
        f"A. Best theoretical architecture: **{best_theory.model.architecture}** with raw simulated power {best_theory.raw.power_density_W_cm2:.4e} W/cm^2.",
        f"B. Best manufacturable architecture: **{best_mfg.model.architecture}** with manufacturability-adjusted power {best_mfg.manufacturability_adjusted_power_W_cm2:.4e} W/cm^2.",
        f"C. Best laboratory prototype: **{best_lab.model.architecture}**.",
        f"D. Best commercialization path: **{commercial.model.architecture}**.",
        f"E. Laser-written graphitic channels can substitute for embedded graphene networks while retaining most of the manufacturing-adjusted benefit: **{'YES' if laser_substitute else 'NO'}**. Laser channels retain {laser.manufacturability_adjusted_power_W_cm2 / max(best_embedded.manufacturability_adjusted_power_W_cm2, 1e-30):.2f}x of the best embedded-network manufacturing-adjusted power.",
        "",
        "## Most Important Answer",
        "",
        f"Highest expected real-world power per unit cost and complexity: **{best_cost.model.architecture}**.",
        "",
        "## Ranked Architecture Table",
        "",
        "| Rank | Architecture | TRL | Raw power | Yield-adjusted | Mfg-adjusted | Cost-adjusted | CCE | Lifetime | Mfg score | Dominant failure |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for idx, result in enumerate(ranked(results, "cost_adjusted_performance"), 1):
        lines.append(
            f"| {idx} | {result.model.architecture} | {result.model.trl} | {result.raw.power_density_W_cm2:.4e} | {result.yield_adjusted_power_W_cm2:.4e} | {result.manufacturability_adjusted_power_W_cm2:.4e} | {result.cost_adjusted_performance:.4e} | {result.charge_collection_efficiency:.3f} | {result.lifetime_years:.3g} | {result.manufacturability_score:.2f} | {result.dominant_failure_mechanism} |"
        )
    lines.extend(
        [
            "",
            "## Technology Readiness",
            "",
            "| Architecture | Current feasibility | 5-year feasibility | 10-20 year feasibility |",
            "|---|---|---|---|",
        ]
    )
    for result in results:
        m = result.model
        lines.append(f"| {m.architecture} | {m.current_feasibility} | {m.near_term_feasibility} | {m.medium_term_feasibility} |")
    lines.extend(
        [
            "",
            "## Falsification Results",
            "",
            f"1. Embedded graphene collectors are practical: {'PARTLY' if best_embedded.manufacturability_score >= 0.35 else 'NO'}; transferred-pattern architectures remain yield-limited.",
            f"2. Interdigitated combs are worth their complexity: {'NO' if best_cost.model.architecture != 'interdigitated_graphene_combs' else 'YES'} after cost/yield penalties.",
            "3. Nanometer-scale collector geometries are manufacturable at useful scale: NO for the aggressive nanopore, vertical-ribbon, fractal, and multilayer cases in this model.",
            f"4. Graphene provides net benefit after fabrication defects: {'YES' if any(r.graphene_net_benefit and r.cost_adjusted_performance > 0 for r in results) else 'NO'}, but only for architectures with controlled damage and tolerable interface area.",
            "",
            "## Recommendations",
            "",
            f"- Recommended prototype architecture: **{best_lab.model.architecture}**.",
            f"- Recommended laboratory-scale proof-of-concept: **{laser.model.architecture}** if rapid fabrication is prioritized; **{best_lab.model.architecture}** if maximum demonstrated power is prioritized.",
            f"- Recommended commercial-scale architecture: **{commercial.model.architecture}**.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_plots(results: list[Gen4Result], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    labels = [r.model.architecture for r in results]
    fig, ax = plt.subplots(figsize=(12, 5))
    positions = list(range(len(labels)))
    ax.bar(positions, [r.cost_adjusted_performance for r in results], color="#2c7fb8")
    ax.set_ylabel("Cost-adjusted performance")
    ax.set_xticks(positions, labels, rotation=30, ha="right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen4_cost_adjusted_ranking.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(
        [r.manufacturability_score for r in results],
        [r.power_density_W_cm2 for r in results],
        s=60,
        color="#2ca25f",
    )
    for r in results:
        ax.annotate(r.model.architecture.replace("_", "\n"), (r.manufacturability_score, r.power_density_W_cm2), fontsize=6)
    ax.set_xlabel("Manufacturability score")
    ax.set_ylabel("Post-fabrication power density (W/cm^2)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen4_power_vs_manufacturability.png", dpi=160)
    plt.close(fig)


def run_gen4_study(db: MaterialDatabase, out_dir: Path) -> list[Gen4Result]:
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline = simulate_gen3(Gen3Params("baseline", source="Ni63", diamond_um=20.0), db)
    results = [simulate_gen4(model, db, baseline.power_density_W_cm2) for model in manufacturing_models()]
    write_csv(out_dir / "gen4_architecture_rankings.csv", [result_row(r) for r in ranked(results, "cost_adjusted_performance")])
    write_csv(out_dir / "gen4_yield_adjusted_performance.csv", [result_row(r) for r in ranked(results, "yield_adjusted_power_W_cm2")])
    write_csv(out_dir / "gen4_manufacturability_adjusted_performance.csv", [result_row(r) for r in ranked(results, "manufacturability_adjusted_power_W_cm2")])
    write_csv(out_dir / "gen4_fabrication_risk_matrix.csv", risk_rows(results))
    make_plots(results, out_dir / "plots")
    write_report(out_dir / "gen4_final_report.md", results, baseline.power_density_W_cm2)
    return results
