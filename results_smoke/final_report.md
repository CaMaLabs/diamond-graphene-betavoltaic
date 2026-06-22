# Ferrite Interlayer Radiovoltaic Simulation Report

## Conclusion

**C. Ferrite layer appears detrimental.**

Best median variant is diamond_ferrite, but median power ratio is 0.36 and interface loss is 0.40.

## Architecture Median Metrics

| Architecture | CCE | Power (W/cm^2) | Lifetime (yr) | Interface loss | Recombination |
|---|---:|---:|---:|---:|---:|
| baseline | 0.1107 | 6.5301e-10 | 0.2641 | 0.351 | 0.197 |
| diamond_ferrite | 0.07149 | 2.3578e-10 | 0.2211 | 0.397 | 0.219 |
| diamond_ferrite_graphene | 0.04699 | 1.0184e-10 | 0.2211 | 0.612 | 0.338 |
| multi_ferrite_graphene | 0.03106 | 4.2537e-11 | 0.2052 | 0.644 | 0.355 |

## Falsification Tests

- diamond_ferrite: power ratio 0.36, lifetime ratio 0.84, median interface loss 0.40.
- diamond_ferrite_graphene: power ratio 0.16, lifetime ratio 0.84, median interface loss 0.61.
- multi_ferrite_graphene: power ratio 0.07, lifetime ratio 0.78, median interface loss 0.64.
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

1. baseline, source=Ni63, ferrite=none, diamond=12 um, ferrite=0 um, layers=1: power=1.1500e-09 W/cm^2, CCE=0.162, lifetime=0.264 yr, interface loss=0.35.
2. baseline, source=Ni63, ferrite=none, diamond=12 um, ferrite=0 um, layers=1: power=1.1500e-09 W/cm^2, CCE=0.162, lifetime=0.264 yr, interface loss=0.35.
3. diamond_ferrite, source=Ni63, ferrite=Fe3O4, diamond=12 um, ferrite=0.6 um, layers=1: power=1.0048e-09 W/cm^2, CCE=0.151, lifetime=0.2 yr, interface loss=0.40.
4. diamond_ferrite, source=Ni63, ferrite=Fe3O4, diamond=12 um, ferrite=0.1 um, layers=1: power=1.0004e-09 W/cm^2, CCE=0.151, lifetime=0.237 yr, interface loss=0.40.
5. diamond_ferrite, source=Ni63, ferrite=NiFe2O4, diamond=12 um, ferrite=0.1 um, layers=1: power=9.6933e-10 W/cm^2, CCE=0.149, lifetime=0.242 yr, interface loss=0.38.
6. diamond_ferrite, source=Ni63, ferrite=CoFe2O4, diamond=12 um, ferrite=0.1 um, layers=1: power=8.8853e-10 W/cm^2, CCE=0.142, lifetime=0.232 yr, interface loss=0.39.
7. diamond_ferrite, source=Ni63, ferrite=NiFe2O4, diamond=12 um, ferrite=0.6 um, layers=1: power=5.1343e-10 W/cm^2, CCE=0.108, lifetime=0.21 yr, interface loss=0.40.
8. diamond_ferrite_graphene, source=Ni63, ferrite=Fe3O4, diamond=12 um, ferrite=0.6 um, layers=1: power=4.3460e-10 W/cm^2, CCE=0.100, lifetime=0.2 yr, interface loss=0.60.

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
- `uncertainty.csv`: perturbed ensemble for benefit significance.
- `sensitivity.csv`: one-factor sensitivity ranking.
- `plots/`: CCE, power, lifetime, interface loss, and sensitivity plots.
