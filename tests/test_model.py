from radiovoltaic.materials import load_materials
from radiovoltaic.model import DeviceParams, beta_deposition_fraction, simulate


def test_deposition_increases_with_thickness():
    thin = beta_deposition_fraction(17.0, 1.0, 3.51)
    thick = beta_deposition_fraction(17.0, 20.0, 3.51)
    assert 0.0 <= thin < thick <= 1.0


def test_baseline_outputs_are_physical():
    db = load_materials()
    result = simulate(DeviceParams("baseline"), db)
    assert 0.0 <= result.charge_collection_efficiency <= 1.0
    assert result.current_density_A_cm2 >= 0.0
    assert result.power_density_W_cm2 >= 0.0
    assert result.estimated_lifetime_years > 0.0


def test_bad_interfaces_can_make_ferrite_worse_than_baseline():
    db = load_materials()
    baseline = simulate(DeviceParams("baseline", interface_recombination_cm_s=1e3), db)
    variant = simulate(
        DeviceParams(
            "diamond_ferrite_graphene",
            ferrite="CoFe2O4",
            interface_recombination_cm_s=1e7,
            ferrite_um=2.0,
        ),
        db,
    )
    assert variant.power_density_W_cm2 < baseline.power_density_W_cm2
    assert variant.interface_loss_fraction > baseline.interface_loss_fraction

