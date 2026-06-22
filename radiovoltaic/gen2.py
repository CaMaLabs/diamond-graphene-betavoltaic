from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from itertools import product
from math import exp, log, sqrt
from pathlib import Path
from statistics import median
from typing import Literal
import csv

import matplotlib.pyplot as plt
import numpy as np

from .materials import MaterialDatabase
from .model import KB_EV, Q_E, SECONDS_PER_YEAR, beta_deposition_fraction


Gen2Architecture = Literal[
    "baseline",
    "ferrite_transport",
    "ferrite_graphene",
    "graded_interface",
    "composite_layer",
    "embedded_graphene_fingers",
    "diamond_high_entropy_alloy",
    "diamond_ideal_defect_sink",
]

HealingMode = Literal["none", "weak", "strong", "idealized"]
MixtureKind = Literal["none", "diamond_ferrite", "diamond_graphene", "diamond_hea"]


@dataclass(frozen=True)
class InterfacePhysics:
    band_mismatch_eV: float
    interface_trap_density_cm2: float
    scattering_probability: float
    contact_resistance_ohm_cm2: float
    surface_recombination_cm_s: float
    grading_factor: float = 1.0


@dataclass(frozen=True)
class Gen2Params:
    architecture: Gen2Architecture
    source: str = "Ni63"
    ferrite: str = "Fe3O4"
    healing_mode: HealingMode = "weak"
    mixture_kind: MixtureKind = "none"
    composition_fraction: float = 0.0
    diamond_um: float = 8.0
    interlayer_um: float = 0.3
    graphene_fraction: float = 0.0
    temperature_K: float = 300.0
    electric_field_V_cm: float = 5.0e4
    trap_density_cm3: float = 1.0e14
    interface_trap_density_cm2: float = 1.0e11
    surface_recombination_cm_s: float = 1.0e4
    contact_resistance_ohm_cm2: float = 5.0e-3
    operation_years: float = 10.0
    activity_Bq_cm2: float | None = None
    load_resistance_ohm_cm2: float = 1.0e8
    interface_loss_scale: float = 1.0
    bulk_recombination_scale: float = 1.0
    trap_loss_scale: float = 1.0
    healing_rate_scale: float = 1.0
    mobility_scale: float = 1.0
    thermal_loss_scale: float = 1.0


@dataclass(frozen=True)
class Gen2Result:
    params: Gen2Params
    collection_efficiency: float
    power_density_W_cm2: float
    current_density_A_cm2: float
    voltage_V: float
    lifetime_years: float
    carrier_survival_fraction: float
    healing_benefit: float
    interface_loss_fraction: float
    bulk_recombination_fraction: float
    trap_loss_fraction: float
    mobility_loss_fraction: float
    thermal_loss_fraction: float
    peak_temperature_K: float
    loss_budget: dict[str, float]
    interface_budget: dict[str, float]
    effective_properties: dict[str, float]


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _mix(a: float, b: float, fraction: float, log_scale: bool = False) -> float:
    f = _clip01(fraction)
    if log_scale:
        return exp((1.0 - f) * log(max(a, 1e-30)) + f * log(max(b, 1e-30)))
    return (1.0 - f) * a + f * b


def _material_for_arch(params: Gen2Params, db: MaterialDatabase) -> dict[str, float]:
    if params.architecture in {"ferrite_transport", "ferrite_graphene", "graded_interface"}:
        return db.ferrites[params.ferrite]
    if params.architecture == "diamond_high_entropy_alloy":
        return db.raw["materials"]["high_entropy_alloy"]
    if params.architecture == "diamond_ideal_defect_sink":
        return db.raw["materials"]["ideal_defect_sink"]
    return db.diamond


def _composite_properties(params: Gen2Params, db: MaterialDatabase) -> dict[str, float]:
    diamond = db.diamond
    f = _clip01(params.composition_fraction)
    if params.mixture_kind == "diamond_ferrite":
        other = db.ferrites[params.ferrite]
        sink = other["defect_sink_strength"]
        trap = other["trap_density_cm3"]
        mobility = other["mobility_cm2_Vs"]
        thermal = other["thermal_conductivity_W_mK"]
        damage = other["radiation_damage_coeff_cm2"]
    elif params.mixture_kind == "diamond_graphene":
        other = db.graphene
        sink = 0.18
        trap = 2.0e15
        mobility = other["mobility_cm2_Vs"]
        thermal = other["thermal_conductivity_W_mK"]
        damage = diamond["radiation_damage_coeff_cm2"] * 0.75
    elif params.mixture_kind == "diamond_hea":
        other = db.raw["materials"]["high_entropy_alloy"]
        sink = other["defect_sink_strength"]
        trap = other["trap_density_cm3"]
        mobility = other["mobility_cm2_Vs"]
        thermal = other["thermal_conductivity_W_mK"]
        damage = other["radiation_damage_coeff_cm2"]
    else:
        return {
            "mobility_cm2_Vs": min(diamond["electron_mobility_cm2_Vs"], diamond["hole_mobility_cm2_Vs"]),
            "thermal_conductivity_W_mK": diamond["thermal_conductivity_W_mK"],
            "trap_density_cm3": params.trap_density_cm3,
            "defect_sink_strength": diamond["defect_sink_strength"],
            "radiation_damage_coeff_cm2": diamond["radiation_damage_coeff_cm2"],
            "percolation_penalty": 0.0,
        }
    # Composite disorder is intentionally punitive near mixed midpoints.
    disorder = 4.0 * f * (1.0 - f)
    return {
        "mobility_cm2_Vs": _mix(
            min(diamond["electron_mobility_cm2_Vs"], diamond["hole_mobility_cm2_Vs"]),
            mobility,
            f,
            log_scale=True,
        )
        * (1.0 - 0.45 * disorder),
        "thermal_conductivity_W_mK": _mix(diamond["thermal_conductivity_W_mK"], thermal, f, log_scale=True),
        "trap_density_cm3": params.trap_density_cm3 + _mix(0.0, trap, f, log_scale=False) * (0.35 + 0.65 * disorder),
        "defect_sink_strength": _mix(diamond["defect_sink_strength"], sink, f),
        "radiation_damage_coeff_cm2": _mix(diamond["radiation_damage_coeff_cm2"], damage, f),
        "percolation_penalty": _clip01(0.20 * disorder + 0.10 * max(0.0, f - 0.65)),
    }


def _interface_physics(
    params: Gen2Params,
    db: MaterialDatabase,
    target: dict[str, float],
    target_name: str,
) -> InterfacePhysics:
    diamond = db.diamond
    bandgap = target.get("bandgap_eV", 0.0)
    target_affinity = target.get("electron_affinity_eV", None)
    if target_affinity is None:
        target_affinity = target.get("work_function_eV", 4.5) - max(bandgap, 0.1) / 2.0
    mismatch = abs(diamond["electron_affinity_eV"] - target_affinity) + 0.12 * abs(diamond["bandgap_eV"] - bandgap)
    scattering = target.get("spin_scattering_penalty", target.get("scattering_penalty", 0.04))
    grading = 1.0
    if params.architecture == "graded_interface":
        grading = 0.35
    if target_name == "graphene":
        grading = min(grading, 0.65)
    return InterfacePhysics(
        band_mismatch_eV=mismatch,
        interface_trap_density_cm2=params.interface_trap_density_cm2 * grading,
        scattering_probability=scattering * grading,
        contact_resistance_ohm_cm2=params.contact_resistance_ohm_cm2 * (0.6 + 0.4 * grading),
        surface_recombination_cm_s=params.surface_recombination_cm_s * grading,
        grading_factor=grading,
    )


def _interface_budget(physics: InterfacePhysics, carrier_lifetime_s: float, thickness_um: float) -> dict[str, float]:
    thickness_cm = max(thickness_um * 1e-4, 1e-8)
    band_alignment = _clip01(0.28 * (1.0 - exp(-physics.band_mismatch_eV / 0.35)))
    traps = _clip01(0.24 * physics.interface_trap_density_cm2 / (physics.interface_trap_density_cm2 + 8.0e11))
    scattering = _clip01(0.20 * physics.scattering_probability)
    contact = _clip01(0.16 * log(1.0 + physics.contact_resistance_ohm_cm2 / 1e-3) / log(1.0 + 1e3))
    recombination_arg = physics.surface_recombination_cm_s * carrier_lifetime_s / thickness_cm
    surface_recombination = _clip01(0.34 * recombination_arg / (1.0 + recombination_arg))
    return {
        "band_alignment_mismatch": band_alignment,
        "interface_trap_states": traps,
        "carrier_scattering": scattering,
        "contact_resistance": contact,
        "surface_recombination_velocity": surface_recombination,
    }


def _healing_rate(params: Gen2Params, damage_rate_cm3_s: float, base_rate_s: float) -> float:
    multipliers = {
        "none": 0.0,
        "weak": 0.35,
        "strong": 2.5,
        "idealized": 25.0,
    }
    temp_factor = exp(-0.45 / (KB_EV * params.temperature_K)) / exp(-0.45 / (KB_EV * 300.0))
    radiation_factor = 1.0 / (1.0 + damage_rate_cm3_s / 1.0e8)
    time_factor = 1.0 - exp(-max(params.operation_years, 1e-6) / 2.0)
    return base_rate_s * multipliers[params.healing_mode] * temp_factor * radiation_factor * time_factor


def _defect_density(generation_rate_cm3_s: float, sink: float, healing_rate_s: float, years: float) -> float:
    removal = max(1e-14, 2.0e-8 + sink * 1.4e-7 + healing_rate_s)
    return generation_rate_cm3_s / removal * (1.0 - exp(-removal * years * SECONDS_PER_YEAR))


def _survival(losses: dict[str, float]) -> float:
    s = 1.0
    for value in losses.values():
        s *= 1.0 - _clip01(value)
    return _clip01(s)


def simulate_gen2(params: Gen2Params, db: MaterialDatabase) -> Gen2Result:
    source = db.sources[params.source]
    diamond = db.diamond
    active_thickness = params.diamond_um
    if params.architecture in {
        "ferrite_transport",
        "ferrite_graphene",
        "graded_interface",
        "diamond_high_entropy_alloy",
        "diamond_ideal_defect_sink",
    }:
        active_thickness += params.interlayer_um
    dep_frac = beta_deposition_fraction(source.mean_beta_energy_keV, params.diamond_um, diamond["density_g_cm3"])
    activity = params.activity_Bq_cm2 or source.default_activity_Bq_cm2
    generated_current = activity * source.mean_beta_energy_keV * 1e3 * dep_frac / diamond["pair_creation_energy_eV"] * Q_E
    deposited_power = activity * source.mean_beta_energy_keV * 1e3 * Q_E * dep_frac

    props = _composite_properties(params, db)
    discrete_target = _material_for_arch(params, db)
    if params.architecture == "composite_layer":
        active_thickness = params.diamond_um
    if params.architecture == "embedded_graphene_fingers":
        props = replace_composite_for_graphene_network(params, db)

    damage_rate = (
        activity
        * dep_frac
        * source.mean_beta_energy_keV
        * props["radiation_damage_coeff_cm2"]
        / max(active_thickness * 1e-4, 1e-9)
        * 1e18
    )
    if params.architecture not in {"baseline", "composite_layer", "embedded_graphene_fingers"}:
        sink = discrete_target.get("defect_sink_strength", props["defect_sink_strength"])
        base_healing = discrete_target.get("healing_rate_s", 1e-7)
        mobility = min(props["mobility_cm2_Vs"], discrete_target.get("mobility_cm2_Vs", props["mobility_cm2_Vs"]))
        thermal_k = min(props["thermal_conductivity_W_mK"], discrete_target.get("thermal_conductivity_W_mK", props["thermal_conductivity_W_mK"]))
        trap_material = discrete_target.get("trap_density_cm3", props["trap_density_cm3"])
    else:
        sink = props["defect_sink_strength"]
        base_healing = 1e-7
        mobility = props["mobility_cm2_Vs"]
        thermal_k = props["thermal_conductivity_W_mK"]
        trap_material = props["trap_density_cm3"]

    healing_rate = _healing_rate(params, damage_rate, base_healing) * params.healing_rate_scale
    defects_no_healing = _defect_density(damage_rate, sink, 0.0, params.operation_years)
    defects = _defect_density(damage_rate, sink, healing_rate, params.operation_years)
    healing_benefit = max(0.0, 1.0 - defects / max(defects_no_healing, 1e-30))
    effective_traps = params.trap_density_cm3 + 0.10 * trap_material + defects

    carrier_lifetime_s = 1.0 / (
        1.0 / diamond["baseline_lifetime_s"]
        + diamond["trap_capture_coeff_cm3_s"] * effective_traps
        + 1e3 * exp(-(diamond["bandgap_eV"] / 2.0) / (KB_EV * params.temperature_K))
    )
    thickness_cm = max(active_thickness * 1e-4, 1e-9)
    mobility_for_transport = mobility * params.mobility_scale
    drift_velocity = max(1.0, mobility_for_transport * params.electric_field_V_cm)
    drift_length = drift_velocity * carrier_lifetime_s
    diffusion_length = sqrt(max(0.0, mobility_for_transport * KB_EV * params.temperature_K * carrier_lifetime_s))
    carrier_survival = _clip01(1.0 - exp(-(drift_length + diffusion_length) / thickness_cm))

    interface_budget: dict[str, float] = {}
    if params.architecture == "baseline":
        interface_budget = _interface_budget(
            InterfacePhysics(0.20, params.interface_trap_density_cm2, 0.01, params.contact_resistance_ohm_cm2, params.surface_recombination_cm_s),
            carrier_lifetime_s,
            active_thickness,
        )
    elif params.architecture in {"composite_layer", "embedded_graphene_fingers"}:
        interface_budget = _interface_budget(
            InterfacePhysics(0.12, params.interface_trap_density_cm2 * 0.35, 0.02, params.contact_resistance_ohm_cm2 * 0.6, params.surface_recombination_cm_s * 0.35),
            carrier_lifetime_s,
            active_thickness,
        )
        interface_budget["composite_percolation_disorder"] = props.get("percolation_penalty", 0.0)
    else:
        target_name = "ferrite"
        if params.architecture == "diamond_high_entropy_alloy":
            target_name = "hea"
        elif params.architecture == "diamond_ideal_defect_sink":
            target_name = "ideal_defect_sink"
        physics = _interface_physics(params, db, discrete_target, target_name)
        interface_budget = _interface_budget(physics, carrier_lifetime_s, active_thickness)
        if params.architecture == "ferrite_graphene":
            graphene_physics = _interface_physics(params, db, db.graphene, "graphene")
            graphene_budget = _interface_budget(graphene_physics, carrier_lifetime_s, max(params.interlayer_um, 0.01))
            interface_budget.update({f"graphene_{key}": value * 0.75 for key, value in graphene_budget.items()})

    interface_survival = _survival(interface_budget)
    interface_loss = _clip01((1.0 - interface_survival) * params.interface_loss_scale)

    mobility_loss = _clip01(
        0.32
        * log(max(1200.0 / max(mobility_for_transport, 1e-9), 1.0))
        / log(1.0e6)
    )
    trap_loss = _clip01((0.28 * effective_traps / (effective_traps + 8.0e15)) * params.trap_loss_scale)
    bulk_recombination = _clip01((1.0 - carrier_survival) * params.bulk_recombination_scale)
    thermal_resistance = active_thickness * 1e-6 / max(thermal_k, 1e-9)
    thermal_rise = deposited_power * 1e4 * thermal_resistance
    peak_temp = params.temperature_K + thermal_rise
    thermal_loss = _clip01((0.12 * max(0.0, peak_temp - 330.0) / 120.0) * params.thermal_loss_scale)

    losses = {
        "interface_losses": interface_loss,
        "bulk_recombination": bulk_recombination,
        "trap_density": trap_loss,
        "carrier_mobility": mobility_loss,
        "thermal_effects": thermal_loss,
    }
    total_survival = _survival(losses)
    cce = _clip01(dep_frac * total_survival)
    current = generated_current * total_survival
    voltage = min(0.92 * diamond["bandgap_eV"], current * params.load_resistance_ohm_cm2)
    # Contact resistance causes an explicit voltage drop after collection.
    voltage = max(0.0, voltage - current * params.contact_resistance_ohm_cm2)
    power = current * voltage

    threshold = max(effective_traps * (1.0 + healing_benefit), 1.0e12)
    lifetime_years = min(source.half_life_years, threshold / max(damage_rate * SECONDS_PER_YEAR * (1.0 - healing_benefit), 1e-30))

    return Gen2Result(
        params=params,
        collection_efficiency=cce,
        power_density_W_cm2=power,
        current_density_A_cm2=current,
        voltage_V=voltage,
        lifetime_years=lifetime_years,
        carrier_survival_fraction=carrier_survival,
        healing_benefit=healing_benefit,
        interface_loss_fraction=interface_loss,
        bulk_recombination_fraction=bulk_recombination,
        trap_loss_fraction=trap_loss,
        mobility_loss_fraction=mobility_loss,
        thermal_loss_fraction=thermal_loss,
        peak_temperature_K=peak_temp,
        loss_budget=losses,
        interface_budget=interface_budget,
        effective_properties={
            "mobility_cm2_Vs": mobility,
            "thermal_conductivity_W_mK": thermal_k,
            "effective_traps_cm3": effective_traps,
            "damage_rate_cm3_s": damage_rate,
            "healing_rate_s": healing_rate,
            "defects_cm3": defects,
        },
    )


def replace_composite_for_graphene_network(params: Gen2Params, db: MaterialDatabase) -> dict[str, float]:
    network_fraction = max(params.graphene_fraction, params.composition_fraction)
    p = replace(params, mixture_kind="diamond_graphene", composition_fraction=network_fraction)
    props = _composite_properties(p, db)
    # Embedded fingers improve collection path length but add only limited bulk disorder.
    props["mobility_cm2_Vs"] = max(props["mobility_cm2_Vs"], 600.0 + 2500.0 * network_fraction)
    props["percolation_penalty"] *= 0.35
    props["trap_density_cm3"] *= 0.55
    return props


def gen2_sweep_params(preset: str = "focused") -> list[Gen2Params]:
    if preset == "smoke":
        diamonds = [8.0]
        interlayers = [0.1, 0.5]
        fractions = [0.0, 0.5, 1.0]
        healing = ["none", "strong"]
        interfaces = [1e3, 1e5]
        temps = [300.0]
        fields = [5e4]
        sources = ["Ni63"]
    else:
        diamonds = [5.0, 12.0, 20.0]
        interlayers = [0.05, 0.2, 0.8]
        fractions = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]
        healing = ["none", "weak", "strong", "idealized"]
        interfaces = [1e3, 1e4, 1e5]
        temps = [300.0, 360.0]
        fields = [1e4, 5e4, 1e5]
        sources = ["Ni63", "C14"]

    rows: list[Gen2Params] = []
    base_arches: list[Gen2Architecture] = [
        "baseline",
        "ferrite_transport",
        "ferrite_graphene",
        "graded_interface",
        "composite_layer",
        "embedded_graphene_fingers",
        "diamond_high_entropy_alloy",
        "diamond_ideal_defect_sink",
    ]
    ferrites = ["Fe3O4", "NiFe2O4", "CoFe2O4"]
    for source, d, h, iface, temp, field in product(sources, diamonds, healing, interfaces, temps, fields):
        rows.append(
            Gen2Params(
                architecture="baseline",
                source=source,
                diamond_um=d,
                healing_mode=h,
                surface_recombination_cm_s=iface,
                temperature_K=temp,
                electric_field_V_cm=field,
            )
        )
        for arch in base_arches[1:]:
            for interlayer in interlayers:
                if arch in {"composite_layer", "embedded_graphene_fingers"}:
                    kinds: list[MixtureKind] = (
                        ["diamond_graphene"] if arch == "embedded_graphene_fingers" else ["diamond_ferrite", "diamond_graphene", "diamond_hea"]
                    )
                    for kind, frac in product(kinds, fractions):
                        for ferrite in ferrites if kind == "diamond_ferrite" else ["Fe3O4"]:
                            rows.append(
                                Gen2Params(
                                    architecture=arch,
                                    source=source,
                                    ferrite=ferrite,
                                    healing_mode=h,
                                    mixture_kind=kind,
                                    composition_fraction=frac,
                                    graphene_fraction=frac if kind == "diamond_graphene" else 0.0,
                                    diamond_um=d,
                                    interlayer_um=interlayer,
                                    surface_recombination_cm_s=iface,
                                    temperature_K=temp,
                                    electric_field_V_cm=field,
                                )
                            )
                else:
                    for ferrite in ferrites if arch in {"ferrite_transport", "ferrite_graphene", "graded_interface"} else ["Fe3O4"]:
                        rows.append(
                            Gen2Params(
                                architecture=arch,
                                source=source,
                                ferrite=ferrite,
                                healing_mode=h,
                                diamond_um=d,
                                interlayer_um=interlayer,
                                surface_recombination_cm_s=iface,
                                temperature_K=temp,
                                electric_field_V_cm=field,
                            )
                        )
    return rows


def result_row(result: Gen2Result) -> dict[str, object]:
    p = result.params
    row = {
        "architecture": p.architecture,
        "source": p.source,
        "ferrite": p.ferrite,
        "healing_mode": p.healing_mode,
        "mixture_kind": p.mixture_kind,
        "composition_fraction": p.composition_fraction,
        "diamond_um": p.diamond_um,
        "interlayer_um": p.interlayer_um,
        "temperature_K": p.temperature_K,
        "electric_field_V_cm": p.electric_field_V_cm,
        "surface_recombination_cm_s": p.surface_recombination_cm_s,
        "collection_efficiency": result.collection_efficiency,
        "power_density_W_cm2": result.power_density_W_cm2,
        "current_density_A_cm2": result.current_density_A_cm2,
        "voltage_V": result.voltage_V,
        "lifetime_years": result.lifetime_years,
        "interface_loss_fraction": result.interface_loss_fraction,
        "healing_benefit": result.healing_benefit,
        "carrier_survival_fraction": result.carrier_survival_fraction,
        "bulk_recombination_fraction": result.bulk_recombination_fraction,
        "trap_loss_fraction": result.trap_loss_fraction,
        "mobility_loss_fraction": result.mobility_loss_fraction,
        "thermal_loss_fraction": result.thermal_loss_fraction,
        "peak_temperature_K": result.peak_temperature_K,
    }
    row.update(result.effective_properties)
    return row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def loss_rows(results: list[Gen2Result]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_id, result in enumerate(results):
        p = result.params
        for name, value in result.loss_budget.items():
            rows.append(
                {
                    "case_id": case_id,
                    "architecture": p.architecture,
                    "loss_channel": name,
                    "loss_fraction": value,
                }
            )
        for name, value in result.interface_budget.items():
            rows.append(
                {
                    "case_id": case_id,
                    "architecture": p.architecture,
                    "loss_channel": f"interface:{name}",
                    "loss_fraction": value,
                }
            )
    return rows


def median_by_arch(results: list[Gen2Result], attr: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in results:
        grouped[result.params.architecture].append(float(getattr(result, attr)))
    return {arch: median(vals) for arch, vals in grouped.items()}


def sensitivity_rows(db: MaterialDatabase) -> list[dict[str, object]]:
    base = Gen2Params("graded_interface", ferrite="Fe3O4", healing_mode="strong", interlayer_um=0.2)
    baseline = simulate_gen2(base, db).power_density_W_cm2
    knobs = {
        "interface_losses": ("surface_recombination_cm_s", 0.1, 10.0),
        "bulk_recombination": ("operation_years", 0.5, 2.0),
        "trap_density": ("trap_density_cm3", 0.1, 10.0),
        "healing_rate": ("healing_mode", "none", "idealized"),
        "carrier_mobility": ("electric_field_V_cm", 0.2, 5.0),
        "thermal_effects": ("temperature_K", 0.85, 1.25),
    }
    rows: list[dict[str, object]] = []
    for label, spec in knobs.items():
        field = spec[0]
        if field == "healing_mode":
            low = simulate_gen2(replace(base, healing_mode=spec[1]), db).power_density_W_cm2
            high = simulate_gen2(replace(base, healing_mode=spec[2]), db).power_density_W_cm2
        else:
            value = getattr(base, field)
            low = simulate_gen2(replace(base, **{field: value * spec[1]}), db).power_density_W_cm2
            high = simulate_gen2(replace(base, **{field: value * spec[2]}), db).power_density_W_cm2
        rows.append(
            {
                "factor": label,
                "low_power_W_cm2": low,
                "base_power_W_cm2": baseline,
                "high_power_W_cm2": high,
                "absolute_swing_W_cm2": abs(high - low),
                "relative_swing_vs_base": abs(high - low) / max(baseline, 1e-30),
            }
        )
    rows.sort(key=lambda row: float(row["relative_swing_vs_base"]), reverse=True)
    return rows


def normalized_sensitivity_rows(db: MaterialDatabase, epsilon: float = 0.10) -> list[dict[str, object]]:
    """Local dimensionless sensitivities d ln(power) / d ln(coefficient).

    Each factor is perturbed by the same +/- epsilon multiplier. Sensitivities
    are aggregated across viable, non-saturated design points so dead devices
    near clipping boundaries cannot create artificial dominance.
    """

    bases = [
        Gen2Params("baseline"),
        Gen2Params("embedded_graphene_fingers", mixture_kind="diamond_graphene", composition_fraction=0.5, graphene_fraction=0.5),
        Gen2Params("composite_layer", mixture_kind="diamond_graphene", composition_fraction=0.5),
        Gen2Params("diamond_ideal_defect_sink", healing_mode="strong", interlayer_um=0.2),
        Gen2Params("graded_interface", ferrite="Fe3O4", healing_mode="strong", interlayer_um=0.2),
    ]
    factors = {
        "interface_losses": "interface_loss_scale",
        "bulk_recombination": "bulk_recombination_scale",
        "trap_density": "trap_loss_scale",
        "healing_rate": "healing_rate_scale",
        "carrier_mobility": "mobility_scale",
        "thermal_effects": "thermal_loss_scale",
    }
    rows: list[dict[str, object]] = []
    denominator = log((1.0 + epsilon) / (1.0 - epsilon))
    for label, field in factors.items():
        elasticities: list[float] = []
        skipped_saturated = 0
        skipped_dead = 0
        base_powers: list[float] = []
        for base in bases:
            base_result = simulate_gen2(base, db)
            base_power = base_result.power_density_W_cm2
            base_loss = base_result.loss_budget.get(label, 0.0)
            if base_power <= 1e-20:
                skipped_dead += 1
                continue
            if label != "healing_rate" and base_loss >= 0.95:
                skipped_saturated += 1
                continue
            low = simulate_gen2(replace(base, **{field: 1.0 - epsilon}), db)
            high = simulate_gen2(replace(base, **{field: 1.0 + epsilon}), db)
            low_power = max(low.power_density_W_cm2, 1e-300)
            high_power = max(high.power_density_W_cm2, 1e-300)
            elasticities.append((log(high_power) - log(low_power)) / denominator)
            base_powers.append(base_power)
        if elasticities:
            elasticity = median(elasticities)
            p10 = float(np.percentile(elasticities, 10))
            p90 = float(np.percentile(elasticities, 90))
            base_power_median = median(base_powers)
        else:
            elasticity = 0.0
            p10 = 0.0
            p90 = 0.0
            base_power_median = 0.0
        rows.append(
            {
                "factor": label,
                "dimensionless_parameter": field,
                "epsilon": epsilon,
                "base_power_W_cm2": base_power_median,
                "log_sensitivity": elasticity,
                "p10_log_sensitivity": p10,
                "p90_log_sensitivity": p90,
                "absolute_log_sensitivity": abs(elasticity),
                "dominance_ratio_vs_median": 0.0,
                "included_points": len(elasticities),
                "skipped_saturated_points": skipped_saturated,
                "skipped_dead_points": skipped_dead,
                "interpretation": "",
            }
        )
    median_abs = median([float(row["absolute_log_sensitivity"]) for row in rows]) or 1e-30
    for row in rows:
        ratio = float(row["absolute_log_sensitivity"]) / median_abs
        row["dominance_ratio_vs_median"] = ratio
        if ratio > 10.0:
            row["interpretation"] = "dominates; inspect for scaling or saturation bias"
        elif ratio > 3.0:
            row["interpretation"] = "strong but not singular"
        else:
            row["interpretation"] = "comparable local sensitivity"
    rows.sort(key=lambda row: float(row["absolute_log_sensitivity"]), reverse=True)
    return rows


def failure_ranking(results: list[Gen2Result]) -> list[dict[str, object]]:
    baseline_power = median_by_arch(results, "power_density_W_cm2").get("baseline", 1e-30)
    grouped: dict[str, list[Gen2Result]] = defaultdict(list)
    for result in results:
        grouped[result.params.architecture].append(result)
    rows: list[dict[str, object]] = []
    for arch, vals in grouped.items():
        channel_medians: dict[str, float] = defaultdict(list)  # type: ignore[assignment]
        for result in vals:
            for name, loss in result.loss_budget.items():
                channel_medians[name].append(loss)  # type: ignore[union-attr]
        ranked = sorted(
            ((name, median(items)) for name, items in channel_medians.items()),  # type: ignore[attr-defined]
            key=lambda item: item[1],
            reverse=True,
        )
        power = median([v.power_density_W_cm2 for v in vals])
        rows.append(
            {
                "architecture": arch,
                "median_power_ratio_vs_baseline": power / max(baseline_power, 1e-30),
                "rank_1_loss": ranked[0][0],
                "rank_1_loss_fraction": ranked[0][1],
                "rank_2_loss": ranked[1][0],
                "rank_2_loss_fraction": ranked[1][1],
                "rank_3_loss": ranked[2][0],
                "rank_3_loss_fraction": ranked[2][1],
            }
        )
    rows.sort(key=lambda row: float(row["median_power_ratio_vs_baseline"]), reverse=True)
    return rows


def architecture_rankings(results: list[Gen2Result]) -> list[dict[str, object]]:
    power = median_by_arch(results, "power_density_W_cm2")
    cce = median_by_arch(results, "collection_efficiency")
    life = median_by_arch(results, "lifetime_years")
    iface = median_by_arch(results, "interface_loss_fraction")
    baseline_power = power["baseline"]
    rows = [
        {
            "architecture": arch,
            "median_power_W_cm2": power[arch],
            "power_ratio_vs_baseline": power[arch] / max(baseline_power, 1e-30),
            "median_cce": cce[arch],
            "median_lifetime_years": life[arch],
            "median_interface_loss": iface[arch],
        }
        for arch in power
    ]
    rows.sort(key=lambda row: float(row["median_power_W_cm2"]), reverse=True)
    return rows


def best_cases(results: list[Gen2Result], n: int = 12) -> list[Gen2Result]:
    unique: dict[tuple[object, ...], Gen2Result] = {}
    for result in sorted(results, key=lambda r: (r.power_density_W_cm2, r.lifetime_years), reverse=True):
        p = result.params
        key = (
            p.architecture,
            p.source,
            p.ferrite,
            p.healing_mode,
            p.mixture_kind,
            p.composition_fraction,
            p.diamond_um,
            p.interlayer_um,
            p.temperature_K,
            p.electric_field_V_cm,
            p.surface_recombination_cm_s,
        )
        unique.setdefault(key, result)
        if len(unique) >= n:
            break
    return list(unique.values())


def write_report(
    path: Path,
    results: list[Gen2Result],
    sensitivity: list[dict[str, object]],
    normalized_sensitivity: list[dict[str, object]],
    failures: list[dict[str, object]],
    rankings: list[dict[str, object]],
) -> None:
    best = best_cases(results, 1)[0]
    baseline_best = max((r for r in results if r.params.architecture == "baseline"), key=lambda r: r.power_density_W_cm2)
    median_power = median_by_arch(results, "power_density_W_cm2")
    median_interface = median_by_arch(results, "interface_loss_fraction")
    median_life = median_by_arch(results, "lifetime_years")
    failure_by_arch = {str(row["architecture"]): row for row in failures}
    ferrite_failure = failure_by_arch.get("ferrite_transport", {})
    graded_lift = median_power.get("graded_interface", 0.0) / max(median_power.get("ferrite_transport", 1e-30), 1e-30)
    interface_primary = (
        ferrite_failure.get("rank_1_loss") == "interface_losses"
        or (graded_lift > 2.0 and median_power.get("graded_interface", 0.0) > median_power.get("ferrite_transport", 0.0))
    )
    ferrite_bulk_primary = ferrite_failure.get("rank_1_loss") in {"carrier_mobility", "bulk_recombination"}
    composite_best = max(median_power.get("composite_layer", 0.0), median_power.get("embedded_graphene_fingers", 0.0))
    layered_best = max(median_power.get("ferrite_transport", 0.0), median_power.get("ferrite_graphene", 0.0), median_power.get("graded_interface", 0.0))
    healing_lift = median_life.get("diamond_ideal_defect_sink", 0.0) / max(median_life.get("baseline", 1e-30), 1e-30)
    max_norm = max(normalized_sensitivity, key=lambda row: float(row["absolute_log_sensitivity"]))
    mobility_norm = next(row for row in normalized_sensitivity if row["factor"] == "carrier_mobility")
    mobility_artifact = (
        sensitivity[0]["factor"] == "carrier_mobility"
        and float(mobility_norm["dominance_ratio_vs_median"]) <= 3.0
    )
    def _is_real_architectural_change(result: Gen2Result) -> bool:
        p = result.params
        if p.architecture in {"composite_layer", "embedded_graphene_fingers"}:
            return p.composition_fraction > 0.0
        return p.architecture != "baseline"

    successful_modified = [
        r
        for r in results
        if r.params.architecture != "baseline"
        and _is_real_architectural_change(r)
        and r.power_density_W_cm2 > baseline_best.power_density_W_cm2 * 1.01
        and (r.healing_benefit > 0.0 or r.params.composition_fraction > 0.0 or r.params.architecture != "embedded_graphene_fingers")
    ]
    modified_exceeds = bool(successful_modified)
    architecture_distance = {
        "ferrite_transport": 1,
        "ferrite_graphene": 2,
        "graded_interface": 2,
        "composite_layer": 3,
        "embedded_graphene_fingers": 4,
        "diamond_high_entropy_alloy": 5,
        "diamond_ideal_defect_sink": 6,
    }
    minimum_success = min(
        successful_modified,
        key=lambda r: (
            architecture_distance.get(r.params.architecture, 99),
            r.params.composition_fraction,
            r.params.interlayer_um,
            -r.power_density_W_cm2,
        ),
        default=None,
    )

    lines = [
        "# Generation-2 Ferrite Interface Falsification Study",
        "",
        "## Required Conclusions",
        "",
        f"- A. Interface losses are the primary bottleneck: {'YES' if interface_primary else 'NO'}.",
        f"- B. Bulk ferrite transport is the primary bottleneck: {'YES' if ferrite_bulk_primary and not interface_primary else 'NO'}.",
        f"- C. Composite architectures outperform layered architectures: {'YES' if composite_best > layered_best else 'NO'}.",
        f"- D. Self-healing effects are too small to matter: {'YES' if healing_lift < 1.10 else 'NO'}.",
        f"- E. Self-healing effects materially improve lifetime: {'YES' if healing_lift >= 1.10 else 'NO'}; idealized sink median lifetime ratio is {healing_lift:.2f}.",
        f"- F. A modified architecture exceeds the baseline: {'YES' if modified_exceeds else 'NO'}.",
        f"- G. No tested architecture exceeds the baseline: {'YES' if not modified_exceeds else 'NO'}.",
        "",
        "## Most Important Question",
        "",
    ]
    if modified_exceeds:
        lines.append(
            f"Yes. The smallest successful tested departure is `{minimum_success.params.architecture}`; the best-power individual case is `{best.params.architecture}`."
        )
    else:
        lines.append(
            "No. In this reduced-order falsification sweep, defect tolerance and self-healing benefits were not preserved strongly enough to overcome the remaining interface, trap, and mobility penalties."
        )
    lines.extend(
        [
            "",
        "Interface ablation check: graded interfaces change median ferrite-layer power by "
            f"{graded_lift:.2f}x relative to abrupt ferrite transport. This is the direct test of whether reducing the diamond-ferrite interface alone reverses the first-study result.",
            "",
            "## Mobility Sensitivity Bias Check",
            "",
            f"The earlier broad sensitivity ranked carrier mobility first. The normalized local coefficient sensitivity ranks `{max_norm['factor']}` first with |d ln P / d ln coefficient| = {float(max_norm['absolute_log_sensitivity']):.3g}. Carrier mobility has normalized sensitivity {float(mobility_norm['log_sensitivity']):.3g} and dominance ratio {float(mobility_norm['dominance_ratio_vs_median']):.2f} versus the median absolute sensitivity.",
            f"Verdict: {'the original carrier-mobility dominance is likely a parameter-scaling artifact' if mobility_artifact else 'carrier mobility remains a physically meaningful dominant sensitivity after normalization'}.",
        ]
    )
    lines.extend(
        [
            "",
            "## Architecture Rankings",
            "",
            "| Rank | Architecture | Median power (W/cm^2) | Ratio vs baseline | Median CCE | Median lifetime (yr) | Median interface loss |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for idx, row in enumerate(rankings, 1):
        lines.append(
            f"| {idx} | {row['architecture']} | {float(row['median_power_W_cm2']):.4e} | {float(row['power_ratio_vs_baseline']):.2f} | {float(row['median_cce']):.4g} | {float(row['median_lifetime_years']):.4g} | {float(row['median_interface_loss']):.3f} |"
        )
    lines.extend(["", "## Failure Mode Ranking", "", "| Architecture | Power ratio | #1 loss | #2 loss | #3 loss |", "|---|---:|---|---|---|"])
    for row in failures:
        lines.append(
            f"| {row['architecture']} | {float(row['median_power_ratio_vs_baseline']):.2f} | {row['rank_1_loss']} ({float(row['rank_1_loss_fraction']):.3f}) | {row['rank_2_loss']} ({float(row['rank_2_loss_fraction']):.3f}) | {row['rank_3_loss']} ({float(row['rank_3_loss_fraction']):.3f}) |"
        )
    lines.extend(["", "## Sensitivity Rankings", "", "| Rank | Factor | Relative swing vs base | Absolute swing (W/cm^2) |", "|---:|---|---:|---:|"])
    for idx, row in enumerate(sensitivity, 1):
        lines.append(f"| {idx} | {row['factor']} | {float(row['relative_swing_vs_base']):.3f} | {float(row['absolute_swing_W_cm2']):.4e} |")
    lines.extend(["", "## Normalized Dimensionless Sensitivity", "", "| Rank | Factor | Parameter | Log sensitivity | Dominance ratio | Interpretation |", "|---:|---|---|---:|---:|---|"])
    for idx, row in enumerate(normalized_sensitivity, 1):
        lines.append(
            f"| {idx} | {row['factor']} | {row['dimensionless_parameter']} | {float(row['log_sensitivity']):.4g} | {float(row['dominance_ratio_vs_median']):.2f} | {row['interpretation']} |"
        )
    lines.extend(["", "## Best Individual Cases", ""])
    for idx, result in enumerate(best_cases(results), 1):
        p = result.params
        lines.append(
            f"{idx}. {p.architecture}, source={p.source}, ferrite={p.ferrite}, healing={p.healing_mode}, mixture={p.mixture_kind}, fraction={p.composition_fraction:g}, diamond={p.diamond_um:g} um, interlayer={p.interlayer_um:g} um, T={p.temperature_K:g} K, E={p.electric_field_V_cm:.2g} V/cm, SRV={p.surface_recombination_cm_s:.2g} cm/s: power={result.power_density_W_cm2:.4e} W/cm^2, CCE={result.collection_efficiency:.3f}, lifetime={result.lifetime_years:.3g} yr, interface loss={result.interface_loss_fraction:.3f}."
        )
    lines.extend(
        [
            "",
            "## Minimum Architectural Change Assessment",
            "",
            "The minimum successful change is defined as the smallest departure from the failed ferrite layer that produces power above the best baseline while retaining a nonzero defect-sink or healing benefit.",
        ]
    )
    if modified_exceeds:
        p = minimum_success.params
        lines.append(f"The minimum observed change is `{p.architecture}` with healing `{p.healing_mode}` and mixture `{p.mixture_kind}` at fraction {p.composition_fraction:g}.")
    else:
        lines.append("No minimum successful change was found in this sweep; the closest changes reduce but do not eliminate penalties.")
    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `gen2_summary.csv`: all generation-2 cases and required outputs.",
            "- `gen2_loss_budget.csv`: interface and non-interface loss channels by case.",
            "- `gen2_sensitivity.csv`: sensitivity ranking.",
            "- `gen2_normalized_sensitivity.csv`: equal dimensionless coefficient sensitivity and implementation-bias check.",
            "- `gen2_failure_modes.csv`: dominant loss-channel ranking.",
            "- `gen2_architecture_rankings.csv`: median architecture ranking.",
            "- `plots/`: power, interface-loss, and failure-channel visualizations.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_gen2_plots(results: list[Gen2Result], failures: list[dict[str, object]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[float]] = defaultdict(list)
    iface: dict[str, list[float]] = defaultdict(list)
    for result in results:
        grouped[result.params.architecture].append(result.power_density_W_cm2)
        iface[result.params.architecture].append(result.interface_loss_fraction)
    labels = sorted(grouped)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.boxplot([grouped[label] for label in labels], labels=labels, showfliers=False)
    ax.set_yscale("log")
    ax.set_ylabel("Power density (W/cm^2)")
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen2_power_by_architecture.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.boxplot([iface[label] for label in labels], labels=labels, showfliers=False)
    ax.set_ylabel("Interface loss fraction")
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen2_interface_loss_by_architecture.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    y = [row["architecture"] for row in failures]
    x = [float(row["rank_1_loss_fraction"]) for row in failures]
    ax.barh(y, x, color="#9f4d3f")
    ax.set_xlabel("Dominant loss fraction")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "gen2_dominant_failure_modes.png", dpi=160)
    plt.close(fig)


def run_gen2_study(db: MaterialDatabase, out_dir: Path, preset: str = "focused") -> list[Gen2Result]:
    out_dir.mkdir(parents=True, exist_ok=True)
    results = [simulate_gen2(params, db) for params in gen2_sweep_params(preset)]
    sensitivity = sensitivity_rows(db)
    normalized_sensitivity = normalized_sensitivity_rows(db)
    failures = failure_ranking(results)
    rankings = architecture_rankings(results)
    write_csv(out_dir / "gen2_summary.csv", [result_row(result) for result in results])
    write_csv(out_dir / "gen2_loss_budget.csv", loss_rows(results))
    write_csv(out_dir / "gen2_sensitivity.csv", sensitivity)
    write_csv(out_dir / "gen2_normalized_sensitivity.csv", normalized_sensitivity)
    write_csv(out_dir / "gen2_failure_modes.csv", failures)
    write_csv(out_dir / "gen2_architecture_rankings.csv", rankings)
    make_gen2_plots(results, failures, out_dir / "plots")
    write_report(out_dir / "gen2_final_report.md", results, sensitivity, normalized_sensitivity, failures, rankings)
    return results
