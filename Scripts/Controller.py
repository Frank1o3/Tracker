import ctypes
import time


class VirtualMouse:
    """
    A class to simulate mouse movements and clicks using ctypes and Windows API.
    """

    class POINT(ctypes.Structure):
        """
        Structure to represent a point with x and y coordinates.
        """

        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def __init__(self) -> None:
        """
        Initialize the VirtualMouse object with necessary constants for mouse events.
        """
        self.MOUSEEVENTF_MOVE = 0x0001
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010

    def get_cursor_position(self):
        """
        Get the current cursor position on the screen.

        Returns:
            tuple: (x, y) coordinates of the cursor.
        """
        pt = VirtualMouse.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_mouse_relative(self, dx: int = 0, dy: int = 0):
        """
        Move the mouse cursor relative to its current position.

        Args:
            dx (int): Horizontal movement in pixels.
            dy (int): Vertical movement in pixels.
        """
        x_orig, y_orig = self.get_cursor_position()
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
        ctypes.windll.user32.SetCursorPos(x_orig + dx, y_orig + dy)

    def left_click(self):
        """
        Perform a left mouse button click.
        """
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.1)

    def left_down(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def left_up(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def right_click(self):
        """
        Perform a right mouse button click.
        """
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        time.sleep(0.1)

    def right_down(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)

    def right_up(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


class VirtualKeyboard:
    """
    A class to simulate keyboard key presses using ctypes and Windows API.

    Attributes:
        KEYEVENTF_EXTENDEDKEY (int): Constant for key down event.
        KEYEVENTF_KEYUP (int): Constant for key up event.
        char_to_keycode_map (dict): Mapping of characters to their virtual key codes.
    """

    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002

    char_to_keycode_map = {
        "a": 0x41,
        "b": 0x42,
        "c": 0x43,
        "d": 0x44,
        "e": 0x45,
        "f": 0x46,
        "g": 0x47,
        "h": 0x48,
        "i": 0x49,
        "j": 0x4A,
        "k": 0x4B,
        "l": 0x4C,
        "m": 0x4D,
        "n": 0x4E,
        "o": 0x4F,
        "p": 0x50,
        "q": 0x51,
        "r": 0x52,
        "s": 0x53,
        "t": 0x54,
        "u": 0x55,
        "v": 0x56,
        "w": 0x57,
        "x": 0x58,
        "y": 0x59,
        "z": 0x5A,
        "0": 0x30,
        "1": 0x31,
        "2": 0x32,
        "3": 0x33,
        "4": 0x34,
        "5": 0x35,
        "6": 0x36,
        "7": 0x37,
        "8": 0x38,
        "9": 0x39,
        " ": 0x20,  # Space
        "enter": 0x0D,  # Enter
        "left_shift": 0xA0,  # Left Shift
        "right_shift": 0xA1,  # Right Shift
        "left_ctrl": 0xA2,  # Left Control
        "right_ctrl": 0xA3,  # Right Control
        "alt": 0x12,  # Alt
        "esc": 0x1B,  # Escape
        "backspace": 0x08,  # Backspace
        "tab": 0x09,  # Tab
        "capslock": 0x14,  # Caps Lock
        "left_arrow": 0x25,  # Left Arrow
        "up_arrow": 0x26,  # Up Arrow
        "right_arrow": 0x27,  # Right Arrow
        "down_arrow": 0x28,  # Down Arrow
    }

    def __init__(self) -> None:
        """
        Initializes a VirtualKeyboard instance.
        """
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)

    def char_to_keycode(self, char: str) -> int:
        """
        Converts a character to its corresponding virtual key code.

        Args:
            char (str): The character to convert.

        Returns:
            int: The virtual key code.
        """
        return self.char_to_keycode_map.get(char.lower(), None)

    def key_down(self, hexKeyCode: int):
        """
        Simulates pressing a key down.

        Args:
            hexKeyCode (int): The virtual key code of the key to press.
        """
        self.user32.keybd_event(hexKeyCode, 0, self.KEYEVENTF_EXTENDEDKEY, 0)

    def key_up(self, hexKeyCode: int):
        """
        Simulates releasing a key.

        Args:
            hexKeyCode (int): The virtual key code of the key to release.
        """
        self.user32.keybd_event(
            hexKeyCode, 0, self.KEYEVENTF_EXTENDEDKEY | self.KEYEVENTF_KEYUP, 0
        )

    def press_key(self, hexKeyCode: int):
        """
        Simulates pressing and releasing a key.

        Args:
            hexKeyCode (int): The virtual key code of the key to press and release.
        """
        self.key_down(hexKeyCode)
        time.sleep(0.1)
        self.key_up(hexKeyCode)
        time.sleep(0.1)

    def toggle_capslock(self):
        """
        Toggles the Caps Lock key state.
        """
        self.user32.keybd_event(0x14, 0, self.KEYEVENTF_EXTENDEDKEY, 0)
        self.user32.keybd_event(
            0x14, 0, self.KEYEVENTF_EXTENDEDKEY | self.KEYEVENTF_KEYUP, 0
        )

    def type_string(self, input_string: str):
        """
        Types a string by pressing each character sequentially.

        Args:
            input_string (str): The string to type.
        """
        for char in input_string:
            keycode = self.char_to_keycode(char)
            if keycode is not None:
                self.press_key(keycode)
            else:
                raise ValueError(
                    f"Character '{char}' does not have a virtual key code mapping."
                )

    def type_key_combination(self, *args):
        """
        Simulates typing a key combination (e.g., Ctrl+C, Ctrl+V).

        Args:
            *args: Variable length list of key names to press in combination.
                   Supported key names: 'ctrl', 'shift', 'alt', and any character key.
        """
        for key in args:
            if key.lower() == "ctrl":
                self.key_down(self.char_to_keycode("left_ctrl"))
            elif key.lower() == "shift":
                self.key_down(self.char_to_keycode("left_shift"))
            elif key.lower() == "alt":
                self.key_down(self.char_to_keycode("alt"))
            else:
                keycode = self.char_to_keycode(key)
                if keycode is not None:
                    self.press_key(keycode)
                else:
                    raise ValueError(
                        f"Key '{key}' does not have a virtual key code mapping."
                    )
        time.sleep(0.1)  # Optional delay between key presses
        for key in args[::-1]:
            if key.lower() == "ctrl":
                self.key_up(self.char_to_keycode("left_ctrl"))
            elif key.lower() == "shift":
                self.key_up(self.char_to_keycode("left_shift"))
            elif key.lower() == "alt":
                self.key_up(self.char_to_keycode("alt"))
            else:
                keycode = self.char_to_keycode(key)
                if keycode is not None:
                    self.key_up(keycode)
                else:
                    raise ValueError(
                        f"Key '{key}' does not have a virtual key code mapping."
                    )
