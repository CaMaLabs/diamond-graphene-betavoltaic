# Generation-3 Embedded Graphene Collector Geometry Optimization

## Conclusion

Best net-power geometry: **interdigitated_combs** with power 2.3604e-09 W/cm^2, CCE 0.232, interface loss 0.195, trap penalty 0.079, and manufacturability score 0.63.
Smallest geometry departure beating baseline by at least 2x: **straight_fingers**, pitch 6 um, width 25 nm, layers 1, depth fraction 0.75; ratio 5.59x, manufacturability 0.71.

## Architecture Ranking

| Rank | Geometry | Median power (W/cm^2) | Ratio vs baseline | Median CCE | Carrier survival | Interface loss | Trap penalty | Lifetime (yr) | Manufacturability |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | straight_fingers | 2.0162e-09 | 5.17 | 0.2143 | 0.813 | 0.205 | 0.079 | 0.000872 | 0.64 |
| 2 | radial_spokes | 1.8455e-09 | 4.73 | 0.205 | 0.815 | 0.209 | 0.079 | 0.000875 | 0.43 |
| 3 | interdigitated_combs | 1.7822e-09 | 4.57 | 0.2013 | 0.824 | 0.212 | 0.079 | 0.000877 | 0.46 |
| 4 | honeycomb_mesh | 1.3899e-09 | 3.57 | 0.1769 | 0.832 | 0.221 | 0.079 | 0.000884 | 0.18 |
| 5 | fractal_tree | 1.1880e-09 | 3.05 | 0.1627 | 0.832 | 0.226 | 0.079 | 0.000889 | 0.00 |
| 6 | random_percolating_nanoribbons | 7.3602e-10 | 1.89 | 0.1262 | 0.771 | 0.236 | 0.080 | 0.000903 | 0.02 |
| 7 | multilayer_3d_mesh | 6.4109e-10 | 1.64 | 0.1141 | 0.803 | 0.242 | 0.081 | 0.000917 | 0.00 |
| 8 | baseline | 3.8981e-10 | 1.00 | 0.09423 | 0.326 | 0.180 | 0.078 | 0.000864 | 0.98 |

## Best Individual Geometries

1. interdigitated_combs: pitch=6 um, width=100 nm, layers=1, depth=0.75, diamond=20 um; power=2.3604e-09 W/cm^2, ratio=6.06x, CCE=0.232, travel=2.22 um, area ratio=6.77, traps=1.694e+13 cm^-3, manufacturability=0.63.
2. interdigitated_combs: pitch=6 um, width=25 nm, layers=1, depth=0.75, diamond=20 um; power=2.3282e-09 W/cm^2, ratio=5.97x, CCE=0.230, travel=2.22 um, area ratio=6.76, traps=1.354e+13 cm^-3, manufacturability=0.58.
3. honeycomb_mesh: pitch=6 um, width=100 nm, layers=1, depth=0.75, diamond=20 um; power=2.2938e-09 W/cm^2, ratio=5.88x, CCE=0.229, travel=2.08 um, area ratio=9.28, traps=2.728e+13 cm^-3, manufacturability=0.38.
4. honeycomb_mesh: pitch=6 um, width=25 nm, layers=1, depth=0.75, diamond=20 um; power=2.2553e-09 W/cm^2, ratio=5.79x, CCE=0.227, travel=2.08 um, area ratio=9.26, traps=2.260e+13 cm^-3, manufacturability=0.33.
5. radial_spokes: pitch=6 um, width=100 nm, layers=1, depth=0.75, diamond=20 um; power=2.2484e-09 W/cm^2, ratio=5.77x, CCE=0.226, travel=2.37 um, area ratio=6.02, traps=1.401e+13 cm^-3, manufacturability=0.61.
6. radial_spokes: pitch=6 um, width=25 nm, layers=1, depth=0.75, diamond=20 um; power=2.2211e-09 W/cm^2, ratio=5.70x, CCE=0.225, travel=2.37 um, area ratio=6.00, traps=1.098e+13 cm^-3, manufacturability=0.55.
7. straight_fingers: pitch=6 um, width=100 nm, layers=1, depth=0.75, diamond=20 um; power=2.2010e-09 W/cm^2, ratio=5.65x, CCE=0.224, travel=2.5 um, area ratio=5.02, traps=1.080e+13 cm^-3, manufacturability=0.77.
8. fractal_tree: pitch=6 um, width=100 nm, layers=1, depth=0.75, diamond=20 um; power=2.1806e-09 W/cm^2, ratio=5.59x, CCE=0.223, travel=2.01 um, area ratio=10.79, traps=3.454e+13 cm^-3, manufacturability=0.19.
9. straight_fingers: pitch=6 um, width=25 nm, layers=1, depth=0.75, diamond=20 um; power=2.1774e-09 W/cm^2, ratio=5.59x, CCE=0.223, travel=2.5 um, area ratio=5.00, traps=8.277e+12 cm^-3, manufacturability=0.71.
10. fractal_tree: pitch=6 um, width=25 nm, layers=1, depth=0.75, diamond=20 um; power=2.1413e-09 W/cm^2, ratio=5.49x, CCE=0.221, travel=2.01 um, area ratio=10.76, traps=2.909e+13 cm^-3, manufacturability=0.14.
11. straight_fingers: pitch=2 um, width=100 nm, layers=1, depth=0.75, diamond=20 um; power=2.0369e-09 W/cm^2, ratio=5.23x, CCE=0.215, travel=1.89 um, area ratio=15.05, traps=3.239e+13 cm^-3, manufacturability=0.67.
12. straight_fingers: pitch=6 um, width=100 nm, layers=2, depth=0.75, diamond=20 um; power=2.0292e-09 W/cm^2, ratio=5.21x, CCE=0.215, travel=2.68 um, area ratio=7.87, traps=1.642e+13 cm^-3, manufacturability=0.67.
13. straight_fingers: pitch=6 um, width=25 nm, layers=2, depth=0.75, diamond=20 um; power=2.0033e-09 W/cm^2, ratio=5.14x, CCE=0.214, travel=2.67 um, area ratio=7.85, traps=1.286e+13 cm^-3, manufacturability=0.61.
14. straight_fingers: pitch=2 um, width=25 nm, layers=1, depth=0.75, diamond=20 um; power=1.9974e-09 W/cm^2, ratio=5.12x, CCE=0.213, travel=1.89 um, area ratio=15.01, traps=2.483e+13 cm^-3, manufacturability=0.61.
15. interdigitated_combs: pitch=6 um, width=100 nm, layers=2, depth=0.75, diamond=20 um; power=1.9788e-09 W/cm^2, ratio=5.08x, CCE=0.212, travel=2.42 um, area ratio=10.63, traps=2.589e+13 cm^-3, manufacturability=0.51.

## Interpretation

- Straight fingers are the conservative minimum-change geometry; they improve travel distance with the lowest added interface area.
- Interdigitated combs and radial spokes add more collection reach but pay more interface and fabrication penalty.
- Honeycomb, fractal/tree, random nanoribbon, and multilayer 3D meshes can reduce travel distance strongly, but interface/trap area and manufacturability penalties decide whether the gain survives.
- The optimization criterion is net electrical power after added graphene/diamond interface, interface traps, geometric occlusion, and manufacturability-risk penalties.
