from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .model import SimulationResult


def _group(values: list[SimulationResult], attr: str) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for result in values:
        grouped[result.params.architecture].append(float(getattr(result, attr)))
    return grouped


def boxplot_metric(results: list[SimulationResult], metric: str, ylabel: str, path: Path) -> None:
    grouped = _group(results, metric)
    labels = list(grouped)
    data = [grouped[label] for label in labels]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot(data, labels=labels, showfliers=False)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(labels, rotation=18, ha="right")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def scatter_interface_vs_power(results: list[SimulationResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for arch in sorted({r.params.architecture for r in results}):
        subset = [r for r in results if r.params.architecture == arch]
        ax.scatter(
            [r.interface_loss_fraction for r in subset],
            [r.power_density_W_cm2 for r in subset],
            s=10,
            alpha=0.35,
            label=arch,
        )
    ax.set_xlabel("Interface loss fraction")
    ax.set_ylabel("Power density (W/cm^2)")
    ax.set_yscale("log")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def sensitivity_bar(rows: list[dict[str, object]], path: Path) -> None:
    labels = [str(row["parameter"]) for row in rows]
    values = [float(row["log_elasticity"]) for row in rows]
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#b94a48" if v < 0 else "#2c7fb8" for v in values]
    ax.barh(labels, values, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Log elasticity of power density")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def lifetime_vs_cce(results: list[SimulationResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for arch in sorted({r.params.architecture for r in results}):
        subset = [r for r in results if r.params.architecture == arch]
        ax.scatter(
            [r.charge_collection_efficiency for r in subset],
            [r.estimated_lifetime_years for r in subset],
            s=10,
            alpha=0.35,
            label=arch,
        )
    ax.set_xlabel("Charge collection efficiency")
    ax.set_ylabel("Estimated lifetime (years)")
    ax.set_yscale("log")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def thermal_profile(results: list[SimulationResult], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for arch in sorted({r.params.architecture for r in results}):
        subset = sorted(
            [r for r in results if r.params.architecture == arch],
            key=lambda r: r.params.diamond_um,
        )
        xs = [r.params.diamond_um + r.params.ferrite_um * r.params.ferrite_layers for r in subset]
        ys = [r.peak_temperature_K for r in subset]
        ax.scatter(xs, ys, s=10, alpha=0.35, label=arch)
    ax.set_xlabel("Total active stack thickness (um)")
    ax.set_ylabel("Peak temperature (K)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def make_plots(results: list[SimulationResult], sensitivity: list[dict[str, object]], plot_dir: Path) -> None:
    plot_dir.mkdir(parents=True, exist_ok=True)
    boxplot_metric(results, "charge_collection_efficiency", "Charge collection efficiency", plot_dir / "cce_by_architecture.png")
    boxplot_metric(results, "power_density_W_cm2", "Power density (W/cm^2)", plot_dir / "power_by_architecture.png")
    scatter_interface_vs_power(results, plot_dir / "interface_loss_vs_power.png")
    lifetime_vs_cce(results, plot_dir / "lifetime_vs_cce.png")
    thermal_profile(results, plot_dir / "thermal_profile.png")
    sensitivity_bar(sensitivity, plot_dir / "sensitivity.png")
