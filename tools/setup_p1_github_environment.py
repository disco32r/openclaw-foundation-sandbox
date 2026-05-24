#!/usr/bin/env python3
"""Configure P1 GitHub fork environment from a GitHub token.

This script is intentionally token-safe:

- it reads the token from GITHUB_TOKEN only,
- it never writes the token into git remote URLs,
- it writes non-secret config and branch-protection evidence,
- it creates or uses the authenticated user's fork when no config exists.

Required environment:

- GITHUB_TOKEN: token able to create/use the fork, push contents, and manage branch protection.

Optional config:

- governance/p1-environment.json, based on governance/p1-environment.example.json.
  If missing, it is generated from the authenticated GitHub user.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "governance" / "p1-environment.json"
EVIDENCE = ROOT / "governance" / "evidence"
UPSTREAM = "openclaw/openclaw"


def fail(message: str) -> int:
    print(json.dumps({"ok": False, "error": message}, indent=2))
    return 1


def run(*args: str, env: dict[str, str] | None = None, timeout_s: int | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            list(args),
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        return 124, f"timed out after {timeout_s}s\n{output}".strip()
    return proc.returncode, proc.stdout.strip()


def api(token: str, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "openclaw-p1-setup",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"https://api.github.com{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def write_default_config(login: str) -> dict[str, Any]:
    config = {
        "fork_full_name": f"{login}/openclaw",
        "default_branch": "main",
        "working_branch": "codex/foundation-governance-bootstrap",
        "upstream_remote": "https://github.com/openclaw/openclaw.git",
        "origin_remote": f"https://github.com/{login}/openclaw.git",
        "branch_protection": {
            "required_pull_request_reviews": True,
            "required_approving_review_count": 1,
            "enforce_admins": False,
            "allow_deletions": False,
            "allow_force_pushes": False,
        },
    }
    CONFIG.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return config


def load_config() -> dict[str, Any]:
    with CONFIG.open("r", encoding="utf-8") as f:
        config = json.load(f)
    required = ["fork_full_name", "default_branch", "working_branch", "upstream_remote", "origin_remote"]
    missing = [field for field in required if not config.get(field)]
    if missing:
        raise ValueError(f"missing required config fields: {missing}")
    if config["fork_full_name"] == UPSTREAM:
        raise ValueError("fork_full_name must not be openclaw/openclaw")
    if "/OWNER/" in config["origin_remote"] or config["fork_full_name"].startswith("OWNER/"):
        raise ValueError("replace OWNER placeholders in governance/p1-environment.json")
    return config


def ensure_config(token: str) -> dict[str, Any]:
    if CONFIG.exists():
        return load_config()
    status, user = api(token, "GET", "/user")
    if status != 200 or not isinstance(user, dict) or not user.get("login"):
        raise ValueError(f"cannot identify authenticated GitHub user: HTTP {status}: {user}")
    return write_default_config(str(user["login"]))


def ensure_fork(config: dict[str, Any], token: str) -> tuple[int, Any]:
    owner, repo = config["fork_full_name"].split("/", 1)
    repo_status, repo_data = api(token, "GET", f"/repos/{owner}/{repo}")
    if repo_status == 200:
        if not (
            isinstance(repo_data, dict)
            and repo_data.get("fork") is True
            and isinstance(repo_data.get("parent"), dict)
            and repo_data["parent"].get("full_name") == UPSTREAM
        ):
            return 409, {
                "message": f"{config['fork_full_name']} exists but is not a fork of {UPSTREAM}",
                "observed_fork": repo_data.get("fork") if isinstance(repo_data, dict) else None,
                "observed_parent": (
                    repo_data.get("parent", {}).get("full_name")
                    if isinstance(repo_data, dict) and isinstance(repo_data.get("parent"), dict)
                    else None
                ),
            }
        return repo_status, repo_data

    body = {"name": repo} if repo != UPSTREAM.split("/", 1)[1] else {}
    create_status, create_data = api(token, "POST", f"/repos/{UPSTREAM}/forks", body)
    if create_status not in {200, 201, 202}:
        return create_status, create_data

    for _ in range(12):
        time.sleep(5)
        repo_status, repo_data = api(token, "GET", f"/repos/{owner}/{repo}")
        if repo_status == 200:
            return repo_status, repo_data
    return repo_status, repo_data


def configure_remotes(config: dict[str, Any]) -> None:
    code, origin = run("git", "remote", "get-url", "origin")
    if code == 0 and origin == config["upstream_remote"]:
        run("git", "remote", "rename", "origin", "upstream")
    code, _ = run("git", "remote", "get-url", "upstream")
    if code != 0:
        run("git", "remote", "add", "upstream", config["upstream_remote"])
    else:
        run("git", "remote", "set-url", "upstream", config["upstream_remote"])

    code, _ = run("git", "remote", "get-url", "origin")
    if code != 0:
        run("git", "remote", "add", "origin", config["origin_remote"])
    else:
        run("git", "remote", "set-url", "origin", config["origin_remote"])


def push_branch(config: dict[str, Any], token: str) -> None:
    askpass = ROOT / ".git" / "p1-askpass.sh"
    askpass.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "*Username*) printf '%s\\n' x-access-token ;;\n"
        "*Password*) printf '%s\\n' \"$GITHUB_TOKEN\" ;;\n"
        "*) printf '\\n' ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    askpass.chmod(0o700)
    env = os.environ.copy()
    env["GIT_ASKPASS"] = str(askpass)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GITHUB_TOKEN"] = token
    code, output = run(
        "git",
        "-c",
        "http.lowSpeedLimit=1",
        "-c",
        "http.lowSpeedTime=20",
        "push",
        "--porcelain",
        "-u",
        "origin",
        config["working_branch"],
        env=env,
        timeout_s=75,
    )
    try:
        askpass.unlink(missing_ok=True)
    finally:
        if code != 0:
            raise RuntimeError(f"git push failed: {output}")


def put_branch_protection(config: dict[str, Any], token: str) -> tuple[int, Any]:
    protection = config.get("branch_protection", {})
    body = {
        "required_status_checks": None,
        "enforce_admins": bool(protection.get("enforce_admins", False)),
        "required_pull_request_reviews": {
            "required_approving_review_count": int(protection.get("required_approving_review_count", 1))
        },
        "restrictions": None,
        "allow_force_pushes": bool(protection.get("allow_force_pushes", False)),
        "allow_deletions": bool(protection.get("allow_deletions", False)),
    }
    owner, repo = config["fork_full_name"].split("/", 1)
    branch = config["default_branch"]
    return api(token, "PUT", f"/repos/{owner}/{repo}/branches/{branch}/protection", body)


def write_evidence(config: dict[str, Any], repo_data: Any, protection_status: int, protection_data: Any) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    code, remotes = run("git", "remote", "-v")
    code2, status = run("git", "status", "--short", "--branch")
    evidence = {
        "ok": 200 <= protection_status < 300,
        "fork_full_name": config["fork_full_name"],
        "default_branch": config["default_branch"],
        "working_branch": config["working_branch"],
        "remote_status": remotes,
        "git_status": status,
        "repo_private": repo_data.get("private") if isinstance(repo_data, dict) else None,
        "repo_fork": repo_data.get("fork") if isinstance(repo_data, dict) else None,
        "branch_protection_status": protection_status,
        "branch_protection_summary": {
            "url": protection_data.get("url") if isinstance(protection_data, dict) else None,
            "required_pull_request_reviews": bool(
                isinstance(protection_data, dict) and protection_data.get("required_pull_request_reviews")
            ),
            "enforce_admins": bool(isinstance(protection_data, dict) and protection_data.get("enforce_admins")),
        },
    }
    (EVIDENCE / "p1-branch-protection.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if not token:
        return fail("missing GITHUB_TOKEN")

    try:
        config = ensure_config(token)
    except ValueError as exc:
        return fail(str(exc))

    repo_status, repo_data = ensure_fork(config, token)
    if repo_status != 200:
        return fail(f"cannot create or access fork repo {config['fork_full_name']}: HTTP {repo_status}: {repo_data}")

    try:
        configure_remotes(config)
        push_branch(config, token)
    except Exception as exc:
        return fail(str(exc))

    protection_status, protection_data = put_branch_protection(config, token)
    write_evidence(config, repo_data, protection_status, protection_data)
    if not (200 <= protection_status < 300):
        return fail(f"branch protection API failed: HTTP {protection_status}: {protection_data}")

    print(
        json.dumps(
            {
                "ok": True,
                "fork_full_name": config["fork_full_name"],
                "evidence": "governance/evidence/p1-branch-protection.json",
                "next_action": "run python3 tools/check_p1_environment.py",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
