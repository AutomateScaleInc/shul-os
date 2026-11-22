#!/usr/bin/env python3
"""Torah Sanctuary OS — Omarchy Synagogue, Chabad House & Residence Broadcast Mesh.

Links Synagogues, Chabad Houses, Kollels, and Family Residences together over
Omarchy's zero-config encrypted Tailscale WireGuard mesh (or LAN / Cloudflare
Tunnels) so any Rabbi or host can:
  1. Auto-discover sibling Torah Sanctuary Omarchy nodes on the Tailnet.
  2. Broadcast live synchronized Torah slides + Omarchy Studio virtual camera
     (`OmarchyStudioProgram` / `:53317/program.mjpg`) to every linked building.
  3. Push dignified real-time Sanctuary Announcements (Minyan alerts, Simchas,
     Emergency Tehillim, Holiday reminders) across the network.
  4. Respect every receiving node's LOCAL Shabbat & Yom Tov Stillness Zmanim
     automatically (a broadcast in New York never wakes a Brussels Shabbat screen).

Pure Python standard library — zero external dependencies.
"""

import concurrent.futures
import datetime
import json
import os
import pathlib
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request

import ai_engine
import broadcast_hub
import sacred_astronomy
import torah_db

_LOCK = threading.Lock()
_CAP_CACHE = {"ts": 0.0, "data": None}
_INCOMING_ACTIVE = None

NODE_TYPES = {
    "synagogue": {"label": "Main Synagogue", "icon": "🏛️", "color": "#e4bc69"},
    "chabad": {"label": "Chabad House", "icon": "🕯️", "color": "#5cb6e5"},
    "residence": {"label": "Family Residence", "icon": "🏠", "color": "#4ade80"},
    "mobile": {"label": "Mobile / Outreach Kiosk", "icon": "📡", "color": "#c084fc"},
}


def init_tables():
    with torah_db.get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS mesh_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            node_type TEXT NOT NULL DEFAULT 'synagogue',
            endpoint_url TEXT NOT NULL UNIQUE,
            camera_feed_url TEXT NOT NULL DEFAULT '',
            city TEXT NOT NULL DEFAULT '',
            rabbi_host TEXT NOT NULL DEFAULT '',
            shabbat_respect INTEGER NOT NULL DEFAULT 1,
            auto_follow INTEGER NOT NULL DEFAULT 0,
            is_self INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'unknown',
            last_seen TEXT NOT NULL DEFAULT '',
            last_latency_ms INTEGER NOT NULL DEFAULT 0,
            active_broadcast INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS mesh_broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT NOT NULL DEFAULT 'outbound',
            kind TEXT NOT NULL DEFAULT 'shiur',
            from_name TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            watch_url TEXT NOT NULL DEFAULT '',
            camera_feed_url TEXT NOT NULL DEFAULT '',
            delivered_count INTEGER NOT NULL DEFAULT 0,
            skipped_shabbat INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()


def _check_tcp_local(port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except Exception:
        return False


def _pgrep_exists(pattern: str) -> bool:
    if not shutil.which("pgrep"):
        return False
    try:
        res = subprocess.run(["pgrep", "-f", pattern], capture_output=True, timeout=1.2)
        return res.returncode == 0
    except Exception:
        return False


def _read_tailscale_status() -> dict:
    info = {
        "installed": bool(shutil.which("tailscale")),
        "active": False,
        "self_ip": "",
        "self_host": socket.gethostname(),
        "self_dns": "",
        "peers": [],
    }
    if not info["installed"]:
        return info
    try:
        res = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=2.5)
        if res.returncode != 0 or not res.stdout:
            return info
        data = json.loads(res.stdout)
        self_node = data.get("Self") or {}
        ips = self_node.get("TailscaleIPs") or []
        ipv4 = next((ip for ip in ips if "." in ip), ips[0] if ips else "")
        info["active"] = (data.get("BackendState") == "Running") and bool(ipv4)
        info["self_ip"] = ipv4
        info["self_host"] = self_node.get("HostName") or info["self_host"]
        info["self_dns"] = (self_node.get("DNSName") or "").rstrip(".")
        peers = []
        for p in (data.get("Peer") or {}).values():
            p_ips = p.get("TailscaleIPs") or []
            p_v4 = next((ip for ip in p_ips if "." in ip), "")
            if not p_v4:
                continue
            peers.append({
                "host": p.get("HostName") or p.get("DNSName", "").split(".")[0],
                "dns": (p.get("DNSName") or "").rstrip("."),
                "ip": p_v4,
                "os": p.get("OS") or "",
                "online": bool(p.get("Online")),
                "relay": p.get("Relay") or "",
                "direct": bool(p.get("CurAddr")),
            })
        peers.sort(key=lambda x: (not x["online"], x["host"].lower()))
        info["peers"] = peers
    except Exception:
        pass
    return info


def detect_omarchy_capabilities(force: bool = False) -> dict:
    """Detect real local Omarchy OS, Tailscale WireGuard mesh, and Studio Camera capabilities."""
    now = time.time()
    with _LOCK:
        if not force and _CAP_CACHE["data"] is not None and (now - _CAP_CACHE["ts"]) < 10.0:
            return _CAP_CACHE["data"]

    ts = _read_tailscale_status()
    lan_ip = broadcast_hub._detect_lan_ip()
    is_omarchy = pathlib.Path("/usr/share/omarchy").exists() or pathlib.Path.home().joinpath(".config/omarchy").exists()
    hyprland_active = bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")) or _pgrep_exists("Hyprland")
    studio_cam_pipewire = _pgrep_exists("omarchy_studio_program") or _pgrep_exists("omarchy-cam-switcher")
    director_mjpeg_live = _check_tcp_local(53317)
    visual_mesh_live = _check_tcp_local(8765)
    ble_lighting_live = _pgrep_exists("omarchy-ble-rgb-daemon")
    hyprsunset_available = bool(shutil.which("hyprsunset"))
    cloudflared_available = bool(shutil.which("cloudflared"))
    video_devices = sorted(str(p) for p in pathlib.Path("/dev").glob("video*"))[:6]

    cfg = ai_engine.load_config()
    custom_cam = (cfg.get("mesh_camera_url") or "").strip()
    auto_cam_url = ""
    if custom_cam:
        auto_cam_url = custom_cam
    elif director_mjpeg_live:
        host_ip = ts["self_ip"] or lan_ip
        auto_cam_url = f"http://{host_ip}:53317/program.mjpg"

    caps = {
        "is_omarchy": is_omarchy,
        "hostname": socket.gethostname(),
        "lan_ip": lan_ip,
        "tailscale": ts,
        "hyprland_active": hyprland_active,
        "hyprsunset_available": hyprsunset_available,
        "ble_lighting_live": ble_lighting_live,
        "studio_cam_pipewire": studio_cam_pipewire,
        "director_mjpeg_live": director_mjpeg_live,
        "visual_mesh_live": visual_mesh_live,
        "cloudflared_available": cloudflared_available,
        "video_devices": video_devices,
        "recommended_camera_url": auto_cam_url,
        "mesh_endpoint": f"http://{ts['self_ip']}:8080" if ts["self_ip"] else f"http://{lan_ip}:8080",
        "online_tailscale_peers": sum(1 for p in ts["peers"] if p["online"]),
        "total_tailscale_peers": len(ts["peers"]),
    }
    with _LOCK:
        _CAP_CACHE["ts"] = now
        _CAP_CACHE["data"] = caps
    return caps


def ensure_self_node(port: int = 8080) -> dict:
    """Ensure this Sanctuary node is registered as the local hub in mesh_nodes."""
    init_tables()
    cfg = ai_engine.load_config()
    caps = detect_omarchy_capabilities()
    name = (cfg.get("synagogue_name") or "The European Synagogue · Torah Sanctuary").strip()
    node_type = (cfg.get("mesh_node_type") or "synagogue").strip()
    if node_type not in NODE_TYPES:
        node_type = "synagogue"
    city = ((cfg.get("location") or {}).get("city") or "Brussels, Belgium").strip()
    endpoint = caps["mesh_endpoint"]
    cam_url = (cfg.get("mesh_camera_url") or caps["recommended_camera_url"] or "").strip()
    now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    with torah_db.get_conn() as conn:
        existing = conn.execute("SELECT id, endpoint_url FROM mesh_nodes WHERE is_self = 1 LIMIT 1").fetchone()
        if existing:
            conn.execute(
                """
                UPDATE mesh_nodes
                SET name=?, node_type=?, endpoint_url=?, camera_feed_url=?, city=?, status='online', last_seen=?, last_latency_ms=1
                WHERE id=?
                """,
                (name, node_type, endpoint, cam_url, city, now_iso, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT OR REPLACE INTO mesh_nodes
                (name, node_type, endpoint_url, camera_feed_url, city, rabbi_host, shabbat_respect, auto_follow, is_self, status, last_seen, last_latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0, 1, 'online', ?, 1)
                """,
                (name, node_type, endpoint, cam_url, city, "Rabbi Michoel Rosenblum", now_iso),
            )
        conn.commit()
        row = conn.execute("SELECT * FROM mesh_nodes WHERE is_self = 1 LIMIT 1").fetchone()
        return dict(row) if row else {}


def build_beacon() -> dict:
    """Lightweight live status beacon returned at GET /api/mesh/beacon for peer discovery."""
    cfg = ai_engine.load_config()
    caps = detect_omarchy_capabilities()
    cel = sacred_astronomy.get_sacred_moment(location=cfg.get("location"))
    bc = broadcast_hub.get_state(include_deck=False)
    return {
        "ok": True,
        "protocol": "torah-sanctuary-omarchy-mesh/1.0",
        "name": cfg.get("synagogue_name") or "Torah Sanctuary",
        "node_type": cfg.get("mesh_node_type") or "synagogue",
        "city": ((cfg.get("location") or {}).get("city") or "Brussels, Belgium"),
        "hostname": caps["hostname"],
        "is_omarchy": caps["is_omarchy"],
        "tailscale_ip": caps["tailscale"]["self_ip"],
        "lan_ip": caps["lan_ip"],
        "endpoint_url": caps["mesh_endpoint"],
        "camera_feed_url": (cfg.get("mesh_camera_url") or caps["recommended_camera_url"] or ""),
        "studio_cam_ready": caps["studio_cam_pipewire"] or caps["director_mjpeg_live"] or bool(cfg.get("mesh_camera_url")),
        "shabbat_stillness": bool(cel.get("shabbat_mode")),
        "hebrew_date": (cel.get("hebrew_date") or {}).get("en_str", ""),
        "active_broadcast": bool(bc.get("active")),
        "broadcast_watch_url": bc.get("watch_url") or "",
        "broadcast_deck_slug": bc.get("deck_slug") or "",
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def _probe_single_endpoint(endpoint_url: str, timeout: float = 1.6) -> dict:
    url = endpoint_url.rstrip("/") + "/api/mesh/beacon"
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TorahSanctuaryMesh/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            data = json.loads(raw)
            if data.get("protocol", "").startswith("torah-sanctuary"):
                return {
                    "online": True,
                    "latency_ms": max(1, int((time.monotonic() - t0) * 1000)),
                    "beacon": data,
                }
    except Exception:
        pass
    return {"online": False, "latency_ms": 0, "beacon": None}


def list_nodes(probe: bool = False) -> list:
    ensure_self_node()
    with torah_db.get_conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM mesh_nodes ORDER BY is_self DESC, id ASC").fetchall()]

    bc_self = broadcast_hub.get_state(include_deck=False)
    for r in rows:
        meta = NODE_TYPES.get(r["node_type"], NODE_TYPES["synagogue"])
        r["type_label"] = meta["label"]
        r["type_icon"] = meta["icon"]
        r["type_color"] = meta["color"]
        if r.get("is_self"):
            r["status"] = "online"
            r["active_broadcast"] = 1 if bc_self.get("active") else 0

    if probe:
        remotes = [r for r in rows if not r.get("is_self")]
        if remotes:
            now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(remotes))) as ex:
                fut_map = {ex.submit(_probe_single_endpoint, r["endpoint_url"]): r for r in remotes}
                with torah_db.get_conn() as conn:
                    for fut, r in fut_map.items():
                        res = fut.result()
                        r["status"] = "online" if res["online"] else "offline"
                        r["last_latency_ms"] = res["latency_ms"]
                        if res["online"] and res["beacon"]:
                            b = res["beacon"]
                            r["active_broadcast"] = 1 if b.get("active_broadcast") else 0
                            r["shabbat_stillness"] = bool(b.get("shabbat_stillness"))
                            r["last_seen"] = now_iso
                            if not r.get("camera_feed_url") and b.get("camera_feed_url"):
                                r["camera_feed_url"] = b["camera_feed_url"]
                            conn.execute(
                                "UPDATE mesh_nodes SET status=?, last_seen=?, last_latency_ms=?, active_broadcast=? WHERE id=?",
                                ("online", now_iso, res["latency_ms"], r["active_broadcast"], r["id"]),
                            )
                        else:
                            r["active_broadcast"] = 0
                            conn.execute(
                                "UPDATE mesh_nodes SET status='offline', last_latency_ms=0, active_broadcast=0 WHERE id=?",
                                (r["id"],),
                            )
                    conn.commit()
    return rows


def add_or_update_node(payload: dict) -> dict:
    init_tables()
    name = (payload.get("name") or "").strip()
    endpoint = (payload.get("endpoint_url") or "").strip().rstrip("/")
    if not name or not endpoint:
        raise ValueError("Please provide both a Synagogue / Residence name and a Tailscale or web URL.")
    if not endpoint.startswith(("http://", "https://")):
        endpoint = "http://" + endpoint
    node_type = (payload.get("node_type") or "chabad").strip().lower()
    if node_type not in NODE_TYPES:
        node_type = "synagogue"
    camera_url = (payload.get("camera_feed_url") or "").strip()
    city = (payload.get("city") or "").strip()
    rabbi_host = (payload.get("rabbi_host") or "").strip()
    shabbat_respect = 1 if payload.get("shabbat_respect", True) else 0
    auto_follow = 1 if payload.get("auto_follow", False) else 0

    probe_res = _probe_single_endpoint(endpoint, timeout=1.4)
    status = "online" if probe_res["online"] else "standby"
    now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds") if probe_res["online"] else ""
    if probe_res["online"] and probe_res["beacon"]:
        b = probe_res["beacon"]
        if not city and b.get("city"):
            city = b["city"]
        if not camera_url and b.get("camera_feed_url"):
            camera_url = b["camera_feed_url"]

    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO mesh_nodes (name, node_type, endpoint_url, camera_feed_url, city, rabbi_host, shabbat_respect, auto_follow, is_self, status, last_seen, last_latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            ON CONFLICT(endpoint_url) DO UPDATE SET
                name=excluded.name,
                node_type=excluded.node_type,
                camera_feed_url=excluded.camera_feed_url,
                city=excluded.city,
                rabbi_host=excluded.rabbi_host,
                shabbat_respect=excluded.shabbat_respect,
                auto_follow=excluded.auto_follow,
                status=excluded.status,
                last_seen=excluded.last_seen,
                last_latency_ms=excluded.last_latency_ms
            """,
            (name, node_type, endpoint, camera_url, city, rabbi_host, shabbat_respect, auto_follow, status, now_iso, probe_res["latency_ms"]),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM mesh_nodes WHERE endpoint_url = ?", (endpoint,)).fetchone()
        return {"ok": True, "node": dict(row), "probed_online": probe_res["online"]}


def delete_node(node_id: int) -> dict:
    init_tables()
    with torah_db.get_conn() as conn:
        row = conn.execute("SELECT is_self FROM mesh_nodes WHERE id = ?", (int(node_id),)).fetchone()
        if not row:
            return {"ok": False, "error": "Node not found"}
        if row["is_self"]:
            return {"ok": False, "error": "Cannot remove this primary host node"}
        conn.execute("DELETE FROM mesh_nodes WHERE id = ?", (int(node_id),))
        conn.commit()
    return {"ok": True}


def discover_tailscale_sanctuaries() -> dict:
    """Scan online Tailscale peers on port 8080 for running Torah Sanctuary OS nodes."""
    caps = detect_omarchy_capabilities(force=True)
    ts = caps["tailscale"]
    online_peers = [p for p in ts["peers"] if p["online"]]
    discovered = []
    if online_peers:
        def _check_peer(p):
            ep = f"http://{p['ip']}:8080"
            res = _probe_single_endpoint(ep, timeout=1.1)
            return {
                "host": p["host"],
                "ip": p["ip"],
                "os": p["os"],
                "direct": p["direct"],
                "endpoint_url": ep,
                "sanctuary_running": res["online"],
                "latency_ms": res["latency_ms"],
                "beacon": res["beacon"],
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(online_peers))) as ex:
            discovered = list(ex.map(_check_peer, online_peers))
        discovered.sort(key=lambda x: (not x["sanctuary_running"], x["host"].lower()))

    return {
        "tailscale_active": ts["active"],
        "self_ip": ts["self_ip"],
        "scanned_count": len(online_peers),
        "sanctuaries_found": sum(1 for d in discovered if d["sanctuary_running"]),
        "peers": discovered,
    }


def _push_to_peer(node: dict, payload: dict) -> dict:
    url = node["endpoint_url"].rstrip("/") + "/api/mesh/receive"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "TorahSanctuaryMesh/1.0"},
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            d = json.loads(resp.read().decode("utf-8", "ignore"))
            return {"node": node["name"], "endpoint": node["endpoint_url"], "status": "delivered" if d.get("ok") else d.get("reason", "declined"), "detail": d}
    except Exception as e:
        return {"node": node["name"], "endpoint": node["endpoint_url"], "status": "unreachable", "error": str(e)[:120]}


def broadcast_to_mesh(payload: dict) -> dict:
    """Broadcast a Live Shiur (slides + optional Omarchy Studio Camera) or Announcement across all linked nodes."""
    init_tables()
    cfg = ai_engine.load_config()
    caps = detect_omarchy_capabilities()
    kind = (payload.get("kind") or "shiur").strip().lower()  # shiur | announcement
    title = (payload.get("title") or "").strip()
    message = (payload.get("message") or "").strip()
    deck_kind = (payload.get("deck_kind") or "parasha").strip()
    deck_slug = (payload.get("deck_slug") or "").strip()
    include_camera = bool(payload.get("include_camera", True))
    camera_url = (payload.get("camera_feed_url") or cfg.get("mesh_camera_url") or (caps["recommended_camera_url"] if include_camera else "")).strip()
    target_types = payload.get("target_types")  # optional list e.g. ["synagogue","chabad","residence"]

    watch_url = ""
    bc_state = None
    if kind == "shiur":
        bc_state = broadcast_hub.start_broadcast(
            deck_kind=deck_kind,
            deck_slug=deck_slug,
            slide_idx=int(payload.get("slide_idx") or 0),
            public_tunnel=bool(payload.get("public_tunnel", True)),
            camera_feed_url=camera_url,
            network_scope="mesh",
        )
        watch_url = bc_state.get("watch_url") or f"{caps['mesh_endpoint']}/watch"
        if not title:
            title = f"Live Torah Broadcast · {(deck_slug or deck_kind).replace('-', ' ').title()}"
        if not message:
            message = "Synchronized slides & study stream are live now. Tap Tune In to watch together."
    else:
        if not title and not message:
            raise ValueError("Please write an announcement title or message to broadcast.")
        title = title or "Synagogue Mesh Announcement"
        watch_url = (payload.get("watch_url") or "").strip()

    signal_body = {
        "kind": kind,
        "from_name": cfg.get("synagogue_name") or "The European Synagogue",
        "from_type": cfg.get("mesh_node_type") or "synagogue",
        "city": ((cfg.get("location") or {}).get("city") or "Brussels, Belgium"),
        "title": title,
        "message": message,
        "watch_url": watch_url,
        "camera_feed_url": camera_url,
        "sent_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    nodes = [n for n in list_nodes(probe=False) if not n.get("is_self")]
    if isinstance(target_types, list) and target_types:
        allowed = {str(t).lower() for t in target_types}
        nodes = [n for n in nodes if n.get("node_type") in allowed]

    results = []
    if nodes:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(nodes))) as ex:
            results = list(ex.map(lambda n: _push_to_peer(n, signal_body), nodes))

    delivered = sum(1 for r in results if r["status"] == "delivered")
    skipped_shabbat = sum(1 for r in results if r["status"] == "shabbat_stillness")

    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO mesh_broadcasts (direction, kind, from_name, title, message, watch_url, camera_feed_url, delivered_count, skipped_shabbat)
            VALUES ('outbound', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (kind, signal_body["from_name"], title, message, watch_url, camera_url, delivered, skipped_shabbat),
        )
        conn.commit()

    return {
        "ok": True,
        "kind": kind,
        "signal": signal_body,
        "broadcast_state": bc_state,
        "peers_targeted": len(nodes),
        "delivered": delivered,
        "skipped_shabbat": skipped_shabbat,
        "results": results,
    }


def receive_mesh_signal(payload: dict) -> dict:
    """Receive an incoming live broadcast or announcement from a linked Synagogue/Chabad node."""
    global _INCOMING_ACTIVE
    init_tables()
    cfg = ai_engine.load_config()
    if not cfg.get("mesh_auto_receive", True):
        return {"ok": False, "reason": "auto_receive_disabled"}

    cel = sacred_astronomy.get_sacred_moment(location=cfg.get("location"))
    if cel.get("shabbat_mode"):
        return {"ok": False, "reason": "shabbat_stillness"}

    now = time.time()
    item = {
        "id": int(now * 1000),
        "kind": (payload.get("kind") or "announcement").strip(),
        "from_name": (payload.get("from_name") or "Linked Synagogue").strip(),
        "from_type": (payload.get("from_type") or "synagogue").strip(),
        "city": (payload.get("city") or "").strip(),
        "title": (payload.get("title") or "Live Sanctuary Broadcast").strip(),
        "message": (payload.get("message") or "").strip(),
        "watch_url": (payload.get("watch_url") or "").strip(),
        "camera_feed_url": (payload.get("camera_feed_url") or "").strip(),
        "received_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "expires_at": now + 3600,
    }
    with _LOCK:
        _INCOMING_ACTIVE = item

    with torah_db.get_conn() as conn:
        conn.execute(
            """
            INSERT INTO mesh_broadcasts (direction, kind, from_name, title, message, watch_url, camera_feed_url, delivered_count, skipped_shabbat)
            VALUES ('inbound', ?, ?, ?, ?, ?, ?, 1, 0)
            """,
            (item["kind"], item["from_name"], item["title"], item["message"], item["watch_url"], item["camera_feed_url"]),
        )
        conn.commit()

    return {"ok": True, "received": item}


def get_active_incoming() -> dict:
    with _LOCK:
        if _INCOMING_ACTIVE and time.time() < _INCOMING_ACTIVE.get("expires_at", 0):
            return {"active": True, "signal": dict(_INCOMING_ACTIVE)}
    return {"active": False, "signal": None}


def dismiss_incoming() -> dict:
    global _INCOMING_ACTIVE
    with _LOCK:
        _INCOMING_ACTIVE = None
    return {"ok": True}


def list_broadcast_history(limit: int = 12) -> list:
    init_tables()
    with torah_db.get_conn() as conn:
        rows = conn.execute("SELECT * FROM mesh_broadcasts ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]


def build_join_pack(request_host: str = "") -> dict:
    """Return zero-touch invite details for linking a new Synagogue, Chabad House, or Residence."""
    caps = detect_omarchy_capabilities()
    cfg = ai_engine.load_config()
    hub_url = (cfg.get("broadcast_public_base_url") or caps["mesh_endpoint"]).rstrip("/")
    watch_url = f"{hub_url}/watch"
    name = cfg.get("synagogue_name") or "The European Synagogue · Torah Sanctuary"
    join_cmd = (
        f"# On any Shul.OS Synagogue / Chabad / Residence node:\n"
        f"curl -sS -X POST http://127.0.0.1:8080/api/config "
        f"-H 'Content-Type: application/json' "
        f"-d '{{\"broadcast_follow_url\":\"{hub_url}\",\"mesh_auto_receive\":true}}'"
    )
    return {
        "hub_name": name,
        "hub_url": hub_url,
        "tailscale_ip": caps["tailscale"]["self_ip"],
        "lan_ip": caps["lan_ip"],
        "watch_url": watch_url,
        "beacon_url": f"{hub_url}/api/mesh/beacon",
        "join_command": join_cmd,
        "qr_svg_url": "/api/mesh/join-qr.svg",
    }


def get_mesh_overview(probe: bool = False, request_host: str = "") -> dict:
    caps = detect_omarchy_capabilities()
    nodes = list_nodes(probe=probe)
    return {
        "capabilities": caps,
        "nodes": nodes,
        "node_types": NODE_TYPES,
        "incoming": get_active_incoming(),
        "history": list_broadcast_history(10),
        "join_pack": build_join_pack(request_host),
        "broadcast": broadcast_hub.get_state(include_deck=False),
    }
