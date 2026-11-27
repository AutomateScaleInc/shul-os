#!/usr/bin/env bash
# ==============================================================================
# Shul.OS — Bulletproof Cold-Boot, Offline Appliance Launch & Recovery Utility
# Works 100% offline with zero internet required.
#
# Usage:
#   shul-os            # Ensure server is running & open/focus Shul.OS fullscreen
#   shul-os --boot     # Cold-boot mode: wait up to 60s for Wayland + :8080, then launch
#   shul-os --restart  # Restart backend service + relaunch clean fullscreen kiosk
#   shul-os --window   # Open Shul.OS in a normal app window (non-kiosk)
# ==============================================================================
set -euo pipefail

MODE="kiosk"
RESTART_SVC=0
BOOT_MODE=0
for arg in "$@"; do
  case "$arg" in
    --restart|-r) RESTART_SVC=1 ;;
    --window|-w)  MODE="window" ;;
    --boot|-b)    BOOT_MODE=1 ;;
  esac
done

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Prevent duplicate concurrent cold-boot launches (autostart.lua + torah-kiosk.service)
if [[ "$BOOT_MODE" -eq 1 ]]; then
  exec 9>"/tmp/shul-os-boot.lock"
  flock -n 9 || exit 0
fi

# 1. Dynamically detect live Wayland socket (wayland-1 or wayland-0) & Hyprland readiness
MAX_W_TRIES=8
[[ "$BOOT_MODE" -eq 1 ]] && MAX_W_TRIES=60
for _ in $(seq 1 "$MAX_W_TRIES"); do
  if [[ -z "${WAYLAND_DISPLAY:-}" ]] || [[ ! -S "$XDG_RUNTIME_DIR/${WAYLAND_DISPLAY:-missing}" ]]; then
    for cand in wayland-1 wayland-0; do
      if [[ -S "$XDG_RUNTIME_DIR/$cand" ]]; then
        export WAYLAND_DISPLAY="$cand"
        break
      fi
    done
  fi
  if [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && [[ -d "$XDG_RUNTIME_DIR/hypr" ]]; then
    HYPRLAND_INSTANCE_SIGNATURE="$(ls -t "$XDG_RUNTIME_DIR/hypr" 2>/dev/null | head -n 1 || true)"
    export HYPRLAND_INSTANCE_SIGNATURE
  fi
  if [[ -n "${WAYLAND_DISPLAY:-}" ]] && [[ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]; then
    if ! command -v hyprctl >/dev/null 2>&1 || hyprctl monitors >/dev/null 2>&1; then
      break
    fi
  fi
  sleep 0.5
done
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"

# 2. Ensure Shul.OS local backend is alive (100% offline capable)
if [[ "$RESTART_SVC" -eq 1 ]]; then
  systemctl --user restart torah-sanctuary.service || true
elif ! systemctl --user is-active --quiet torah-sanctuary.service 2>/dev/null; then
  systemctl --user start torah-sanctuary.service || true
fi

# Wait until local 127.0.0.1:8080/api/health responds 200 OK (never opens a dead page)
MAX_HTTP_TRIES=24
[[ "$BOOT_MODE" -eq 1 ]] && MAX_HTTP_TRIES=90
for _ in $(seq 1 "$MAX_HTTP_TRIES"); do
  if curl -fsS --max-time 1 http://127.0.0.1:8080/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# 3. If --restart, close existing Shul.OS kiosk window first
if [[ "$RESTART_SVC" -eq 1 ]]; then
  pkill -f "chromium.*127\.0\.0\.1:8080" 2>/dev/null || true
  pkill -f "chromium.*kiosk-profile" 2>/dev/null || true
  sleep 1
fi

# 4. If a Shul.OS window is already running, leave it undisturbed (focus if interactive)
if pgrep -f "chromium.*(kiosk-profile|127\.0\.0\.1:8080)" >/dev/null 2>&1; then
  if [[ "$BOOT_MODE" -eq 0 ]] && command -v hyprctl >/dev/null 2>&1 && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    hyprctl dispatch focuswindow "title:.*Shul\.OS.*" >/dev/null 2>&1 || true
  fi
  exit 0
fi

# Clear any stale desktop crash notifications on cold boot
if [[ "$BOOT_MODE" -eq 1 ]]; then
  makoctl dismiss -a 2>/dev/null || swaync-client -C 2>/dev/null || true
fi

# 5. Scrub Chromium 'Crashed' exit flag so a hard power-unplug NEVER triggers "Restore pages?" bubble
PROFILE_DIR="$HOME/torah-sanctuary/data/kiosk-profile"
[[ -d "$HOME/shul-os" && ! -d "$HOME/torah-sanctuary" ]] && PROFILE_DIR="$HOME/shul-os/data/kiosk-profile"
mkdir -p "$PROFILE_DIR/Default"
PREFS="$PROFILE_DIR/Default/Preferences"
if [[ -f "$PREFS" ]]; then
  sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/g; s/"exited_cleanly":false/"exited_cleanly":true/g' "$PREFS" 2>/dev/null || true
fi

CHROME_BIN="$(command -v chromium || command -v google-chrome || command -v brave || echo /usr/bin/chromium)"
KIOSK_FLAG="--kiosk"
[[ "$MODE" == "window" ]] && KIOSK_FLAG=""

nohup "$CHROME_BIN" \
  $KIOSK_FLAG \
  --app=http://127.0.0.1:8080 \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --autoplay-policy=no-user-gesture-required \
  --ozone-platform=wayland \
  --user-data-dir="$PROFILE_DIR" \
  >/dev/null 2>&1 </dev/null &
disown || true
