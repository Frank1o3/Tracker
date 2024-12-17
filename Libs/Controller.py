import ctypes
import time
import random
import math

class VirtualMouse:
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def __init__(self) -> None:
        self.MOUSEEVENTF_MOVE_RELATIVE = 0x0001
        self.MOUSEEVENTF_MOVE = 0x8000
        self.MOUSEEVENTF_LEFTDOWN = 0x0002
        self.MOUSEEVENTF_LEFTUP = 0x0004
        self.MOUSEEVENTF_RIGHTDOWN = 0x0008
        self.MOUSEEVENTF_RIGHTUP = 0x0010

    def get_cursor_position(self):
        pt = VirtualMouse.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_to(self, x: int, y: int):
        # Get the screen width and height
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)

        # Normalize the coordinates to 0-65535
        normalized_x = int(x * 65535 / screen_width)
        normalized_y = int(y * 65535 / screen_height)

        # Perform absolute mouse movement
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_MOVE, normalized_x, normalized_y, 0, 0)


    def move_relative(self, dx: int = 0, dy: int = 0):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_MOVE_RELATIVE, dx, dy, 0, 0)

    def move_in_steps(self, dx: int = 0, dy: int = 0, steps: int = 10):
        step_dx = dx / steps
        step_dy = dy / steps

        for step in range(steps):
            ctypes.windll.user32.mouse_event(
                self.MOUSEEVENTF_MOVE_RELATIVE, int(step_dx), int(step_dy), 0, 0
            )
        remaining_dx = dx - int(step_dx) * steps
        remaining_dy = dy - int(step_dy) * steps
        ctypes.windll.user32.mouse_event(
            self.MOUSEEVENTF_MOVE_RELATIVE, remaining_dx, remaining_dy, 0, 0
        )

    def move_in_curve(self, dx: int = 0, dy: int = 0, steps: int = 10):
        """
        Move the mouse cursor in a curved path using sine function for smooth oscillations.

        Args:
            dx (int): Final horizontal movement in pixels.
            dy (int): Final vertical movement in pixels.
            steps (int): Number of steps to make the movement smoother.
        """
        # Get the current position of the cursor
        x_start, y_start = self.get_cursor_position()
        x_end = x_start + dx
        y_end = y_start + dy

        total_dx, total_dy = 0, 0  # Track cumulative movement

        # Move in steps using sine to create curvature
        for i in range(1, steps + 1):
            t = i / steps  # Normalized step (0 to 1)

            # Smooth sine curve oscillation
            curve_offset = math.sin(t * math.pi)  # Sine oscillation between 0 and 1

            # Calculate the current step's movement with curve offset
            step_x = int(dx * t - total_dx)  # Move along the x-axis
            step_y = int(dy * t - total_dy)  # Move along the y-axis

            # Apply a small curved offset using sine
            offset_x = int(curve_offset * (dx / 4))  # Add horizontal curvature
            offset_y = int(curve_offset * (dy / 4))  # Add vertical curvature

            # Final movement for this step
            move_x = step_x + offset_x
            move_y = step_y + offset_y

            # Move relative to the current position
            ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_MOVE_RELATIVE, move_x, move_y, 0, 0)

            total_dx += step_x
            total_dy += step_y

            time.sleep(0.01)  # Small delay for smooth movement

        # Correct any small remaining movement to hit the exact target
        remaining_dx = x_end - (x_start + total_dx)
        remaining_dy = y_end - (y_start + total_dy)
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_MOVE_RELATIVE, remaining_dx, remaining_dy, 0, 0)




    def left_click(self, delay: float = 0.1):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(delay)
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def left_down(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

    def left_up(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def right_click(self, delay: float = 0.1):
        ctypes.windll.user32.mouse_event(
            self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(delay)
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        time.sleep(delay)

    def right_down(self):
        ctypes.windll.user32.mouse_event(
            self.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)

    def right_up(self):
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
