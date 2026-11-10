# rata-tools documentation

RATA audits a transcriptomic signature at three levels:

1. **Selection robustness** asks whether apparent performance is
   distinguishable from feature-selection noise.
2. **Independent transport** asks whether the score retains its prespecified
   direction in reuse-aware, unseen cohorts.
3. **Role-aware evidence** distinguishes target axes from confounders and
   mediators before adjustment.

The package also reports an evidence-capacity vector and a structured
`GateDecision`. Gate outputs are deliberately separate; provisional,
indeterminate and failed results are not collapsed into one label.

## Inputs

- Binary scores and labels for selection-null and binary-transport gates.
- Expression matrices for selection-aware cross-validation.
- Score, follow-up, event and reuse-aware cohort identifiers for survival
  transport.
- Cluster identifiers, events and platforms for evidence capacity.

## Outputs

- `SelectionDecision`
- binary and multi-cohort gate records
- survival gate record with per-cohort HR, Q, I-squared and instability flags
- evidence-capacity record
- `GateDecision`

