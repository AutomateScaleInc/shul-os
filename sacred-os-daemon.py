#!/usr/bin/env python3
"""Torah Sanctuary OS — Living Holy Operating Layer Daemon (one-shot or periodic).

Synchronizes the underlying Linux / Hyprland operating system with the real-time
Jewish calendar, solar elevation, lunar phase, and Halachic Zmanim:
1. Publishes live JSON state to $XDG_RUNTIME_DIR/torah-sanctuary-state.json
2. Generates a rich Sacred Terminal MOTD (~/.cache/torah-sanctuary/motd.txt)
3. Gently shifts display color temperature with hyprsunset according to the Halachic watch
   (Dawn 4600K -> Morning 6200K -> Midday 5900K -> Golden Hour 4700K -> Twilight 4000K -> Night 3700K)
4. Honors Shabbat & Yom Tov stillness cleanly (no noisy notifications or intrusive popups)
"""
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
MOTD_PATH = CACHE_DIR / "motd.txt"


def load_cfg() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def apply_display_kelvin(target_k: int) -> str:
    """Gently align Hyprland display warmth with the real-time solar/Halachic watch via hyprsunset."""
    if not shutil.which("hyprsunset"):
        return "hyprsunset_not_installed"
    prev_k = None
    if KELVIN_STATE.exists():
        try:
            prev_k = int(KELVIN_STATE.read_text().strip())
        except Exception:
            prev_k = None
    # Avoid needless restarts if already within 150K
    if prev_k is not None and abs(prev_k - target_k) < 150:
        # Still check if hyprsunset is running when target_k < 6400
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

    # Replace existing hyprsunset cleanly
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


def render_motd(snap: dict, parasha_name: str, parasha_he: str) -> str:
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
    shabbat_tag = f"  {g}[SHABBAT SANCTUARY MODE]{r}" if snap.get("shabbat_mode") else ""

    lines = [
        f"{g}╭──────────────────────────────────────────────────────────────────────╮{r}",
        f"{g}│{r} {b}{g}✡ TORAH SANCTUARY OS{r}  {d}·  {snap['location']['city']}{r}{shabbat_tag}",
        f"{g}├──────────────────────────────────────────────────────────────────────┤{r}",
        f"{g}│{r} {b}Hebrew Date:{r}  {g}{he['en_str']}{r}  ({he['he_str']}){'  · After Sunset' if snap['after_sunset'] else ''}",
        f"{g}│{r} {b}Parashah:{r}     {c}Parashat {parasha_name}{r}  ({parasha_he})  ·  {snap['year_context']['tekufah']['en']}",
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

    color_status = "disabled"
    if cfg.get("os_color_temp_sync", True):
        color_status = apply_display_kelvin(int(snap["watch"]["kelvin"]))

    state_payload = {
        "updated_at": snap["timestamp_iso"],
        "parasha": {"en": p_en, "he": p_he},
        "hebrew_date": snap["hebrew_date"],
        "watch": snap["watch"],
        "shabbat_mode": snap["shabbat_mode"],
        "sun": snap["sun"],
        "moon": snap["moon"],
        "mizrach": snap["mizrach"],
        "next_zman": snap["next_zman"],
        "color_temp_sync": color_status,
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
        MOTD_PATH.write_text(render_motd(snap, p_en, p_he), encoding="utf-8")
    except Exception:
        pass

    return state_payload


if __name__ == "__main__":
    res = sync_once()
    if "--quiet" not in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
