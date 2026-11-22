#!/usr/bin/env bash
# Torah Sanctuary OS — 1-Command Node Cloner over SSH
# Clones this entire Holy Node (including pre-built offline Tanakh DB + 16 illuminated artworks)
# onto ANY target Linux / Omarchy computer in one command!
#
# Usage:
#   ./scripts/clone-to-node.sh user@new-imac --synagogue "The European Synagogue" --city brussels
#   ./scripts/clone-to-node.sh user@house-node --synagogue "Rabbi Michoel Home" --city brussels --follow-url https://live.theshul.eu
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <ssh-target> [--synagogue NAME] [--city brussels|jerusalem|new_york|...] [--follow-url URL] [--no-kiosk]"
  exit 1
fi

TARGET="$1"
shift
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "✡ Cloning Torah Sanctuary OS -> $TARGET ..."
tar -C "$REPO_DIR" --exclude='.git' --exclude='__pycache__' --exclude='config.json' --exclude='data/kiosk-profile' -czf - . \
  | ssh -o BatchMode=yes "$TARGET" "mkdir -p ~/torah-sanctuary && tar -C ~/torah-sanctuary -xzf -"

ARGS=""
if [[ $# -gt 0 ]]; then
  ARGS="$(printf '%q ' "$@")"
fi
echo "Running turnkey installer on $TARGET ..."
ssh -o BatchMode=yes "$TARGET" "cd ~/torah-sanctuary && chmod +x install.sh && ./install.sh --dir \$HOME/torah-sanctuary ${ARGS}"

echo "✅ Clone complete on $TARGET!"
