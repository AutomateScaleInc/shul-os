#!/usr/bin/env python3
"""Shul.OS — Living Sanctuary Operating Layer Daemon (one-shot or periodic).

Synchronizes the underlying Linux / Wayland operating system with the real-time
Jewish calendar, solar elevation, lunar phase, and Halachic Zmanim:
1. Publishes live JSON state to $XDG_RUNTIME_DIR/torah-sanctuary-state.json
2. Generates a rich Shul.OS Terminal MOTD (~/.cache/torah-sanctuary/motd.txt) with live Daf Yomi
3. Gently shifts display color temperature (`hyprsunset`) AND hardware backlight (`brightnessctl`)
   according to the Halachic watch of day (Dawn 4600K/78% -> Morning 6200K/95% -> Midday 5900K/100%
   -> Golden Hour 4700K/84% -> Twilight 4000K/68% -> Night 3700K/54%)
4. Enforces the reverent Sanctuary Volume Guard (default <= 0.42)
5. Collects live hardware & service telemetry (CPU temp, RAM, SSD, uptime, systemd units)
6. Honors Shabbat & Yom Tov stillness cleanly (zero noisy popups, calm steady glow)
"""
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

import sacred_astronomy
import torah_db

CONFIG_PATH = APP_DIR / "config.json"
CACHE_DIR = Path.home() / ".cache" / "torah-sanctuary"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
KELVIN_STATE = CACHE_DIR / "last_kelvin.txt"
BRIGHT_STATE = CACHE_DIR / "last_brightness.txt"
MOTD_PATH = CACHE_DIR / "motd.txt"

# Gentle Halachic-watch backlight curve (%) to avoid nighttime glare & save power
WATCH_BRIGHTNESS_PCT = {
    "dawn": 78,
    "morning": 95,
    "midday": 100,
    "golden": 84,
    "twilight": 68,
    "night": 54,
}


def load_cfg() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def apply_display_kelvin(target_k: int) -> str:
    """Gently align Wayland display warmth with the real-time solar/Halachic watch via hyprsunset."""
    if not shutil.which("hyprsunset"):
        return "hyprsunset_not_installed"
    prev_k = None
    if KELVIN_STATE.exists():
        try:
            prev_k = int(KELVIN_STATE.read_text().strip())
        except Exception:
            prev_k = None
    if prev_k is not None and abs(prev_k - target_k) < 150:
        chk = subprocess.run(["pgrep", "-x", "hyprsunset"], capture_output=True)
        if target_k >= 6400 or chk.returncode == 0:
            return f"unchanged:{prev_k}K"

    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    env = dict(os.environ)
    env["XDG_RUNTIME_DIR"] = runtime
    if not env.get("WAYLAND_DISPLAY"):
        for cand in ("wayland-1", "wayland-0"):
            if Path(runtime, cand).exists():
                env["WAYLAND_DISPLAY"] = cand
                break
    if not env.get("WAYLAND_DISPLAY"):
        return "no_wayland_session"

    subprocess.run(["pkill", "-x", "hyprsunset"], capture_output=True)
    if target_k < 6400:
        subprocess.Popen(
            ["hyprsunset", "-t", str(int(target_k))],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    KELVIN_STATE.write_text(str(int(target_k)), encoding="utf-8")
    return f"applied:{target_k}K"


def apply_display_brightness(target_pct: int) -> str:
    """Smoothly match hardware backlight to the Halachic watch (e.g., Apple iMac acpi_video0)."""
    if not shutil.which("brightnessctl"):
        return "brightnessctl_not_installed"
    target_pct = max(35, min(100, int(target_pct)))
    prev_pct = None
    if BRIGHT_STATE.exists():
        try:
            prev_pct = int(BRIGHT_STATE.read_text().strip())
        except Exception:
            prev_pct = None
    if prev_pct is not None and abs(prev_pct - target_pct) < 5:
        return f"unchanged:{prev_pct}%"
    try:
        res = subprocess.run(
            ["brightnessctl", "-c", "backlight", "set", f"{target_pct}%"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0:
            BRIGHT_STATE.write_text(str(target_pct), encoding="utf-8")
            return f"applied:{target_pct}%"
        return "no_backlight_device"
    except Exception:
        return "unavailable"


def read_current_brightness_pct() -> int | None:
    if not shutil.which("brightnessctl"):
        return None
    try:
        cur = int(subprocess.check_output(["brightnessctl", "-c", "backlight", "g"], text=True, stderr=subprocess.DEVNULL, timeout=2).strip())
        mx = int(subprocess.check_output(["brightnessctl", "-c", "backlight", "m"], text=True, stderr=subprocess.DEVNULL, timeout=2).strip())
        if mx > 0:
            return int(round((cur / mx) * 100))
    except Exception:
        pass
    return None


def enforce_sanctuary_volume(max_vol: float) -> str:
    """Keep synagogue lobby speaker volume gentle & reverent (never startlingly loud)."""
    if not shutil.which("wpctl"):
        return "wpctl_not_installed"
    try:
        max_vol = max(0.05, min(1.0, float(max_vol)))
        runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
        env = dict(os.environ)
        env["XDG_RUNTIME_DIR"] = runtime
        out = subprocess.check_output(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            env=env,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).strip()
        parts = out.split()
        cur = float(parts[1]) if len(parts) >= 2 else 0.0
        if cur > max_vol + 0.01:
            subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{max_vol:.2f}"],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return f"capped:{cur:.2f}->{max_vol:.2f}"
        return f"ok:{cur:.2f}"
    except Exception:
        return "unavailable"


def get_os_telemetry() -> dict:
    """Read live bare-metal Linux appliance vitals: CPU temp, RAM, SSD, uptime, load, display & services."""
    cpu_temp_c = None
    for pat in ("/sys/class/thermal/thermal_zone*/temp", "/sys/class/hwmon/hwmon*/temp1_input"):
        for p in sorted(glob.glob(pat)):
            try:
                val = int(Path(p).read_text().strip())
                if 15000 <= val <= 115000:
                    cpu_temp_c = round(val / 1000.0, 1)
                    break
            except Exception:
                continue
        if cpu_temp_c is not None:
            break

    mem_total_gb = mem_avail_gb = mem_used_pct = None
    try:
        kv = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                kv[parts[0].rstrip(":")] = int(parts[1])
        tot = kv.get("MemTotal", 0)
        avail = kv.get("MemAvailable", 0)
        if tot > 0:
            mem_total_gb = round(tot / (1024 * 1024), 1)
            mem_avail_gb = round(avail / (1024 * 1024), 1)
            mem_used_pct = round(((tot - avail) / tot) * 100.0, 1)
    except Exception:
        pass

    disk_free_gb = disk_total_gb = disk_used_pct = None
    try:
        du = shutil.disk_usage(str(APP_DIR))
        disk_total_gb = round(du.total / (1024 ** 3), 1)
        disk_free_gb = round(du.free / (1024 ** 3), 1)
        disk_used_pct = round((du.used / du.total) * 100.0, 1) if du.total else 0.0
    except Exception:
        pass

    uptime_str = ""
    try:
        secs = int(float(Path("/proc/uptime").read_text().split()[0]))
        days, rem = divmod(secs, 86400)
        hrs, rem = divmod(rem, 3600)
        mins = rem // 60
        uptime_str = f"{days}d {hrs}h {mins}m" if days else f"{hrs}h {mins}m"
    except Exception:
        pass

    load_1m = None
    try:
        load_1m = round(os.getloadavg()[0], 2)
    except Exception:
        pass

    units = [
        ("torah-sanctuary.service", "Shul.OS Core"),
        ("torah-tunnel.service", "Public HTTPS Tunnel"),
        ("torah-celestial.timer", "Celestial OS Sync"),
        ("torah-scribe.timer", "Mini-Orca Scribe"),
        ("shul-os-update.timer", "Fleet Auto-Updater"),
    ]
    services = []
    for unit_id, label in units:
        st = "unknown"
        try:
            r = subprocess.run(["systemctl", "--user", "is-active", unit_id], capture_output=True, text=True, timeout=2)
            st = (r.stdout or "").strip() or "inactive"
        except Exception:
            pass
        services.append({"unit": unit_id, "label": label, "state": st, "active": st == "active"})

    kelvin = None
    if KELVIN_STATE.exists():
        try:
            kelvin = int(KELVIN_STATE.read_text().strip())
        except Exception:
            pass

    cfg = load_cfg()
    vol_str = enforce_sanctuary_volume(cfg.get("max_sanctuary_volume", 0.42))
    return {
        "hostname": os.uname().nodename,
        "cpu_temp_c": cpu_temp_c,
        "load_1m": load_1m,
        "mem_total_gb": mem_total_gb,
        "mem_avail_gb": mem_avail_gb,
        "mem_used_pct": mem_used_pct,
        "disk_total_gb": disk_total_gb,
        "disk_free_gb": disk_free_gb,
        "disk_used_pct": disk_used_pct,
        "uptime": uptime_str,
        "display_kelvin": kelvin,
        "backlight_pct": read_current_brightness_pct(),
        "volume_guard": vol_str,
        "services": services,
    }


def render_motd(snap: dict, parasha_name: str, parasha_he: str, daf_label: str = "") -> str:
    g = "\033[38;5;221m"  # Warm gold
    c = "\033[38;5;117m"  # Sky blue
    d = "\033[38;5;247m"  # Muted
    b = "\033[1m"
    r = "\033[0m"
    he = snap["hebrew_date"]
    sun = snap["sun"]
    moon = snap["moon"]
    w = snap["watch"]
    nz = snap.get("next_zman") or {}
    mizrach = snap["mizrach"]
    kl = snap["year_context"]["kiddush_levana"]
    shabbat_tag = f"  {g}[SHABBAT STILLNESS MODE]{r}" if snap.get("shabbat_mode") else ""

    lines = [
        f"{g}╭──────────────────────────────────────────────────────────────────────╮{r}",
        f"{g}│{r} {b}{g}✡ SHUL.OS{r}  {d}·  {snap['location']['city']}{r}{shabbat_tag}",
        f"{g}├──────────────────────────────────────────────────────────────────────┤{r}",
        f"{g}│{r} {b}Hebrew Date:{r}  {g}{he['en_str']}{r}  ({he['he_str']}){'  · After Sunset' if snap['after_sunset'] else ''}",
        f"{g}│{r} {b}Parashah:{r}     {c}Parashat {parasha_name}{r}  ({parasha_he})  ·  {snap['year_context']['tekufah']['en']}",
    ]
    if daf_label:
        lines.append(f"{g}│{r} {b}Daf Yomi:{r}     {g}{daf_label}{r}")
    lines += [
        f"{g}│{r} {b}Sacred Watch:{r} {w['en']}  ({w['he']})  ·  Display {w['kelvin']}K",
        f"{g}│{r} {b}Sun:{r}          ☀ Alt {sun['altitude_deg']:+.1f}° {sun['compass']} ({sun['azimuth_deg']}°)  ·  Mizrach (Jerusalem) {mizrach['bearing_deg']}° {mizrach['compass']}",
        f"{g}│{r} {b}Moon:{r}         {moon['emoji']} {moon['phase_en']} ({moon['illumination_pct']}%)  ·  Alt {moon['altitude_deg']:+.1f}° {moon['compass']}  ·  Rise {moon['moonrise']} / Set {moon['moonset']}",
    ]
    if nz:
        lines.append(f"{g}│{r} {b}Next Zman:{r}    {g}{nz['name']}{r} at {b}{nz['time']}{r} (in {nz['countdown']})")
    lines.append(f"{g}│{r} {d}Lunar Cycle:  {kl['status']}{r}")
    lines.append(f"{g}╰──────────────────────────────────────────────────────────────────────╯{r}")
    return "\n".join(lines) + "\n"


def sync_once() -> dict:
    cfg = load_cfg()
    snap = sacred_astronomy.get_sacred_moment()
    try:
        wp = torah_db.get_weekly_parasha()
        p_en, p_he = wp.get("en_name", ""), wp.get("he_name", "")
    except Exception:
        p_en, p_he = "", ""

    daf_label = ""
    try:
        import sacred_books
        daf_label = sacred_books.get_daily_daf_yomi()["label"]
    except Exception:
        pass

    color_status = "disabled"
    if cfg.get("os_color_temp_sync", True):
        color_status = apply_display_kelvin(int(snap["watch"]["kelvin"]))

    bright_status = "disabled"
    if cfg.get("os_brightness_sync", True):
        watch_mood = (snap["watch"].get("mood") or "midday").lower()
        target_pct = WATCH_BRIGHTNESS_PCT.get(watch_mood, 90)
        if snap.get("shabbat_mode") and target_pct < 62:
            target_pct = 62  # Peaceful warm Shabbat sanctuary glow
        bright_status = apply_display_brightness(target_pct)

    vol_status = enforce_sanctuary_volume(cfg.get("max_sanctuary_volume", 0.42))

    state_payload = {
        "updated_at": snap["timestamp_iso"],
        "parasha": {"en": p_en, "he": p_he},
        "daf_yomi": daf_label,
        "hebrew_date": snap["hebrew_date"],
        "watch": snap["watch"],
        "shabbat_mode": snap["shabbat_mode"],
        "sun": snap["sun"],
        "moon": snap["moon"],
        "mizrach": snap["mizrach"],
        "next_zman": snap["next_zman"],
        "color_temp_sync": color_status,
        "brightness_sync": bright_status,
        "volume_guard": vol_status,
    }

    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
    for target in (runtime_dir / "torah-sanctuary-state.json", CACHE_DIR / "celestial-state.json"):
        try:
            tmp = target.with_suffix(".tmp")
            tmp.write_text(json.dumps(state_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(target)
        except Exception:
            pass

    try:
        MOTD_PATH.write_text(render_motd(snap, p_en, p_he, daf_label), encoding="utf-8")
    except Exception:
        pass

    return state_payload


if __name__ == "__main__":
    if "--telemetry" in sys.argv:
        print(json.dumps(get_os_telemetry(), ensure_ascii=False, indent=2))
    else:
        res = sync_once()
        if "--quiet" not in sys.argv:
            print(json.dumps(res, ensure_ascii=False, indent=2))
