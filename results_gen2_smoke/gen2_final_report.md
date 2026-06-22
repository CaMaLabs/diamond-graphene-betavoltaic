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
| 1 | embedded_graphene_fingers | 4.4243e-10 | 1.64 | 0.1004 | 0.9161 | 0.134 |
| 2 | baseline | 2.7025e-10 | 1.00 | 0.07846 | 1.314 | 0.183 |
| 3 | diamond_ideal_defect_sink | 2.3796e-11 | 0.09 | 0.02328 | 0.2311 | 0.331 |
| 4 | composite_layer | 2.1889e-11 | 0.08 | 0.02233 | 0.7031 | 0.154 |
| 5 | diamond_high_entropy_alloy | 9.3314e-13 | 0.00 | 0.004611 | 0.5369 | 0.336 |
| 6 | graded_interface | 1.2773e-17 | 0.00 | 1.706e-05 | 0.4231 | 0.316 |
| 7 | ferrite_transport | 1.2091e-17 | 0.00 | 1.66e-05 | 0.4231 | 0.336 |
| 8 | ferrite_graphene | 6.6293e-18 | 0.00 | 1.229e-05 | 0.4231 | 0.504 |

## Failure Mode Ranking

| Architecture | Power ratio | #1 loss | #2 loss | #3 loss |
|---|---:|---|---|---|
| embedded_graphene_fingers | 1.64 | trap_density (0.279) | interface_losses (0.134) | bulk_recombination (0.025) |
| baseline | 1.00 | trap_density (0.280) | bulk_recombination (0.240) | interface_losses (0.183) |
| diamond_ideal_defect_sink | 0.09 | bulk_recombination (0.703) | interface_losses (0.331) | trap_density (0.278) |
| composite_layer | 0.08 | bulk_recombination (0.747) | trap_density (0.279) | interface_losses (0.154) |
| diamond_high_entropy_alloy | 0.00 | bulk_recombination (0.939) | interface_losses (0.336) | trap_density (0.279) |
| graded_interface | 0.00 | bulk_recombination (1.000) | interface_losses (0.316) | trap_density (0.279) |
| ferrite_transport | 0.00 | bulk_recombination (1.000) | interface_losses (0.336) | trap_density (0.279) |
| ferrite_graphene | 0.00 | bulk_recombination (1.000) | interface_losses (0.504) | trap_density (0.279) |

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

1. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=strong, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.1 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.2598e-10 W/cm^2, CCE=0.109, lifetime=0.705 yr, interface loss=0.134.
2. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=strong, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.5 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.2598e-10 W/cm^2, CCE=0.109, lifetime=0.705 yr, interface loss=0.134.
3. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=none, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.1 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.2597e-10 W/cm^2, CCE=0.109, lifetime=0.701 yr, interface loss=0.134.
4. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=none, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.5 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.2597e-10 W/cm^2, CCE=0.109, lifetime=0.701 yr, interface loss=0.134.
5. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=strong, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.1 um, T=300 K, E=5e+04 V/cm, SRV=1e+05 cm/s: power=5.2526e-10 W/cm^2, CCE=0.109, lifetime=0.705 yr, interface loss=0.135.
6. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=strong, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.5 um, T=300 K, E=5e+04 V/cm, SRV=1e+05 cm/s: power=5.2526e-10 W/cm^2, CCE=0.109, lifetime=0.705 yr, interface loss=0.135.
7. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=none, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.1 um, T=300 K, E=5e+04 V/cm, SRV=1e+05 cm/s: power=5.2526e-10 W/cm^2, CCE=0.109, lifetime=0.701 yr, interface loss=0.135.
8. embedded_graphene_fingers, source=Ni63, ferrite=Fe3O4, healing=none, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.5 um, T=300 K, E=5e+04 V/cm, SRV=1e+05 cm/s: power=5.2526e-10 W/cm^2, CCE=0.109, lifetime=0.701 yr, interface loss=0.135.
9. composite_layer, source=Ni63, ferrite=Fe3O4, healing=strong, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.1 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.0203e-10 W/cm^2, CCE=0.107, lifetime=0.705 yr, interface loss=0.154.
10. composite_layer, source=Ni63, ferrite=Fe3O4, healing=strong, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.5 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.0203e-10 W/cm^2, CCE=0.107, lifetime=0.705 yr, interface loss=0.154.
11. composite_layer, source=Ni63, ferrite=Fe3O4, healing=none, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.1 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.0202e-10 W/cm^2, CCE=0.107, lifetime=0.701 yr, interface loss=0.154.
12. composite_layer, source=Ni63, ferrite=Fe3O4, healing=none, mixture=diamond_graphene, fraction=1, diamond=8 um, interlayer=0.5 um, T=300 K, E=5e+04 V/cm, SRV=1e+03 cm/s: power=5.0202e-10 W/cm^2, CCE=0.107, lifetime=0.701 yr, interface loss=0.154.

## Minimum Architectural Change Assessment

The minimum successful change is defined as the smallest departure from the failed ferrite layer that produces power above the best baseline while retaining a nonzero defect-sink or healing benefit.
The minimum observed change is `composite_layer` with healing `strong` and mixture `diamond_graphene` at fraction 0.5.

## Files

- `gen2_summary.csv`: all generation-2 cases and required outputs.
- `gen2_loss_budget.csv`: interface and non-interface loss channels by case.
- `gen2_sensitivity.csv`: sensitivity ranking.
- `gen2_normalized_sensitivity.csv`: equal dimensionless coefficient sensitivity and implementation-bias check.
- `gen2_failure_modes.csv`: dominant loss-channel ranking.
- `gen2_architecture_rankings.csv`: median architecture ranking.
- `plots/`: power, interface-loss, and failure-channel visualizations.
