from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import median

from .model import SimulationResult


def _median_by_arch(results: list[SimulationResult], attr: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in results:
        grouped[result.params.architecture].append(float(getattr(result, attr)))
    return {arch: median(vals) for arch, vals in grouped.items()}


def _best_designs(results: list[SimulationResult], n: int = 8) -> list[SimulationResult]:
    unique: dict[tuple[object, ...], SimulationResult] = {}
    for result in sorted(
        results,
        key=lambda r: (
            r.power_density_W_cm2,
            r.estimated_lifetime_years,
            -r.interface_loss_fraction,
        ),
        reverse=True,
    ):
        p = result.params
        key = (
            p.architecture,
            p.source,
            p.ferrite,
            p.diamond_um,
            p.ferrite_um,
            p.ferrite_layers,
            p.interface_recombination_cm_s,
            p.electric_field_V_cm,
        )
        unique.setdefault(key, result)
        if len(unique) >= n:
            break
    return list(unique.values())


def _conclusion(results: list[SimulationResult], uncertainty: list[SimulationResult]) -> tuple[str, str]:
    power = _median_by_arch(results, "power_density_W_cm2")
    interface = _median_by_arch(results, "interface_loss_fraction")
    lifetime = _median_by_arch(results, "estimated_lifetime_years")
    baseline_power = power.get("baseline", 0.0)
    baseline_life = lifetime.get("baseline", 0.0)
    variants = [k for k in power if k != "baseline"]
    best_variant = max(variants, key=lambda k: power[k]) if variants else "baseline"
    power_ratio = power.get(best_variant, 0.0) / max(baseline_power, 1e-30)
    life_ratio = lifetime.get(best_variant, 0.0) / max(baseline_life, 1e-30)

    uncertain_power = _median_by_arch(uncertainty, "power_density_W_cm2")
    uncertain_baseline = uncertain_power.get("baseline", 0.0)
    uncertain_best = max((v for k, v in uncertain_power.items() if k != "baseline"), default=0.0)
    uncertainty_ratio = uncertain_best / max(uncertain_baseline, 1e-30)

    if power_ratio > 1.15 and life_ratio > 1.15 and uncertainty_ratio > 1.05:
        return "A. Ferrite layer appears beneficial.", f"Best median variant is {best_variant} with {power_ratio:.2f}x power and {life_ratio:.2f}x lifetime versus baseline."
    if power_ratio < 0.90 or interface.get(best_variant, 0.0) > 0.45:
        return "C. Ferrite layer appears detrimental.", f"Best median variant is {best_variant}, but median power ratio is {power_ratio:.2f} and interface loss is {interface.get(best_variant, 0.0):.2f}."
    if 0.90 <= power_ratio <= 1.15 and 0.90 <= life_ratio <= 1.15:
        return "B. Ferrite layer appears neutral.", f"Best median variant is {best_variant}; power and lifetime shifts are within +/-15%."
    return "D. Current evidence insufficient.", f"Signals are mixed: best median variant is {best_variant}, power ratio {power_ratio:.2f}, lifetime ratio {life_ratio:.2f}, uncertainty ratio {uncertainty_ratio:.2f}."


def write_report(
    path: Path,
    results: list[SimulationResult],
    uncertainty: list[SimulationResult],
    sensitivity: list[dict[str, object]],
) -> None:
    cce = _median_by_arch(results, "charge_collection_efficiency")
    power = _median_by_arch(results, "power_density_W_cm2")
    lifetime = _median_by_arch(results, "estimated_lifetime_years")
    interface = _median_by_arch(results, "interface_loss_fraction")
    recomb = _median_by_arch(results, "recombination_fraction")
    conclusion, rationale = _conclusion(results, uncertainty)

    lines: list[str] = []
    lines.append("# Ferrite Interlayer Radiovoltaic Simulation Report")
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append(f"**{conclusion}**")
    lines.append("")
    lines.append(rationale)
    lines.append("")
    lines.append("## Architecture Median Metrics")
    lines.append("")
    lines.append("| Architecture | CCE | Power (W/cm^2) | Lifetime (yr) | Interface loss | Recombination |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for arch in sorted(cce):
        lines.append(
            f"| {arch} | {cce[arch]:.4g} | {power[arch]:.4e} | {lifetime[arch]:.4g} | {interface[arch]:.3f} | {recomb[arch]:.3f} |"
        )
    lines.append("")
    lines.append("## Falsification Tests")
    lines.append("")
    baseline_power = power.get("baseline", 0.0)
    baseline_life = lifetime.get("baseline", 0.0)
    for arch in sorted(k for k in power if k != "baseline"):
        lines.append(
            f"- {arch}: power ratio {power[arch] / max(baseline_power, 1e-30):.2f}, "
            f"lifetime ratio {lifetime[arch] / max(baseline_life, 1e-30):.2f}, "
            f"median interface loss {interface[arch]:.2f}."
        )
    lines.append("- Interface-loss disproof criterion: ferrite is rejected where added diamond-ferrite and ferrite-graphene losses exceed the collection or lifetime gain.")
    lines.append("- Radiation-tolerance criterion: ferrite must reduce trap accumulation enough to extend lifetime after accounting for extra series and interface losses.")
    lines.append("- Defect-sink criterion: defect populations must decline relative to baseline without an offsetting recombination increase.")
    lines.append("- Long-term output criterion: power density must remain above baseline beyond uncertainty, not only at beginning of life.")
    lines.append("- Uncertainty criterion: median benefit below 5% in the perturbed ensemble is treated as insufficient evidence.")
    lines.append("")
    lines.append("## Sensitivity Ranking")
    lines.append("")
    lines.append("| Rank | Parameter | Log elasticity | Absolute power swing (W/cm^2) |")
    lines.append("|---:|---|---:|---:|")
    for idx, row in enumerate(sensitivity, 1):
        lines.append(
            f"| {idx} | {row['parameter']} | {float(row['log_elasticity']):.3f} | {float(row['absolute_swing_W_cm2']):.4e} |"
        )
    lines.append("")
    lines.append("## Ranked Design Recommendations")
    lines.append("")
    for idx, result in enumerate(_best_designs(results), 1):
        p = result.params
        lines.append(
            f"{idx}. {p.architecture}, source={p.source}, ferrite={p.ferrite or 'none'}, "
            f"diamond={p.diamond_um:g} um, ferrite={p.ferrite_um:g} um, "
            f"layers={p.ferrite_layers}: power={result.power_density_W_cm2:.4e} W/cm^2, "
            f"CCE={result.charge_collection_efficiency:.3f}, lifetime={result.estimated_lifetime_years:.3g} yr, "
            f"interface loss={result.interface_loss_fraction:.2f}."
        )
    lines.append("")
    lines.append("## Assumptions")
    lines.append("")
    lines.append("- Beta deposition uses a compact empirical CSDA-like range approximation, not a particle Monte Carlo.")
    lines.append("- Carrier collection is represented by drift plus diffusion length relative to diamond thickness.")
    lines.append("- Trap-limited lifetime uses a Shockley-Read-Hall-style capture term with reduced-order defect kinetics.")
    lines.append("- Ferrites are represented by mobility/resistivity, interface barrier, trap density, defect-sink strength, and healing rate.")
    lines.append("- Graphene is modeled as a low-loss collection sheet with finite sheet resistance and interface recombination scaling.")
    lines.append("- Thermal rise is one-dimensional conduction under areal beta heating.")
    lines.append("- Voltage is a load-limited estimate capped below the diamond bandgap, not a full diode solution.")
    lines.append("")
    lines.append("## Failure Modes")
    lines.append("")
    lines.append("- Diamond-ferrite barrier or surface recombination dominates before defect-sink benefits appear.")
    lines.append("- High-resistivity ferrites reduce current through series transport penalties.")
    lines.append("- Multi-layer ferrites add internal interfaces faster than they add defect tolerance.")
    lines.append("- Low beta energy sources fail to deposit enough usable energy in the chosen diamond thickness.")
    lines.append("- Annealing and defect-healing rates are too slow at operating temperature.")
    lines.append("- Graphene sheet resistance or contact quality dominates collector losses.")
    lines.append("- Thermal assumptions break down if source activity is pushed far above the default areal activity.")
    lines.append("")
    lines.append("## Output Files")
    lines.append("")
    lines.append("- `summary.csv`: full parameter sweep.")
    lines.append("- `interface_loss_budget.csv`: per-interface and per-transport-channel loss budget.")
    lines.append("- `uncertainty.csv`: perturbed ensemble for benefit significance.")
    lines.append("- `sensitivity.csv`: one-factor sensitivity ranking.")
    lines.append("- `plots/`: CCE, power, lifetime, thermal, interface loss, and sensitivity plots.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
