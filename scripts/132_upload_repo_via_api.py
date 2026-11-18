"""Populate the empty GitHub repository through the GitHub API.

This is a fallback for networks where api.github.com is reachable but the
github.com Git HTTPS endpoint is not.
"""

from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "rata_tools_release_0.2.0"
OWNER = "626619622"
NAME = "rata-tools"
API_REPO = f"repos/{OWNER}/{NAME}"
TEMP = ROOT / "release_api_tmp"
TEMP.mkdir(parents=True, exist_ok=True)


def gh_api(method: str, endpoint: str, payload: dict | None = None, fields: dict | None = None):
    command = ["gh", "api", "--method", method, endpoint]
    if payload is not None:
        path = TEMP / "payload.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        command.extend(["--input", str(path)])
    if fields:
        for key, value in fields.items():
            command.extend(["-f", f"{key}={value}"])
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"gh api failed: {result.stderr}\n{result.stdout}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def main() -> None:
    repository = gh_api("GET", API_REPO)
    if repository.get("size", 0) != 0 or repository.get("defaultBranchRef"):
        raise RuntimeError("Repository is not empty; refusing to create a second root commit")

    excluded_parts = {".git", "__pycache__", "dist", ".pytest_cache", "build"}
    files = []
    for path in sorted(REPO.rglob("*")):
        if not path.is_file():
            continue
        if any(part in excluded_parts for part in path.relative_to(REPO).parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)

    tree_entries = []
    for index, path in enumerate(files):
        relative = path.relative_to(REPO).as_posix()
        content = base64.b64encode(path.read_bytes()).decode("ascii")
        blob = gh_api(
            "POST",
            f"{API_REPO}/git/blobs",
            payload={"content": content, "encoding": "base64"},
        )
        tree_entries.append(
            {
                "path": relative,
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"],
            }
        )
        print(f"blob {index + 1}/{len(files)}: {relative}")

    tree = gh_api("POST", f"{API_REPO}/git/trees", payload={"tree": tree_entries})
    commit = gh_api(
        "POST",
        f"{API_REPO}/git/commits",
        payload={
            "message": "Release rata-tools 0.2.0",
            "tree": tree["sha"],
            "parents": [],
        },
    )
    ref = gh_api(
        "POST",
        f"{API_REPO}/git/refs",
        payload={"ref": "refs/heads/main", "sha": commit["sha"]},
    )
    gh_api("PATCH", API_REPO, payload={"default_branch": "main"})

    summary = {
        "repository": repository["html_url"],
        "commit": commit["sha"],
        "ref": ref["ref"],
        "default_branch": "main",
        "files": len(files),
    }
    (TEMP / "upload_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
