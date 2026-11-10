"""Public API for rata-tools."""

from .core import (
    GateDecision,
    SelectionDecision,
    binary_transport_gate,
    bootstrap_auc_ci,
    cindex_difference_in_differences,
    effective_cluster_number,
    evidence_capacity,
    harrell_c_index,
    multi_cohort_binary_gate,
    selection_cv_auc,
    selection_null_decision,
    survival_transport_gate,
    three_gate_decision,
)

__version__ = "0.2.0"

__all__ = [
    "GateDecision",
    "SelectionDecision",
    "__version__",
    "binary_transport_gate",
    "bootstrap_auc_ci",
    "cindex_difference_in_differences",
    "effective_cluster_number",
    "evidence_capacity",
    "harrell_c_index",
    "multi_cohort_binary_gate",
    "selection_cv_auc",
    "selection_null_decision",
    "survival_transport_gate",
    "three_gate_decision",
]

