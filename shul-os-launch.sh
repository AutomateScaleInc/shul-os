#!/usr/bin/env bash
# ==============================================================================
# Shul.OS — Instant One-Tap Launch & Recovery Utility
# Brings Shul.OS back immediately if the kiosk window or service was closed.
#
# Usage:
#   shul-os            # Ensure server is running & open/focus Shul.OS fullscreen
#   shul-os --restart  # Restart backend service + relaunch clean fullscreen kiosk
#   shul-os --window   # Open Shul.OS in a normal app window (non-kiosk)
# ==============================================================================
set -euo pipefail

MODE="kiosk"
RESTART_SVC=0
for arg in "$@"; do
  case "$arg" in
    --restart|-r) RESTART_SVC=1 ;;
    --window|-w)  MODE="window" ;;
  esac
done

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
if [[ -z "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && [[ -d "$XDG_RUNTIME_DIR/hypr" ]]; then
  HYPRLAND_INSTANCE_SIGNATURE="$(ls -1 "$XDG_RUNTIME_DIR/hypr" 2>/dev/null | head -n 1 || true)"
  export HYPRLAND_INSTANCE_SIGNATURE
fi

# 1. Ensure Shul.OS backend service is alive
if [[ "$RESTART_SVC" -eq 1 ]]; then
  systemctl --user restart torah-sanctuary.service || true
elif ! systemctl --user is-active --quiet torah-sanctuary.service 2>/dev/null; then
  systemctl --user start torah-sanctuary.service || true
fi

# Wait up to 8 seconds for :8080 to respond
for _ in $(seq 1 16); do
  if curl -fsS --max-time 1 http://127.0.0.1:8080/api/celestial >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# 2. If --restart, close existing Shul.OS kiosk window first
if [[ "$RESTART_SVC" -eq 1 ]]; then
  pkill -f "chromium.*127\.0\.0\.1:8080" 2>/dev/null || true
  pkill -f "chromium.*kiosk-profile" 2>/dev/null || true
  sleep 1
fi

# 3. If a Shul.OS window is already running, focus it cleanly in Hyprland
if pgrep -f "chromium.*(kiosk-profile|127\.0\.0\.1:8080)" >/dev/null 2>&1; then
  if command -v hyprctl >/dev/null 2>&1 && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    hyprctl dispatch focuswindow "title:.*Shul\.OS.*" >/dev/null 2>&1 || \
    hyprctl dispatch focuswindow "class:.*chrome-127\.0\.0\.1.*" >/dev/null 2>&1 || true
    exit 0
  fi
fi

# 4. Launch Shul.OS fullscreen kiosk (or windowed)
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
