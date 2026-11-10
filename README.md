# rata-tools 0.2.0

`rata-tools` implements reusable primitives for Role-Aware Transportability
Audit (RATA). The package reports selection robustness, independent transport,
role-aware evidence and evidence capacity as separate outputs. It does not
produce a composite "quality score".

## Install

```bash
pip install rata-tools
```

For a local development install:

```bash
pip install -e ".[test]"
```

## Minimal API

```python
import numpy as np
from rata_tools import (
    evidence_capacity,
    selection_null_decision,
    three_gate_decision,
)

capacity = evidence_capacity(
    ["ASU", "ASU", "Michigan", "ENSAT", "ENSAT"],
    events_per_cluster={"ASU": 17, "Michigan": 16, "ENSAT": 20},
    independent_clusters={"ASU", "Michigan"},
    platform_per_cluster={"ASU": "GPL570", "Michigan": "GPL570", "ENSAT": "GPL570"},
)
selection = selection_null_decision(
    observed=0.91,
    null_values=np.random.default_rng(1).normal(0.75, 0.05, 500),
)
decision = three_gate_decision(
    selection.decision,
    "positive_control_binary_pass",
    "role_integrity_pass",
)
print(capacity)
print(decision.to_dict())
```

## Command line

```bash
rata-tools --version
rata-tools demo --observed 0.91
```

## Implemented components

- `evidence_capacity`: claim counts, effective cluster number, events and
  platform diversity.
- `selection_cv_auc`: five-fold selection-aware AUC.
- `selection_null_decision`: matched pure/realistic selection-null decision.
- `binary_transport_gate` and `multi_cohort_binary_gate`: endpoint-specific
  binary rules.
- `survival_transport_gate`: cohort-stratified Cox model, per-cohort HR,
  direction, Cochran's Q, I-squared and unstable-cohort flags.
- `cindex_difference_in_differences`: control-normalized transport contrast.
- `three_gate_decision`: separate gate fields and a structured overall status.

## Scope

RATA audits evidence. It does not estimate causal effects, replace batch
correction, deconvolution or domain-generalization methods, or manufacture
independent cohorts.

