#!/usr/bin/env python3
"""
Shul.OS — Shabbat-Safe Fleet Auto-Updater & Version Manager.

Keeps every deployed Synagogue, Chabad House, and Family Residence appliance on one
shared open-source `main` branch while strictly preserving each building's private
`config.json`, `data/torah.db`, and `data/voice_cache/` untouched.
"""

import json
import os
import pathlib
import subprocess
import threading
import time
import urllib.request
from datetime import datetime, timezone

import ai_engine
import sacred_astronomy

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_REPO_URL = "https://github.com/AutomateScaleInc/shul-os"
DEFAULT_API_COMMITS = "https://api.github.com/repos/AutomateScaleInc/shul-os/commits/main"


def _run_git(args: list[str], timeout: int = 12) -> tuple[int, str, str]:
    try:
        p = subprocess.run(
            ["git", "-C", str(BASE_DIR), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as e:
        return 1, "", str(e)


def _repo_api_url(repo_url: str) -> str:
    clean = (repo_url or DEFAULT_REPO_URL).strip().rstrip("/")
    if clean.endswith(".git"):
        clean = clean[:-4]
    if "github.com/" in clean:
        slug = clean.split("github.com/", 1)[1].strip("/")
        if "/" in slug:
            return f"https://api.github.com/repos/{slug}/commits/main"
    return DEFAULT_API_COMMITS


def get_local_version() -> dict:
    cfg = ai_engine.load_config()
    repo_url = (cfg.get("update_repo_url") or DEFAULT_REPO_URL).strip()
    is_git = (BASE_DIR / ".git").exists()
    sha = ""
    short_sha = "tarball"
    commit_date = ""
    commit_msg = "Shul.OS Standalone Appliance"
    branch = "main"
    if is_git:
        rc, out, _ = _run_git(["rev-parse", "HEAD"])
        if rc == 0 and out:
            sha = out
            short_sha = out[:7]
        rc, b, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if rc == 0 and b:
            branch = b
        rc, dt, _ = _run_git(["show", "-s", "--format=%ci", "HEAD"])
        if rc == 0 and dt:
            commit_date = dt
        rc, msg, _ = _run_git(["show", "-s", "--format=%s", "HEAD"])
        if rc == 0 and msg:
            commit_msg = msg
    cel = {}
    try:
        cel = sacred_astronomy.get_sacred_moment(location=cfg.get("location"))
    except Exception:
        pass
    return {
        "is_git_repo": is_git,
        "branch": branch,
        "current_sha": sha,
        "short_sha": short_sha,
        "commit_date": commit_date,
        "commit_msg": commit_msg,
        "repo_url": repo_url,
        "auto_update_enabled": bool(cfg.get("auto_update_enabled", True)),
        "shabbat_stillness": bool(cel.get("shabbat_mode")),
    }


def check_for_updates(timeout: int = 8) -> dict:
    info = get_local_version()
    latest_sha = ""
    latest_msg = ""
    latest_date = ""
    behind_count = 0
    error = ""

    if info["is_git_repo"]:
        rc, _, err = _run_git(["fetch", "--quiet", "origin", "main"], timeout=timeout)
        if rc == 0:
            rc2, out, _ = _run_git(["rev-parse", "origin/main"])
            if rc2 == 0 and out:
                latest_sha = out
            rc3, msg, _ = _run_git(["show", "-s", "--format=%s", "origin/main"])
            if rc3 == 0:
                latest_msg = msg
            rc4, dt, _ = _run_git(["show", "-s", "--format=%ci", "origin/main"])
            if rc4 == 0:
                latest_date = dt
            if info["current_sha"] and latest_sha:
                rc5, cnt, _ = _run_git(["rev-list", "--count", f"{info['current_sha']}..origin/main"])
                if rc5 == 0 and cnt.isdigit():
                    behind_count = int(cnt)
        else:
            error = err or "Offline or remote unreachable"

    # Fallback: read latest commit from GitHub API if git fetch wasn't available
    if not latest_sha:
        try:
            req = urllib.request.Request(
                _repo_api_url(info["repo_url"]),
                headers={"User-Agent": "Shul.OS-Updater/1.0", "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
                latest_sha = data.get("sha", "")
                c = data.get("commit") or {}
                latest_msg = (c.get("message") or "").splitlines()[0]
                latest_date = (c.get("committer") or {}).get("date", "")
                if info["current_sha"] and latest_sha and info["current_sha"] != latest_sha:
                    behind_count = max(1, behind_count)
                error = ""
        except Exception as e:
            if not error:
                error = f"Offline ({type(e).__name__})"

    available = bool(latest_sha and info["current_sha"] and latest_sha != info["current_sha"])
    return {
        **info,
        "latest_sha": latest_sha,
        "latest_short_sha": latest_sha[:7] if latest_sha else "",
        "latest_msg": latest_msg,
        "latest_date": latest_date,
        "behind_count": behind_count,
        "update_available": available,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }


def _schedule_service_restart(delay_sec: float = 1.6):
    def _worker():
        time.sleep(delay_sec)
        try:
            subprocess.run(["systemctl", "--user", "restart", "torah-sanctuary.service"], timeout=15)
        except Exception:
            pass
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def apply_update(force: bool = False, restart_service: bool = True) -> dict:
    """Pull latest Shul.OS main branch cleanly (respecting Shabbat Stillness unless forced)."""
    status = check_for_updates(timeout=12)
    if status["shabbat_stillness"] and not force:
        return {
            "ok": False,
            "skipped": True,
            "reason": "🕯 Shabbat / Yom Tov Stillness active — automatic updates pause until after Havdalah.",
            "status": status,
        }
    if not status["is_git_repo"]:
        return {
            "ok": False,
            "skipped": False,
            "reason": "This installation was unpacked without .git; download the latest Shul.OS bundle or run install.sh to link GitHub updates.",
            "status": status,
        }
    if not status["update_available"] and not force:
        return {
            "ok": True,
            "updated": False,
            "message": f"Shul.OS is already up to date ({status['short_sha']}).",
            "status": status,
        }

    # Pull cleanly using fast-forward only so local untracked config.json / torah.db are NEVER touched
    rc, out, err = _run_git(["pull", "--ff-only", "origin", "main"], timeout=30)
    if rc != 0:
        return {
            "ok": False,
            "updated": False,
            "reason": f"git pull --ff-only failed: {err or out}",
            "status": status,
        }

    # Re-index any newly added sacred books into local SQLite FTS5
    try:
        import sacred_books
        sacred_books.index_into_db()
    except Exception:
        pass

    new_info = get_local_version()
    if restart_service:
        _schedule_service_restart(1.6)
    return {
        "ok": True,
        "updated": True,
        "restarting": bool(restart_service),
        "message": f"Updated Shul.OS to {new_info['short_sha']} ({new_info['commit_msg']}). Restarting service...",
        "status": new_info,
    }


if __name__ == "__main__":
    import sys
    if "--apply" in sys.argv:
        res = apply_update(force=("--force" in sys.argv), restart_service=("--no-restart" not in sys.argv))
        print(json.dumps(res, indent=2))
    else:
        print(json.dumps(check_for_updates(), indent=2))
