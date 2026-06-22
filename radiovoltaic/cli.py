from __future__ import annotations

import argparse
from pathlib import Path

from .materials import load_materials
from .gen2 import run_gen2_study
from .gen3 import run_gen3_study
from .gen4 import run_gen4_study
from .gen5 import run_gen5_study
from .gen6 import run_gen6_study
from .plots import make_plots
from .report import write_report
from .selftest import run_selftest
from .sweeps import run_sensitivity, run_sweep, run_uncertainty


ROOT = Path(__file__).resolve().parents[1]


def run(args: argparse.Namespace) -> None:
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    db = load_materials(args.materials)
    results = run_sweep(db, out_dir, args.preset)
    uncertainty = run_uncertainty(db, out_dir, args.uncertainty_samples)
    sensitivity = run_sensitivity(db, out_dir)
    make_plots(results, sensitivity, out_dir / "plots")
    write_report(out_dir / "final_report.md", results, uncertainty, sensitivity)
    print(f"Wrote {len(results)} sweep rows, {len(uncertainty)} uncertainty rows to {out_dir}")
    print(f"Report: {out_dir / 'final_report.md'}")


def run_gen2(args: argparse.Namespace) -> None:
    out_dir = Path(args.out).resolve()
    db = load_materials(args.materials)
    results = run_gen2_study(db, out_dir, args.preset)
    print(f"Wrote {len(results)} generation-2 cases to {out_dir}")
    print(f"Report: {out_dir / 'gen2_final_report.md'}")


def run_gen3(args: argparse.Namespace) -> None:
    out_dir = Path(args.out).resolve()
    db = load_materials(args.materials)
    results = run_gen3_study(db, out_dir, args.preset)
    print(f"Wrote {len(results)} generation-3 geometry cases to {out_dir}")
    print(f"Report: {out_dir / 'gen3_final_report.md'}")


def run_gen4(args: argparse.Namespace) -> None:
    out_dir = Path(args.out).resolve()
    db = load_materials(args.materials)
    results = run_gen4_study(db, out_dir)
    print(f"Wrote {len(results)} generation-4 manufacturing cases to {out_dir}")
    print(f"Report: {out_dir / 'gen4_final_report.md'}")


def run_gen5(args: argparse.Namespace) -> None:
    out_dir = Path(args.out).resolve()
    db = load_materials(args.materials)
    results = run_gen5_study(db, out_dir)
    print(f"Wrote {len(results)} generation-5 substrate cases to {out_dir}")
    print(f"Report: {out_dir / 'gen5_final_report.md'}")


def run_gen6(args: argparse.Namespace) -> None:
    out_dir = Path(args.out).resolve()
    db = load_materials(args.materials)
    results = run_gen6_study(db, out_dir)
    print(f"Wrote {len(results)} generation-6 device cases to {out_dir}")
    print(f"Report: {out_dir / 'gen6_final_report.md'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Radiovoltaic ferrite interlayer simulator")
    sub = parser.add_subparsers(required=True)
    run_parser = sub.add_parser("run", help="run sweeps, uncertainty analysis, plots, and report")
    run_parser.add_argument("--preset", choices=["smoke", "focused"], default="focused")
    run_parser.add_argument("--materials", default=str(ROOT / "config" / "materials.yaml"))
    run_parser.add_argument("--out", default=str(ROOT / "results"))
    run_parser.add_argument("--uncertainty-samples", type=int, default=200)
    run_parser.set_defaults(func=run)
    gen2_parser = sub.add_parser("run-gen2", help="run second-generation interface falsification study")
    gen2_parser.add_argument("--preset", choices=["smoke", "focused"], default="focused")
    gen2_parser.add_argument("--materials", default=str(ROOT / "config" / "materials.yaml"))
    gen2_parser.add_argument("--out", default=str(ROOT / "results_gen2"))
    gen2_parser.set_defaults(func=run_gen2)
    gen3_parser = sub.add_parser("run-gen3", help="run embedded graphene collector geometry optimization")
    gen3_parser.add_argument("--preset", choices=["smoke", "focused"], default="focused")
    gen3_parser.add_argument("--materials", default=str(ROOT / "config" / "materials.yaml"))
    gen3_parser.add_argument("--out", default=str(ROOT / "results_gen3"))
    gen3_parser.set_defaults(func=run_gen3)
    gen4_parser = sub.add_parser("run-gen4", help="run manufacturability-constrained diamond-graphene study")
    gen4_parser.add_argument("--materials", default=str(ROOT / "config" / "materials.yaml"))
    gen4_parser.add_argument("--out", default=str(ROOT / "results_gen4"))
    gen4_parser.set_defaults(func=run_gen4)
    gen5_parser = sub.add_parser("run-gen5", help="run substrate shootout for graphene-assisted betavoltaics")
    gen5_parser.add_argument("--materials", default=str(ROOT / "config" / "materials.yaml"))
    gen5_parser.add_argument("--out", default=str(ROOT / "results_gen5"))
    gen5_parser.set_defaults(func=run_gen5)
    gen6_parser = sub.add_parser("run-gen6", help="run device-level diamond-graphene architecture study")
    gen6_parser.add_argument("--materials", default=str(ROOT / "config" / "materials.yaml"))
    gen6_parser.add_argument("--out", default=str(ROOT / "results_gen6"))
    gen6_parser.set_defaults(func=run_gen6)
    test_parser = sub.add_parser("selftest", help="run dependency-free model checks")
    test_parser.set_defaults(func=lambda _args: (run_selftest(), print("selftest passed")))
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
