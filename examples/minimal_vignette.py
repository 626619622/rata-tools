import numpy as np

from rata_tools import evidence_capacity, selection_null_decision, three_gate_decision

capacity = evidence_capacity(
    ["ASU", "ASU", "Michigan", "ENSAT", "ENSAT"],
    events_per_cluster={"ASU": 17, "Michigan": 16, "ENSAT": 20},
    independent_clusters={"ASU", "Michigan"},
    platform_per_cluster={"ASU": "GPL570", "Michigan": "GPL570", "ENSAT": "GPL570"},
)
selection = selection_null_decision(
    0.91,
    np.random.default_rng(1).normal(0.75, 0.05, 500),
)
decision = three_gate_decision(
    selection.decision,
    "positive_control_binary_pass",
    "role_integrity_pass",
)

print(capacity)
print(selection)
print(decision.to_dict())

