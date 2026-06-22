# Diamond-Graphene Betavoltaic Research

Simulation-driven research notes and reduced-order models for a diamond/graphene
radiovoltaic device concept.

## Current Leading Concept

```text
regulated beta-energy source
down
diamond active layer
down
straight internal graphene or graphitic collection fingers
down
collector and contact routing
```

## Summary

This project explores whether internal graphene or graphitic collector
structures can improve charge collection in diamond-based betavoltaic devices by
shortening carrier travel distance before recombination and trapping.

The research is simulation-first and falsification-oriented. The current
direction favors a simple diamond device with straight internal graphitic or
graphene collection fingers rather than ferrite transport layers, complex mesh
collectors, or embedded source layers.

## Simulation Generations

| Generation | Question | Main Outcome |
|---|---|---|
| Gen 1 | Do ferrite transport layers help? | No; ferrite transport was detrimental in the tested model. |
| Gen 2 | Are interfaces or bulk ferrite transport the bottleneck? | Bulk ferrite transport dominated; embedded graphene helped. |
| Gen 3 | Which collector geometry works best? | Interdigitated combs won theory; straight fingers won practical balance. |
| Gen 4 | Which geometry survives manufacturing penalties? | Straight fingers won. |
| Gen 5 | Which substrate is best? | Diamond remained best absolute performer. |
| Gen 6 | Which complete device architecture wins? | Simple top-source diamond/graphitic-finger layout was the practical path. |

## Quick Start

```bash
python3 -m radiovoltaic.cli selftest
python3 -m radiovoltaic.cli run --preset focused
python3 -m radiovoltaic.cli run-gen2 --preset focused
python3 -m radiovoltaic.cli run-gen3 --preset focused
python3 -m radiovoltaic.cli run-gen4
python3 -m radiovoltaic.cli run-gen5
python3 -m radiovoltaic.cli run-gen6
```

Generated reports and CSV/plot artifacts are stored under `results*` directories.

## Model Scope

This is not a calibrated TCAD or Monte Carlo radiation transport code. It is a
transparent reduced-order modeling framework intended to identify dominant loss
channels, design cliffs, and falsification conditions. Assumptions and failure
modes are emitted in the generation reports.

## Safety Boundary

This repository is for simulation, documentation, and professional research
planning. It does not include instructions for acquiring, handling, preparing, or
encapsulating radioactive materials.
