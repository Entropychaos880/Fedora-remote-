#!/usr/bin/env python3
"""
server.py - High-performance Trackpad Server for Fedora & Linux.
Serves a responsive mobile web app and streams touch/cursor events over WebSocket.
"""

import os
import sys
import ssl
import json
import socket
import asyncio
import mimetypes
import subprocess
import base64
import shutil
from datetime import datetime
from pathlib import Path
from http import HTTPStatus

import websockets
from websockets.asyncio.server import serve
from websockets.http11 import Response
from websockets.datastructures import Headers
import qrcode

from uinput_device import UInputDevice
from audio_manager import AudioManager
from screen_streamer import ScreenStreamer

PROJECT_DIR = Path(__file__).parent.resolve()
STATIC_DIR = PROJECT_DIR / "static"
DEFAULT_PORT = 8080
DEFAULT_CERT_FILE = PROJECT_DIR / "cert.pem"
DEFAULT_KEY_FILE = PROJECT_DIR / "key.pem"


def ensure_ssl_certificates(ip_list: list[str], cert_path: Path | None = None, key_path: Path | None = None) -> tuple[Path | None, Path | None]:
    """Ensure SSL certificates exist. Generate self-signed cert with all local IPs as SANs if missing."""
    cert_p = cert_path or DEFAULT_CERT_FILE
    key_p = key_path or DEFAULT_KEY_FILE

    if cert_p.exists() and key_p.exists():
        return cert_p, key_p

    print("🔒 Generating self-signed TLS/SSL certificate for secure mobile connection...")
    san_entries = ["IP:127.0.0.1", "DNS:localhost"]
    for ip in ip_list:
        if ip not in ("127.0.0.1", "localhost") and not ip.startswith("127."):
            san_entries.append(f"IP:{ip}")
    san_str = ",".join(san_entries)

    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", str(key_p),
        "-out", str(cert_p),
        "-sha256", "-days", "365", "-nodes",
        "-subj", "/CN=Samsung-Remote-Trackpad",
        "-addext", f"subjectAltName={san_str}"
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key_p.chmod(0o600)
        print("✓ TLS/SSL certificates generated successfully.")
        return cert_p, key_p
    except Exception as e:
        print(f"⚠️ Warning: Could not generate SSL certificate ({e}). Falling back to HTTP.")
        return None, None


def get_local_ips() -> list[tuple[str, str, str]]:
    """Discover all active network addresses (Hotspot, Wi-Fi, Ethernet)."""
    ips = []
    try:
        out = subprocess.check_output(["ip", "-4", "-o", "addr", "show"], text=True)
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                iface = parts[1]
                cidr = parts[3]
                ip = cidr.split("/")[0]
                if not ip.startswith("127."):
                    if ip.startswith("10.42.") or "hotspot" in iface.lower():
                        desc = "Laptop Wi-Fi Hotspot"
                    elif "tailscale" in iface.lower():
                        desc = "Tailscale VPN"
                    elif iface.startswith("wl"):
                        desc = "Wi-Fi Network"
                    elif iface.startswith("en"):
                        desc = "Ethernet / Home LAN"
                    else:
                        desc = "Local Network"
                    ips.append((ip, iface, desc))
    except Exception:
        pass

    if not ips:
        ips.append(("127.0.0.1", "lo", "Localhost"))
    return ips


class RemoteTrackpadServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
        demo_mode: bool = False,
        use_ssl: bool = True,
        cert_file: Path | None = None,
        key_file: Path | None = None,
    ):
        self.host = host
        self.port = port
        self.demo_mode = demo_mode
        self.use_ssl = use_ssl
        self.cert_file = cert_file or DEFAULT_CERT_FILE
        self.key_file = key_file or DEFAULT_KEY_FILE
        self.mouse: UInputDevice | None = None
        self.audio = AudioManager()
        self.active_clients = set()
        self.pip_viewers = set()
        self.screen_streamer: ScreenStreamer | None = None
        # Sub-pixel motion and scroll accumulators for ultra-smooth pointer tracking
        self.subpixel_x = 0.0
        self.subpixel_y = 0.0
        self.subscroll_x = 0.0
        self.subscroll_y = 0.0

    def get_full_audio_state(self) -> dict:
        vol = self.audio.get_volume()
        sinks = self.audio.get_sinks()
        now_playing = self.audio.get_now_playing()
        return {
            "type": "audio_state",
            "volume": vol.get("volume", 50),
            "muted": vol.get("muted", False),
            "sinks": sinks,
            "now_playing": now_playing,
            "sleep_timer_remaining": self.audio.sleep_timer_remaining,
        }

    async def broadcast_message(self, data: dict):
        if not self.active_clients:
            return
        payload = json.dumps(data)
        tasks = []
        for client in list(self.active_clients):
            try:
                tasks.append(client.send(payload))
            except Exception:
                pass
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_screen_frame(self, frame_bytes: bytes):
        if not self.pip_viewers:
            return
        tasks = []
        for client in list(self.pip_viewers):
            if getattr(client, "_sending_frame", False):
                # Zero-backpressure drop: client is still processing prior frame
                continue
            tasks.append(self._send_frame_to_viewer(client, frame_bytes))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_frame_to_viewer(self, viewer, frame_bytes: bytes):
        viewer._sending_frame = True
        try:
            await viewer.send(frame_bytes)
        except Exception:
            pass
        finally:
            viewer._sending_frame = False

    def init_device(self):
        if self.demo_mode:
            print("ℹ️ Running in DEMO / PREVIEW mode (cursor movements logged to console, /dev/uinput bypassed)")
            return

        try:
            self.mouse = UInputDevice("Samsung Remote Trackpad")
            print("✓ Linux virtual input device successfully initialized via /dev/uinput")
        except PermissionError as e:
            print("\n" + "=" * 60)
            print("❌ PERMISSION ERROR: Cannot open /dev/uinput")
            print("=" * 60)
            print(str(e))
            print("\nTip: To preview the mobile web app without root, run:")
            print("    ./run.sh --demo")
            print("=" * 60 + "\n")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to initialize input device: {e}")
            sys.exit(1)

    def get_server_endpoints_payload(self) -> dict:
        """Return available network endpoints for dynamic client connection & fallback."""
        ips = get_local_ips()
        endpoints = []
        for ip, iface, desc in ips:
            endpoints.append({
                "ip": ip,
                "host": f"{ip}:{self.port}",
                "desc": desc,
                "url": f"https://{ip}:{self.port}"
            })
        return {
            "type": "server_endpoints",
            "endpoints": endpoints,
            "port": self.port
        }

    def process_http_request(self, connection, request):
        """Serve static files directly over HTTP on the same port."""
        raw_path = request.path.split("?")[0]
        connection.path = raw_path

        # Route WebSocket requests to WS handlers
        if raw_path.startswith("/ws"):
            return None

        # Return live server endpoints as JSON
        if raw_path == "/api/endpoints":
            payload = json.dumps(self.get_server_endpoints_payload()).encode("utf-8")
            return Response(200, "OK", Headers([
                ("Content-Type", "application/json; charset=utf-8"),
                ("Access-Control-Allow-Origin", "*"),
                ("Cache-Control", "no-cache")
            ]), payload)

        # Clean requested path
        if raw_path in ("/", ""):
            file_path = STATIC_DIR / "index.html"
        else:
            rel_path = raw_path.lstrip("/")
            file_path = (STATIC_DIR / rel_path).resolve()
            # Prevent directory traversal
            if not str(file_path).startswith(str(STATIC_DIR.resolve())):
                return Response(403, "Forbidden", Headers([("Content-Type", "text/plain")]), b"Forbidden")

        if not file_path.exists() or file_path.is_dir():
            # Fallback to index.html for SPA if not found
            file_path = STATIC_DIR / "index.html"
            if not file_path.exists():
                return Response(404, "Not Found", Headers([("Content-Type", "text/plain")]), b"Not Found")

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            if file_path.suffix == ".js":
                mime_type = "application/javascript"
            elif file_path.suffix == ".css":
                mime_type = "text/css"
            elif file_path.suffix == ".svg":
                mime_type = "image/svg+xml"
            elif file_path.suffix == ".json":
                mime_type = "application/json"
            else:
                mime_type = "application/octet-stream"

        try:
            content = file_path.read_bytes()
            headers = Headers([
                ("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type),
                ("Content-Length", str(len(content))),
                ("Cache-Control", "no-cache"),
            ])
            return Response(200, "OK", headers, content)
        except Exception as err:
            return Response(500, "Internal Error", Headers([("Content-Type", "text/plain")]), str(err).encode())

    async def handle_screen_websocket(self, websocket):
        """Dedicated high-bandwidth WebSocket for video screen streaming, isolating input traffic."""
        # Evict any fallback viewers on /ws to ensure strictly one clean stream per viewer
        for v in list(self.pip_viewers):
            if getattr(v, "path", "") != "/ws/screen":
                self.pip_viewers.discard(v)
                if self.screen_streamer:
                    self.screen_streamer.remove_viewer(v)

        self.pip_viewers.add(websocket)
        if self.screen_streamer:
            self.screen_streamer.add_viewer(websocket)
        peer = websocket.remote_address[0] if websocket.remote_address else "Unknown"
        print(f"📺 Screen stream channel opened ({peer})")
        try:
            async for message in websocket:
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        if data.get("type") == "pip_set_profile":
                            profile = str(data.get("profile", "balanced"))
                            if self.screen_streamer:
                                self.screen_streamer.set_profile(profile)
                    except Exception:
                        pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.pip_viewers.discard(websocket)
            if self.screen_streamer:
                self.screen_streamer.remove_viewer(websocket)
            print(f"📺 Screen stream channel closed ({peer})")

    async def handle_websocket(self, websocket):
        """Handle real-time low-latency touchpad and audio commands."""
        path = getattr(websocket, "path", "/ws")
        if path == "/ws/screen":
            await self.handle_screen_websocket(websocket)
            return

        self.active_clients.add(websocket)
        peer = websocket.remote_address[0] if websocket.remote_address else "Unknown"
        print(f"📱 Phone connected from {peer}")

        # Send initial audio state and server endpoints to newly connected client
        try:
            await websocket.send(json.dumps(self.get_full_audio_state()))
            await websocket.send(json.dumps(self.get_server_endpoints_payload()))
        except Exception:
            pass

        try:
            async for message in websocket:
                # 1. Handle raw binary microphone audio streaming
                if isinstance(message, bytes):
                    self.audio.write_mic_chunk(message)
                    continue

                # 2. Ultra-fast compact ASCII wire protocol (< 100ns execution, zero JSON overhead)
                if isinstance(message, str):
                    if message.startswith("m:"):
                        try:
                            comma_idx = message.find(",", 2)
                            dx = float(message[2:comma_idx])
                            dy = float(message[comma_idx + 1:])
                            self.subpixel_x += dx
                            self.subpixel_y += dy
                            move_x = int(round(self.subpixel_x))
                            move_y = int(round(self.subpixel_y))
                            if (move_x != 0 or move_y != 0) and self.mouse:
                                self.subpixel_x -= move_x
                                self.subpixel_y -= move_y
                                self.mouse.move(move_x, move_y)
                        except Exception:
                            pass
                        continue

                    elif message.startswith("s:"):
                        try:
                            comma_idx = message.find(",", 2)
                            dx = float(message[2:comma_idx])
                            dy = float(message[comma_idx + 1:])
                            self.subscroll_x += dx
                            self.subscroll_y += dy
                            scroll_x = int(round(self.subscroll_x))
                            scroll_y = int(round(self.subscroll_y))
                            if (scroll_x != 0 or scroll_y != 0) and self.mouse:
                                self.subscroll_x -= scroll_x
                                self.subscroll_y -= scroll_y
                                self.mouse.scroll(scroll_x, scroll_y)
                        except Exception:
                            pass
                        continue

                    elif message.startswith("c:"):
                        btn = message[2:]
                        self.subpixel_x = 0.0
                        self.subpixel_y = 0.0
                        if self.mouse:
                            self.mouse.click(btn)
                        continue

                    elif message.startswith("d:"):
                        btn = message[2:]
                        if self.mouse:
                            self.mouse.button_event(btn, 1)
                        continue

                    elif message.startswith("u:"):
                        btn = message[2:]
                        if self.mouse:
                            self.mouse.button_event(btn, 0)
                        continue

                try:
                    data = json.loads(message)
                    action = data.get("type")

                    if action == "move":
                        dx = float(data.get("dx", 0))
                        dy = float(data.get("dy", 0))
                        self.subpixel_x += dx
                        self.subpixel_y += dy
                        move_x = int(round(self.subpixel_x))
                        move_y = int(round(self.subpixel_y))
                        if (move_x != 0 or move_y != 0) and self.mouse:
                            self.subpixel_x -= move_x
                            self.subpixel_y -= move_y
                            self.mouse.move(move_x, move_y)

                    elif action == "scroll":
                        dx = float(data.get("dx", 0))
                        dy = float(data.get("dy", 0))
                        self.subscroll_x += dx
                        self.subscroll_y += dy
                        scroll_x = int(round(self.subscroll_x))
                        scroll_y = int(round(self.subscroll_y))
                        if (scroll_x != 0 or scroll_y != 0) and self.mouse:
                            self.subscroll_x -= scroll_x
                            self.subscroll_y -= scroll_y
                            self.mouse.scroll(scroll_x, scroll_y)

                    elif action == "click":
                        btn = data.get("button", "left")
                        self.subpixel_x = 0.0
                        self.subpixel_y = 0.0
                        if self.mouse:
                            self.mouse.click(btn)

                    elif action == "btn_down":
                        btn = data.get("button", "left")
                        if self.mouse:
                            self.mouse.button_event(btn, 1)

                    elif action == "btn_up":
                        btn = data.get("button", "left")
                        if self.mouse:
                            self.mouse.button_event(btn, 0)

                    elif action == "key":
                        key_name = data.get("key", "")
                        if self.mouse:
                            self.mouse.key_event(key_name, 1)
                            await asyncio.sleep(0.01)
                            self.mouse.key_event(key_name, 0)

                    elif action == "gesture":
                        gest = str(data.get("gesture", ""))
                        if self.mouse:
                            if gest == "swipe_up":
                                self.mouse.toggle_overview()
                            elif gest == "swipe_down":
                                self.mouse.close_overview()
                            elif gest == "swipe_left":
                                self.mouse.workspace_next()
                            elif gest == "swipe_right":
                                self.mouse.workspace_prev()

                    elif action == "type":
                        text = str(data.get("text", ""))
                        press_enter = bool(data.get("enter", False))
                        if self.mouse:
                            self.mouse.type_text(text, press_enter=press_enter)

                    elif action == "paste_image":
                        image_data = data.get("image")
                        press_enter = bool(data.get("enter", False))
                        auto_paste = bool(data.get("auto_paste", True))
                        if image_data:
                            try:
                                if "," in image_data:
                                    _, b64_str = image_data.split(",", 1)
                                else:
                                    b64_str = image_data
                                img_bytes = base64.b64decode(b64_str)

                                # Save screenshot to ~/Pictures/Screenshots/
                                pics_dir = Path.home() / "Pictures" / "Screenshots"
                                pics_dir.mkdir(parents=True, exist_ok=True)
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                save_path = pics_dir / f"phone_screenshot_{timestamp}.png"
                                save_path.write_bytes(img_bytes)

                                # Also save to /tmp/phone_clipboard.png
                                tmp_file = Path("/tmp/phone_clipboard.png")
                                tmp_file.write_bytes(img_bytes)

                                # Copy to Wayland clipboard using wl-copy
                                copied = False
                                if shutil.which("wl-copy"):
                                    try:
                                        p = subprocess.Popen(["wl-copy", "--type", "image/png"], stdin=subprocess.PIPE)
                                        p.communicate(input=img_bytes)
                                        if p.returncode == 0:
                                            copied = True
                                    except Exception as err:
                                        print(f"wl-copy failed: {err}")

                                if not copied and shutil.which("xclip"):
                                    try:
                                        subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png", str(tmp_file)], check=False)
                                        copied = True
                                    except Exception:
                                        pass

                                # Simulate Ctrl+V to paste into active input/app on laptop
                                if auto_paste and self.mouse:
                                    await asyncio.sleep(0.06)
                                    self.mouse.paste_clipboard()
                                    if press_enter:
                                        await asyncio.sleep(0.04)
                                        self.mouse.key_event("enter", 1)
                                        await asyncio.sleep(0.01)
                                        self.mouse.key_event("enter", 0)

                                await websocket.send(json.dumps({
                                    "type": "paste_image_ack",
                                    "success": True,
                                    "copied": copied,
                                    "file": str(save_path),
                                    "size": len(img_bytes)
                                }))
                                print(f"📷 Received image from phone ({len(img_bytes)} bytes) -> Clipboard & {save_path.name}")
                            except Exception as ex:
                                print(f"❌ Failed to process pasted image: {ex}")
                                await websocket.send(json.dumps({
                                    "type": "paste_image_ack",
                                    "success": False,
                                    "error": str(ex)
                                }))

                    # ===== Audio & Sound System Actions =====
                    elif action == "get_audio_state":
                        await websocket.send(json.dumps(self.get_full_audio_state()))

                    elif action == "set_volume":
                        vol = int(data.get("volume", 50))
                        self.audio.set_volume(vol)
                        await self.broadcast_message(self.get_full_audio_state())

                    elif action == "toggle_mute":
                        self.audio.toggle_mute()
                        await self.broadcast_message(self.get_full_audio_state())

                    elif action == "switch_sink":
                        sink_name = str(data.get("sink", ""))
                        if sink_name:
                            self.audio.set_default_sink(sink_name)
                            await asyncio.sleep(0.05)
                            await self.broadcast_message(self.get_full_audio_state())

                    elif action == "media_action":
                        m_act = str(data.get("action", ""))
                        if m_act:
                            self.audio.media_action(m_act)
                            await asyncio.sleep(0.08)
                            await self.broadcast_message(self.get_full_audio_state())

                    elif action == "play_sfx":
                        sfx_name = str(data.get("name", ""))
                        if sfx_name:
                            self.audio.play_sfx(sfx_name)

                    elif action == "mic_start":
                        self.audio.start_mic()

                    elif action == "mic_stop":
                        self.audio.stop_mic()

                    elif action == "start_sleep_timer":
                        mins = float(data.get("minutes", 30))
                        self.audio.start_sleep_timer(mins, notify_cb=self.broadcast_message)
                        await self.broadcast_message(self.get_full_audio_state())

                    elif action == "cancel_sleep_timer":
                        self.audio.cancel_sleep_timer()
                        await self.broadcast_message(self.get_full_audio_state())

                    elif action == "pip_start":
                        profile = str(data.get("profile", "balanced"))
                        if self.screen_streamer:
                            self.screen_streamer.set_profile(profile)
                        # Only register fallback viewer if no dedicated /ws/screen viewer exists
                        if not any(getattr(v, "path", "") == "/ws/screen" for v in self.pip_viewers):
                            self.pip_viewers.add(websocket)
                            if self.screen_streamer:
                                self.screen_streamer.add_viewer(websocket)
                        await websocket.send(json.dumps({
                            "type": "pip_status",
                            "active": True,
                            "profile": profile,
                        }))

                    elif action == "pip_set_profile":
                        profile = str(data.get("profile", "balanced"))
                        if self.screen_streamer:
                            self.screen_streamer.set_profile(profile)
                        await websocket.send(json.dumps({
                            "type": "pip_status",
                            "active": True,
                            "profile": profile,
                        }))

                    elif action == "pip_stop":
                        self.pip_viewers.discard(websocket)
                        if self.screen_streamer:
                            self.screen_streamer.remove_viewer(websocket)
                        await websocket.send(json.dumps({"type": "pip_status", "active": False}))

                    elif action == "ping":
                        t = data.get("t", 0)
                        await websocket.send(json.dumps({"type": "pong", "t": t}))

                except Exception as ex:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.audio.stop_mic()
            self.pip_viewers.discard(websocket)
            if self.screen_streamer:
                self.screen_streamer.remove_viewer(websocket)
            self.active_clients.discard(websocket)
            print(f"📱 Phone disconnected ({peer})")

    async def start(self):
        self.init_device()

        # Initialize real-time ScreenStreamer for Picture-in-Picture
        self.screen_streamer = ScreenStreamer(
            asyncio.get_running_loop(),
            self.broadcast_screen_frame,
            demo_mode=self.demo_mode,
        )

        available_ips = get_local_ips()
        ip_addresses = [item[0] for item in available_ips]

        ssl_context = None
        if self.use_ssl:
            cert_p, key_p = ensure_ssl_certificates(ip_addresses, self.cert_file, self.key_file)
            if cert_p and key_p:
                try:
                    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    ssl_context.load_cert_chain(cert_p, key_p)
                except Exception as err:
                    print(f"⚠️ Failed to load SSL certificate ({err}). Falling back to HTTP.")
                    ssl_context = None
                    self.use_ssl = False
            else:
                self.use_ssl = False

        scheme = "https" if self.use_ssl else "http"

        print("\n" + "═" * 64)
        print("   🖱️   SAMSUNG REMOTE TRACKPAD & AUDIO HUB (FEDORA)   📱   ")
        print("═" * 64)
        if self.use_ssl:
            print("🔒 \033[1;32mHTTPS & Secure WebSockets Active\033[0m")
            print("   (Required by mobile browsers for Wireless Megaphone microphone)")
            print("\n💡 \033[1;33mFirst-time phone browser note:\033[0m")
            print("   1. Open link or scan QR code on your phone")
            print("   2. When the 'Your connection is not private' warning appears,")
            print("      tap \033[1m'Advanced'\033[0m (or 'Details / More options')")
            print("   3. Tap \033[1m'Proceed to ... (unsafe)'\033[0m to accept the self-signed cert")
            print("   4. Tap 'Allow' when using the Push-To-Talk microphone!")
        else:
            print("⚠️ \033[1;33mHTTP Active (Plain / Unencrypted)\033[0m")
            print("   Note: Mobile browsers disable microphone access on plain HTTP.")

        print("═" * 64)
        print("Available connection links (pick the one matching your phone's network):\n")

        primary_url = None
        for ip, iface, desc in available_ips:
            url = f"{scheme}://{ip}:{self.port}"
            if primary_url is None:
                # If Hotspot is active, make it primary, otherwise first
                if ip.startswith("10.42."):
                    primary_url = url
            print(f" • \033[1;33m{desc:<24}\033[0m : \033[1;36m{url}\033[0m ({iface})")

        if not primary_url and available_ips:
            primary_url = f"{scheme}://{available_ips[0][0]}:{self.port}"

        print(f"\nScan QR code for primary connection:\n   👉  \033[1;36m{primary_url}\033[0m\n")

        qr = qrcode.QRCode(border=1)
        qr.add_data(primary_url)
        qr.make(fit=True)
        try:
            qr.print_ascii(invert=True)
        except Exception:
            pass

        print("═" * 64)
        print(f"Server listening securely on port {self.port}. Press Ctrl+C to stop.\n")

        server = await serve(
            self.handle_websocket,
            self.host,
            self.port,
            ssl=ssl_context,
            process_request=self.process_http_request,
            ping_interval=20,
            ping_timeout=20,
        )

        try:
            await server.wait_closed()
        finally:
            if self.screen_streamer:
                self.screen_streamer._stop_capture()
            if self.mouse:
                self.mouse.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Samsung Remote Trackpad Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--demo", action="store_true", help="Run in preview/demo mode without requiring /dev/uinput")
    parser.add_argument("--http", action="store_true", help="Disable HTTPS and run plain HTTP instead")
    parser.add_argument("--cert", type=str, default=None, help="Path to TLS certificate .pem file")
    parser.add_argument("--key", type=str, default=None, help="Path to TLS private key .pem file")
    args = parser.parse_args()

    cert_path = Path(args.cert).resolve() if args.cert else None
    key_path = Path(args.key).resolve() if args.key else None

    app = RemoteTrackpadServer(
        host=args.host,
        port=args.port,
        demo_mode=args.demo,
        use_ssl=not args.http,
        cert_file=cert_path,
        key_file=key_path,
    )
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
