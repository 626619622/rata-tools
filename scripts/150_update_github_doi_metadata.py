"""Add the Zenodo DOI to GitHub README, CITATION.cff and release notes."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_REPO = "repos/626619622/rata-tools"
TEMP = ROOT / "release_api_tmp_doi"
TEMP.mkdir(parents=True, exist_ok=True)
SOFTWARE_DOI = "10.5281/zenodo.24156617"
RELEASE_URL = "https://github.com/626619622/rata-tools/releases/tag/v0.2.0"


def gh_api(method: str, endpoint: str, payload: dict | None = None):
    command = ["gh", "api", "--method", method, endpoint]
    if payload is not None:
        path = TEMP / "payload.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        command.extend(["--input", str(path)])
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"gh api failed: {result.stderr}\n{result.stdout}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def update_file(path: str, content: str, message: str) -> str:
    current = gh_api("GET", f"{API_REPO}/contents/{path}")
    updated = gh_api(
        "PUT",
        f"{API_REPO}/contents/{path}",
        payload={
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "sha": current["sha"],
        },
    )
    return updated["commit"]["sha"]


def main() -> None:
    current_readme = subprocess.run(
        ["gh", "api", f"{API_REPO}/contents/README.md", "--jq", ".content"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip().replace("\n", "")
    readme = base64.b64decode(current_readme).decode("utf-8")
    if SOFTWARE_DOI not in readme:
        readme += (
            "\n## Archived release\n\n"
            f"Software DOI: [`{SOFTWARE_DOI}`](https://doi.org/{SOFTWARE_DOI})\n\n"
            f"GitHub release: {RELEASE_URL}\n"
        )
    commit_sha = update_file(
        "README.md",
        readme,
        "Add Zenodo DOI to README",
    )

    citation = (ROOT / "release_artifacts" / "CITATION_v0.2.0_with_doi.cff").read_text(
        encoding="utf-8"
    )
    commit_sha = update_file(
        "CITATION.cff",
        citation,
        "Add DOI to CITATION.cff",
    )

    gh_api(
        "PATCH",
        f"{API_REPO}/git/refs/tags/v0.2.0",
        payload={"sha": commit_sha, "force": True},
    )

    release = gh_api("GET", f"{API_REPO}/releases/tags/v0.2.0")
    body = release["body"]
    if SOFTWARE_DOI not in body:
        body += f"\n\nArchived DOI: https://doi.org/{SOFTWARE_DOI}\n"
    gh_api(
        "PATCH",
        f"{API_REPO}/releases/{release['id']}",
        payload={"body": body},
    )
    print(json.dumps({"commit": commit_sha, "doi": SOFTWARE_DOI}, indent=2))


if __name__ == "__main__":
    main()
