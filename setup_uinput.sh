#!/usr/bin/env bash
# setup_uinput.sh - Configure Fedora permissions for /dev/uinput
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this setup script with sudo:"
  echo "    sudo ./setup_uinput.sh"
  exit 1
fi

echo "=================================================="
echo " Setting up /dev/uinput permissions for Fedora"
echo "=================================================="

# 1. Ensure uinput kernel module is loaded
modprobe uinput || true

# 2. Write udev rule with uaccess and input group support
cat << 'EOF' > /etc/udev/rules.d/99-uinput-trackpad.rules
# Enable access to /dev/uinput for active desktop user and input group
KERNEL=="uinput", SUBSYSTEM=="misc", TAG+="uaccess", OPTIONS+="static_node=uinput", MODE="0660", GROUP="input"
EOF

# 3. Add original user to input group
TARGET_USER="${SUDO_USER:-$USER}"
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
  echo "Adding user '$TARGET_USER' to 'input' group..."
  usermod -aG input "$TARGET_USER" || true
fi

# 4. Reload udev rules
udevadm control --reload-rules
udevadm trigger /dev/uinput 2>/dev/null || true

# 5. Immediately grant rw permissions to current session
chmod 0666 /dev/uinput

# 6. Open port 8080 in firewall (firewalld for Fedora/RHEL/openSUSE or ufw for Ubuntu/Debian/Mint)
if command -v firewall-cmd &>/dev/null && systemctl is-active --quiet firewalld 2>/dev/null; then
  echo "Opening port 8080 in firewalld..."
  firewall-cmd --permanent --zone=FedoraWorkstation --add-port=8080/tcp 2>/dev/null || true
  firewall-cmd --permanent --zone=nm-shared --add-port=8080/tcp 2>/dev/null || true
  firewall-cmd --permanent --add-port=8080/tcp 2>/dev/null || true
  firewall-cmd --reload 2>/dev/null || true
  echo "✓ Firewall port 8080 opened in firewalld."
elif command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -qw "active"; then
  echo "Opening port 8080 in ufw..."
  ufw allow 8080/tcp || true
  echo "✓ Firewall port 8080 opened in ufw."
fi

echo ""
echo "✓ Success! /dev/uinput is now accessible."
echo "You can now run the trackpad server as a normal user without sudo:"
echo "    ./run.sh"
echo "=================================================="
