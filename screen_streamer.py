"""
screen_streamer.py - Real-time Wayland Desktop Screen Streamer for Fedora.
Captures laptop screen with embedded hardware cursor via GNOME Mutter & PipeWire.
Uses ultra-compressed WebP streaming and motion deduplication to minimize network data
and keep mobile CPU/battery usage negligible.
"""

import sys
import time
import asyncio
import threading
from typing import Callable, Optional

QUALITY_PROFILES = {
    "eco": {
        "width": 680,
        "height": 384,
        "fps": 8,
        "quality": 60,
        "name": "ECO (8 fps · Battery)",
    },
    "balanced": {
        "width": 1024,
        "height": 576,
        "fps": 12,
        "quality": 78,
        "name": "BALANCED (12 fps · Fast)",
    },
    "hd": {
        "width": 1366,
        "height": 768,
        "fps": 15,
        "quality": 88,
        "name": "HD (1366x768 Native Crisp)",
    },
}

# Attempt to load GStreamer and DBus
HAS_GST = False
HAS_WEBP = False
try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst, GLib
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop

    Gst.init(None)
    HAS_GST = True
    HAS_WEBP = Gst.ElementFactory.find("webpenc") is not None
except Exception as e:
    HAS_GST = False
    HAS_WEBP = False


class ScreenStreamer:
    """
    Manages a background GNOME Mutter ScreenCast session via PipeWire and GStreamer.
    Streams ultra-compressed WebP frames with embedded cursor directly to WebSocket clients.
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        on_frame_callback: Callable[[bytes], asyncio.Future],
        profile: str = "balanced",
        demo_mode: bool = False,
    ):
        self.loop = loop
        self.on_frame_callback = on_frame_callback
        self.demo_mode = demo_mode

        self.profile_name = profile if profile in QUALITY_PROFILES else "balanced"
        p = QUALITY_PROFILES[self.profile_name]
        self.width = p["width"]
        self.height = p["height"]
        self.fps = p["fps"]
        self.quality = p["quality"]

        self.active_viewers = set()
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.glib_loop = None
        self.pipeline = None
        self.session_obj = None
        self._running = False
        self._demo_task = None

        # Change detection / deduplication state
        self._last_frame_bytes = b""
        self._last_sent_time = 0.0

    def set_profile(self, profile: str):
        """Update compression profile (eco, balanced, hd). Restarts pipeline if active."""
        if profile not in QUALITY_PROFILES or profile == self.profile_name:
            return

        with self.lock:
            self.profile_name = profile
            p = QUALITY_PROFILES[self.profile_name]
            self.width = p["width"]
            self.height = p["height"]
            self.fps = p["fps"]
            self.quality = p["quality"]
            print(f"📺 Screen Streamer: Switched to {p['name']}")

            if self._running:
                # Restart capture with new parameters
                self._stop_capture()
                self._start_capture()

    def add_viewer(self, client_id) -> bool:
        """Register a client viewer. Starts capture pipeline on first viewer."""
        with self.lock:
            self.active_viewers.add(client_id)
            if not self._running:
                return self._start_capture()
            return True

    def remove_viewer(self, client_id):
        """Unregister a client viewer. Stops capture pipeline if no viewers remain."""
        with self.lock:
            self.active_viewers.discard(client_id)
            if not self.active_viewers and self._running:
                self._stop_capture()

    def has_viewers(self) -> bool:
        with self.lock:
            return len(self.active_viewers) > 0

    def _start_capture(self) -> bool:
        if self._running:
            return True

        self._running = True
        self._last_frame_bytes = b""
        self._last_sent_time = 0.0

        if self.demo_mode or not HAS_GST:
            print(f"📺 Screen Streamer: Starting synthetic preview demo stream ({self.profile_name})")
            self._demo_task = asyncio.run_coroutine_threadsafe(self._run_demo_loop(), self.loop)
            return True

        enc_type = "WebP (compressed)" if HAS_WEBP else "JPEG"
        print(f"📺 Screen Streamer: Starting Mutter ScreenCast pipeline [{enc_type}] ({self.width}x{self.height} @ {self.fps}fps)")
        self.thread = threading.Thread(target=self._run_glib_thread, name="ScreenCastThread", daemon=True)
        self.thread.start()
        return True

    def _stop_capture(self):
        if not self._running:
            return

        print("📺 Screen Streamer: Stopping capture pipeline (zero resource idle)")
        self._running = False

        if self._demo_task:
            self._demo_task.cancel()
            self._demo_task = None

        if self.pipeline:
            try:
                self.pipeline.set_state(Gst.State.NULL)
            except Exception:
                pass
            self.pipeline = None

        if self.session_obj:
            try:
                self.session_obj.Stop(dbus_interface="org.gnome.Mutter.ScreenCast.Session")
            except Exception:
                pass
            self.session_obj = None

        if self.glib_loop:
            try:
                self.glib_loop.quit()
            except Exception:
                pass
            self.glib_loop = None

    def _run_glib_thread(self):
        """Runs the GLib mainloop for Mutter D-Bus signals and GStreamer pipeline."""
        try:
            DBusGMainLoop(set_as_default=True)
            self.glib_loop = GLib.MainLoop()
            bus = dbus.SessionBus()

            mutter = bus.get_object("org.gnome.Mutter.ScreenCast", "/org/gnome/Mutter/ScreenCast")
            session_path = mutter.CreateSession(
                dbus.Dictionary({}, signature="sv"),
                dbus_interface="org.gnome.Mutter.ScreenCast"
            )
            self.session_obj = bus.get_object("org.gnome.Mutter.ScreenCast", session_path)

            # cursor-mode 1 = CURSOR_MODE_EMBEDDED (embeds cursor directly in frame)
            stream_props = dbus.Dictionary({"cursor-mode": dbus.UInt32(1)}, signature="sv")
            stream_path = self.session_obj.RecordMonitor(
                "",
                stream_props,
                dbus_interface="org.gnome.Mutter.ScreenCast.Session"
            )

            def on_pw_stream_added(node_id):
                if not self._running:
                    return

                # Choose best encoder: WebP (3-4x smaller) with text-tuning or fallback to JPEG
                if HAS_WEBP:
                    encoder = f"webpenc quality={self.quality} speed=1 preset=text"
                else:
                    encoder = f"jpegenc quality={self.quality}"

                pipe_str = (
                    f"pipewiresrc path={node_id} do-timestamp=true keepalive-time=1000 ! "
                    f"videorate ! video/x-raw,framerate={self.fps}/1 ! "
                    f"videoscale ! video/x-raw,width={self.width},height={self.height} ! "
                    f"videoconvert ! "
                    f"{encoder} ! "
                    f"appsink name=sink emit-signals=True max-buffers=1 drop=True"
                )
                try:
                    self.pipeline = Gst.parse_launch(pipe_str)
                    sink = self.pipeline.get_by_name("sink")
                    sink.connect("new-sample", self._on_new_sample)
                    self.pipeline.set_state(Gst.State.PLAYING)
                    print(f"✓ Screen capture pipeline active (Node ID: {node_id})")
                except Exception as err:
                    print(f"❌ Failed to start GStreamer pipeline: {err}")

            bus.add_signal_receiver(
                on_pw_stream_added,
                signal_name="PipeWireStreamAdded",
                dbus_interface="org.gnome.Mutter.ScreenCast.Stream",
                path=stream_path
            )

            self.session_obj.Start(dbus_interface="org.gnome.Mutter.ScreenCast.Session")
            self.glib_loop.run()
        except Exception as ex:
            print(f"⚠️ Mutter ScreenCast error: {ex}. Falling back to preview mode.")
            if self._running:
                asyncio.run_coroutine_threadsafe(self._run_demo_loop(), self.loop)

    def _on_new_sample(self, sink):
        """Triggered on each ready compressed frame."""
        if not self._running:
            return Gst.FlowReturn.OK

        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.OK

        buf = sample.get_buffer()
        res, map_info = buf.map(Gst.MapFlags.READ)
        if res:
            try:
                frame_bytes = bytes(map_info.data)
                now = time.time()

                # Change detection / Deduplication:
                # If frame is identical to previous and sent within last 1.2s, skip it!
                if frame_bytes == self._last_frame_bytes and (now - self._last_sent_time < 1.2):
                    return Gst.FlowReturn.OK

                self._last_frame_bytes = frame_bytes
                self._last_sent_time = now

                asyncio.run_coroutine_threadsafe(
                    self.on_frame_callback(frame_bytes),
                    self.loop
                )
            except Exception:
                pass
            finally:
                buf.unmap(map_info)

        return Gst.FlowReturn.OK

    async def _run_demo_loop(self):
        """Generates synthetic desktop frames for preview mode or fallback."""
        from PIL import Image, ImageDraw
        import io
        import math

        step = 0
        while self._running:
            try:
                img = Image.new("RGB", (self.width, self.height), color=(18, 24, 38))
                draw = ImageDraw.Draw(img)

                draw.rectangle([0, 0, self.width, 24], fill=(30, 41, 59))
                draw.text((12, 5), f"Fedora Wayland ({self.profile_name.upper()})", fill=(226, 232, 240))
                draw.text((self.width - 70, 5), time.strftime("%H:%M:%S"), fill=(148, 163, 184))

                draw.rounded_rectangle([30, 40, int(self.width * 0.6), int(self.height * 0.75)], radius=6, fill=(15, 23, 42), outline=(56, 189, 248), width=1)
                draw.text((40, 50), "Terminal - High Efficiency", fill=(56, 189, 248))
                draw.text((40, 75), f"$ WebP: ~20KB/frame", fill=(74, 222, 128))

                # Moving simulated cursor
                cx = int(self.width / 2 + math.sin(step * 0.15) * (self.width * 0.3))
                cy = int(self.height / 2 + math.cos(step * 0.12) * (self.height * 0.25))
                draw.polygon([(cx, cy), (cx + 10, cy + 7), (cx + 6, cy + 10)], fill=(255, 255, 255), outline=(0, 0, 0))

                buf = io.BytesIO()
                # Save as WEBP for ultra small footprint
                img.save(buf, format="WEBP", quality=self.quality)
                frame_data = buf.getvalue()

                await self.on_frame_callback(frame_data)
                step += 1
                await asyncio.sleep(1.0 / self.fps)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)
