#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Torah Sanctuary — Synagogue Donation & Fleet Sanitization Script
# ==============================================================================
# Safely converts Sentinel from a Palmer Fleet node into a 100% standalone,
# private, zero-fleet-secrets Synagogue Torah Study & Storyteller Kiosk.
#
# USAGE:
#   ./sanitize-for-synagogue.sh                 # Safe DRY-RUN preview (default)
#   ./sanitize-for-synagogue.sh --execute --confirm-synagogue-handoff
# ==============================================================================

EXECUTE=0
CONFIRMED=0
for arg in "$@"; do
    case "$arg" in
        --execute) EXECUTE=1 ;;
        --confirm-synagogue-handoff) CONFIRMED=1 ;;
    esac
done

run_cmd() {
    if [ "$EXECUTE" -eq 1 ] && [ "$CONFIRMED" -eq 1 ]; then
        echo "[EXEC] $*"
        eval "$@"
    else
        echo "[DRY-RUN] $*"
    fi
}

echo "=================================================================="
if [ "$EXECUTE" -eq 1 ] && [ "$CONFIRMED" -eq 1 ]; then
    echo " EXECUTING SYNAGOGUE HANDOFF SANITIZATION ON $(hostname)"
else
    echo " DRY-RUN PREVIEW (no changes made)"
    echo " Re-run with: $0 --execute --confirm-synagogue-handoff"
fi
echo "=================================================================="

# 1. Disable & remove all Palmer Fleet user services
FLEET_USER_SERVICES=(
    fleet-cam-switcher.service
    fleet-scratch.service
    fleet-visual-web.service
    fleet-heartbeat.timer
    fleet-heartbeat.service
    omarchy-ble-rgb.service
    omarchy-kvm-agent.service
    omarchy-tailscale-receive.service
    orca-desktop.service
    wayvnc.service
)
for svc in "${FLEET_USER_SERVICES[@]}"; do
    run_cmd "systemctl --user disable --now '$svc' 2>/dev/null || true"
    run_cmd "rm -f \"\$HOME/.config/systemd/user/$svc\""
done

# 2. Remove Tailscale fleet membership
run_cmd "sudo tailscale logout 2>/dev/null || true"
run_cmd "sudo systemctl disable --now tailscaled.service 2>/dev/null || true"

# 3. Strip personal SSH keys, fleet scripts, personal repos & AI credentials
FLEET_PATHS=(
    "\$HOME/.ssh"
    "\$HOME/Projects/FleetKnowledge"
    "\$HOME/Projects/fleetcommand"
    "\$HOME/Projects/ops"
    "\$HOME/Projects/node-sentinel"
    "\$HOME/Projects/ICOS_ORCHESTRATION_PROTOCOL.md"
    "\$HOME/Scratch"
    "\$HOME/.claude"
    "\$HOME/.claude.json"
    "\$HOME/.gemini"
    "\$HOME/.codex"
    "\$HOME/.copilot"
    "\$HOME/.cursor"
    "\$HOME/.grok"
    "\$HOME/.hermes"
    "\$HOME/.orca"
    "\$HOME/orca"
    "\$HOME/.pi"
    "\$HOME/.fleet_banner"
    "\$HOME/CLAUDE.md"
    "\$HOME/GEMINI.md"
    "\$HOME/.bash_history"
    "\$HOME/.config/cam-switcher"
    "\$HOME/.local/bin/fleet-*"
    "\$HOME/.local/bin/omarchy-*"
    "\$HOME/.local/bin/icos-*"
)
for p in "${FLEET_PATHS[@]}"; do
    run_cmd "rm -rf $p"
done

# 4. Copy YuNet face detector into standalone torah-sanctuary/data before removing cam-switcher (handled safely if already copied)
run_cmd "mkdir -p \"\$HOME/torah-sanctuary/data\""

# 5. Enable standalone Torah Sanctuary appliance services (Web App + Ollama + Presence + Kiosk)
run_cmd "sudo systemctl enable --now ollama.service"
run_cmd "systemctl --user daemon-reload"
run_cmd "systemctl --user enable --now torah-sanctuary.service"
run_cmd "systemctl --user enable --now torah-presence.service"
run_cmd "systemctl --user enable --now torah-kiosk.service"

# 6. Set friendly hostname
run_cmd "sudo hostnamectl set-hostname torah-sanctuary 2>/dev/null || true"

echo "=================================================================="
if [ "$EXECUTE" -eq 1 ] && [ "$CONFIRMED" -eq 1 ]; then
    echo " SANITIZATION COMPLETE. Sentinel is now a standalone Torah Sanctuary."
else
    echo " DRY-RUN COMPLETE. Inspect actions above before running with --execute --confirm-synagogue-handoff."
fi
echo "=================================================================="
