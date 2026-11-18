"""Balance Implementation and Discussion in the Bioinformatics manuscript."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v8.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v9.md"

IMPLEMENTATION_ADDITION = """### Data contract and failure behavior

The package treats inputs as a typed data contract rather than an unstructured
collection of arrays. Scores, follow-up times and event indicators must have
equal length and finite values; events must use 0/1 coding; cohort labels must
match the score vector; and binary outcomes must contain both classes before
cross-validation or AUC calculation. Evidence-capacity calls reject unknown
independent clusters and missing event or platform mappings. These checks
convert silent misalignment, a common source of apparently favourable
validation results, into an explicit error before a model is fitted.

Failure behavior is equally important for the audit. A saturated null is
labelled uninformative, a single eligible cohort is provisional, a wide
per-cohort confidence interval triggers an instability flag, and conflicting
directions trigger a reversal state. The software never substitutes a global
"quality" score for these fields. It also accepts a random seed for procedures
that require resampling and returns plain dictionaries or frozen dataclasses.
These choices allow result records to be serialized, diffed between analyses
and included in a preregistration or evidence table. The release tests cover
normal operation and these boundary states, including censoring, event-count
guardrails and invalid input dimensions.

"""

DISCUSSION_ADDITION = """A practical RATA audit follows a short sequence. The
analyst first constructs the provenance registry and fixes reuse clusters
before calculating capacity. The role map is specified next, followed by the
selection and endpoint-specific transport analyses. The final record reports
the capacity vector, every gate state and the assumptions that could not be
evaluated. This order prevents a favourable Gate 2 result from driving the
definition of evidence capacity or biological roles after the fact.

The framework can be used in three common settings: reviewing a published
signature before external validation, deciding whether a new cohort adds
independent evidence, and documenting why a planned validation is
underpowered. In each case, the output is an audit rather than a verdict on
biological importance. A provisional result means that the available cohorts
cannot answer the transport question, not that the biology is false. A
role-dependent result identifies an interpretation problem that may require
better confounder measurement or a different target definition.

"""


def section_words(text: str, start: str, end: str) -> int:
    section = text.split(start, 1)[1].split(end, 1)[0]
    return len(re.findall(r"\b[\w-]+\b", section))


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    implementation_marker = "### Software architecture and reproducibility"
    discussion_marker = "These limits define a focused software contribution."
    if implementation_marker not in text:
        raise ValueError("Implementation marker not found")
    if discussion_marker not in text:
        raise ValueError("Discussion marker not found")
    text = text.replace(implementation_marker, IMPLEMENTATION_ADDITION + implementation_marker, 1)
    text = text.replace(discussion_marker, DISCUSSION_ADDITION + discussion_marker, 1)
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)
    print("Implementation words:", section_words(text, "## Implementation", "## Validation"))
    print("Discussion words:", section_words(text, "## Discussion", "## Availability"))


if __name__ == "__main__":
    main()
