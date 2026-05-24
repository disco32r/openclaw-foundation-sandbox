#!/usr/bin/env python3
"""Check whether the P1 foundation repo environment can pass.

This is a read-only readiness check. It does not create forks, install tools,
change remotes, push branches, or mutate GitHub settings.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_REPO = "openclaw/openclaw"
CONFIG = ROOT / "governance" / "p1-environment.json"


def run_git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.strip()


def parse_github_full_name(url: str) -> str | None:
    if url.startswith("git@github.com:"):
        path = url.split(":", 1)[1]
    else:
        parsed = urlparse(url)
        if parsed.netloc.lower() != "github.com":
            return None
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        return None
    return f"{parts[0]}/{parts[1]}"


def main() -> int:
    checks: list[dict[str, object]] = []
    config: dict[str, object] = {}
    if CONFIG.exists():
        try:
            config = json.loads(CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            config = {"error": str(exc)}

    code, status = run_git("status", "--short", "--branch")
    checks.append(
        {
            "id": "git_status_clean",
            "ok": code == 0 and "\n" not in status and status.startswith("## "),
            "observed": status,
            "required": "working tree clean on a named branch",
        }
    )

    code, branch = run_git("branch", "--show-current")
    checks.append(
        {
            "id": "branch_named",
            "ok": code == 0 and bool(branch),
            "observed": branch,
            "required": "current branch is named",
        }
    )

    code, origin_url = run_git("remote", "get-url", "origin")
    origin_full_name = parse_github_full_name(origin_url) if code == 0 else None
    expected_fork = config.get("fork_full_name")
    checks.append(
        {
            "id": "origin_is_ryan_fork",
            "ok": bool(origin_full_name)
            and origin_full_name != UPSTREAM_REPO
            and (not isinstance(expected_fork, str) or origin_full_name == expected_fork),
            "observed": origin_url if code == 0 else "missing",
            "required": "origin points to the configured Ryan-owned fork, not openclaw/openclaw",
        }
    )

    code, upstream_url = run_git("remote", "get-url", "upstream")
    upstream_full_name = parse_github_full_name(upstream_url) if code == 0 else None
    checks.append(
        {
            "id": "upstream_is_openclaw",
            "ok": upstream_full_name == UPSTREAM_REPO,
            "observed": upstream_url if code == 0 else "missing",
            "required": "upstream points to openclaw/openclaw",
        }
    )

    setup_script = ROOT / "tools" / "setup_p1_github_environment.py"
    gh_path = shutil.which("gh")
    checks.append(
        {
            "id": "github_tooling_available",
            "ok": gh_path is not None or setup_script.exists(),
            "observed": gh_path or (str(setup_script.relative_to(ROOT)) if setup_script.exists() else "missing"),
            "required": "gh CLI available or source-controlled authenticated GitHub setup tooling exists",
        }
    )

    branch_proof = ROOT / "governance" / "evidence" / "p1-branch-protection.json"
    checks.append(
        {
            "id": "branch_protection_evidence",
            "ok": branch_proof.exists(),
            "observed": str(branch_proof.relative_to(ROOT)) if branch_proof.exists() else "missing",
            "required": "captured branch protection proof for the fork",
        }
    )

    checks.append(
        {
            "id": "p1_environment_config",
            "ok": CONFIG.exists()
            and isinstance(config.get("fork_full_name"), str)
            and not str(config.get("fork_full_name")).startswith("OWNER/")
            and isinstance(config.get("origin_remote"), str)
            and "OWNER" not in str(config.get("origin_remote")),
            "observed": str(CONFIG.relative_to(ROOT)) if CONFIG.exists() else "missing",
            "required": "governance/p1-environment.json exists without OWNER placeholders",
        }
    )

    ok = all(bool(check["ok"]) for check in checks)
    output = {
        "ok": ok,
        "root": str(ROOT),
        "phase": "P1",
        "checks": checks,
        "next_action": (
            "P1 can be reviewed for pass."
            if ok
            else "Resolve failed checks or keep P1 blocked with approval packet."
        ),
    }
    print(json.dumps(output, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
