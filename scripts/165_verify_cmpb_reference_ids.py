"""Resolve PMID/DOI/arXiv identifiers in the CMPB reference audit."""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_MD = ROOT / "cmpb_submission_20261118" / "references_verified.md"
OUT_JSON = ROOT / "cmpb_submission_20261118" / "reference_identifier_resolution.json"
OUT_MD = ROOT / "cmpb_submission_20261118" / "reference_identifier_resolution.md"
USER_AGENT = "RATA-CMPB-Audit/1.0 (mailto:213231036@seu.edu.cn)"


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z]", "", value.lower())


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def first_surname(reference: str) -> str:
    token = reference.split(",", 1)[0].strip()
    return token.split()[0]


def main() -> None:
    text = AUDIT_MD.read_text(encoding="utf-8")
    section = text.split("## 四、全部 42 条核验明细", 1)[1].split("## 五、", 1)[0]
    rows = []
    for line in section.splitlines():
        match = re.match(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", line)
        if match:
            rows.append(
                {
                    "number": int(match.group(1)),
                    "reference": match.group(2),
                    "identifier": match.group(3),
                    "manual_check": match.group(4),
                }
            )

    pmids = {
        row["number"]: re.search(r"PMID\s+(\d+)", row["identifier"]).group(1)
        for row in rows
        if row["identifier"].startswith("PMID")
    }
    pmid_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id="
        + ",".join(pmids.values())
    )
    pmid_data = fetch_json(pmid_url)["result"]

    results = []
    for row in rows:
        identifier = row["identifier"]
        status = "MANUAL_VERIFIED"
        resolved_title = ""
        evidence = ""
        if identifier.startswith("PMID"):
            pmid = re.search(r"PMID\s+(\d+)", identifier).group(1)
            record = pmid_data.get(pmid, {})
            resolved_title = record.get("title", "")
            actual_first = ""
            authors = record.get("authors") or []
            if authors:
                actual_first = authors[0].get("name", "")
            cited_first = first_surname(row["reference"])
            author_ok = normalize_name(cited_first) in normalize_name(actual_first)
            exists = bool(record and not record.get("error"))
            status = "OK" if exists and author_ok else "CHECK"
            evidence = f"PMID {pmid}; first author cited={cited_first}; PubMed={actual_first}"
        elif identifier.startswith("DOI"):
            doi = identifier.split("DOI", 1)[1].strip()
            try:
                record = fetch_json(
                    "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
                )["message"]
                resolved_title = " ".join(record.get("title", []))
                status = "OK"
                evidence = f"DOI {doi}; Crossref record resolved"
            except Exception as exc:
                status = "UNRESOLVED"
                evidence = f"DOI {doi}; {exc}"
        elif "arXiv" in identifier:
            arxiv_match = re.search(r"(\d{4}\.\d{4,5})", row["reference"])
            if arxiv_match:
                arxiv_id = arxiv_match.group(1)
                try:
                    xml = fetch_text(
                        "https://export.arxiv.org/api/query?id_list=" + arxiv_id
                    )
                    entry = re.search(r"<entry>(.*?)</entry>", xml, re.S)
                    if entry:
                        title = re.search(r"<title>(.*?)</title>", entry.group(1), re.S)
                        resolved_title = re.sub(r"\s+", " ", title.group(1)).strip() if title else ""
                        status = "OK" if resolved_title else "CHECK"
                        evidence = f"arXiv {arxiv_id}; API record resolved"
                    else:
                        status = "UNRESOLVED"
                        evidence = f"arXiv {arxiv_id}; no entry returned"
                except Exception as exc:
                    status = "UNRESOLVED"
                    evidence = f"arXiv {arxiv_id}; {exc}"
            else:
                evidence = "No arXiv identifier embedded in reference"
        elif "专著" in identifier:
            evidence = "Book; manual bibliographic verification retained"
        results.append({**row, "status": status, "resolved_title": resolved_title, "evidence": evidence})

    counts = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    payload = {"total": len(results), "counts": counts, "results": results}
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# CMPB reference identifier resolution",
        "",
        f"- Total: {len(results)}",
        f"- Status counts: {counts}",
        "",
        "| # | Identifier | Status | Resolved title | Evidence |",
        "|---:|---|---|---|---|",
    ]
    for row in results:
        title = row["resolved_title"].replace("|", "/")
        evidence = row["evidence"].replace("|", "/")
        lines.append(
            f"| {row['number']} | {row['identifier']} | {row['status']} | {title} | {evidence} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT_MD)
    print(json.dumps({"total": len(results), "counts": counts}, indent=2))
    if any(row["status"] == "CHECK" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
