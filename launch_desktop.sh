#!/usr/bin/env bash
# launch_desktop.sh - Desktop launcher for Fedora Remote Cursor
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON="$DIR/static/icon-512.png"
APP_NAME="Fedora Remote Cursor"

# Helper to find current active IPs
get_ips() {
    TS_IP=$(tailscale ip -4 2>/dev/null || ip -4 -o addr show tailscale0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
    HOTSPOT_IP=$(ip -4 -o addr show wlp3s0 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
    LAN_IP=$(ip -4 -o addr show enp0s31f6 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
    DEF_IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{print $7}')
}

# Check if server is currently running
PID=$(pgrep -f "python3.*server\.py" || true)

if [ -n "$PID" ]; then
    get_ips
    
    # Build URL info list
    MSG="✅ <b>Fedora Remote Trackpad is currently running!</b> (PID: $PID)\n\n"
    MSG+="Connect from your phone browser:\n"
    [ -n "$TS_IP" ] && MSG+="• <b>Tailscale:</b> <a href=\"https://${TS_IP}:8080\">https://${TS_IP}:8080</a>\n"
    [ -n "$HOTSPOT_IP" ] && MSG+="• <b>Hotspot:</b> <a href=\"https://${HOTSPOT_IP}:8080\">https://${HOTSPOT_IP}:8080</a>\n"
    [ -n "$LAN_IP" ] && MSG+="• <b>Local Wi-Fi/LAN:</b> <a href=\"https://${LAN_IP}:8080\">https://${LAN_IP}:8080</a>\n"
    MSG+="• <b>Localhost:</b> https://localhost:8080\n\n"
    MSG+="<i>What would you like to do?</i>"

    ACTION=$(zenity --question \
        --title="$APP_NAME" \
        --window-icon="$ICON" \
        --text="$MSG" \
        --ok-label="Keep Running" \
        --cancel-label="Stop Server" \
        --extra-button="Open in Browser" \
        --width=450 2>/dev/null || true)
    STATUS=$?

    if [ "$ACTION" = "Open in Browser" ]; then
        xdg-open "https://localhost:8080" >/dev/null 2>&1 &
    elif [ $STATUS -eq 1 ]; then
        # Cancel label was clicked ("Stop Server")
        kill "$PID" 2>/dev/null || true
        notify-send -i "$ICON" -u normal "$APP_NAME" "Server stopped successfully."
    fi
    exit 0
fi

# Server is not running -> Start it
notify-send -i "$ICON" -u low "$APP_NAME" "Starting remote trackpad server..."

# Launch via run.sh in the background
nohup "$DIR/run.sh" > "$DIR/server.log" 2>&1 &
NEW_PID=$!

# Wait up to 3 seconds for port 8080 to become available
STARTED=0
for i in {1..6}; do
    sleep 0.5
    if pgrep -f "python3.*server\.py" >/dev/null 2>&1; then
        STARTED=1
        break
    fi
done

if [ $STARTED -eq 1 ]; then
    get_ips
    
    NOTIF_MSG="Ready to connect!\n"
    [ -n "$TS_IP" ] && NOTIF_MSG+="📱 Tailscale: https://${TS_IP}:8080\n"
    [ -n "$HOTSPOT_IP" ] && NOTIF_MSG+="📶 Hotspot: https://${HOTSPOT_IP}:8080\n"
    [ -z "$HOTSPOT_IP" ] && [ -n "$LAN_IP" ] && NOTIF_MSG+="📶 Wi-Fi: https://${LAN_IP}:8080\n"
    
    notify-send -i "$ICON" -u normal "$APP_NAME Active" "$NOTIF_MSG"

    DIALOG_MSG="🚀 <b>Fedora Remote Trackpad is now running!</b>\n\n"
    DIALOG_MSG+="Open this link on your phone:\n\n"
    [ -n "$TS_IP" ] && DIALOG_MSG+="📱 <b>Tailscale:</b> <a href=\"https://${TS_IP}:8080\">https://${TS_IP}:8080</a>\n"
    [ -n "$HOTSPOT_IP" ] && DIALOG_MSG+="📶 <b>Hotspot:</b> <a href=\"https://${HOTSPOT_IP}:8080\">https://${HOTSPOT_IP}:8080</a>\n"
    [ -n "$LAN_IP" ] && DIALOG_MSG+="🌐 <b>Local Wi-Fi/LAN:</b> <a href=\"https://${LAN_IP}:8080\">https://${LAN_IP}:8080</a>\n\n"
    DIALOG_MSG+="<i>Tip: Click this desktop icon again anytime to stop or check status!</i>"

    CHOICE=$(zenity --info \
        --title="$APP_NAME" \
        --window-icon="$ICON" \
        --text="$DIALOG_MSG" \
        --ok-label="Done" \
        --extra-button="Open in Browser" \
        --width=450 2>/dev/null || true)
    
    if [ "$CHOICE" = "Open in Browser" ]; then
        xdg-open "https://localhost:8080" >/dev/null 2>&1 &
    fi
else
    ERR=$(tail -n 8 "$DIR/server.log" 2>/dev/null || echo "Unknown error")
    notify-send -i "$ICON" -u critical "$APP_NAME Error" "Failed to start server.\nCheck server.log"
    zenity --error \
        --title="$APP_NAME Failed to Start" \
        --window-icon="$ICON" \
        --text="⚠️ <b>Failed to start server:</b>\n\n<tt>${ERR}</tt>" \
        --width=450 2>/dev/null || true
fi
