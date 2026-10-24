# 🖱️ Linux Remote Trackpad & Controller

Turn any smartphone (Samsung Galaxy, Android, iPhone, iPad) into a low-latency, high-performance wireless trackpad, keyboard, and media controller for your Linux computer.

Works seamlessly on **Fedora, Ubuntu, Debian, Arch Linux, Pop!_OS, Linux Mint, openSUSE**, and any modern distribution running **Wayland** or **X11**.

---

## ✨ Features

- **Zero Mobile App Installation**: Runs directly in mobile Chrome, Samsung Internet, or Safari via modern WebSockets.
- **Wayland & X11 Native**: Directly creates kernel-level virtual input devices through `/dev/uinput` (no X11 hacks or Wayland security permission hurdles).
- **Ultra-low Latency**: Sub-5ms input response time over local Wi-Fi, Hotspot, or Tailscale.
- **Full Multi-Touch Gestures**:
  - **1 Finger Move**: Fluid mouse movement with dynamic pointer acceleration.
  - **1 Finger Tap**: Left click.
  - **Double-Tap & Hold**: Drag selection / window move lock.
  - **2 Fingers Tap**: Right click.
  - **2 Fingers Drag**: Smooth bi-directional scrolling (with Natural Scrolling toggle).
  - **3 Fingers Tap**: Middle click (open links in new tab, Linux primary selection paste).
  - **Right Edge Rail**: 1-finger fast scrolling zone.
  - **Physical Button Bar**: Dedicated Left, Middle, and Right click buttons.
- **📺 Live Screen Picture-in-Picture (PiP)**:
  - **Monitor from anywhere**: Floating mini-view of your laptop screen right inside the trackpad.
  - **Hardware WebP Compression**: Employs real-time WebP encoding generating ~10–25 KB frames (over 80% lighter than standard video streams), keeping phone CPU and battery usage near zero.
  - **Motion Deduplication**: Automatically skips redundant frames when the screen is static, dropping idle network bandwidth to near 0 KB/s.
  - **Eco / Balanced / HD Switcher**: Switch between **ECO** (6 fps · 10 KB), **BALANCED** (10 fps · 18 KB), and **HD** (15 fps · 35 KB).
  - **Snap-to-Center Dragging**: Drag the PiP window anywhere or double-tap to snap it dead center.
  - **Android System PiP**: Pop the screen preview out into a native OS picture-in-picture window that floats above all other phone apps.
- **🔊 Audio & Bluetooth Sound System Control**:
  - **Now Playing**: Live song/video metadata (title, artist, album art) from Spotify, YouTube, Netflix, browsers, and media players.
  - **PulseAudio / PipeWire Volume**: 0%–100% volume slider with one-tap instant mute.
  - **Audio Sink Switcher**: Switch instantly between Bluetooth speakers, internal speakers, and headphones.
  - **Push-to-Talk Wireless Megaphone**: Hold the mic button on your phone to broadcast your voice live through your laptop speakers!
  - **Subwoofer SFX Soundboard**: Instant sound effects (808 Sub-bass drop, DJ Airhorn, Impact Boom, Applause, Laser).
  - **Fade-Out Sleep Timer**: Automated volume ramp-down that pauses playback when you fall asleep.
- **⌨️ Keyboard & Search Input**:
  - Dedicated search and text input drawer with Enter / Search submission.
  - Bypasses mobile browser autofill and password manager popups.
- **📷 Phone Screenshot & Image Pasting**:
  - Paste any screenshot taken on your phone directly into the laptop's Wayland or X11 clipboard (`wl-copy` / `xclip`) and automatically simulate `Ctrl+V`.
  - Built-in OCR: Extract text from uploaded screenshots with one tap.
- **📲 Progressive Web App (PWA)**:
  - Install to your phone's home screen for a bezel-to-bezel, full-screen standalone trackpad experience.
  - Multi-Endpoint IP Manager: Automatically switches between Tailscale, Wi-Fi Hotspot, and LAN Wi-Fi.

---

## 🐧 OS & Distribution Compatibility

This application is built on Linux kernel standards (`/dev/uinput`, `evdev`, `PipeWire`/`PulseAudio`, and `systemd`) and works across all major distributions:

| Distribution | Input & Mouse | Audio & Volume | PiP Screen View | Image Paste |
| :--- | :---: | :---: | :---: | :---: |
| **Fedora Workstation** (38, 39, 40, 41) | ✅ Kernel `/dev/uinput` | ✅ PipeWire | ✅ Native GNOME Mutter | ✅ `wl-copy` |
| **Ubuntu Desktop** (22.04, 24.04 LTS) | ✅ Kernel `/dev/uinput` | ✅ PipeWire | ✅ Native GNOME Mutter | ✅ `wl-copy` |
| **Debian** (11 Bullseye, 12 Bookworm) | ✅ Kernel `/dev/uinput` | ✅ PipeWire / Pulse | ✅ Native GNOME Mutter | ✅ `wl-copy` |
| **Arch Linux / Manjaro / Endeavour** | ✅ Kernel `/dev/uinput` | ✅ PipeWire | ✅ Native GNOME Mutter | ✅ `wl-copy` |
| **Pop!_OS** (22.04 LTS) | ✅ Kernel `/dev/uinput` | ✅ PipeWire | ✅ Native GNOME Mutter | ✅ `wl-copy` |
| **Linux Mint** (Cinnamon / XFCE / MATE)| ✅ Kernel `/dev/uinput` | ✅ PulseAudio | ✅ Fallback preview | ✅ `xclip` |
| **openSUSE** (Tumbleweed / Leap) | ✅ Kernel `/dev/uinput` | ✅ PipeWire | ✅ Native GNOME Mutter | ✅ `wl-copy` |

---

## 📦 Installation & Setup by Operating System

### 1. Fedora / RHEL / CentOS Stream

```bash
# 1. Install dependencies
sudo dnf install -y python3 python3-pip openssl playerctl gstreamer1-plugins-bad-free wl-clipboard

# 2. Clone repository & navigate into folder
git clone https://github.com/Entropychaos880/Fedora-remote-.git
cd Fedora-remote-

# 3. Configure uinput permissions & firewall (one-time setup)
sudo ./setup_uinput.sh

# 4. Optional: Install Desktop shortcut & App Drawer icon
./install_desktop_app.sh
```

---

### 2. Ubuntu / Debian / Linux Mint / Pop!_OS

```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv openssl playerctl gstreamer1.0-plugins-bad wl-clipboard xclip zenity

# 2. Clone repository & navigate into folder
git clone https://github.com/Entropychaos880/Fedora-remote-.git
cd Fedora-remote-

# 3. Configure uinput permissions & firewall (one-time setup)
sudo ./setup_uinput.sh

# 4. Optional: Install Desktop shortcut & App Drawer icon
./install_desktop_app.sh
```

---

### 3. Arch Linux / Manjaro / EndeavourOS

```bash
# 1. Install dependencies
sudo pacman -S --needed python python-pip openssl playerctl gst-plugins-bad wl-clipboard xclip zenity

# 2. Clone repository & navigate into folder
git clone https://github.com/Entropychaos880/Fedora-remote-.git
cd Fedora-remote-

# 3. Configure uinput permissions (one-time setup)
sudo ./setup_uinput.sh

# 4. Optional: Install Desktop shortcut & App Drawer icon
./install_desktop_app.sh
```

---

### 4. openSUSE (Tumbleweed & Leap)

```bash
# 1. Install dependencies
sudo zypper install -y python3 python3-pip openssl playerctl gstreamer-plugins-bad wl-clipboard zenity

# 2. Clone repository & navigate into folder
git clone https://github.com/Entropychaos880/Fedora-remote-.git
cd Fedora-remote-

# 3. Configure uinput permissions & firewall (one-time setup)
sudo ./setup_uinput.sh

# 4. Optional: Install Desktop shortcut & App Drawer icon
./install_desktop_app.sh
```

---

## 🚀 Running the Controller

### Option A: 1-Click Desktop App (Recommended)
If you ran `./install_desktop_app.sh`:
- Click the **Fedora Remote Cursor** icon on your **Desktop** or in your system **App Drawer / Dash**.
- A desktop notification will pop up showing the connection link and QR code.
- Click the icon again anytime for a menu to stop the server or view status!

### Option B: Terminal / CLI
```bash
./run.sh
```

*(Tip: To run over plain HTTP instead of HTTPS, pass `./run.sh --http`).*

### Option C: Auto-Start on System Boot (Systemd)
To start the remote controller in the background every time you log in:
```bash
systemctl --user enable --now fedora-remote-controller.service
```

---

## 📱 Connecting from your Phone

1. **Ensure your phone is on the same connection as your laptop**:
   - **Local Wi-Fi Hotspot** (e.g. `10.42.0.1`): Turn on your laptop's Wi-Fi hotspot and connect your phone to it.
   - **Local Home / Office Wi-Fi** (e.g. `192.168.x.x`): Both devices connected to the same Wi-Fi router.
   - **Tailscale VPN** (e.g. `100.x.x.x`): Access your laptop securely from anywhere in the world across different networks.

2. **Open the URL in your phone's browser**:
   - Scan the terminal QR code or navigate to:
     ```text
     https://<YOUR-LAPTOP-IP>:8080
     ```

3. **Accept the Local Self-Signed Certificate**:
   - Because this certificate is generated on your machine for private local communication, your browser will display: *"Your connection is not private"*.
   - Tap **Advanced** (or *Details / More options*) → Tap **Proceed to <IP> (unsafe)**.

4. **Install as a Mobile App (PWA)**:
   - **Android (Chrome / Samsung Internet)**: Tap the **Settings (⚙️)** gear in the app and tap **"Install App"** (or use browser menu ⋮ → *"Install app"* / *"Add to Home screen"*).
   - **iOS (Safari)**: Tap the **Share** button (box with arrow) → Select **"Add to Home Screen"**.

---

## 🎛️ Gestures & Controls Cheat Sheet

| Gesture | Action |
| :--- | :--- |
| **1 Finger Move** | Move mouse cursor (with dynamic acceleration) |
| **1 Finger Tap** | Left Click |
| **Double-Tap & Hold** | Lock drag selection (moving windows, highlighting text) |
| **2 Fingers Tap** | Right Click |
| **2 Fingers Drag** | Smooth vertical & horizontal scrolling (Natural scrolling toggle) |
| **3 Fingers Tap** | Middle Click (open links in new tab, paste primary buffer) |
| **3 Fingers Swipe UP** | **Activities Overview** (Swipe up again for full **App Grid**) |
| **3 Fingers Swipe DOWN** | **Close Overview** / Return to Desktop |
| **3 Fingers Swipe LEFT** | **Next Workspace** |
| **3 Fingers Swipe RIGHT** | **Previous Workspace** |
| **Right Rail Drag** | Dedicated one-finger fast scroll strip |
| **Double-Tap PiP Header** | Instantly re-center the Picture-in-Picture window |

---

## ⚙️ Settings Customization

Tap the **Settings gear icon (⚙️)** in the top right of the mobile interface to tune:
- **Pointer Sensitivity**: Scale from `0.5x` to `3.0x`.
- **Dynamic Pointer Acceleration**: Smooth low-speed precision with fast flick speed.
- **Scroll Speed & Direction**: Standard vs Natural Scrolling toggle.
- **Haptic Touch Feedback**: Enable/disable vibration pulses.
- **Connection Manager**: Switch or inspect active fallback IP endpoints.

---

## 🔧 Troubleshooting

### 1. `/dev/uinput` Permission Denied
If the server outputs `Permission denied: '/dev/uinput'`:
```bash
sudo ./setup_uinput.sh
```
Then log out and log back in, or run `sg input -c "./run.sh"` to immediately reload group permissions.

### 2. Firewall Blocking Connection
If your phone cannot load the page, verify port 8080 is open:
- **Fedora / openSUSE (`firewalld`)**:
  ```bash
  sudo firewall-cmd --permanent --add-port=8080/tcp && sudo firewall-cmd --reload
  ```
- **Ubuntu / Debian / Mint (`ufw`)**:
  ```bash
  sudo ufw allow 8080/tcp
  ```

### 3. Screen Preview (PiP) Not Streaming
- Ensure GStreamer plugins are installed:
  - Fedora: `sudo dnf install gstreamer1-plugins-bad-free`
  - Ubuntu/Debian: `sudo apt install gstreamer1.0-plugins-bad`
  - Arch: `sudo pacman -S gst-plugins-bad`
- On GNOME Wayland, the Mutter ScreenCast API will activate automatically with hardware cursor overlay.

---

## 📄 License

MIT License. Free and open source for personal and commercial use.
