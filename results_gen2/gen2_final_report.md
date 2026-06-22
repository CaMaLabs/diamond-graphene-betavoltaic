# Generation-2 Ferrite Interface Falsification Study

## Required Conclusions

- A. Interface losses are the primary bottleneck: NO.
- B. Bulk ferrite transport is the primary bottleneck: YES.
- C. Composite architectures outperform layered architectures: YES.
- D. Self-healing effects are too small to matter: YES.
- E. Self-healing effects materially improve lifetime: NO; idealized sink median lifetime ratio is 0.18.
- F. A modified architecture exceeds the baseline: YES.
- G. No tested architecture exceeds the baseline: NO.

## Most Important Question

Yes. The smallest successful tested departure is `composite_layer`; the best-power individual case is `embedded_graphene_fingers`.

Interface ablation check: graded interfaces change median ferrite-layer power by 1.06x relative to abrupt ferrite transport. This is the direct test of whether reducing the diamond-ferrite interface alone reverses the first-study result.

## Mobility Sensitivity Bias Check

The earlier broad sensitivity ranked carrier mobility first. The normalized local coefficient sensitivity ranks `carrier_mobility` first with |d ln P / d ln coefficient| = 0.921. Carrier mobility has normalized sensitivity 0.921 and dominance ratio 1.65 versus the median absolute sensitivity.
Verdict: the original carrier-mobility dominance is likely a parameter-scaling artifact.

## Architecture Rankings

| Rank | Architecture | Median power (W/cm^2) | Ratio vs baseline | Median CCE | Median lifetime (yr) | Median interface loss |
|---:|---|---:|---:|---:|---:|---:|
| 1 | embedded_graphene_fingers | 4.3326e-10 | 2.38 | 0.05872 | 1.077 | 0.158 |
| 2 | baseline | 1.8194e-10 | 1.00 | 0.03612 | 1.328 | 0.182 |
| 3 | diamond_ideal_defect_sink | 2.8859e-11 | 0.16 | 0.01288 | 0.2396 | 0.330 |
| 4 | composite_layer | 2.7715e-11 | 0.15 | 0.01193 | 0.9065 | 0.221 |
| 5 | diamond_high_entropy_alloy | 9.2589e-13 | 0.01 | 0.002363 | 0.5381 | 0.335 |
| 6 | graded_interface | 1.2872e-17 | 0.00 | 1.376e-05 | 0.4361 | 0.315 |
| 7 | ferrite_transport | 1.2179e-17 | 0.00 | 1.335e-05 | 0.4361 | 0.335 |
| 8 | ferrite_graphene | 6.7279e-18 | 0.00 | 9.879e-06 | 0.4361 | 0.502 |

## Failure Mode Ranking

| Architecture | Power ratio | #1 loss | #2 loss | #3 loss |
|---|---:|---|---|---|
| embedded_graphene_fingers | 2.38 | trap_density (0.279) | interface_losses (0.158) | bulk_recombination (0.055) |
| baseline | 1.00 | bulk_recombination (0.296) | trap_density (0.279) | interface_losses (0.182) |
| diamond_ideal_defect_sink | 0.16 | bulk_recombination (0.728) | interface_losses (0.330) | trap_density (0.277) |
| composite_layer | 0.15 | bulk_recombination (0.790) | trap_density (0.279) | interface_losses (0.221) |
| diamond_high_entropy_alloy | 0.01 | bulk_recombination (0.949) | interface_losses (0.335) | trap_density (0.279) |
| graded_interface | 0.00 | bulk_recombination (1.000) | interface_losses (0.315) | trap_density (0.278) |
| ferrite_transport | 0.00 | bulk_recombination (1.000) | interface_losses (0.335) | trap_density (0.278) |
| ferrite_graphene | 0.00 | bulk_recombination (1.000) | interface_losses (0.502) | trap_density (0.278) |

## Sensitivity Rankings

| Rank | Factor | Relative swing vs base | Absolute swing (W/cm^2) |
|---:|---|---:|---:|
| 1 | carrier_mobility | 13.517 | 5.4706e-14 |
| 2 | thermal_effects | 0.223 | 9.0137e-16 |
| 3 | healing_rate | 0.060 | 2.4182e-16 |
| 4 | interface_losses | 0.002 | 6.8644e-18 |
| 5 | trap_density | 0.001 | 3.9852e-18 |
| 6 | bulk_recombination | 0.000 | 1.9546e-18 |

## Normalized Dimensionless Sensitivity

| Rank | Factor | Parameter | Log sensitivity | Dominance ratio | Interpretation |
|---:|---|---|---:|---:|---|
| 1 | carrier_mobility | mobility_scale | 0.9213 | 1.65 | comparable local sensitivity |
| 2 | interface_losses | interface_loss_scale | -0.8492 | 1.52 | comparable local sensitivity |
| 3 | trap_density | trap_loss_scale | -0.773 | 1.39 | comparable local sensitivity |
| 4 | bulk_recombination | bulk_recombination_scale | -0.3421 | 0.61 | comparable local sensitivity |
| 5 | healing_rate | healing_rate_scale | 0.0009767 | 0.00 | comparable local sensitivity |
| 6 | thermal_effects | thermal_loss_scale | 0 | 0.00 | comparable local sensitivity |

## Best Individual Cases

1. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.05 um, T=300 K, E=1e+05 V/cm, SRV=1e+03 cm/s: power=2.5038e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
2. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.2 um, T=300 K, E=1e+05 V/cm, SRV=1e+03 cm/s: power=2.5038e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
3. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.8 um, T=300 K, E=1e+05 V/cm, SRV=1e+03 cm/s: power=2.5038e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
4. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.05 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=2.5038e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
5. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.2 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=2.5038e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
6. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.8 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=2.5038e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
7. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.05 um, T=300 K, E=1e+05 V/cm, SRV=1e+04 cm/s: power=2.5037e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
8. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.2 um, T=300 K, E=1e+05 V/cm, SRV=1e+04 cm/s: power=2.5037e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
9. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.8 um, T=300 K, E=1e+05 V/cm, SRV=1e+04 cm/s: power=2.5037e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
10. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.05 um, T=300 K, E=5e+04 V/cm, SRV=1e+04 cm/s: power=2.5037e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
11. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.2 um, T=300 K, E=5e+04 V/cm, SRV=1e+04 cm/s: power=2.5037e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.
12. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=idealized, mixture=diamond_graphene, fraction=1, diamond=20 um, interlayer=0.8 um, T=300 K, E=5e+04 V/cm, SRV=1e+04 cm/s: power=2.5037e-09 W/cm^2, CCE=0.239, lifetime=0.743 yr, interface loss=0.134.

## Minimum Architectural Change Assessment

The minimum successful change is defined as the smallest departure from the failed ferrite layer that produces power above the best baseline while retaining a nonzero defect-sink or healing benefit.
The minimum observed change is `composite_layer` with healing `idealized` and mixture `diamond_graphene` at fraction 0.1.

## Files

- `gen2_summary.csv`: all generation-2 cases and required outputs.
- `gen2_loss_budget.csv`: interface and non-interface loss channels by case.
- `gen2_sensitivity.csv`: sensitivity ranking.
- `gen2_normalized_sensitivity.csv`: equal dimensionless coefficient sensitivity and implementation-bias check.
- `gen2_failure_modes.csv`: dominant loss-channel ranking.
- `gen2_architecture_rankings.csv`: median architecture ranking.
- `plots/`: power, interface-loss, and failure-channel visualizations.
