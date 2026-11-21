#!/usr/bin/env bash
# Torah Sanctuary OS — 1-Command Turnkey Installer (Arch / Omarchy / Debian / Ubuntu)
# Usage:
#   ./install.sh --synagogue "The European Synagogue" --city brussels
#   ./install.sh --synagogue "Congregation Beth El" --city new_york --no-kiosk
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${TORAH_INSTALL_DIR:-$HOME/torah-sanctuary}"
SYNAGOGUE_NAME="Torah Sanctuary · Synagogue Study Station"
CITY_KEY="brussels"
ENABLE_KIOSK=1
ENABLE_VOICE=1
ENABLE_OLLAMA=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --synagogue) SYNAGOGUE_NAME="$2"; shift 2 ;;
    --city) CITY_KEY="$2"; shift 2 ;;
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    --no-kiosk) ENABLE_KIOSK=0; shift ;;
    --no-voice) ENABLE_VOICE=0; shift ;;
    --no-ollama) ENABLE_OLLAMA=0; shift ;;
    -h|--help)
      echo "Usage: $0 [--synagogue NAME] [--city brussels|antwerp|jerusalem|tel_aviv|london|paris|new_york|miami|los_angeles] [--dir PATH] [--no-kiosk] [--no-voice] [--no-ollama]"
      exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "✡ Installing Torah Sanctuary OS into $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR" "$HOME/.local/bin" "$HOME/.config/systemd/user"

# 1. Copy application files (preserving existing data/ and voice/ if re-running)
if [[ "$SRC_DIR" != "$INSTALL_DIR" ]]; then
  tar -C "$SRC_DIR" --exclude='.git' --exclude='__pycache__' --exclude='config.json' --exclude='data/kiosk-profile' -cf - . | tar -C "$INSTALL_DIR" -xf -
fi
chmod +x "$INSTALL_DIR"/server.py "$INSTALL_DIR"/sacred_astronomy.py "$INSTALL_DIR"/sacred-os-daemon.py \
         "$INSTALL_DIR"/torah-ctl "$INSTALL_DIR"/torah-mcp "$INSTALL_DIR"/torah-motd "$INSTALL_DIR"/torah-presence.py \
         "$INSTALL_DIR"/ingest_corpus.py "$INSTALL_DIR"/seed_knowledge.py "$INSTALL_DIR"/scripts/*.sh 2>/dev/null || true

# 2. Install base OS dependencies (Arch / Omarchy or Debian / Ubuntu)
if command -v pacman >/dev/null 2>&1; then
  MISSING=()
  for pkg in python sqlite ffmpeg chromium ollama; do
    pacman -Qi "$pkg" >/dev/null 2>&1 || MISSING+=("$pkg")
  done
  if (( ${#MISSING[@]} > 0 )) && sudo -n true 2>/dev/null; then
    echo "Installing Arch packages: ${MISSING[*]}"
    sudo pacman -S --noconfirm --needed "${MISSING[@]}" || true
  fi
elif command -v apt-get >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y python3 sqlite3 ffmpeg curl || true
fi

# 3. Auto-select Ollama model by RAM
RAM_GB=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 8)
OLLAMA_MODEL="qwen2.5:1.5b"
if (( RAM_GB >= 24 )); then
  OLLAMA_MODEL="qwen2.5:3b"
elif (( RAM_GB >= 14 )); then
  OLLAMA_MODEL="qwen2.5:3b"
fi
echo "Detected ${RAM_GB} GB RAM -> local AI model: ${OLLAMA_MODEL}"

# 4. Write config.json cleanly if absent (or update synagogue/location)
python3 - "$INSTALL_DIR" "$SYNAGOGUE_NAME" "$CITY_KEY" "$OLLAMA_MODEL" <<'PY'
import json, sys
from pathlib import Path
idir, syn_name, city_key, model = sys.argv[1:5]
sys.path.insert(0, idir)
import sacred_astronomy as sa

cfg_p = Path(idir) / "config.json"
cfg = json.loads((Path(idir) / "config.example.json").read_text(encoding="utf-8"))
if cfg_p.exists():
    try:
        cfg.update(json.loads(cfg_p.read_text(encoding="utf-8")))
    except Exception:
        pass
cfg["synagogue_name"] = syn_name
cfg["ollama_model"] = model
if city_key.lower() in sa.CITY_PRESETS:
    cfg["location"] = sa.CITY_PRESETS[city_key.lower()]
cfg_p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
cfg_p.chmod(0o600)
print("Configured:", cfg["synagogue_name"], "| Location:", cfg["location"]["city"])
PY

# 5. Build 100% offline Tanakh + Classical Commentaries DB if missing
if [[ ! -s "$INSTALL_DIR/data/torah.db" ]]; then
  echo "Building offline Tanakh, Rashi, Ramban, Ibn Ezra, Sforno & Midrash database (one-time)..."
  python3 "$INSTALL_DIR/ingest_corpus.py"
  python3 "$INSTALL_DIR/seed_knowledge.py"
fi

# 6. Install local Piper neural voice (en_US-ryan-high warm natural baritone) if requested
if (( ENABLE_VOICE == 1 )); then
  mkdir -p "$INSTALL_DIR/voice/piper" "$INSTALL_DIR/voice/models"
  if [[ ! -x "$INSTALL_DIR/voice/piper/piper" ]]; then
    echo "Downloading Piper offline neural TTS..."
    curl -fsSL "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz" | tar -C "$INSTALL_DIR/voice" -xzf - || true
  fi
  if [[ ! -s "$INSTALL_DIR/voice/models/en_US-ryan-high.onnx" ]]; then
    echo "Downloading warm baritone narrator voice model (en_US-ryan-high)..."
    curl -fsSL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx" -o "$INSTALL_DIR/voice/models/en_US-ryan-high.onnx" || true
    curl -fsSL "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json" -o "$INSTALL_DIR/voice/models/en_US-ryan-high.onnx.json" || true
  fi
fi

# 7. Enable Ollama & pull local model
if (( ENABLE_OLLAMA == 1 )) && command -v ollama >/dev/null 2>&1; then
  sudo -n systemctl enable --now ollama.service 2>/dev/null || true
  sleep 1
  if ! ollama list 2>/dev/null | grep -q "${OLLAMA_MODEL}"; then
    echo "Pulling local offline AI model ${OLLAMA_MODEL}..."
    ollama pull "${OLLAMA_MODEL}" || true
  fi
fi

# 8. Symlink CLI, MCP server & Sacred MOTD
ln -sf "$INSTALL_DIR/torah-ctl" "$HOME/.local/bin/torah-ctl"
ln -sf "$INSTALL_DIR/torah-mcp" "$HOME/.local/bin/torah-mcp"
ln -sf "$INSTALL_DIR/torah-motd" "$HOME/.local/bin/torah-motd"

# Hook Sacred MOTD into interactive bash shells (idempotent)
if [[ -f "$HOME/.bashrc" ]] && ! grep -q "torah-motd" "$HOME/.bashrc"; then
  printf '\n# Torah Sanctuary OS — Sacred Celestial & Hebrew Calendar Greeting\n[[ $- == *i* ]] && command -v torah-motd >/dev/null 2>&1 && torah-motd\n' >> "$HOME/.bashrc"
fi

# 9. Install & enable systemd user units
cp "$INSTALL_DIR/systemd/torah-sanctuary.service" "$HOME/.config/systemd/user/"
cp "$INSTALL_DIR/systemd/torah-celestial.service" "$HOME/.config/systemd/user/"
cp "$INSTALL_DIR/systemd/torah-celestial.timer" "$HOME/.config/systemd/user/"
cp "$INSTALL_DIR/systemd/torah-scribe.service" "$HOME/.config/systemd/user/"
cp "$INSTALL_DIR/systemd/torah-scribe.timer" "$HOME/.config/systemd/user/"
if (( ENABLE_KIOSK == 1 )); then
  cp "$INSTALL_DIR/systemd/torah-kiosk.service" "$HOME/.config/systemd/user/"
fi
systemctl --user daemon-reload
systemctl --user enable torah-sanctuary.service
systemctl --user restart torah-sanctuary.service
systemctl --user enable --now torah-celestial.timer
systemctl --user enable --now torah-scribe.timer
python3 "$INSTALL_DIR/sacred-os-daemon.py" --quiet || true

# Gentle comfortable speaker volume (42%)
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.42 2>/dev/null || true

echo ""
"$HOME/.local/bin/torah-motd" || true
echo "✅ Torah Sanctuary OS is LIVE at http://127.0.0.1:8080"
