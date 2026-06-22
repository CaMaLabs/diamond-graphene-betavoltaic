# Generation-3 Embedded Graphene Collector Geometry Optimization

## Conclusion

Best net-power geometry: **interdigitated_combs** with power 2.8084e-09 W/cm^2, CCE 0.253, interface loss 0.198, trap penalty 0.079, and manufacturability score 0.61.
Smallest geometry departure beating baseline by at least 2x: **straight_fingers**, pitch 12 um, width 15 nm, layers 1, depth fraction 0.35; ratio 2.39x, manufacturability 0.69.

## Architecture Ranking

| Rank | Geometry | Median power (W/cm^2) | Ratio vs baseline | Median CCE | Carrier survival | Interface loss | Trap penalty | Lifetime (yr) | Manufacturability |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | straight_fingers | 6.5728e-10 | 1.79 | 0.1224 | 0.823 | 0.207 | 0.079 | 0.000801 | 0.59 |
| 2 | interdigitated_combs | 6.2907e-10 | 1.71 | 0.1197 | 0.847 | 0.215 | 0.079 | 0.00081 | 0.43 |
| 3 | radial_spokes | 6.2874e-10 | 1.71 | 0.1197 | 0.835 | 0.211 | 0.079 | 0.000806 | 0.41 |
| 4 | honeycomb_mesh | 5.5463e-10 | 1.51 | 0.1124 | 0.864 | 0.224 | 0.079 | 0.000829 | 0.16 |
| 5 | fractal_tree | 5.3727e-10 | 1.46 | 0.1106 | 0.871 | 0.229 | 0.080 | 0.00084 | 0.00 |
| 6 | multilayer_3d_mesh | 4.3953e-10 | 1.20 | 0.1001 | 0.870 | 0.245 | 0.081 | 0.00088 | 0.00 |
| 7 | random_percolating_nanoribbons | 4.2460e-10 | 1.16 | 0.09835 | 0.812 | 0.240 | 0.081 | 0.00087 | 0.02 |
| 8 | baseline | 3.6711e-10 | 1.00 | 0.09145 | 0.482 | 0.180 | 0.078 | 0.000789 | 0.98 |

## Best Individual Geometries

1. interdigitated_combs: pitch=6 um, width=120 nm, layers=1, depth=0.9, diamond=20 um; power=2.8084e-09 W/cm^2, ratio=7.20x, CCE=0.253, travel=1.63 um, area ratio=8.13, traps=2.033e+13 cm^-3, manufacturability=0.61.
2. interdigitated_combs: pitch=6 um, width=60 nm, layers=1, depth=0.9, diamond=20 um; power=2.7914e-09 W/cm^2, ratio=7.16x, CCE=0.252, travel=1.63 um, area ratio=8.11, traps=1.761e+13 cm^-3, manufacturability=0.61.
3. interdigitated_combs: pitch=6 um, width=30 nm, layers=1, depth=0.9, diamond=20 um; power=2.7748e-09 W/cm^2, ratio=7.12x, CCE=0.251, travel=1.63 um, area ratio=8.11, traps=1.625e+13 cm^-3, manufacturability=0.59.
4. interdigitated_combs: pitch=6 um, width=15 nm, layers=1, depth=0.9, diamond=20 um; power=2.7464e-09 W/cm^2, ratio=7.05x, CCE=0.250, travel=1.63 um, area ratio=8.10, traps=1.556e+13 cm^-3, manufacturability=0.50.
5. radial_spokes: pitch=6 um, width=120 nm, layers=1, depth=0.9, diamond=20 um; power=2.6886e-09 W/cm^2, ratio=6.90x, CCE=0.247, travel=1.79 um, area ratio=7.22, traps=1.681e+13 cm^-3, manufacturability=0.59.
6. radial_spokes: pitch=6 um, width=60 nm, layers=1, depth=0.9, diamond=20 um; power=2.6746e-09 W/cm^2, ratio=6.86x, CCE=0.247, travel=1.79 um, area ratio=7.21, traps=1.439e+13 cm^-3, manufacturability=0.59.
7. straight_fingers: pitch=3 um, width=120 nm, layers=1, depth=0.9, diamond=20 um; power=2.6652e-09 W/cm^2, ratio=6.84x, CCE=0.246, travel=1.35 um, area ratio=12.04, traps=2.591e+13 cm^-3, manufacturability=0.70.
8. radial_spokes: pitch=6 um, width=30 nm, layers=1, depth=0.9, diamond=20 um; power=2.6597e-09 W/cm^2, ratio=6.82x, CCE=0.246, travel=1.79 um, area ratio=7.21, traps=1.318e+13 cm^-3, manufacturability=0.56.
9. straight_fingers: pitch=3 um, width=60 nm, layers=1, depth=0.9, diamond=20 um; power=2.6447e-09 W/cm^2, ratio=6.78x, CCE=0.245, travel=1.34 um, area ratio=12.02, traps=2.188e+13 cm^-3, manufacturability=0.70.
10. radial_spokes: pitch=6 um, width=15 nm, layers=1, depth=0.9, diamond=20 um; power=2.6330e-09 W/cm^2, ratio=6.75x, CCE=0.245, travel=1.79 um, area ratio=7.20, traps=1.257e+13 cm^-3, manufacturability=0.48.
11. straight_fingers: pitch=6 um, width=120 nm, layers=1, depth=0.9, diamond=20 um; power=2.6324e-09 W/cm^2, ratio=6.75x, CCE=0.245, travel=1.93 um, area ratio=6.02, traps=1.295e+13 cm^-3, manufacturability=0.76.
12. straight_fingers: pitch=3 um, width=30 nm, layers=1, depth=0.9, diamond=20 um; power=2.6268e-09 W/cm^2, ratio=6.74x, CCE=0.245, travel=1.34 um, area ratio=12.01, traps=1.986e+13 cm^-3, manufacturability=0.67.
13. straight_fingers: pitch=6 um, width=60 nm, layers=1, depth=0.9, diamond=20 um; power=2.6216e-09 W/cm^2, ratio=6.73x, CCE=0.244, travel=1.93 um, area ratio=6.01, traps=1.094e+13 cm^-3, manufacturability=0.76.
14. straight_fingers: pitch=6 um, width=30 nm, layers=1, depth=0.9, diamond=20 um; power=2.6087e-09 W/cm^2, ratio=6.69x, CCE=0.244, travel=1.93 um, area ratio=6.00, traps=9.932e+12 cm^-3, manufacturability=0.73.
15. straight_fingers: pitch=3 um, width=15 nm, layers=1, depth=0.9, diamond=20 um; power=2.5989e-09 W/cm^2, ratio=6.67x, CCE=0.243, travel=1.34 um, area ratio=12.01, traps=1.886e+13 cm^-3, manufacturability=0.59.

## Interpretation

- Straight fingers are the conservative minimum-change geometry; they improve travel distance with the lowest added interface area.
- Interdigitated combs and radial spokes add more collection reach but pay more interface and fabrication penalty.
- Honeycomb, fractal/tree, random nanoribbon, and multilayer 3D meshes can reduce travel distance strongly, but interface/trap area and manufacturability penalties decide whether the gain survives.
- The optimization criterion is net electrical power after added graphene/diamond interface, interface traps, geometric occlusion, and manufacturability-risk penalties.
