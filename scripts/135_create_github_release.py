"""Create the GitHub v0.2.0 release and upload software assets."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_REPO = "repos/626619622/rata-tools"
RELEASE_DIR = ROOT / "rata_tools_release_0.2.0" / "dist"
TEMP = ROOT / "release_api_tmp_release"
TEMP.mkdir(parents=True, exist_ok=True)

ASSETS = [
    RELEASE_DIR / "rata_tools-0.2.0-py3-none-any.whl",
    RELEASE_DIR / "rata_tools-0.2.0-source-final.zip",
    RELEASE_DIR / "rata-tools-v0.2.0-final.bundle",
]


def run_gh(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"gh failed: {result.stderr}\n{result.stdout}")
    return result.stdout


def gh_json(method: str, endpoint: str, payload: dict | None = None):
    command = ["gh", "api", "--method", method, endpoint]
    if payload is not None:
        path = TEMP / "payload.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        command.extend(["--input", str(path)])
    return json.loads(run_gh(command)) if run_gh(command).strip() else {}


def main() -> None:
    releases = json.loads(run_gh(["gh", "api", f"{API_REPO}/releases"]))
    release = next((item for item in releases if item.get("tag_name") == "v0.2.0"), None)
    if release is None:
        release = json.loads(
            run_gh(
                [
                    "gh",
                    "api",
                    "--method",
                    "POST",
                    f"{API_REPO}/releases",
                    "--input",
                    str(TEMP / "release.json"),
                ]
            )
        ) if False else None
        payload = {
            "tag_name": "v0.2.0",
            "target_commitish": "main",
            "name": "rata-tools 0.2.0",
            "body": (
                "Initial public release of rata-tools.\n\n"
                "- evidence-capacity API\n"
                "- selection-aware cross-validation and matched null decisions\n"
                "- binary and cohort-stratified survival transport gates\n"
                "- structured GateDecision outputs\n"
                "- 13 passing tests, documentation, vignette and CI\n"
            ),
            "draft": False,
            "prerelease": False,
        }
        payload_path = TEMP / "release.json"
        payload_path.write_text(json.dumps(payload), encoding="utf-8")
        release = json.loads(
            run_gh(
                [
                    "gh",
                    "api",
                    "--method",
                    "POST",
                    f"{API_REPO}/releases",
                    "--input",
                    str(payload_path),
                ]
            )
        )

    existing_assets = {item["name"] for item in release.get("assets", [])}
    for asset in ASSETS:
        if asset.name in existing_assets:
            print(f"asset exists: {asset.name}")
            continue
        endpoint = (
            f"https://uploads.github.com/repos/626619622/rata-tools/releases/"
            f"{release['id']}/assets?name={asset.name}"
        )
        result = subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                "--header",
                "Content-Type: application/octet-stream",
                "--input",
                str(asset),
                endpoint,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode != 0:
            print(f"asset upload failed: {asset.name}: {result.stderr}")
        else:
            uploaded = json.loads(result.stdout)
            print(f"uploaded: {uploaded['name']}")

    final = json.loads(run_gh(["gh", "api", f"{API_REPO}/releases/tags/v0.2.0"]))
    summary = {
        "url": final["html_url"],
        "tag": final["tag_name"],
        "published_at": final["published_at"],
        "assets": [item["name"] for item in final.get("assets", [])],
    }
    (TEMP / "release_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
