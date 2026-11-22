#!/usr/bin/env bash
# ==============================================================================
# Torah Sanctuary / ShulOS — Open-Source Turnkey Installer for Synagogues,
# Chabad Houses & Jewish Residences (Omarchy / Arch Linux / Debian / Ubuntu)
#
# Usage:
#   ./install-omarchy-shul.sh [--name "Chabad House City"] [--type chabad] [--follow "https://shul.automatescale.com"]
# ==============================================================================
set -euo pipefail

INSTALL_DIR="${TORAH_INSTALL_DIR:-$HOME/torah-sanctuary}"
SHUL_NAME="Torah Sanctuary · ShulOS"
NODE_TYPE="chabad"
FOLLOW_URL=""
MODEL="qwen2.5:3b"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)   SHUL_NAME="$2"; shift 2 ;;
    --type)   NODE_TYPE="$2"; shift 2 ;;
    --follow) FOLLOW_URL="$2"; shift 2 ;;
    --model)  MODEL="$2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "✡ Installing Torah Sanctuary / ShulOS into $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR" "$HOME/.config/systemd/user"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" != "$INSTALL_DIR" ]]; then
  rsync -a --exclude '.git' --exclude 'data/kiosk-profile' "$SCRIPT_DIR/" "$INSTALL_DIR/"
fi

# 1. Pull smart offline Ollama model if Ollama is available
if command -v ollama >/dev/null 2>&1; then
  echo "🧠 Ensuring local offline AI model ($MODEL) is ready..."
  ollama pull "$MODEL" || true
fi

# 2. Optional Studio Neural Hebrew & English voice venv (edge-tts)
if [[ ! -x "$INSTALL_DIR/voice/venv/bin/edge-tts" ]]; then
  echo "🎙 Setting up Studio Hebrew & English voice runtime..."
  python3 -m venv "$INSTALL_DIR/voice/venv" || true
  "$INSTALL_DIR/voice/venv/bin/pip" install -q --upgrade edge-tts || true
fi

# 3. Write initial config.json if missing or update Mesh/Shul identity
python3 - "$INSTALL_DIR/config.json" "$SHUL_NAME" "$NODE_TYPE" "$FOLLOW_URL" "$MODEL" << 'PYEOF'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg.setdefault("synagogue_name", sys.argv[2])
cfg["mesh_node_type"] = sys.argv[3]
cfg["ollama_model"] = sys.argv[5]
cfg.setdefault("mesh_auto_receive", True)
if sys.argv[4]:
    cfg["broadcast_follow_url"] = sys.argv[4]
p.write_text(json.dumps(cfg, indent=2))
print("Configured:", p)
PYEOF

# 4. Index Haggadah, Siddur & offline sacred books into local SQLite FTS5
(cd "$INSTALL_DIR" && python3 -c "import sacred_books; print('Indexed offline books:', sacred_books.index_into_db())")

# 5. Install systemd user service for automatic boot
cat > "$HOME/.config/systemd/user/torah-sanctuary.service" << EOF
[Unit]
Description=Torah Sanctuary / ShulOS Web & Study Station (Port 8080)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now torah-sanctuary.service

echo "✅ ShulOS is LIVE at http://127.0.0.1:8080"
echo "🌐 Open http://127.0.0.1:8080/?view=mesh to link with sister Synagogues & Chabad Houses over Tailscale!"
