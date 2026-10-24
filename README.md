# 🖱️ Fedora Remote Trackpad for Samsung / Android

Turn your Samsung phone (or any mobile device) into a high-performance, low-latency wireless trackpad and keyboard controller for your Fedora laptop running **Wayland** or **X11**.

---

## ✨ Features

- **Zero Phone App Installation**: Open your Samsung browser or scan the terminal QR code.
- **Wayland Native**: Communicates directly through Linux `/dev/uinput` kernel virtual input, avoiding Wayland's security blocks.
- **Ultra-low Latency**: Sub-5ms response time over local Wi-Fi WebSockets.
- **Full Multi-Touch Gestures**:
  - **1 Finger Drag**: Move mouse cursor (with dynamic acceleration).
  - **1 Finger Tap**: Left click.
  - **Double-Tap & Hold**: Drag selection / window move lock.
  - **2 Fingers Tap**: Right click.
  - **2 Fingers Drag**: Smooth vertical & horizontal scrolling (supports Natural Scrolling).
  - **3 Fingers Tap**: Middle click (opens link in new tab, Linux clipboard paste).
- **Dedicated Scroll Rail**: One-finger fast scroll zone on the right edge.
- **Physical Style Buttons**: Left, middle, and right click zones at the bottom.
- **Live Screen Picture-in-Picture (PiP) with WebP Compression**:
  - **See from across the room**: Floating live mini-view of your laptop screen directly on your phone while using the trackpad!
  - **Hardware WebP Compression**: Employs real-time WebP encoding delivering tiny ~10–20 KB frames (over 80% smaller than standard video/JPEG), using almost zero bandwidth or phone battery.
  - **Motion Deduplication**: Automatically skips redundant frames when the laptop screen is static, dropping idle data transfer to near 0 KB/s.
  - **Eco / Balanced / HD Switcher**: Tap the header badge to cycle between **ECO** (6 fps · 10 KB/frame), **BALANCED** (10 fps · 18 KB/frame), and **HD** (15 fps · 35 KB/frame).
  - **Live Bandwidth Counter**: Real-time throughput meter directly in the PiP header showing actual data rate (e.g. `10 fps · 18 KB/s`).
  - **Embedded Real Cursor**: Watch your laptop mouse cursor move in real-time on your phone display.
  - **Draggable & Resizable**: Move the PiP window anywhere with your thumb; toggle between Mini corner thumbnail, Medium float, and Full wide view.
  - **System PiP Pop-out**: Supports native Android Picture-in-Picture window so your screen can float over other apps!
  - **Zero CPU Waste**: Screen capture runs only while PiP is toggled open and shuts down automatically when closed.
- **Sound System & Bluetooth Control (ECOMAX LX-500)**:
  - **Live Now Playing**: View song/video title, artist, and playback status from YouTube, Netflix, Spotify, or Brave/Firefox.
  - **PipeWire Volume Slider**: Precise 0% to 100% volume slider and instant mute toggle.
  - **Audio Output Switcher**: Instant one-tap switch between Bluetooth speaker and Laptop internal speakers.
  - **Wireless Megaphone (Push-to-Talk)**: Hold a button on your phone to speak live through your laptop into the ECOMAX speaker!
  - **Subwoofer Soundboard**: Punchy SFX (808 Sub-bass drop, DJ Airhorn, Impact Boom, Cheer, Laser) tuned for subwoofers.
  - **Fade-Out Sleep Timer**: Automated volume ramp-down that pauses playback when you fall asleep.
- **Laptop Typing & Search**: Integrated search bar with Enter & Search button and anti-autofill protections.
- **Phone Screenshot & Image Pasting**:
  - **Paste Screenshots from Phone**: Take a screenshot on your phone, paste it directly into the search/keyboard area (or tap the 📷 attachment button to pick recent screenshots).
  - **Auto-Paste to Laptop (Ctrl+V)**: Instantly transfers the image to your laptop's Wayland clipboard (`wl-copy`), triggers `Ctrl+V`, and saves to `~/Pictures/Screenshots/`!
  - **Extract Text (OCR)**: Extracts text from the screenshot directly into the search input box with one tap so you can search or edit it on your laptop.
- **Haptic Touch**: Real vibration feedback on clicks, gestures, and audio controls.
- **PWA & Fullscreen**: Add to your Samsung home screen for a bezel-to-bezel trackpad experience.

---

## 🚀 Quick Start

### 🖥️ Option A: 1-Click Desktop App (Recommended)
You don't need to open a terminal every time!
- **Click the Desktop Icon**: Click **Fedora Remote Cursor** on your Desktop or search for it in your GNOME App Drawer / Dash.
- **Auto-Activation**: The app starts automatically in the background and sends a desktop notification with your connection URLs (`Tailscale` & `Local Hotspot/Wi-Fi`).
- **One-Click Stop/Manage**: Clicking the desktop icon again gives you a quick menu to stop the server or open the local dashboard.

*(To reinstall the desktop shortcuts anytime, simply run `./install_desktop_app.sh`).*

---

### 💻 Option B: Terminal / CLI
```bash
./run.sh
```

---

### 📲 Mobile App (PWA) Installation on your Phone
You can install this directly onto your phone as a standalone app with its own home screen icon, splash screen, and bezel-to-bezel fullscreen mode:
1. Open the URL in Chrome (Android) or Safari (iOS).
2. **Android**: Tap the **Settings (⚙️)** icon in the top right and tap **"Install App"** (or open the Chrome menu ⋮ and tap **"Install app"** / **"Add to Home screen"**).
3. **iOS (iPhone/iPad)**: In Safari, tap the **Share** button (box with upward arrow) and select **"Add to Home Screen"**.
4. Now launch **Fedora Cursor** straight from your phone's home screen anytime!

---

### 3. Connect from your Phone (Secure HTTPS)
1. Ensure your phone is connected to the same Wi-Fi network (or your laptop's Wi-Fi Hotspot `10.42.0.1`, or Tailscale `100.98.255.122`).
2. Scan the **QR code** in the terminal or navigate to `https://100.98.255.122:8080` (or `https://10.42.0.1:8080`).
3. **Accept the Self-Signed Certificate**:
   - Because this is a private local network certificate, your browser will display a *"Your connection is not private"* warning.
   - Tap **Advanced** (or *Details / More options*).
   - Tap **Proceed to 10.42.0.1 (unsafe)**.
4. **Wireless Megaphone Mic Permission**:
   - Tap **Allow** when prompted for microphone access so you can broadcast live through the ECOMAX speaker!
   - *(Note: Modern mobile browsers strictly require HTTPS to enable microphone access).*

*(Tip: If you ever want to run plain unencrypted HTTP, run `./run.sh --http`).*

---

## 🎛️ Gestures Reference

| Gesture | Action |
| :--- | :--- |
| **1 Finger Move** | Move cursor |
| **1 Finger Tap** | Left Click |
| **Double-Tap & Hold** | Drag selection lock |
| **2 Fingers Tap** | Right Click |
| **2 Fingers Drag** | Smooth Scroll |
| **3 Fingers Tap** | Middle Click |
| **Right Rail Drag** | 1-Finger Fast Scroll |

---

## ⚙️ Customization
Tap the **Settings gear icon (⚙️)** in the top right of the phone interface to customize:
- Pointer Sensitivity (`0.5x` to `3.0x`)
- Scroll Speed
- Natural Scrolling (Inverted vs Normal)
- Pointer Dynamic Acceleration
- Haptic Feedback (On/Off)

---

## 🐧 Linux Distribution Support

This project is built directly on Linux kernel standards (`/dev/uinput`, `evdev`, `PipeWire`/`PulseAudio`, and `systemd`) and works across virtually all modern Linux distributions on both **Wayland** and **X11**:

| Distribution | Input & Mouse | Audio & Media | PiP Screen View | Image Paste |
| :--- | :---: | :---: | :---: | :---: |
| **Fedora Workstation** (38, 39, 40, 41) | ✅ Out of box | ✅ PipeWire | ✅ Native Mutter | ✅ `wl-copy` |
| **Ubuntu Desktop** (22.04, 24.04+) | ✅ Out of box | ✅ PipeWire | ✅ Native Mutter | ✅ `wl-copy` |
| **Debian** (11, 12 Bookworm) | ✅ Out of box | ✅ PipeWire / Pulse | ✅ Native Mutter | ✅ `wl-copy` |
| **Arch Linux / Manjaro** | ✅ Out of box | ✅ PipeWire | ✅ Native Mutter | ✅ `wl-copy` |
| **Pop!_OS** (22.04+) | ✅ Out of box | ✅ PipeWire | ✅ Native Mutter | ✅ `wl-copy` |
| **Linux Mint** (Cinnamon / XFCE) | ✅ Out of box | ✅ PulseAudio | ✅ Fallback / Demo | ✅ `xclip` |
| **openSUSE Tumbleweed / Leap** | ✅ Out of box | ✅ PipeWire | ✅ Native Mutter | ✅ `wl-copy` |

### Installing Dependencies by Distro:

- **Fedora / RHEL / CentOS**:
  ```bash
  sudo dnf install python3-pip openssl playerctl gstreamer1-plugins-bad-free wl-clipboard
  ```

- **Ubuntu / Debian / Linux Mint / Pop!_OS**:
  ```bash
  sudo apt update
  sudo apt install python3-pip python3-venv openssl playerctl gstreamer1.0-plugins-bad wl-clipboard xclip
  ```

- **Arch Linux / Manjaro**:
  ```bash
  sudo pacman -S python-pip openssl playerctl gst-plugins-bad wl-clipboard xclip
  ```

- **openSUSE**:
  ```bash
  sudo zypper install python3-pip openssl playerctl gstreamer-plugins-bad wl-clipboard
  ```

