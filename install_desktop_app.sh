#!/usr/bin/env bash
# install_desktop_app.sh - Install desktop shortcut, app drawer icon, and systemd service
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON="$DIR/static/icon-512.png"

echo "📦 Installing Fedora Remote Cursor Desktop Integration..."

# 1. Ensure user directories exist
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/Desktop"
mkdir -p "$HOME/.config/systemd/user"
mkdir -p "$HOME/.local/share/icons/hicolor/512x512/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/192x192/apps"

# 2. Copy icons
cp "$DIR/static/icon-512.png" "$HOME/.local/share/icons/hicolor/512x512/apps/fedora-remote-controller.png"
cp "$DIR/static/icon-192.png" "$HOME/.local/share/icons/hicolor/192x192/apps/fedora-remote-controller.png"
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

# 3. Install to Applications Menu (App Drawer & Dash)
cp "$DIR/fedora-remote-controller.desktop" "$HOME/.local/share/applications/fedora-remote-controller.desktop"
chmod +x "$HOME/.local/share/applications/fedora-remote-controller.desktop"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

# 4. Install to Desktop
cp "$DIR/fedora-remote-controller.desktop" "$HOME/Desktop/Fedora-Remote-Controller.desktop"
chmod +x "$HOME/Desktop/Fedora-Remote-Controller.desktop"
gio set "$HOME/Desktop/Fedora-Remote-Controller.desktop" metadata::trusted true 2>/dev/null || true

# 5. Install systemd user service
cp "$DIR/fedora-remote-controller.service" "$HOME/.config/systemd/user/fedora-remote-controller.service"
systemctl --user daemon-reload

echo "✅ Desktop Integration Installed Successfully!"
echo "   • Applications Menu / Dash: Fedora Remote Cursor"
echo "   • Desktop Icon: ~/Desktop/Fedora-Remote-Controller.desktop"
echo "   • Optional Auto-start: systemctl --user enable fedora-remote-controller"

notify-send -i "$DIR/static/icon-192.png" "Fedora Remote Cursor" "Desktop app installed! You can now launch it from your desktop or app menu."
