"""Remove generated egg-info files from the GitHub default branch."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_REPO = "repos/626619622/rata-tools"
TEMP = ROOT / "release_api_tmp_cleanup"
TEMP.mkdir(parents=True, exist_ok=True)

DELETE_PATHS = [
    "src/rata_tools.egg-info/dependency_links.txt",
    "src/rata_tools.egg-info/entry_points.txt",
    "src/rata_tools.egg-info/PKG-INFO",
    "src/rata_tools.egg-info/requires.txt",
    "src/rata_tools.egg-info/SOURCES.txt",
    "src/rata_tools.egg-info/top_level.txt",
]


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


def main() -> None:
    ref = gh_api("GET", f"{API_REPO}/git/ref/heads/main")
    parent = gh_api("GET", f"{API_REPO}/git/commits/{ref['object']['sha']}")
    tree = gh_api(
        "POST",
        f"{API_REPO}/git/trees",
        payload={
            "base_tree": parent["tree"]["sha"],
            "tree": [
                {
                    "path": path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": None,
                }
                for path in DELETE_PATHS
            ],
        },
    )
    commit = gh_api(
        "POST",
        f"{API_REPO}/git/commits",
        payload={
            "message": "Remove generated package metadata",
            "tree": tree["sha"],
            "parents": [parent["sha"]],
        },
    )
    gh_api(
        "PATCH",
        f"{API_REPO}/git/refs/heads/main",
        payload={"sha": commit["sha"], "force": False},
    )
    print(json.dumps({"commit": commit["sha"], "removed": DELETE_PATHS}, indent=2))


if __name__ == "__main__":
    main()
