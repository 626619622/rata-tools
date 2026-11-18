"""Benchmark rata-tools 0.2.0 on synthetic transcriptomic audit tasks."""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import psutil
import scipy
import sklearn
import statsmodels

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rata_tools_release_0.2.0" / "src"))

from rata_tools import (
    evidence_capacity,
    multi_cohort_binary_gate,
    selection_cv_auc,
    selection_null_decision,
    survival_transport_gate,
)


RESULTS = ROOT / "results"
OUT_CSV = RESULTS / "Bioinformatics_RuntimeBenchmark.csv"
OUT_JSON = RESULTS / "Bioinformatics_RuntimeBenchmark.json"


def measure(function, repeats: int):
    process = psutil.Process()
    times = []
    memories = []
    for _ in range(repeats):
        start = time.perf_counter()
        function()
        times.append(time.perf_counter() - start)
        memories.append(process.memory_info().rss / (1024**2))
    return {
        "time_median_s": statistics.median(times),
        "time_min_s": min(times),
        "time_max_s": max(times),
        "rss_peak_mb": max(memories),
    }


def main() -> None:
    rng = np.random.default_rng(20261110)

    cluster_ids = np.repeat([f"C{i:02d}" for i in range(10)], 100)
    events = {f"C{i:02d}": 10 + i for i in range(10)}
    platforms = {f"C{i:02d}": "GPL570" if i < 8 else "RNA-seq" for i in range(10)}

    null_aucs = rng.normal(0.75, 0.05, 5000)
    external_aucs = {f"C{i:02d}": 0.62 + 0.02 * i for i in range(10)}

    n_survival = 500
    score = rng.normal(size=n_survival)
    cohort = np.repeat([f"C{i:02d}" for i in range(10)], 50)
    cohort_effect = np.where(
        np.arange(10)[:, None] % 2 == 0,
        0.5,
        0.3,
    )
    cohort_effect = np.repeat(cohort_effect.ravel(), 50, axis=0)
    event_time = -np.log(rng.uniform(size=n_survival)) / np.exp(
        cohort_effect * score
    )
    event = np.ones(n_survival, dtype=int)

    n_samples, n_features = 500, 1000
    expression = rng.normal(size=(n_samples, n_features))
    labels = np.repeat([0, 1], n_samples // 2)
    expression[:, :12] += labels[:, None] * 0.18

    tasks = {
        "evidence_capacity_10_clusters_1000_claims": (
            lambda: evidence_capacity(
                cluster_ids,
                events_per_cluster=events,
                independent_clusters=set(events) - {"C09"},
                platform_per_cluster=platforms,
            ),
            100,
        ),
        "selection_null_5000_values": (
            lambda: selection_null_decision(0.86, null_aucs),
            1000,
        ),
        "multi_cohort_binary_10_cohorts": (
            lambda: multi_cohort_binary_gate(external_aucs, 0.60, "min"),
            1000,
        ),
        "survival_gate_500_samples_10_cohorts": (
            lambda: survival_transport_gate(score, event_time, event, cohort),
            5,
        ),
        "selection_cv_500_samples_1000_features_k3": (
            lambda: selection_cv_auc(expression, labels, selected_k=3, folds=5),
            3,
        ),
    }

    rows = []
    for name, (function, repeats) in tasks.items():
        result = measure(function, repeats)
        rows.append(
            {
                "task": name,
                "repeats": repeats,
                **result,
            }
        )

    import pandas as pd

    frame = pd.DataFrame(rows)
    frame.to_csv(OUT_CSV, index=False)
    report = {
        "software_version": "0.2.0",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "statsmodels": statsmodels.__version__,
        "benchmarks": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(frame.to_string(index=False))
    print(OUT_CSV)
    print(OUT_JSON)


if __name__ == "__main__":
    main()
