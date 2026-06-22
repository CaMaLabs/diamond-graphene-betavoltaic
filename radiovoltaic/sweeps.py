from __future__ import annotations

from dataclasses import asdict, replace
from itertools import product
from pathlib import Path
from typing import Iterable

import csv
import numpy as np

from .materials import MaterialDatabase
from .model import DeviceParams, SimulationResult, perturb, simulate


def default_cases() -> list[DeviceParams]:
    common = dict(diamond_um=8.0, trap_density_cm3=1.0e14, interface_recombination_cm_s=1.0e4)
    return [
        DeviceParams("baseline", source="Ni63", **common),
        DeviceParams("diamond_ferrite", source="Ni63", ferrite="Fe3O4", ferrite_um=0.3, **common),
        DeviceParams("diamond_ferrite_graphene", source="Ni63", ferrite="Fe3O4", ferrite_um=0.3, **common),
        DeviceParams("multi_ferrite_graphene", source="Ni63", ferrite="Fe3O4", ferrite_um=0.2, ferrite_layers=3, **common),
    ]


def sweep_params(preset: str = "focused") -> Iterable[DeviceParams]:
    if preset == "smoke":
        diamond = [4.0, 12.0]
        ferrite = [0.1, 0.6]
        traps = [1e14]
        interfaces = [1e4]
        temps = [300.0]
        fields = [5e4]
        anneal = [2e-8]
        healing = [1e-7]
        sources = ["Ni63"]
    else:
        diamond = [2.0, 8.0, 20.0]
        ferrite = [0.05, 0.3, 1.5]
        traps = [1e13, 1e15]
        interfaces = [1e3, 1e5]
        temps = [300.0, 360.0]
        fields = [1e4, 1e5]
        anneal = [5e-9, 1e-7]
        healing = [2e-8, 5e-7]
        sources = ["Ni63", "C14"]

    variant_architectures = ["diamond_ferrite", "diamond_ferrite_graphene", "multi_ferrite_graphene"]
    ferrites = ["Fe3O4", "NiFe2O4", "CoFe2O4"]

    for source, d, trap, iface, temp, field, ann, heal in product(
        sources, diamond, traps, interfaces, temps, fields, anneal, healing
    ):
        yield DeviceParams(
            architecture="baseline",
            source=source,
            diamond_um=d,
            ferrite_um=0.0,
            trap_density_cm3=trap,
            interface_recombination_cm_s=iface,
            temperature_K=temp,
            electric_field_V_cm=field,
            annealing_rate_s=ann,
            defect_healing_rate_s=heal,
        )
        for arch in variant_architectures:
            for ferrite_name in ferrites:
                for f in ferrite:
                    yield DeviceParams(
                        architecture=arch,
                        source=source,
                        ferrite=ferrite_name,
                        diamond_um=d,
                        ferrite_um=f,
                        ferrite_layers=3 if arch == "multi_ferrite_graphene" else 1,
                        trap_density_cm3=trap,
                        interface_recombination_cm_s=iface,
                        temperature_K=temp,
                        electric_field_V_cm=field,
                        annealing_rate_s=ann,
                        defect_healing_rate_s=heal,
                    )


def result_row(result: SimulationResult) -> dict[str, object]:
    p = result.params
    return {
        "architecture": p.architecture,
        "source": p.source,
        "ferrite": p.ferrite or "",
        "diamond_um": p.diamond_um,
        "ferrite_um": p.ferrite_um,
        "graphene_nm": p.graphene_nm,
        "ferrite_layers": p.ferrite_layers,
        "trap_density_cm3": p.trap_density_cm3,
        "interface_recombination_cm_s": p.interface_recombination_cm_s,
        "annealing_rate_s": p.annealing_rate_s,
        "defect_healing_rate_s": p.defect_healing_rate_s,
        "temperature_K": p.temperature_K,
        "electric_field_V_cm": p.electric_field_V_cm,
        "cce": result.charge_collection_efficiency,
        "current_density_A_cm2": result.current_density_A_cm2,
        "voltage_V": result.voltage_V,
        "power_density_W_cm2": result.power_density_W_cm2,
        "carrier_lifetime_s": result.carrier_lifetime_s,
        "recombination_fraction": result.recombination_fraction,
        "trap_accumulation_rate_cm3_s": result.trap_accumulation_rate_cm3_s,
        "estimated_lifetime_years": result.estimated_lifetime_years,
        "peak_temperature_K": result.peak_temperature_K,
        "thermal_rise_K": result.thermal_rise_K,
        "interface_loss_fraction": result.interface_loss_fraction,
        "dominant_interface_loss": max(result.interface_loss_budget, key=result.interface_loss_budget.get),
        "dominant_interface_loss_value": max(result.interface_loss_budget.values()),
        "vacancies_cm3": result.defect_populations_cm3["vacancies"],
        "interstitials_cm3": result.defect_populations_cm3["interstitials"],
        "effective_traps_cm3": result.defect_populations_cm3["effective_traps"],
        "ferrite_benefit_factor": result.ferrite_benefit_factor,
        "radiation_tolerance_factor": result.radiation_tolerance_factor,
        "defect_sink_factor": result.defect_sink_factor,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def interface_budget_rows(results: list[SimulationResult]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, result in enumerate(results):
        p = result.params
        for loss_name, loss in result.interface_loss_budget.items():
            rows.append(
                {
                    "case_id": idx,
                    "architecture": p.architecture,
                    "source": p.source,
                    "ferrite": p.ferrite or "",
                    "diamond_um": p.diamond_um,
                    "ferrite_um": p.ferrite_um,
                    "ferrite_layers": p.ferrite_layers,
                    "interface_or_transport_channel": loss_name,
                    "loss_fraction": loss,
                }
            )
    return rows


def run_sweep(db: MaterialDatabase, out_dir: Path, preset: str = "focused") -> list[SimulationResult]:
    results = [simulate(params, db) for params in sweep_params(preset)]
    write_csv(out_dir / "summary.csv", [result_row(result) for result in results])
    write_csv(out_dir / "interface_loss_budget.csv", interface_budget_rows(results))
    return results


def run_uncertainty(db: MaterialDatabase, out_dir: Path, samples: int = 200) -> list[SimulationResult]:
    rng = np.random.default_rng(42)
    base_cases = default_cases()
    results: list[SimulationResult] = []
    for case in base_cases:
        for _ in range(samples):
            results.append(simulate(perturb(case, rng), db))
    write_csv(out_dir / "uncertainty.csv", [result_row(result) for result in results])
    return results


def run_sensitivity(db: MaterialDatabase, out_dir: Path) -> list[dict[str, object]]:
    base = DeviceParams("diamond_ferrite_graphene", ferrite="Fe3O4")
    baseline = simulate(base, db).power_density_W_cm2
    knobs = {
        "diamond_um": base.diamond_um,
        "ferrite_um": base.ferrite_um,
        "trap_density_cm3": base.trap_density_cm3,
        "interface_recombination_cm_s": base.interface_recombination_cm_s,
        "annealing_rate_s": base.annealing_rate_s,
        "defect_healing_rate_s": base.defect_healing_rate_s,
        "temperature_K": base.temperature_K,
        "electric_field_V_cm": base.electric_field_V_cm,
    }
    rows: list[dict[str, object]] = []
    for name, value in knobs.items():
        low = replace(base, **{name: value * 0.5})
        high = replace(base, **{name: value * 2.0})
        low_power = simulate(low, db).power_density_W_cm2
        high_power = simulate(high, db).power_density_W_cm2
        elasticity = (np.log(max(high_power, 1e-30)) - np.log(max(low_power, 1e-30))) / np.log(4.0)
        rows.append(
            {
                "parameter": name,
                "base_value": value,
                "low_power_W_cm2": low_power,
                "base_power_W_cm2": baseline,
                "high_power_W_cm2": high_power,
                "log_elasticity": elasticity,
                "absolute_swing_W_cm2": abs(high_power - low_power),
            }
        )
    rows.sort(key=lambda row: abs(float(row["log_elasticity"])), reverse=True)
    write_csv(out_dir / "sensitivity.csv", rows)
    return rows
