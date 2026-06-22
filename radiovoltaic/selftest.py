from __future__ import annotations

from .materials import load_materials
from .gen2 import Gen2Params, simulate_gen2
from .gen3 import Gen3Params, simulate_gen3
from .gen4 import manufacturing_models, manufacturability_score
from .gen5 import GEOMETRIES as GEN5_GEOMETRIES, SOURCES as GEN5_SOURCES, SUBSTRATES, simulate_case
from .gen6 import Gen6Params, simulate as simulate_gen6
from .model import DeviceParams, beta_deposition_fraction, simulate


def run_selftest() -> None:
    db = load_materials()
    thin = beta_deposition_fraction(17.0, 1.0, 3.51)
    thick = beta_deposition_fraction(17.0, 20.0, 3.51)
    assert 0.0 <= thin < thick <= 1.0, "deposition should increase with thickness"

    baseline = simulate(DeviceParams("baseline"), db)
    assert 0.0 <= baseline.charge_collection_efficiency <= 1.0
    assert baseline.current_density_A_cm2 >= 0.0
    assert baseline.power_density_W_cm2 >= 0.0
    assert baseline.estimated_lifetime_years > 0.0

    bad_variant = simulate(
        DeviceParams(
            "diamond_ferrite_graphene",
            ferrite="CoFe2O4",
            interface_recombination_cm_s=1e7,
            ferrite_um=2.0,
        ),
        db,
    )
    assert bad_variant.power_density_W_cm2 < baseline.power_density_W_cm2
    assert bad_variant.interface_loss_fraction > baseline.interface_loss_fraction

    abrupt = simulate_gen2(Gen2Params("ferrite_transport", ferrite="Fe3O4"), db)
    graded = simulate_gen2(Gen2Params("graded_interface", ferrite="Fe3O4"), db)
    composite = simulate_gen2(
        Gen2Params(
            "composite_layer",
            ferrite="Fe3O4",
            mixture_kind="diamond_ferrite",
            composition_fraction=0.25,
        ),
        db,
    )
    assert graded.interface_loss_fraction < abrupt.interface_loss_fraction
    assert composite.interface_loss_fraction < abrupt.interface_loss_fraction

    gen3_baseline = simulate_gen3(Gen3Params("baseline"), db)
    fingers = simulate_gen3(
        Gen3Params("straight_fingers", pitch_um=3.0, ribbon_width_nm=30.0, graphene_layers=1),
        db,
        gen3_baseline.power_density_W_cm2,
    )
    dense_mesh = simulate_gen3(
        Gen3Params("multilayer_3d_mesh", pitch_um=0.75, ribbon_width_nm=120.0, graphene_layers=4),
        db,
        gen3_baseline.power_density_W_cm2,
    )
    assert fingers.mean_carrier_travel_um < gen3_baseline.mean_carrier_travel_um
    assert dense_mesh.graphene_interface_area_ratio > fingers.graphene_interface_area_ratio

    models = {m.architecture: m for m in manufacturing_models()}
    assert manufacturability_score(models["straight_graphene_fingers"]) > manufacturability_score(models["multilayer_graphene_mesh"])
    assert models["laser_written_graphitic_channels"].trl >= models["graphene_coated_nanopore_channels"].trl

    substrates = {s.name: s for s in SUBSTRATES}
    assert substrates["Diamond"].laser_graphitic_feasible
    assert not substrates["4H-SiC"].laser_graphitic_feasible
    si = simulate_case(substrates["Silicon"], GEN5_GEOMETRIES["straight_fingers"], GEN5_SOURCES["Ni63"])
    diamond = simulate_case(substrates["Diamond"], GEN5_GEOMETRIES["straight_fingers"], GEN5_SOURCES["Ni63"])
    assert si.substrate.cost_relative < diamond.substrate.cost_relative

    top = simulate_gen6(Gen6Params("top_source", "Ni63", 20.0, 0.5, 0.15, 6.0, 60.0, 0.75, 64, 1e-3, 1e8, 1.0), db)
    dist = simulate_gen6(Gen6Params("distributed_source", "Ni63", 20.0, 0.5, 0.45, 6.0, 60.0, 0.75, 64, 1e-3, 1e8, 1.0), db)
    assert 0.0 <= top.cce <= 1.0
    assert dist.source_utilization >= top.source_utilization
