from __future__ import annotations

from dataclasses import dataclass, replace
from math import exp, log, sqrt
from typing import Literal

import numpy as np

from .materials import MaterialDatabase

Architecture = Literal["baseline", "diamond_ferrite", "diamond_ferrite_graphene", "multi_ferrite_graphene"]

Q_E = 1.602176634e-19
KB_EV = 8.617333262e-5
SECONDS_PER_YEAR = 365.25 * 24 * 3600


@dataclass(frozen=True)
class DeviceParams:
    architecture: Architecture
    source: str = "Ni63"
    ferrite: str | None = None
    diamond_um: float = 8.0
    ferrite_um: float = 0.3
    graphene_nm: float = 0.34
    ferrite_layers: int = 1
    trap_density_cm3: float = 1.0e14
    interface_recombination_cm_s: float = 1.0e4
    annealing_rate_s: float = 2.0e-8
    defect_healing_rate_s: float = 1.0e-7
    temperature_K: float = 300.0
    electric_field_V_cm: float = 5.0e4
    activity_Bq_cm2: float | None = None
    load_resistance_ohm_cm2: float = 1.0e8
    uncertainty_scale: float = 1.0


@dataclass(frozen=True)
class SimulationResult:
    params: DeviceParams
    charge_collection_efficiency: float
    current_density_A_cm2: float
    voltage_V: float
    power_density_W_cm2: float
    carrier_lifetime_s: float
    recombination_fraction: float
    trap_accumulation_rate_cm3_s: float
    estimated_lifetime_years: float
    peak_temperature_K: float
    thermal_rise_K: float
    deposited_power_density_W_cm2: float
    interface_loss_fraction: float
    interface_loss_budget: dict[str, float]
    defect_populations_cm3: dict[str, float]
    ferrite_benefit_factor: float
    radiation_tolerance_factor: float
    defect_sink_factor: float


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def beta_deposition_fraction(mean_keV: float, thickness_um: float, density_g_cm3: float) -> float:
    """Approximate beta energy deposition in diamond from an empirical CSDA range.

    The range relation is intentionally simple and monotonic. It is adequate for
    sweep-level falsification but should be replaced by Geant4/PENELOPE for a
    publishable device claim.
    """

    range_mg_cm2 = 0.412 * mean_keV**1.265 - 0.0954 * log(max(mean_keV, 1.01))
    range_um = max(0.05, range_mg_cm2 / density_g_cm3 * 10.0)
    return _clip01(1.0 - exp(-thickness_um / range_um))


def _transit_collection(thickness_um: float, mobility_cm2_Vs: float, lifetime_s: float, field_V_cm: float) -> float:
    thickness_cm = thickness_um * 1e-4
    drift_velocity = max(1.0, mobility_cm2_Vs * field_V_cm)
    drift_length = drift_velocity * lifetime_s
    diffusion_length = sqrt(max(0.0, mobility_cm2_Vs * KB_EV * 300.0 * lifetime_s))
    transport_length = drift_length + diffusion_length
    return _clip01(1.0 - exp(-transport_length / max(thickness_cm, 1e-12)))


def _interface_loss(velocity_cm_s: float, lifetime_s: float, thickness_um: float, barrier_eV: float = 0.0) -> float:
    thickness_cm = max(thickness_um * 1e-4, 1e-8)
    surface_term = velocity_cm_s * lifetime_s / thickness_cm
    barrier_term = 1.0 - exp(-barrier_eV / max(KB_EV * 300.0, 1e-9))
    return _clip01(0.55 * surface_term / (1.0 + surface_term) + 0.35 * barrier_term)


def _annealed_defect_density(
    generation_rate_cm3_s: float,
    annealing_rate_s: float,
    healing_rate_s: float,
    sink_strength: float,
    years: float = 10.0,
) -> float:
    removal = max(1e-12, annealing_rate_s + healing_rate_s + sink_strength * 1e-7)
    steady = generation_rate_cm3_s / removal
    return steady * (1.0 - exp(-removal * years * SECONDS_PER_YEAR))


def simulate(params: DeviceParams, db: MaterialDatabase) -> SimulationResult:
    source = db.sources[params.source]
    diamond = db.diamond
    activity = params.activity_Bq_cm2 or source.default_activity_Bq_cm2
    mean_keV = source.mean_beta_energy_keV
    dep_frac = beta_deposition_fraction(mean_keV, params.diamond_um, diamond["density_g_cm3"])
    deposited_power = activity * mean_keV * 1e3 * Q_E * dep_frac

    pairs_per_decay = mean_keV * 1e3 * dep_frac / diamond["pair_creation_energy_eV"]
    generated_current = activity * pairs_per_decay * Q_E

    damage_rate = (
        activity
        * dep_frac
        * mean_keV
        * diamond["radiation_damage_coeff_cm2"]
        / max(params.diamond_um * 1e-4, 1e-9)
        * 1e18
        * params.uncertainty_scale
    )

    ferrite_props = None
    ferrite_sink = 0.0
    ferrite_damage_reduction = 1.0
    ferrite_transport_penalty = 0.0
    ferrite_series_penalty = 0.0
    if params.architecture != "baseline":
        ferrite_name = params.ferrite or "Fe3O4"
        ferrite_props = db.ferrites[ferrite_name]
        ferrite_sink = ferrite_props["defect_sink_strength"] * (1.0 - exp(-params.ferrite_um * params.ferrite_layers / 0.25))
        ferrite_damage_reduction = 1.0 - 0.45 * ferrite_sink
        resistivity = ferrite_props["resistivity_ohm_cm"]
        ferrite_series_penalty = _clip01(log(1.0 + resistivity) / 25.0 * (params.ferrite_um * params.ferrite_layers))
        ferrite_transport_penalty = _clip01(
            0.18 * ferrite_series_penalty
            + ferrite_props["spin_scattering_penalty"]
            + 0.10 / max(ferrite_props["relative_permittivity"], 1.0)
        )
        damage_rate *= ferrite_damage_reduction

    diamond_defects = _annealed_defect_density(
        damage_rate,
        params.annealing_rate_s,
        params.defect_healing_rate_s,
        ferrite_sink,
    )
    effective_traps = params.trap_density_cm3 + diamond_defects
    lifetime = 1.0 / (
        1.0 / diamond["baseline_lifetime_s"]
        + diamond["trap_capture_coeff_cm3_s"] * effective_traps
        + 1e3 * exp(-(diamond["bandgap_eV"] / 2.0) / (KB_EV * params.temperature_K))
    )

    diamond_collection = _transit_collection(
        params.diamond_um,
        min(diamond["electron_mobility_cm2_Vs"], diamond["hole_mobility_cm2_Vs"]),
        lifetime,
        params.electric_field_V_cm,
    )

    interface_budget: dict[str, float] = {}
    interface_budget["diamond_collector"] = 0.0
    if params.architecture == "baseline":
        interface_budget["diamond_collector"] = _interface_loss(
            params.interface_recombination_cm_s, lifetime, params.diamond_um, 0.20
        )
    else:
        barrier = float(ferrite_props["interface_barrier_eV"]) if ferrite_props else 0.5
        interface_budget["diamond_ferrite"] = _interface_loss(
            params.interface_recombination_cm_s, lifetime, params.diamond_um, barrier
        )
        interface_budget["ferrite_bulk_transport"] = ferrite_transport_penalty
        if params.architecture in {"diamond_ferrite_graphene", "multi_ferrite_graphene"}:
            graphene = db.graphene
            graphene_loss = _interface_loss(
                params.interface_recombination_cm_s * graphene["interface_recombination_scale"],
                lifetime,
                max(params.ferrite_um, 0.01),
                0.08,
            )
            sheet_penalty = _clip01(graphene["sheet_resistance_ohm_sq"] * params.graphene_nm / 2.0e5)
            interface_budget["ferrite_graphene"] = graphene_loss
            interface_budget["graphene_sheet"] = sheet_penalty
        if params.architecture == "multi_ferrite_graphene":
            interface_budget["internal_ferrite_interfaces"] = _clip01(0.025 * max(0, params.ferrite_layers - 1))

    total_interface_survival = 1.0
    for loss in interface_budget.values():
        total_interface_survival *= 1.0 - _clip01(loss)
    interface_loss = 1.0 - total_interface_survival

    recombination_fraction = _clip01(1.0 - diamond_collection + 0.55 * interface_loss)
    cce = _clip01(dep_frac * diamond_collection * total_interface_survival * (1.0 - ferrite_series_penalty))
    current = generated_current * cce / max(dep_frac, 1e-9)
    voltage = min(0.92 * diamond["bandgap_eV"], current * params.load_resistance_ohm_cm2)
    power = current * voltage

    thickness_m = params.diamond_um * 1e-6
    thermal_resistance = thickness_m / diamond["thermal_conductivity_W_mK"]
    if ferrite_props:
        thermal_resistance += params.ferrite_um * params.ferrite_layers * 1e-6 / ferrite_props["thermal_conductivity_W_mK"]
    if params.architecture in {"diamond_ferrite_graphene", "multi_ferrite_graphene"}:
        thermal_resistance += params.graphene_nm * 1e-9 / db.graphene["thermal_conductivity_W_mK"]
    thermal_rise = deposited_power * 1e4 * thermal_resistance
    peak_temp = params.temperature_K + thermal_rise

    end_of_life_cce = max(0.5 * cce, 1e-9)
    yearly_defect = max(damage_rate * SECONDS_PER_YEAR, 1e-30)
    threshold_defects = max(effective_traps * (cce / end_of_life_cce - 1.0), 1.0e12)
    estimated_lifetime_years = min(source.half_life_years, threshold_defects / yearly_defect)

    baseline_damage = (
        activity
        * dep_frac
        * mean_keV
        * diamond["radiation_damage_coeff_cm2"]
        / max(params.diamond_um * 1e-4, 1e-9)
        * 1e18
    )
    radiation_tolerance_factor = baseline_damage / max(damage_rate, 1e-30)
    defect_sink_factor = 1.0 + ferrite_sink
    ferrite_benefit_factor = cce * radiation_tolerance_factor / max(1.0 + interface_loss + ferrite_series_penalty, 1e-9)

    return SimulationResult(
        params=params,
        charge_collection_efficiency=cce,
        current_density_A_cm2=current,
        voltage_V=voltage,
        power_density_W_cm2=power,
        carrier_lifetime_s=lifetime,
        recombination_fraction=recombination_fraction,
        trap_accumulation_rate_cm3_s=damage_rate,
        estimated_lifetime_years=estimated_lifetime_years,
        peak_temperature_K=peak_temp,
        thermal_rise_K=thermal_rise,
        deposited_power_density_W_cm2=deposited_power,
        interface_loss_fraction=interface_loss,
        interface_loss_budget=interface_budget,
        defect_populations_cm3={
            "vacancies": 0.58 * diamond_defects,
            "interstitials": 0.42 * diamond_defects,
            "effective_traps": effective_traps,
        },
        ferrite_benefit_factor=ferrite_benefit_factor,
        radiation_tolerance_factor=radiation_tolerance_factor,
        defect_sink_factor=defect_sink_factor,
    )


def perturb(params: DeviceParams, rng: np.random.Generator) -> DeviceParams:
    factor = lambda sigma: float(np.exp(rng.normal(0.0, sigma)))
    return replace(
        params,
        trap_density_cm3=params.trap_density_cm3 * factor(0.8),
        interface_recombination_cm_s=params.interface_recombination_cm_s * factor(0.7),
        annealing_rate_s=params.annealing_rate_s * factor(0.5),
        defect_healing_rate_s=params.defect_healing_rate_s * factor(0.5),
        electric_field_V_cm=params.electric_field_V_cm * factor(0.25),
        uncertainty_scale=factor(0.45),
    )

