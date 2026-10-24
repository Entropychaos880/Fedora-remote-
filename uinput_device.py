"""
uinput_device.py - Pure-Python Linux virtual mouse and keyboard controller via /dev/uinput.
Works universally on Wayland and X11 without external C-bindings or dependencies.
"""

import os
import fcntl
import struct
import time
from typing import Optional

# Linux input subsystem constants
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02

SYN_REPORT = 0

# Relative axes
REL_X = 0x00
REL_Y = 0x01
REL_HWHEEL = 0x06
REL_WHEEL = 0x08
REL_WHEEL_HI_RES = 0x0B
REL_HWHEEL_HI_RES = 0x0C

# Mouse buttons
BTN_LEFT = 0x110
BTN_RIGHT = 0x111
BTN_MIDDLE = 0x112
BTN_SIDE = 0x113
BTN_EXTRA = 0x114

# Common keyboard keys
KEY_ESC = 1
KEY_1 = 2
KEY_2 = 3
KEY_3 = 4
KEY_5 = 6
KEY_BACKSPACE = 14
KEY_TAB = 15
KEY_ENTER = 28
KEY_LEFTCTRL = 29
KEY_LEFTSHIFT = 42
KEY_SPACE = 57
KEY_LEFTALT = 56
KEY_UP = 103
KEY_LEFT = 105
KEY_RIGHT = 106
KEY_DOWN = 108
KEY_MUTE = 113
KEY_VOLUMEDOWN = 114
KEY_VOLUMEUP = 115
KEY_PLAYPAUSE = 164
KEY_NEXTSONG = 163
KEY_PREVIOUSSONG = 165

# Bus type
BUS_USB = 0x03

# Linux ioctls for /dev/uinput (calculated according to Linux kernel ABI)
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
UI_DEV_SETUP = 0x405C5503  # _IOW('U', 3, sizeof(struct uinput_setup))
UI_SET_EVBIT = 0x40045564  # _IOW('U', 100, int)
UI_SET_KEYBIT = 0x40045565  # _IOW('U', 101, int)
UI_SET_RELBIT = 0x40045566  # _IOW('U', 102, int)

# Character to keycode mapping for basic text typing
CHAR_TO_KEY = {
    'a': 30, 'b': 48, 'c': 46, 'd': 32, 'e': 18, 'f': 33, 'g': 34,
    'h': 35, 'i': 23, 'j': 36, 'k': 37, 'l': 38, 'm': 50, 'n': 49,
    'o': 24, 'p': 25, 'q': 16, 'r': 19, 's': 31, 't': 20, 'u': 22,
    'v': 47, 'w': 17, 'x': 45, 'y': 21, 'z': 44,
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, '0': 11,
    ' ': KEY_SPACE, '\n': KEY_ENTER, '\t': KEY_TAB,
    '-': 12, '=': 13, '[': 26, ']': 27, ';': 39, "'": 40, '`': 41, '\\': 43,
    ',': 51, '.': 52, '/': 53
}

# Shifted symbol mappings (maps character -> (keycode, need_shift))
SHIFTED_SYMBOLS = {
    '!': (2, True), '@': (3, True), '#': (4, True), '$': (5, True), '%': (6, True),
    '^': (7, True), '&': (8, True), '*': (9, True), '(': (10, True), ')': (11, True),
    '_': (12, True), '+': (13, True), '{': (26, True), '}': (27, True),
    ':': (39, True), '"': (40, True), '~': (41, True), '|': (43, True),
    '<': (51, True), '>': (52, True), '?': (53, True)
}


class UInputDevice:
    """Manages a Linux virtual pointer/keyboard device via /dev/uinput."""

    def __init__(self, name: str = "Samsung Remote Trackpad"):
        self.device_name = name
        self.fd: Optional[int] = None
        self._init_device()

    def _init_device(self):
        try:
            self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        except PermissionError:
            raise PermissionError(
                "Cannot access /dev/uinput! Permission denied.\n"
                "To grant non-root access permanently on Fedora, run:\n"
                "    sudo ./setup_uinput.sh\n"
                "Or run the server with sudo:\n"
                "    sudo .venv/bin/python server.py"
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                "/dev/uinput was not found. Please ensure the kernel module is loaded:\n"
                "    sudo modprobe uinput"
            )

        # 1. Enable Event types
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_SYN)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.fd, UI_SET_EVBIT, EV_REL)

        # 2. Enable Relative movement & scroll axes
        for rel in (REL_X, REL_Y, REL_WHEEL, REL_HWHEEL, REL_WHEEL_HI_RES, REL_HWHEEL_HI_RES):
            fcntl.ioctl(self.fd, UI_SET_RELBIT, rel)

        # 3. Enable Mouse Buttons
        for btn in (BTN_LEFT, BTN_RIGHT, BTN_MIDDLE, BTN_SIDE, BTN_EXTRA):
            fcntl.ioctl(self.fd, UI_SET_KEYBIT, btn)

        # 4. Enable Keyboard & Media Keys
        keys = [
            KEY_ESC, KEY_ENTER, KEY_BACKSPACE, KEY_TAB, KEY_SPACE,
            KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
            KEY_LEFTCTRL, KEY_LEFTSHIFT, KEY_LEFTALT,
            KEY_MUTE, KEY_VOLUMEDOWN, KEY_VOLUMEUP,
            KEY_PLAYPAUSE, KEY_NEXTSONG, KEY_PREVIOUSSONG
        ]
        # Include A-Z, 0-9
        keys.extend(CHAR_TO_KEY.values())
        for key in set(keys):
            fcntl.ioctl(self.fd, UI_SET_KEYBIT, key)

        # 5. Setup device metadata
        # struct uinput_setup: id(bustype=2, vendor=2, product=2, version=2), name[80], ff_effects_max=4
        name_bytes = self.device_name.encode("utf-8")[:79].ljust(80, b"\0")
        setup_bytes = struct.pack("HHHH80sI", BUS_USB, 0x1234, 0x5678, 1, name_bytes, 0)
        fcntl.ioctl(self.fd, UI_DEV_SETUP, setup_bytes)

        # 6. Create device
        fcntl.ioctl(self.fd, UI_DEV_CREATE)
        # Allow kernel a brief moment to register the new input node
        time.sleep(0.05)

    def _emit(self, event_type: int, code: int, value: int):
        """Pack and write a struct input_event (24 bytes on 64-bit Linux)."""
        if self.fd is None:
            return
        # struct input_event { timeval time (8+8 bytes); __u16 type; __u16 code; __s32 value; }
        event_bytes = struct.pack("qqHHi", 0, 0, event_type, code, value)
        os.write(self.fd, event_bytes)

    def _sync(self):
        """Send EV_SYN to flush events."""
        self._emit(EV_SYN, SYN_REPORT, 0)

    def move(self, dx: int, dy: int):
        """Relative cursor movement."""
        if dx == 0 and dy == 0:
            return
        if dx != 0:
            self._emit(EV_REL, REL_X, int(dx))
        if dy != 0:
            self._emit(EV_REL, REL_Y, int(dy))
        self._sync()

    def scroll(self, dx: int, dy: int):
        """
        Scroll wheel movement.
        dy > 0: scroll up, dy < 0: scroll down
        dx > 0: scroll right, dx < 0: scroll left
        """
        if dy != 0:
            self._emit(EV_REL, REL_WHEEL, int(dy))
            # Also emit high-res wheel (120 units per notch)
            self._emit(EV_REL, REL_WHEEL_HI_RES, int(dy * 120))
        if dx != 0:
            self._emit(EV_REL, REL_HWHEEL, int(dx))
            self._emit(EV_REL, REL_HWHEEL_HI_RES, int(dx * 120))
        self._sync()

    def button_event(self, button_name: str, state: int):
        """state: 1 for press, 0 for release."""
        btn_map = {
            "left": BTN_LEFT,
            "right": BTN_RIGHT,
            "middle": BTN_MIDDLE,
            "side": BTN_SIDE,
            "extra": BTN_EXTRA,
        }
        btn_code = btn_map.get(button_name.lower())
        if btn_code:
            self._emit(EV_KEY, btn_code, 1 if state else 0)
            self._sync()

    def click(self, button_name: str = "left"):
        """Instant click (press and release)."""
        self.button_event(button_name, 1)
        time.sleep(0.01)
        self.button_event(button_name, 0)

    def key_event(self, key_name: str, state: int):
        """state: 1 for down, 0 for up."""
        name_map = {
            "esc": KEY_ESC,
            "escape": KEY_ESC,
            "enter": KEY_ENTER,
            "return": KEY_ENTER,
            "backspace": KEY_BACKSPACE,
            "tab": KEY_TAB,
            "space": KEY_SPACE,
            "up": KEY_UP,
            "down": KEY_DOWN,
            "left": KEY_LEFT,
            "right": KEY_RIGHT,
            "mute": KEY_MUTE,
            "volumedown": KEY_VOLUMEDOWN,
            "volumeup": KEY_VOLUMEUP,
            "playpause": KEY_PLAYPAUSE,
            "next": KEY_NEXTSONG,
            "prev": KEY_PREVIOUSSONG,
        }
        key_code = name_map.get(key_name.lower())
        if key_code:
            self._emit(EV_KEY, key_code, 1 if state else 0)
            self._sync()

    def type_text(self, text: str, press_enter: bool = False):
        """Simulate typing text characters, punctuation, and optional enter."""
        for char in text:
            key_code = None
            need_shift = False

            if char in SHIFTED_SYMBOLS:
                key_code, need_shift = SHIFTED_SYMBOLS[char]
            elif char.lower() in CHAR_TO_KEY:
                key_code = CHAR_TO_KEY[char.lower()]
                need_shift = char.isupper()

            if key_code:
                if need_shift:
                    self._emit(EV_KEY, KEY_LEFTSHIFT, 1)
                    self._sync()
                self._emit(EV_KEY, key_code, 1)
                self._sync()
                time.sleep(0.005)
                self._emit(EV_KEY, key_code, 0)
                self._sync()
                if need_shift:
                    self._emit(EV_KEY, KEY_LEFTSHIFT, 0)
                    self._sync()
                time.sleep(0.005)

        if press_enter:
            time.sleep(0.02)
            self._emit(EV_KEY, KEY_ENTER, 1)
            self._sync()
            time.sleep(0.01)
            self._emit(EV_KEY, KEY_ENTER, 0)
            self._sync()

    def paste_clipboard(self):
        """Simulate Ctrl+V keyboard shortcut to paste system clipboard."""
        self._emit(EV_KEY, KEY_LEFTCTRL, 1)
        self._sync()
        time.sleep(0.02)
        self._emit(EV_KEY, 47, 1)  # KEY_V (code 47)
        self._sync()
        time.sleep(0.02)
        self._emit(EV_KEY, 47, 0)
        self._sync()
        time.sleep(0.01)
        self._emit(EV_KEY, KEY_LEFTCTRL, 0)
        self._sync()

    def close(self):
        """Destroy the virtual device and close descriptor."""
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, UI_DEV_DESTROY)
                os.close(self.fd)
            except Exception:
                pass
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
