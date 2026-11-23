#!/usr/bin/env bash
# ==============================================================================
# Shul.OS — Instant One-Tap Launch, Cold-Boot & Recovery Utility
# Brings Shul.OS up cleanly on cold boot or if the display window was closed.
#
# Usage:
#   shul-os            # Ensure server is running & open/focus Shul.OS fullscreen
#   shul-os --boot     # Cold-boot mode: wait up to 45s for Wayland + :8080, then launch
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
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"

# Prevent duplicate concurrent cold-boot launches
if [[ "$BOOT_MODE" -eq 1 ]]; then
  exec 9>"/tmp/shul-os-boot.lock"
  flock -n 9 || exit 0
fi

# 1. Wait for Wayland & Hyprland compositor readiness (especially on cold boot)
MAX_W_TRIES=6
[[ "$BOOT_MODE" -eq 1 ]] && MAX_W_TRIES=45
for _ in $(seq 1 "$MAX_W_TRIES"); do
  if [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && [[ -d "$XDG_RUNTIME_DIR/hypr" ]]; then
    HYPRLAND_INSTANCE_SIGNATURE="$(ls -t "$XDG_RUNTIME_DIR/hypr" 2>/dev/null | head -n 1 || true)"
    export HYPRLAND_INSTANCE_SIGNATURE
  fi
  if [[ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]; then
    if ! command -v hyprctl >/dev/null 2>&1 || hyprctl monitors >/dev/null 2>&1; then
      break
    fi
  fi
  sleep 0.6
done

# 2. Ensure Shul.OS backend service is alive
if [[ "$RESTART_SVC" -eq 1 ]]; then
  systemctl --user restart torah-sanctuary.service || true
elif ! systemctl --user is-active --quiet torah-sanctuary.service 2>/dev/null; then
  systemctl --user start torah-sanctuary.service || true
fi

# Wait up to 45s on cold boot (10s interactively) until :8080 actually responds 200 OK
MAX_HTTP_TRIES=20
[[ "$BOOT_MODE" -eq 1 ]] && MAX_HTTP_TRIES=90
for _ in $(seq 1 "$MAX_HTTP_TRIES"); do
  if curl -fsS --max-time 1 http://127.0.0.1:8080/api/celestial >/dev/null 2>&1; then
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

# 4. If a Shul.OS window is already running, focus it cleanly in Hyprland
if pgrep -f "chromium.*(kiosk-profile|127\.0\.0\.1:8080)" >/dev/null 2>&1; then
  if command -v hyprctl >/dev/null 2>&1 && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    hyprctl dispatch focuswindow "title:.*Shul\.OS.*" >/dev/null 2>&1 || \
    hyprctl dispatch focuswindow "class:.*chrome-127\.0\.0\.1.*" >/dev/null 2>&1 || true
    exit 0
  fi
fi

# Clear any stale desktop crash notifications on cold boot
if [[ "$BOOT_MODE" -eq 1 ]]; then
  makoctl dismiss -a 2>/dev/null || swaync-client -C 2>/dev/null || true
fi

# 5. Launch Shul.OS fullscreen kiosk (or windowed)
PROFILE_DIR="$HOME/torah-sanctuary/data/kiosk-profile"
[[ -d "$HOME/shul-os" && ! -d "$HOME/torah-sanctuary" ]] && PROFILE_DIR="$HOME/shul-os/data/kiosk-profile"
mkdir -p "$PROFILE_DIR"

CHROME_BIN="$(command -v chromium || command -v google-chrome || command -v brave || echo /usr/bin/chromium)"
KIOSK_FLAG="--kiosk"
[[ "$MODE" == "window" ]] && KIOSK_FLAG=""

exec "$CHROME_BIN" \
  $KIOSK_FLAG \
  --app=http://127.0.0.1:8080 \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --autoplay-policy=no-user-gesture-required \
  --ozone-platform=wayland \
  --user-data-dir="$PROFILE_DIR" \
  >/dev/null 2>&1 &
