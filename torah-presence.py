#!/usr/bin/env python3
"""
Torah Sanctuary — Standalone Synagogue Presence Wake/Sleep Daemon.
100% local & fleet-independent:
- Monitors Sentinel's built-in FaceTime HD camera (/dev/video0) + local Hyprland cursor/keyboard activity.
- Wakes the display smoothly when a visitor steps up to the Torah Sanctuary station.
- Gently dims & sleeps the display after configurable idle timeout (default 5 minutes) when empty.
"""

import glob
import json
import os
import pathlib
import subprocess
import time

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
MODEL_CANDIDATES = [
    BASE_DIR / "data" / "face_detection_yunet.onnx",
    pathlib.Path.home() / ".config/cam-switcher/face_detection_yunet.onnx",
]


def _hypr_env() -> dict:
    env = os.environ.copy()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    env.setdefault("WAYLAND_DISPLAY", "wayland-1")
    hypr_dir = f"{env['XDG_RUNTIME_DIR']}/hypr"
    if os.path.isdir(hypr_dir):
        sigs = sorted(
            (os.path.join(hypr_dir, d) for d in os.listdir(hypr_dir)),
            key=lambda p: os.path.getmtime(p),
            reverse=True,
        )
        if sigs:
            env["HYPRLAND_INSTANCE_SIGNATURE"] = os.path.basename(sigs[0])
    return env


def set_display(on: bool):
    env = _hypr_env()
    if on:
        subprocess.run(["hyprctl", "dispatch", 'hl.dsp.dpms({ action = "enable" })'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        subprocess.run(["hyprctl", "dispatch", "dpms", "on"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        subprocess.run(["brightnessctl", "-c", "backlight", "set", "100%"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        for p in glob.glob("/sys/class/backlight/*/bl_power"):
            try:
                pathlib.Path(p).write_text("0\n")
            except Exception:
                pass
    else:
        subprocess.run(["brightnessctl", "-c", "backlight", "set", "0%"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        subprocess.run(["hyprctl", "dispatch", 'hl.dsp.dpms({ action = "disable" })'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        subprocess.run(["hyprctl", "dispatch", "dpms", "off"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)


def get_cursor_pos():
    try:
        out = subprocess.check_output(["hyprctl", "cursorpos"], env=_hypr_env(), timeout=1.5).decode().strip()
        return out
    except Exception:
        return None


def sleep_timeout_seconds() -> float:
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return max(60.0, float(cfg.get("presence_sleep_minutes", 5)) * 60.0)
    except Exception:
        return 300.0


def main():
    try:
        import cv2
    except Exception:
        cv2 = None

    detector = None
    if cv2 is not None:
        for mp in MODEL_CANDIDATES:
            if mp.exists():
                try:
                    detector = cv2.FaceDetectorYN.create(str(mp), "", (320, 240), 0.72, 0.3, 10)
                    break
                except Exception:
                    pass

    cap = None
    last_active = time.time()
    last_cursor = get_cursor_pos()
    display_on = True
    face_streak = 0

    print("Torah Sanctuary standalone presence monitor active.", flush=True)
    while True:
        now = time.time()
        saw_activity = False

        # 1. Check cursor movement
        cur = get_cursor_pos()
        if cur and cur != last_cursor:
            last_cursor = cur
            saw_activity = True

        # 2. Check camera face presence (~1 Hz — ultra low CPU)
        if cv2 is not None and detector is not None:
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture("/dev/video0")
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            if cap is not None and cap.isOpened():
                ok, frame = cap.read()
                if ok and frame is not None:
                    h, w = frame.shape[:2]
                    detector.setInputSize((w, h))
                    _, faces = detector.detect(frame)
                    if faces is not None and len(faces) > 0:
                        face_streak += 1
                        if face_streak >= 2:
                            saw_activity = True
                    else:
                        face_streak = 0

        if saw_activity:
            last_active = now
            if not display_on:
                set_display(True)
                display_on = True
        else:
            if display_on and (now - last_active) >= sleep_timeout_seconds():
                set_display(False)
                display_on = False

        time.sleep(1.0)


if __name__ == "__main__":
    main()
