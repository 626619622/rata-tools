"""Complete the Implementation section length without changing the argument."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v9.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v10.md"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    pattern = re.compile(
        r"These choices allow result records to be serialized, diffed between analyses\s+"
        r"and included in a preregistration or evidence table\."
    )
    replacement = (
        "These choices allow result records to be serialized, diffed between analyses "
        "and included in a preregistration or evidence table. Each module also returns "
        "the thresholds and cohort-specific inputs used in the decision, so a reviewer "
        "can distinguish a failed test from an unexecuted one. The compact schema is "
        "stable for integration with registries, notebooks and version-to-version comparisons."
    )
    if pattern.search(text) is None:
        raise ValueError("Expected implementation text not found")
    text = pattern.sub(replacement, text, count=1)
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
