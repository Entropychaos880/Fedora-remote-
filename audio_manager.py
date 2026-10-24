"""
audio_manager.py - PipeWire, WirePlumber, Bluetooth, and MPRIS Audio Controller for Fedora.
Handles:
1. Volume control & Mute (wpctl)
2. Audio Sink Switching (ECOMAX Bluetooth LX-500 ⇄ Laptop Speakers)
3. MPRIS Media Metadata (Now Playing title, artist, status, controls)
4. Wireless Megaphone (streams raw PCM microphone audio from phone to pw-cat)
5. Soundboard SFX playback (pw-play)
6. Fade-out Sleep Timer
"""

import os
import re
import math
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Callable

SFX_DIR = Path(__file__).parent / "static" / "sfx"


class AudioManager:
    def __init__(self):
        self._mic_process: Optional[subprocess.Popen] = None
        self._sleep_timer_task: Optional[asyncio.Task] = None
        self.sleep_timer_remaining: int = 0  # remaining seconds
        self.initial_volume_before_fade: Optional[int] = None

    # ================= 1. Volume & Mute =================

    def get_volume(self) -> dict:
        """Returns {'volume': int (0-100), 'muted': bool}."""
        try:
            out = subprocess.check_output(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            # Format: 'Volume: 0.70' or 'Volume: 0.70 [MUTED]'
            parts = out.split()
            vol = 50
            muted = "[MUTED]" in out
            for p in parts:
                try:
                    vol = int(round(float(p) * 100))
                    break
                except ValueError:
                    continue
            return {"volume": max(0, min(100, vol)), "muted": muted}
        except Exception:
            return {"volume": 50, "muted": False}

    def set_volume(self, percent: int) -> dict:
        """Sets default audio sink volume (0-100)."""
        val = max(0, min(100, int(percent))) / 100.0
        try:
            subprocess.run(
                ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{val:.2f}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )
            # Also ensure unmuted if volume raised
            if val > 0:
                subprocess.run(
                    ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                )
        except Exception:
            pass
        return self.get_volume()

    def toggle_mute(self) -> dict:
        """Toggles mute on default audio sink."""
        try:
            subprocess.run(
                ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )
        except Exception:
            pass
        return self.get_volume()

    # ================= 2. Sinks (Bluetooth vs Laptop) =================

    def get_sinks(self) -> list[dict]:
        """Returns list of sinks with human-readable labels and is_default status."""
        sinks = []
        default_sink = ""
        try:
            default_sink = subprocess.check_output(
                ["pactl", "get-default-sink"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            pass

        try:
            out = subprocess.check_output(
                ["pactl", "list", "sinks", "short"],
                text=True, stderr=subprocess.DEVNULL
            )
            for line in out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    sink_id = parts[0]
                    sink_name = parts[1]
                    is_active = (sink_name == default_sink or sink_id == default_sink)

                    # Friendly label
                    if "bluez" in sink_name.lower():
                        label = "ECOMAX Sound System (Bluetooth)"
                        icon = "bluetooth"
                    elif "analog" in sink_name.lower() or "pci" in sink_name.lower():
                        label = "Laptop Internal Speakers"
                        icon = "laptop"
                    else:
                        label = sink_name.split(".")[-1].replace("-", " ").title()
                        icon = "speaker"

                    sinks.append({
                        "id": sink_id,
                        "name": sink_name,
                        "label": label,
                        "icon": icon,
                        "is_default": is_active,
                    })
        except Exception:
            pass
        return sinks

    def set_default_sink(self, sink_name_or_id: str) -> bool:
        """Switch audio output device."""
        try:
            res = subprocess.run(
                ["pactl", "set-default-sink", sink_name_or_id],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
            )
            return res.returncode == 0
        except Exception:
            return False

    # ================= 3. MPRIS (Now Playing) =================

    def _get_active_players(self) -> list[str]:
        try:
            out = subprocess.check_output(["busctl", "--user", "list"], text=True)
            players = []
            for line in out.splitlines():
                if "org.mpris.MediaPlayer2." in line:
                    parts = line.split()
                    if parts:
                        players.append(parts[0])
            return players
        except Exception:
            return []

    def get_now_playing(self) -> dict:
        """Extracts active track title, artist, and playback status from MPRIS."""
        players = self._get_active_players()
        if not players:
            return {
                "has_media": False,
                "title": "No active media",
                "artist": "",
                "player": "",
                "status": "Stopped"
            }

        # Check players, preferring currently 'Playing' player
        best_data = None
        for p in players:
            try:
                # PlaybackStatus
                status_raw = subprocess.check_output([
                    "busctl", "--user", "get-property", p,
                    "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player", "PlaybackStatus"
                ], text=True, stderr=subprocess.DEVNULL).strip()
                # format: s "Playing"
                status = "Playing" if "Playing" in status_raw else ("Paused" if "Paused" in status_raw else "Stopped")

                # Metadata
                meta_raw = subprocess.check_output([
                    "busctl", "--user", "call", p,
                    "/org/mpris/MediaPlayer2", "org.freedesktop.DBus.Properties", "Get",
                    "ss", "org.mpris.MediaPlayer2.Player", "Metadata"
                ], text=True, stderr=subprocess.DEVNULL)

                title_match = re.search(r'"xesam:title"\s+s\s+"([^"]+)"', meta_raw)
                artist_match = re.search(r'"xesam:artist"\s+as\s+\d+\s+"([^"]*)"', meta_raw)

                title = title_match.group(1) if title_match else "Media Playing"
                artist = artist_match.group(1) if artist_match else ""

                player_name = p.replace("org.mpris.MediaPlayer2.", "").split(".")[0].title()

                data = {
                    "has_media": True,
                    "title": title,
                    "artist": artist,
                    "player": player_name,
                    "player_bus": p,
                    "status": status,
                }

                if status == "Playing":
                    return data
                if best_data is None:
                    best_data = data
            except Exception:
                continue

        return best_data or {
            "has_media": False,
            "title": "No active media",
            "artist": "",
            "player": "",
            "status": "Stopped"
        }

    def media_action(self, action: str):
        """Dispatches PlayPause, Next, Previous to MPRIS player."""
        players = self._get_active_players()
        target_action = {
            "playpause": "PlayPause",
            "play": "Play",
            "pause": "Pause",
            "next": "Next",
            "prev": "Previous",
        }.get(action.lower(), "PlayPause")

        for p in players:
            try:
                subprocess.run([
                    "busctl", "--user", "call", p,
                    "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player", target_action
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass

    # ================= 4. Wireless Megaphone (Phone Mic -> pw-cat) =================

    def start_mic(self):
        """Starts pw-cat raw audio stream reader."""
        self.stop_mic()
        try:
            self._mic_process = subprocess.Popen(
                ["pw-cat", "-p", "--raw", "--rate", "16000", "--channels", "1", "--format", "s16", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"Error starting mic stream: {e}")

    def write_mic_chunk(self, data: bytes):
        """Feeds raw PCM audio chunk to pw-cat."""
        if self._mic_process and self._mic_process.stdin:
            try:
                self._mic_process.stdin.write(data)
                self._mic_process.stdin.flush()
            except Exception:
                self.stop_mic()

    def stop_mic(self):
        """Stops mic audio stream."""
        if self._mic_process:
            try:
                if self._mic_process.stdin:
                    self._mic_process.stdin.close()
                self._mic_process.terminate()
                self._mic_process.wait(timeout=0.5)
            except Exception:
                pass
            self._mic_process = None

    # ================= 5. Soundboard SFX =================

    def play_sfx(self, name: str):
        """Plays sound effect WAV asynchronously through default sink."""
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
        wav_path = SFX_DIR / f"{safe_name}.wav"
        if wav_path.exists():
            try:
                subprocess.Popen(
                    ["pw-play", str(wav_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                print(f"Error playing SFX {name}: {e}")

    # ================= 6. Fade-Out Sleep Timer =================

    def start_sleep_timer(self, minutes: int, notify_cb: Optional[Callable] = None):
        """Starts a sleep timer that ramps down volume and pauses media."""
        self.cancel_sleep_timer()
        self.sleep_timer_remaining = int(minutes * 60)
        self.initial_volume_before_fade = self.get_volume().get("volume", 70)

        async def _timer_worker():
            try:
                fade_window = min(120, self.sleep_timer_remaining)  # fade in last 2 mins
                start_vol = self.initial_volume_before_fade or 70

                while self.sleep_timer_remaining > 0:
                    if notify_cb:
                        await notify_cb({
                            "type": "sleep_timer_tick",
                            "remaining": self.sleep_timer_remaining,
                            "active": True
                        })

                    # If inside the fade window, smoothly lower volume
                    if self.sleep_timer_remaining <= fade_window and fade_window > 0:
                        fraction = self.sleep_timer_remaining / fade_window
                        new_vol = int(start_vol * fraction)
                        self.set_volume(new_vol)

                    await asyncio.sleep(1)
                    self.sleep_timer_remaining -= 1

                # Timer reached 0: Pause all media
                self.media_action("pause")
                # Restore original volume setting for morning
                if self.initial_volume_before_fade:
                    self.set_volume(self.initial_volume_before_fade)

                if notify_cb:
                    await notify_cb({
                        "type": "sleep_timer_tick",
                        "remaining": 0,
                        "active": False
                    })
            except asyncio.CancelledError:
                if self.initial_volume_before_fade:
                    self.set_volume(self.initial_volume_before_fade)
            finally:
                self.sleep_timer_remaining = 0
                self._sleep_timer_task = None

        self._sleep_timer_task = asyncio.create_task(_timer_worker())

    def cancel_sleep_timer(self):
        """Cancels active sleep timer and restores volume."""
        if self._sleep_timer_task:
            self._sleep_timer_task.cancel()
            self._sleep_timer_task = None
        self.sleep_timer_remaining = 0
        if self.initial_volume_before_fade is not None:
            self.set_volume(self.initial_volume_before_fade)
            self.initial_volume_before_fade = None
