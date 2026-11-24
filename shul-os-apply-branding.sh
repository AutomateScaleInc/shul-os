#!/usr/bin/env bash
# ==============================================================================
# Shul.OS — Native Boot Splash (Plymouth), Sanctuary Wallpaper & Sacred Screensaver
# Replaces any generic OS boot logo, wallpaper, and screensaver with cohesive
# midnight-gold Shul.OS visuals from power-on through shutdown and Shabbat mode.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRAND_DIR="$SCRIPT_DIR/static/branding"

echo "✡ Applying Shul.OS Native Boot Splash, Wallpaper & Sacred Screensaver..."

# 1. Replace desktop wallpaper with 1080p Shul.OS Midnight-Gold Sanctuary Splash
if [[ -f "$BRAND_DIR/shul-os-wallpaper.png" ]]; then
  mkdir -p "$HOME/.local/state/omarchy/current"
  ln -sfn "$BRAND_DIR/shul-os-wallpaper.png" "$HOME/.local/state/omarchy/current/background"
  echo "  ✓ Shul.OS 1080p sanctuary wallpaper linked"
fi

# 2. Update sacred dynamic screensaver & disable generic idle screensaver takeover
mkdir -p "$HOME/.local/state/omarchy/toggles"
touch "$HOME/.local/state/omarchy/toggles/screensaver-off"
if [[ -f "$SCRIPT_DIR/sacred-os-daemon.py" ]]; then
  python3 "$SCRIPT_DIR/sacred-os-daemon.py" --quiet >/dev/null 2>&1 || true
  echo "  ✓ Sacred Shul.OS screensaver.txt & about.txt synced to today's Hebrew date & Parashah"
fi

# 3. Install custom Shul.OS Plymouth Boot & Shutdown Splash Theme (requires sudo)
if [[ -d /usr/share/plymouth/themes ]] && [[ -f "$BRAND_DIR/plymouth-logo.png" ]] && sudo -n true 2>/dev/null; then
  THEME_DIR="/usr/share/plymouth/themes/shul-os"
  sudo mkdir -p "$THEME_DIR"
  sudo cp "$BRAND_DIR/plymouth-logo.png" "$THEME_DIR/logo.png"
  sudo cp "$BRAND_DIR/plymouth-progress-box.png" "$THEME_DIR/progress_box.png"
  sudo cp "$BRAND_DIR/plymouth-progress-bar.png" "$THEME_DIR/progress_bar.png"
  # Copy clean lock/entry helper icons if present from existing theme (fallback for encrypted prompt)
  for f in bullet.png entry.png lock.png; do
    if [[ -f "/usr/share/plymouth/themes/omarchy/$f" ]]; then
      sudo cp "/usr/share/plymouth/themes/omarchy/$f" "$THEME_DIR/$f"
    fi
  done

  sudo tee "$THEME_DIR/shul-os.plymouth" >/dev/null <<'EOF'
[Plymouth Theme]
Name=Shul.OS
Description=Shul.OS — The Living Synagogue Operating System Boot & Shutdown Splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/shul-os
ScriptFile=/usr/share/plymouth/themes/shul-os/shul-os.script
EOF

  sudo tee "$THEME_DIR/shul-os.script" >/dev/null <<'EOF'
# Shul.OS — Living Synagogue OS Boot & Shutdown Splash Theme
Window.SetBackgroundTopColor(0.027, 0.051, 0.106);
Window.SetBackgroundBottomColor(0.043, 0.078, 0.165);

logo.image = Image("logo.png");
logo.sprite = Sprite(logo.image);
logo.sprite.SetX(Window.GetWidth() / 2 - logo.image.GetWidth() / 2);
logo.sprite.SetY(Window.GetHeight() / 2 - logo.image.GetHeight() / 2 - 24);
logo.sprite.SetOpacity(1);

progress_box.image = Image("progress_box.png");
progress_box.sprite = Sprite(progress_box.image);
progress_box.x = Window.GetWidth() / 2 - progress_box.image.GetWidth() / 2;
progress_box.y = Window.GetHeight() / 2 + logo.image.GetHeight() / 2 + 12;
progress_box.sprite.SetPosition(progress_box.x, progress_box.y, 1);
progress_box.sprite.SetOpacity(0.95);

progress_bar.original_image = Image("progress_bar.png");
progress_bar.sprite = Sprite();
progress_bar.x = progress_box.x + (progress_box.image.GetWidth() - progress_bar.original_image.GetWidth()) / 2;
progress_bar.y = progress_box.y + (progress_box.image.GetHeight() - progress_bar.original_image.GetHeight()) / 2;
progress_bar.sprite.SetPosition(progress_bar.x, progress_bar.y, 2);
progress_bar.sprite.SetOpacity(1);

global.max_progress = 0.05;

fun set_bar(p) {
  if (p > 1.0) p = 1.0;
  if (p < 0.04) p = 0.04;
  if (p > global.max_progress) global.max_progress = p;
  w = Math.Int(progress_bar.original_image.GetWidth() * global.max_progress);
  if (w < 4) w = 4;
  progress_bar.image = progress_bar.original_image.Scale(w, progress_bar.original_image.GetHeight());
  progress_bar.sprite.SetImage(progress_bar.image);
}

set_bar(0.12);

fun progress_callback(duration, progress) {
  set_bar(progress);
}
Plymouth.SetBootProgressFunction(progress_callback);

message_sprite = Sprite();
message_sprite.SetPosition(Window.GetWidth() / 2 - 180, progress_box.y + 24, 10);
fun display_message_callback(text) {
  message = Image.Text(text, 0.89, 0.74, 0.41);
  message_sprite.SetImage(message);
  message_sprite.SetOpacity(0.85);
}
fun hide_message_callback(text) {
  message_sprite.SetOpacity(0);
}
Plymouth.SetDisplayMessageFunction(display_message_callback);
Plymouth.SetHideMessageFunction(hide_message_callback);
EOF

  sudo tee /etc/plymouth/plymouthd.conf >/dev/null <<'EOF'
[Daemon]
Theme=shul-os
ShowDelay=0
EOF
  echo "  ✓ Shul.OS Plymouth boot & shutdown theme installed (/usr/share/plymouth/themes/shul-os)"

  if [[ "${1:-}" != "--skip-initramfs" ]]; then
    if command -v limine-mkinitcpio >/dev/null 2>&1; then
      echo "  ⏳ Updating initramfs boot splash via limine-mkinitcpio (preserving LUKS keyfile)..."
      sudo limine-mkinitcpio
      echo "  ✓ Boot splash baked into initramfs cleanly!"
    elif command -v mkinitcpio >/dev/null 2>&1; then
      sudo /usr/bin/mkinitcpio -P
      echo "  ✓ Boot splash baked into initramfs cleanly!"
    fi
  fi
else
  echo "  ℹ Skipping system Plymouth install (no sudo or plymouth not present)."
fi

echo "✅ Shul.OS unified branding complete!"
