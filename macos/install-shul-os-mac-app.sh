#!/usr/bin/env bash
# ==============================================================================
# Shul.OS — Native macOS App Installer (/Applications/Shul.OS.app)
# Creates a standalone macOS .app bundle with the brushed-gold Shul.OS Retina
# icon, Spotlight integration, and automatic LAN/HTTPS Sanctuary connection.
#
# Usage:
#   ./macos/install-shul-os-mac-app.sh [SANCTUARY_URL]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ICON_SRC="${ROOT_DIR}/static/branding/shulos-logo-icon.png"
PRIMARY_URL="${1:-https://shul.automatescale.com}"
LOCAL_FALLBACK="${2:-http://100.94.73.72:8080}"
APP="/Applications/Shul.OS.app"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer runs on macOS. On Linux, use ./install-shul-os.sh"
  exit 1
fi

echo "✡ Installing Shul.OS.app into /Applications..."
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

if [[ -f "$ICON_SRC" ]] && command -v sips >/dev/null && command -v iconutil >/dev/null; then
  ICONSET="$(mktemp -d)/ShulOS.iconset"
  mkdir -p "$ICONSET"
  for sz in 16 32 128 256 512; do
    sips -z "$sz" "$sz" "$ICON_SRC" --out "$ICONSET/icon_${sz}x${sz}.png" >/dev/null
    sz2=$((sz * 2))
    sips -z "$sz2" "$sz2" "$ICON_SRC" --out "$ICONSET/icon_${sz}x${sz}@2x.png" >/dev/null
  done
  iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
  rm -rf "$(dirname "$ICONSET")"
fi

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>Shul.OS</string>
  <key>CFBundleDisplayName</key>
  <string>Shul.OS</string>
  <key>CFBundleIdentifier</key>
  <string>com.automatescale.shul-os</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleExecutable</key>
  <string>ShulOS</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/ShulOS" <<LAUNCH
#!/usr/bin/env bash
set -euo pipefail
URL="${PRIMARY_URL}"
if [[ -n "${LOCAL_FALLBACK}" ]] && curl -fsS --max-time 1.2 "${LOCAL_FALLBACK}/api/celestial" >/dev/null 2>&1; then
  URL="${LOCAL_FALLBACK}"
fi
PROFILE="\$HOME/Library/Application Support/Shul.OS/profile"
mkdir -p "\$PROFILE"
for CHROME in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
  if [[ -x "\$CHROME" ]]; then
    exec "\$CHROME" --app="\$URL" --user-data-dir="\$PROFILE" --window-size=1600,980 --no-first-run --no-default-browser-check >/dev/null 2>&1 &
    exit 0
  fi
done
open "\$URL"
LAUNCH
chmod +x "$APP/Contents/MacOS/ShulOS"

/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP" >/dev/null 2>&1 || true
touch "$APP"
echo "✅ Installed /Applications/Shul.OS.app! Open via Spotlight (⌘+Space → Shul.OS) or drag it into your Dock."
