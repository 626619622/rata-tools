"""Recompute the final CMPB Gate 1 null calibration without overwriting source results."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = ROOT / "scripts" / "41_rata_double_null_selection_gate.py"
OUT = ROOT / "revisions" / "cmpb_20261118"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    spec = importlib.util.spec_from_file_location("rata_gate1_source", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Gate 1 script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    observed = module.observed_auc_map()
    rows = []
    for index, (signature, (pool_size, k)) in enumerate(module.SIGNATURE_POOLS.items()):
        pure = module.null_distribution(
            pool_size,
            k,
            seed=module.RANDOM_SEED + index * 2,
            mixture=False,
        )
        realistic = module.null_distribution(
            pool_size,
            k,
            seed=module.RANDOM_SEED + index * 2 + 1,
            mixture=True,
        )
        observed_auc = observed[signature]
        pure_q95 = float(np.quantile(pure, 0.95))
        realistic_q95 = float(np.quantile(realistic, 0.95))
        rows.append(
            {
                "signature": signature,
                "candidate_pool": pool_size,
                "selected_k": k,
                "observed_apparent_auc": observed_auc,
                "pure_null_q95": pure_q95,
                "pure_null_percentile": float(np.mean(pure <= observed_auc) * 100),
                "pure_null_p": module.empirical_greater(pure, observed_auc),
                "realistic_null_q95": realistic_q95,
                "realistic_null_percentile": float(np.mean(realistic <= observed_auc) * 100),
                "realistic_null_p": module.empirical_greater(realistic, observed_auc),
                "pass_pure_null_gate": observed_auc > pure_q95,
                "pass_realistic_null_gate": observed_auc > realistic_q95,
                "selection_gate_decision": "pass" if observed_auc > realistic_q95 else "fail",
                "mixture_signal_fraction": module.MIXTURE_SIGNAL_FRACTION,
                "mixture_effect_size": module.MIXTURE_EFFECT_SIZE,
                "simulations_per_null": module.N_SIMULATIONS,
            }
        )

    result = pd.DataFrame(rows)
    csv_path = OUT / "RATA_v5_double_null_selection_gate_recheck_20261118.csv"
    json_path = OUT / "RATA_v5_double_null_selection_gate_recheck_20261118.json"
    result.to_csv(csv_path, index=False)
    payload = {
        "source_script": str(SOURCE_SCRIPT),
        "random_seed": module.RANDOM_SEED,
        "n_sample": module.N_SAMPLE,
        "n_events": module.N_EVENTS,
        "n_simulations": module.N_SIMULATIONS,
        "mixture_signal_fraction": module.MIXTURE_SIGNAL_FRACTION,
        "mixture_effect_size": module.MIXTURE_EFFECT_SIZE,
        "results": result.to_dict(orient="records"),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    published = pd.read_csv(ROOT / "results" / "RATA_v5_double_null_selection_gate.csv")
    comparison = published[["signature", "realistic_null_percentile"]].merge(
        result[["signature", "realistic_null_percentile"]],
        on="signature",
        suffixes=("_published", "_recheck"),
    )
    comparison["difference_pp"] = (
        comparison["realistic_null_percentile_recheck"]
        - comparison["realistic_null_percentile_published"]
    )
    comparison_path = OUT / "Gate1_recheck_comparison.csv"
    comparison.to_csv(comparison_path, index=False)

    print(result.round(4).to_string(index=False))
    print("\nComparison with published CSV:")
    print(comparison.round(4).to_string(index=False))
    print(f"\nSaved: {csv_path}")
    print(f"Saved: {json_path}")
    print(f"Saved: {comparison_path}")


if __name__ == "__main__":
    main()
