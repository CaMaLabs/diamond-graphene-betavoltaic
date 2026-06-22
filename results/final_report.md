# Ferrite Interlayer Radiovoltaic Simulation Report

## Conclusion

**C. Ferrite layer appears detrimental.**

Best median variant is diamond_ferrite, but median power ratio is 0.40 and interface loss is 0.41.

## Architecture Median Metrics

| Architecture | CCE | Power (W/cm^2) | Lifetime (yr) | Interface loss | Recombination |
|---|---:|---:|---:|---:|---:|
| baseline | 0.03163 | 3.3888e-10 | 0.1636 | 0.351 | 0.210 |
| diamond_ferrite | 0.02779 | 1.3401e-10 | 0.1244 | 0.407 | 0.247 |
| diamond_ferrite_graphene | 0.01589 | 2.5146e-11 | 0.1244 | 0.640 | 0.380 |
| multi_ferrite_graphene | 0.01058 | 1.3710e-11 | 0.05867 | 0.680 | 0.392 |

## Falsification Tests

- diamond_ferrite: power ratio 0.40, lifetime ratio 0.76, median interface loss 0.41.
- diamond_ferrite_graphene: power ratio 0.07, lifetime ratio 0.76, median interface loss 0.64.
- multi_ferrite_graphene: power ratio 0.04, lifetime ratio 0.36, median interface loss 0.68.
- Interface-loss disproof criterion: ferrite is rejected where added diamond-ferrite and ferrite-graphene losses exceed the collection or lifetime gain.
- Radiation-tolerance criterion: ferrite must reduce trap accumulation enough to extend lifetime after accounting for extra series and interface losses.
- Defect-sink criterion: defect populations must decline relative to baseline without an offsetting recombination increase.
- Long-term output criterion: power density must remain above baseline beyond uncertainty, not only at beginning of life.
- Uncertainty criterion: median benefit below 5% in the perturbed ensemble is treated as insufficient evidence.

## Sensitivity Ranking

| Rank | Parameter | Log elasticity | Absolute power swing (W/cm^2) |
|---:|---|---:|---:|
| 1 | diamond_um | 1.792 | 6.2955e-10 |
| 2 | interface_recombination_cm_s | -0.045 | 1.2800e-11 |
| 3 | ferrite_um | 0.033 | 9.5346e-12 |
| 4 | defect_healing_rate_s | -0.028 | 8.0496e-12 |
| 5 | electric_field_V_cm | 0.010 | 2.7402e-12 |
| 6 | annealing_rate_s | -0.006 | 1.7028e-12 |
| 7 | trap_density_cm3 | 0.000 | 1.6760e-15 |
| 8 | temperature_K | 0.000 | 0.0000e+00 |

## Ranked Design Recommendations

1. baseline, source=Ni63, ferrite=none, diamond=20 um, ferrite=0 um, layers=1: power=2.7117e-09 W/cm^2, CCE=0.249, lifetime=0.063 yr, interface loss=0.35.
2. baseline, source=Ni63, ferrite=none, diamond=20 um, ferrite=0 um, layers=1: power=2.6793e-09 W/cm^2, CCE=0.247, lifetime=0.264 yr, interface loss=0.35.
3. baseline, source=Ni63, ferrite=none, diamond=20 um, ferrite=0 um, layers=1: power=2.4974e-09 W/cm^2, CCE=0.239, lifetime=0.0528 yr, interface loss=0.35.
4. diamond_ferrite, source=Ni63, ferrite=NiFe2O4, diamond=20 um, ferrite=0.05 um, layers=1: power=2.3991e-09 W/cm^2, CCE=0.234, lifetime=0.0623 yr, interface loss=0.37.
5. baseline, source=Ni63, ferrite=none, diamond=20 um, ferrite=0 um, layers=1: power=2.3916e-09 W/cm^2, CCE=0.233, lifetime=0.0528 yr, interface loss=0.36.
6. diamond_ferrite, source=Ni63, ferrite=NiFe2O4, diamond=20 um, ferrite=0.05 um, layers=1: power=2.3721e-09 W/cm^2, CCE=0.232, lifetime=0.251 yr, interface loss=0.38.
7. diamond_ferrite, source=Ni63, ferrite=Fe3O4, diamond=20 um, ferrite=0.05 um, layers=1: power=2.3378e-09 W/cm^2, CCE=0.231, lifetime=0.0621 yr, interface loss=0.40.
8. diamond_ferrite, source=Ni63, ferrite=Fe3O4, diamond=20 um, ferrite=0.3 um, layers=1: power=2.3373e-09 W/cm^2, CCE=0.231, lifetime=0.212 yr, interface loss=0.40.

## Assumptions

- Beta deposition uses a compact empirical CSDA-like range approximation, not a particle Monte Carlo.
- Carrier collection is represented by drift plus diffusion length relative to diamond thickness.
- Trap-limited lifetime uses a Shockley-Read-Hall-style capture term with reduced-order defect kinetics.
- Ferrites are represented by mobility/resistivity, interface barrier, trap density, defect-sink strength, and healing rate.
- Graphene is modeled as a low-loss collection sheet with finite sheet resistance and interface recombination scaling.
- Thermal rise is one-dimensional conduction under areal beta heating.
- Voltage is a load-limited estimate capped below the diamond bandgap, not a full diode solution.

## Failure Modes

- Diamond-ferrite barrier or surface recombination dominates before defect-sink benefits appear.
- High-resistivity ferrites reduce current through series transport penalties.
- Multi-layer ferrites add internal interfaces faster than they add defect tolerance.
- Low beta energy sources fail to deposit enough usable energy in the chosen diamond thickness.
- Annealing and defect-healing rates are too slow at operating temperature.
- Graphene sheet resistance or contact quality dominates collector losses.
- Thermal assumptions break down if source activity is pushed far above the default areal activity.

## Output Files

- `summary.csv`: full parameter sweep.
- `interface_loss_budget.csv`: per-interface and per-transport-channel loss budget.
- `uncertainty.csv`: perturbed ensemble for benefit significance.
- `sensitivity.csv`: one-factor sensitivity ranking.
- `plots/`: CCE, power, lifetime, thermal, interface loss, and sensitivity plots.
