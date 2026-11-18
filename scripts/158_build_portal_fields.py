"""Generate plain-text portal fields from the final canonical manuscript."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v12.md"
OUT = ROOT / "portal_fields"
OUT.mkdir(parents=True, exist_ok=True)


def strip_markdown(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)
    return value.strip()


def write(name: str, value: str) -> None:
    (OUT / name).write_text(strip_markdown(value).strip() + "\n", encoding="utf-8")


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    abstract = re.sub(r"\n{3,}", "\n\n", abstract).strip()
    keywords_line = next(
        line for line in text.splitlines() if line.startswith("**Keywords:**")
    )
    keywords = keywords_line.split("**Keywords:**", 1)[1].strip()

    write("article_type.txt", "Original Paper")
    write("title.txt", title)
    write("abstract.txt", abstract)
    write("keywords.txt", keywords)
    write(
        "authors.txt",
        "Jiakang Zhao\nZhongda Hospital, Southeast University, Nanjing, Jiangsu, China",
    )
    write(
        "corresponding_author.txt",
        "Jiakang Zhao\nZhongda Hospital, Southeast University, Nanjing, Jiangsu, China\n"
        "Email: 213231036@seu.edu.cn\nTelephone: +86 13205291060\n"
        "ORCID: 0009-0006-4878-0626",
    )

    cover = (ROOT / "manuscript" / "RATA_Bioinformatics_CoverLetter_v3.md").read_text(
        encoding="utf-8"
    )
    write("cover_letter.txt", cover)

    start = text.index("## Availability")
    end = text.index("## Tables", start)
    write("data_availability.txt", text[start + len("## Availability") : end])

    write(
        "author_contributions.txt",
        "J.Z. conceived the study, curated and analysed the data, developed the framework "
        "and software, created the figures, and wrote and approved the manuscript.",
    )
    write("competing_interests.txt", "The author declares no competing interests.")
    write("funding.txt", "This research received no specific funding.")
    write(
        "ethics.txt",
        "This study used publicly available, de-identified data and did not require "
        "additional ethics approval.",
    )
    write(
        "generative_ai_disclosure.txt",
        "Codex was used to assist with code development, data-processing scripts, software "
        "testing and language editing. The author reviewed and verified all code, analyses "
        "and text and takes full responsibility for the work.",
    )
    write(
        "suggested_reviewers.txt",
        "No reviewer names are entered automatically. Select bioinformatics methods, "
        "reproducibility and computational cancer biology experts after checking conflicts.",
    )

    index_lines = [
        "# Bioinformatics portal fields",
        "",
        "Use these plain-text fields without adding Markdown.",
        "",
    ]
    for path in sorted(OUT.glob("*.txt")):
        index_lines.append(f"- `{path.name}`")
    (OUT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(OUT)
    print(f"fields={len(list(OUT.glob('*.txt')))}")


if __name__ == "__main__":
    main()
