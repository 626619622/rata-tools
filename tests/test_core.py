from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rata_tools import (
    __version__,
    binary_transport_gate,
    effective_cluster_number,
    evidence_capacity,
    harrell_c_index,
    multi_cohort_binary_gate,
    selection_cv_auc,
    selection_null_decision,
    survival_transport_gate,
    three_gate_decision,
)


class RATATests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.2.0")

    def test_effective_cluster_number(self):
        self.assertAlmostEqual(effective_cluster_number([4, 2, 2]), 2.6666667)

    def test_evidence_capacity(self):
        result = evidence_capacity(
            ["ASU", "ASU", "Michigan", "ENSAT", "ENSAT"],
            events_per_cluster={"ASU": 17, "Michigan": 16, "ENSAT": 20},
            independent_clusters={"ASU", "Michigan"},
            platform_per_cluster={"ASU": "GPL570", "Michigan": "GPL570", "ENSAT": "GPL570"},
        )
        self.assertEqual(result["claims"], 5)
        self.assertEqual(result["clusters"], 3)
        self.assertEqual(result["independent_events"], 33)
        self.assertEqual(result["platform_count"], 1)

    def test_harrell_c_index_perfect(self):
        score = np.array([3.0, 2.0, 1.0, 0.0])
        time = np.array([1.0, 2.0, 3.0, 4.0])
        event = np.ones(4)
        self.assertEqual(harrell_c_index(score, time, event), 1.0)

    def test_harrell_c_index_censoring(self):
        score = np.array([4.0, 1.0, 3.0, 2.0, 0.0])
        time = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        event = np.array([1, 1, 0, 1, 0])
        self.assertEqual(harrell_c_index(score, time, event), 0.75)

    def test_selection_decision(self):
        null = np.linspace(0.5, 0.8, 100)
        result = selection_null_decision(0.82, null)
        self.assertEqual(result.decision, "above_selection_noise")

    def test_selection_cv_auc(self):
        rng = np.random.default_rng(3)
        expression = rng.normal(size=(80, 20))
        labels = np.repeat([0, 1], 40)
        expression[:, :3] += labels[:, None] * 1.2
        auc = selection_cv_auc(expression, labels, selected_k=3, folds=4)
        self.assertGreater(auc, 0.9)

    def test_gate_decisions(self):
        self.assertEqual(
            binary_transport_gate(0.75, True),
            "positive_control_binary_pass",
        )
        decision = three_gate_decision(
            "above_selection_noise",
            "positive_control_binary_pass",
            "role_integrity_pass",
        )
        self.assertEqual(decision.overall, "three_gate_pass")
        self.assertEqual(decision.to_dict()["gate2"], "positive_control_binary_pass")
        saturated = three_gate_decision(
            "uninformative_saturated",
            "positive_control_binary_pass",
            "role_integrity_pass",
        )
        self.assertEqual(saturated.overall, "selection_uninformative")
        indeterminate = three_gate_decision(
            "above_selection_noise",
            "survival_transport_indeterminate",
            "role_aware_pass",
        )
        self.assertEqual(indeterminate.overall, "transport_indeterminate")

    def test_multi_cohort_binary_gate(self):
        result = multi_cohort_binary_gate({"A": 0.72, "B": 0.65})
        self.assertEqual(result["status"], "multi_cohort_binary_pass")
        failed = multi_cohort_binary_gate({"A": 0.72, "B": 0.53})
        self.assertEqual(failed["status"], "fail_binary_transport")

    def test_survival_gate_underpowered(self):
        score = np.arange(10, dtype=float)
        time = np.arange(1, 11, dtype=float)
        event = np.array([1, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        cohort = np.array(["A"] * 5 + ["B"] * 5)
        result = survival_transport_gate(score, time, event, cohort)
        self.assertEqual(result["status"], "provisional_or_untestable")

    def test_survival_gate_full_pass(self):
        rng = np.random.default_rng(42)
        n = 240
        score = rng.normal(size=n)
        cohort = np.repeat(["A", "B"], n // 2)
        event_time = -np.log(rng.uniform(size=n)) / np.exp(0.9 * score)
        event = np.ones(n, dtype=int)
        result = survival_transport_gate(score, event_time, event, cohort)
        self.assertEqual(result["status"], "full_survival_transport_pass")
        self.assertGreater(result["common_hr"], 1)
        self.assertTrue(result["direction_concordant"])
        self.assertIn("i2", result)

    def test_survival_gate_direction_reversal(self):
        rng = np.random.default_rng(7)
        n = 240
        score = rng.normal(size=n)
        cohort = np.repeat(["A", "B"], n // 2)
        direction = np.where(cohort == "A", 1.0, -1.0)
        event_time = -np.log(rng.uniform(size=n)) / np.exp(direction * score)
        event = np.ones(n, dtype=int)
        result = survival_transport_gate(score, event_time, event, cohort)
        self.assertEqual(result["status"], "direction_reversal")
        self.assertFalse(result["direction_concordant"])

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            effective_cluster_number([0, 0])
        with self.assertRaises(ValueError):
            selection_null_decision(0.8, [])
        with self.assertRaises(ValueError):
            binary_transport_gate(1.2, True)


if __name__ == "__main__":
    unittest.main()

