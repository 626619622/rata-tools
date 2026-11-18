"""Update GitHub README and release notes with a currently valid wheel URL."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "rata_tools_release_0.2.0"
API_REPO = "repos/626619622/rata-tools"
TEMP = ROOT / "release_api_tmp_install"
TEMP.mkdir(parents=True, exist_ok=True)
WHEEL_URL = (
    "https://github.com/626619622/rata-tools/releases/download/v0.2.0/"
    "rata_tools-0.2.0-py3-none-any.whl"
)


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
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    readme = readme.replace(
        "```bash\npip install rata-tools\n```",
        f"```bash\npip install {WHEEL_URL}\n```",
        1,
    )
    current = gh_api("GET", f"{API_REPO}/contents/README.md")
    updated = gh_api(
        "PUT",
        f"{API_REPO}/contents/README.md",
        payload={
            "message": "Clarify installation from the public release wheel",
            "content": base64.b64encode(readme.encode("utf-8")).decode("ascii"),
            "sha": current["sha"],
        },
    )

    commit_sha = updated["commit"]["sha"]
    gh_api(
        "PATCH",
        f"{API_REPO}/git/refs/tags/v0.2.0",
        payload={"sha": commit_sha, "force": True},
    )

    release = gh_api("GET", f"{API_REPO}/releases/tags/v0.2.0")
    body = release["body"].rstrip() + (
        "\n\nInstall the release wheel directly:\n\n"
        f"`pip install {WHEEL_URL}`\n"
    )
    gh_api(
        "PATCH",
        f"{API_REPO}/releases/{release['id']}",
        payload={"body": body},
    )
    print(json.dumps({"commit": commit_sha, "release": release["html_url"]}, indent=2))


if __name__ == "__main__":
    main()
