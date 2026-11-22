#!/usr/bin/env python3
"""Torah Sanctuary OS — Live Broadcast Hub, Public Tunnel & Companion Node Sync.

Enables Rabbi Michoel (or any synagogue educator) to click 'Broadcast Live' inside
Presentation Mode and synchronize slides in real time (<50ms via Server-Sent Events)
to phones, tablets, TVs, and companion Torah Sanctuary nodes at home or in the lobby.

Zero external Python dependencies. Optionally uses `cloudflared` for instant zero-config
public HTTPS URLs and `qrencode` for crisp inline SVG QR codes.
"""
import atexit
import datetime
import json
import queue
import re
import shutil
import socket
import subprocess
import threading
import time

import ai_engine
import sanctuary_rich_data

_LOCK = threading.Lock()
_SUBSCRIBERS: set[queue.Queue] = set()
_TUNNEL_PROC = None
_SANCTUARY_TUNNEL_PROC = None
_SANCTUARY_PUBLIC_BASE = ""
_WATCHDOG_STARTED = False
_STATE = {
    "active": False,
    "started_at": "",
    "seq": 0,
    "host_name": "The European Synagogue · Torah Sanctuary",
    "deck_kind": "parasha",
    "deck_slug": "",
    "slide_idx": 0,
    "deck": None,
    "public_url": "",
    "lan_url": "",
    "camera_feed_url": "",
    "network_scope": "local",
    "tunnel_status": "idle",
}


def _detect_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _stop_tunnel_locked():
    global _TUNNEL_PROC
    if _TUNNEL_PROC is not None:
        try:
            _TUNNEL_PROC.terminate()
            _TUNNEL_PROC.wait(timeout=2)
        except Exception:
            try:
                _TUNNEL_PROC.kill()
            except Exception:
                pass
        _TUNNEL_PROC = None
    _STATE["public_url"] = ""
    _STATE["tunnel_status"] = "idle"


def _tunnel_reader(proc):
    url_re = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    try:
        for raw in proc.stderr:
            line = raw.decode("utf-8", "ignore")
            m = url_re.search(line)
            if m:
                pub = m.group(0).rstrip("/") + "/watch"
                with _LOCK:
                    if _TUNNEL_PROC is proc and _STATE["active"]:
                        _STATE["public_url"] = pub
                        _STATE["tunnel_status"] = "live"
                        _STATE["seq"] += 1
                        _fanout_locked()
                break
    except Exception:
        pass


def _cleanup_tunnels():
    global _TUNNEL_PROC, _SANCTUARY_TUNNEL_PROC
    for proc in (_TUNNEL_PROC, _SANCTUARY_TUNNEL_PROC):
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass


atexit.register(_cleanup_tunnels)


def get_public_base_url() -> str:
    """Return the active persistent HTTPS tunnel base URL (e.g. https://xyz.trycloudflare.com) if live."""
    with _LOCK:
        return _SANCTUARY_PUBLIC_BASE or ""


def _sanctuary_tunnel_reader(proc):
    global _SANCTUARY_PUBLIC_BASE
    url_re = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    try:
        for raw in proc.stderr:
            line = raw.decode("utf-8", "ignore")
            m = url_re.search(line)
            if m:
                base = m.group(0).rstrip("/")
                with _LOCK:
                    if _SANCTUARY_TUNNEL_PROC is proc:
                        _SANCTUARY_PUBLIC_BASE = base
                        if _STATE["active"] and not _STATE["public_url"]:
                            _STATE["public_url"] = base + "/watch"
                            _STATE["tunnel_status"] = "live"
                            _STATE["seq"] += 1
                            _fanout_locked()
    except Exception:
        pass
    finally:
        with _LOCK:
            if _SANCTUARY_TUNNEL_PROC is proc:
                _SANCTUARY_PUBLIC_BASE = ""


def ensure_sanctuary_tunnel(port: int = 8080) -> str:
    """Start (if needed) a single persistent Cloudflare quick tunnel so QR codes work on 4G/5G phones."""
    global _SANCTUARY_TUNNEL_PROC
    cfg = ai_engine.load_config()
    custom = (cfg.get("public_sanctuary_url") or cfg.get("broadcast_public_base_url") or "").strip().rstrip("/")
    if custom:
        return custom
    if not shutil.which("cloudflared"):
        return ""
    with _LOCK:
        if _SANCTUARY_TUNNEL_PROC is not None and _SANCTUARY_TUNNEL_PROC.poll() is None:
            return _SANCTUARY_PUBLIC_BASE
        try:
            proc = subprocess.Popen(
                ["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            _SANCTUARY_TUNNEL_PROC = proc
            threading.Thread(target=_sanctuary_tunnel_reader, args=(proc,), daemon=True).start()
        except Exception:
            pass
        return _SANCTUARY_PUBLIC_BASE


def start_tunnel_watchdog(port: int = 8080):
    """Background daemon that maintains the scannable HTTPS quick tunnel whenever internet is available."""
    global _WATCHDOG_STARTED
    with _LOCK:
        if _WATCHDOG_STARTED:
            return
        _WATCHDOG_STARTED = True

    def _loop():
        while True:
            try:
                ensure_sanctuary_tunnel(port=port)
            except Exception:
                pass
            time.sleep(30)

    threading.Thread(target=_loop, daemon=True).start()


def _start_tunnel_locked(port: int = 8080):
    global _TUNNEL_PROC
    cfg = ai_engine.load_config()
    custom_base = (cfg.get("broadcast_public_base_url") or cfg.get("public_sanctuary_url") or "").strip().rstrip("/")
    if custom_base:
        _STATE["public_url"] = custom_base + "/watch"
        _STATE["tunnel_status"] = "custom"
        return
    if _SANCTUARY_PUBLIC_BASE:
        _STATE["public_url"] = _SANCTUARY_PUBLIC_BASE.rstrip("/") + "/watch"
        _STATE["tunnel_status"] = "live"
        return
    if not shutil.which("cloudflared"):
        _STATE["tunnel_status"] = "lan_only"
        return
    if _TUNNEL_PROC is not None and _TUNNEL_PROC.poll() is None:
        return
    _STATE["tunnel_status"] = "starting"
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _TUNNEL_PROC = proc
    threading.Thread(target=_tunnel_reader, args=(proc,), daemon=True).start()


def _snapshot_locked(include_deck: bool = True) -> dict:
    snap = {
        "active": _STATE["active"],
        "started_at": _STATE["started_at"],
        "seq": _STATE["seq"],
        "host_name": _STATE["host_name"],
        "deck_kind": _STATE["deck_kind"],
        "deck_slug": _STATE["deck_slug"],
        "slide_idx": _STATE["slide_idx"],
        "public_url": _STATE["public_url"],
        "lan_url": _STATE["lan_url"],
        "watch_url": _STATE["public_url"] or _STATE["lan_url"],
        "camera_feed_url": _STATE["camera_feed_url"],
        "network_scope": _STATE["network_scope"],
        "tunnel_status": _STATE["tunnel_status"],
        "viewer_count": len(_SUBSCRIBERS),
        "cloudflared_available": bool(shutil.which("cloudflared")),
    }
    if include_deck:
        snap["deck"] = _STATE["deck"]
    return snap


def _fanout_locked():
    payload = json.dumps(_snapshot_locked(include_deck=True), ensure_ascii=False)
    dead = []
    for q in _SUBSCRIBERS:
        try:
            q.put_nowait(payload)
        except Exception:
            dead.append(q)
    for q in dead:
        _SUBSCRIBERS.discard(q)


def get_state(include_deck: bool = True) -> dict:
    with _LOCK:
        return _snapshot_locked(include_deck=include_deck)


def start_broadcast(deck_kind: str = "parasha", deck_slug: str = "", slide_idx: int = 0, public_tunnel: bool = True, port: int = 8080, camera_feed_url: str = "", network_scope: str = "local") -> dict:
    cfg = ai_engine.load_config()
    deck = sanctuary_rich_data.build_presentation(deck_kind, deck_slug)
    lan_ip = _detect_lan_ip()
    with _LOCK:
        _STATE["active"] = True
        _STATE["started_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        _STATE["host_name"] = cfg.get("synagogue_name") or "The European Synagogue · Torah Sanctuary"
        _STATE["deck_kind"] = deck_kind
        _STATE["deck_slug"] = deck_slug
        _STATE["slide_idx"] = max(0, min(int(slide_idx), max(0, len(deck.get("slides") or []) - 1)))
        _STATE["deck"] = deck
        _STATE["lan_url"] = f"http://{lan_ip}:{port}/watch"
        _STATE["camera_feed_url"] = (camera_feed_url or "").strip()
        _STATE["network_scope"] = (network_scope or "local").strip()
        _STATE["seq"] += 1
        if public_tunnel:
            _start_tunnel_locked(port=port)
        else:
            _stop_tunnel_locked()
        _fanout_locked()
        return _snapshot_locked(include_deck=False)


def sync_broadcast(deck_kind: str = None, deck_slug: str = None, slide_idx: int = None) -> dict:
    with _LOCK:
        if not _STATE["active"]:
            return _snapshot_locked(include_deck=False)
        if deck_kind is not None and (deck_kind != _STATE["deck_kind"] or (deck_slug or "") != _STATE["deck_slug"]):
            deck = sanctuary_rich_data.build_presentation(deck_kind, deck_slug or "")
            _STATE["deck_kind"] = deck_kind
            _STATE["deck_slug"] = deck_slug or ""
            _STATE["deck"] = deck
        if slide_idx is not None:
            total = len((_STATE["deck"] or {}).get("slides") or [])
            _STATE["slide_idx"] = max(0, min(int(slide_idx), max(0, total - 1)))
        _STATE["seq"] += 1
        _fanout_locked()
        return _snapshot_locked(include_deck=False)


def stop_broadcast() -> dict:
    with _LOCK:
        _STATE["active"] = False
        _STATE["deck"] = None
        _STATE["seq"] += 1
        _stop_tunnel_locked()
        _fanout_locked()
        return _snapshot_locked(include_deck=False)


def subscribe() -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=16)
    with _LOCK:
        _SUBSCRIBERS.add(q)
        q.put_nowait(json.dumps(_snapshot_locked(include_deck=True), ensure_ascii=False))
    return q


def unsubscribe(q: queue.Queue):
    with _LOCK:
        _SUBSCRIBERS.discard(q)


def generate_qr_svg(url: str) -> bytes:
    target = (url or "").strip()
    if not target:
        st = get_state(include_deck=False)
        target = st.get("watch_url") or f"http://{_detect_lan_ip()}:8080/watch"
    if shutil.which("qrencode"):
        try:
            res = subprocess.run(
                ["qrencode", "-t", "SVG", "-m", "2", "--foreground=101a2e", "--background=fffdf7", "-o", "-", target],
                capture_output=True,
                timeout=4,
            )
            if res.returncode == 0 and res.stdout:
                return res.stdout
        except Exception:
            pass
    # Graceful fallback SVG badge
    safe = target.replace("&", "&amp;").replace("<", "&lt;")
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" rx="16" fill="#fffdf7"/><text x="120" y="110" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#101a2e">Open Watch URL:</text><text x="120" y="136" text-anchor="middle" font-family="monospace" font-size="11" fill="#2c4470">{safe[:32]}</text></svg>'.encode("utf-8")
