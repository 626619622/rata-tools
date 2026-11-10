# Public API

## Evidence capacity

`evidence_capacity(cluster_ids, events_per_cluster=None, independent_clusters=None, platform_per_cluster=None)`

## Selection

- `selection_cv_auc(expression, label, selected_k=3, folds=5, seed=1)`
- `selection_null_decision(observed, null_values, lower_q=0.50, upper_q=0.95)`

## Transport

- `binary_transport_gate(external_auc, direction_concordant, auc_threshold=0.60)`
- `multi_cohort_binary_gate(external_aucs, auc_threshold=0.60, rule="min")`
- `survival_transport_gate(score, time, event, cohort)`
- `harrell_c_index(score, time, event)`
- `cindex_difference_in_differences(...)`

## Decision

`three_gate_decision(gate1, gate2, gate3)` returns a frozen `GateDecision`
dataclass. Use `.to_dict()` for serialization.

