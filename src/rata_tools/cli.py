"""Command-line entry point for rata-tools."""

from __future__ import annotations

import argparse
import json

import numpy as np

from . import __version__
from .core import selection_null_decision, three_gate_decision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rata-tools")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    demo = subparsers.add_parser(
        "demo",
        help="Run a deterministic selection-null and GateDecision example.",
    )
    demo.add_argument("--observed", type=float, default=0.91)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "demo":
        null = np.random.default_rng(1).normal(0.75, 0.05, 500)
        selection = selection_null_decision(args.observed, null)
        decision = three_gate_decision(
            selection.decision,
            "positive_control_binary_pass",
            "role_integrity_pass",
        )
        print(
            json.dumps(
                {
                    "selection": {
                        "percentile": selection.observed_percentile,
                        "p_value": selection.empirical_p,
                        "decision": selection.decision,
                    },
                    "decision": decision.to_dict(),
                },
                indent=2,
            )
        )
        return
    parser.print_help()


if __name__ == "__main__":
    main()

