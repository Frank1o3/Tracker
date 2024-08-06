from Scripts.Controller import VirtualMouse, VirtualKeyboard
from threading import Thread, Event
from PIL import ImageGrab
import keyboard as kb
from mss import mss
import numpy as np
import cv2 as cv
import math
import time


class Bot:
    def __init__(
        self,
        fov=500,
        threshold=0.5,
        sensitivity=7.5,
        steady_aim_range=25,
        debug=True,
        aim=True,
        steady_aim=False,
    ) -> None:
        # Initialize bot parameters and dependencies
        self.fov = fov
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.steady_aim_range = steady_aim_range
        self.debug = debug
        self.aim = aim
        self.steady_aim = steady_aim

        # Load template image and set colors
        self.template_image = cv.imread("images/point.png", cv.IMREAD_GRAYSCALE)
        self.point_color = (179, 255, 255)

        # Initialize virtual input controllers
        self.vm = VirtualMouse()
        self.vk = VirtualKeyboard()

        # Initialize threading and control variables
        self.stop_event = Event()
        self.positions = []
        self.frame = None
        self.reverse = False
        self.mode = "Idle"
        self.moved = 0
        self.tox = 0
        self.toy = 0
        self.dx = 0
        self.dy = 0
        self.toggle = 0

    def calculate_move(self, current, target) -> int:
        """Calculate the move amount based on sensitivity."""
        return math.ceil((target - current) / self.sensitivity)

    def screenshot_loop(self) -> None:
        """Capture screenshots and filter the relevant color range."""
        sct = mss()
        monitor = sct.monitors[0]
        while not self.stop_event.is_set():
            try:
                # Define the region to capture
                x = (monitor["width"] - self.fov) // 2
                y = (monitor["height"] - self.fov) // 2
                monitor_area = (x, y, x + self.fov, y + self.fov)
                img = ImageGrab.grab(monitor_area)
                img_np = np.array(img)
                img_np = cv.cvtColor(img_np, cv.COLOR_RGB2BGR)

                # Create a mask for the specified color range
                lower_bound = np.array(self.point_color) - np.array([20, 20, 20])
                upper_bound = np.array(self.point_color) + np.array([20, 20, 20])
                mask = cv.inRange(img_np, lower_bound, upper_bound)
                self.frame = cv.bitwise_and(img_np, img_np, mask=mask)
            except Exception as e:
                print(f"Error in screenshot function: {e}")

    def detect_positions(self) -> None:
        """Detect positions of the template image in the frame."""
        if self.template_image is None:
            print("Failed to load template image")
            return

        while not self.stop_event.is_set():
            if self.frame is None:
                continue

            gray_frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
            res = cv.matchTemplate(gray_frame, self.template_image, cv.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)
            self.positions = [
                (x, y, self.template_image.shape[1], self.template_image.shape[0])
                for x, y in zip(*loc[::-1])
            ]

            # Determine the mode based on detection
            if self.mode in ["Idle", "Shooting"]:
                continue
            if not self.positions:
                self.mode = "Scan"
            else:
                self.mode = "Track"

    def move_aim(self) -> None:
        """Move the aim towards detected positions."""
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        top = (monitor["height"] - self.fov) // 2

        while not self.stop_event.is_set():
            cursor_x, cursor_y = self.vm.get_cursor_position()

            if self.mode == "Scan":
                self.scan_mode()
                continue

            if self.mode == "Idle":
                continue

            if not self.positions:
                if kb.is_pressed("shift") and self.toggle <= 15:
                    kb.release("shift")
                    self.toggle += 1
                continue

            self.toggle = 0

            try:
                self.track_mode(cursor_x, cursor_y, left, top)
            except IndexError:
                pass
        time.sleep(0.1)

    def scan_mode(self) -> None:
        """Scan the area by moving the mouse left and right."""
        self.vm.right_down()
        if self.moved > 360:
            self.reverse = True
        elif self.moved < -360:
            self.reverse = False

        move = 5 if not self.reverse else -5
        self.vm.move_relative(move)
        self.moved += move

    def track_mode(self, cursor_x, cursor_y, left, top) -> None:
        """Track and aim at the detected positions."""
        x, y, w, h = self.positions.pop(0)
        target_x = x + left + w // 2
        target_y = y + top + h // 2

        self.dx = target_x - cursor_x
        self.dy = target_y - cursor_y

        move_x = self.calculate_move(cursor_x, target_x)
        move_y = self.calculate_move(cursor_y, target_y)

        move_x = min(move_x, abs(self.dx)) if self.dx >= 0 else max(move_x, -abs(self.dx))
        move_y = min(move_y, abs(self.dy)) if self.dy >= 0 else max(move_y, -abs(self.dy))

        self.tox, self.toy = move_x, move_y
        self.vm.move_relative(int(move_x), int(move_y))

        self.check_and_shoot()

    def check_and_shoot(self) -> None:
        """Check if the aim is steady and perform shooting actions."""
        if (
            abs(self.tox) <= self.steady_aim_range
            and abs(self.toy) <= self.steady_aim_range
        ) and self.steady_aim:
            kb.press("shift")
        else:
            kb.release("shift")

        if abs(self.tox) == 0 and abs(self.toy) == 0:
            self.mode = "Shooting"
            self.moved = 0
            self.reverse = not self.reverse
            self.vm.left_click()
            if self.aim:
                self.vm.right_up()
                time.sleep(0.25)
                self.vm.right_down()
            time.sleep(3.15)
            self.mode = "Track"

    def display_debug_info(self) -> None:
        """Display debug information on the screen."""
        while not self.stop_event.is_set():
            if not self.debug:
                continue

            if self.frame is not None:
                copy = self.frame.copy()
                self.draw_debug_text(copy)
                self.draw_debug_arrows(copy)
                self.draw_detected_positions(copy)
                cv.imshow("feed", copy)
                cv.setWindowProperty("feed", cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL)
                cv.setWindowProperty("feed", cv.WINDOW_FULLSCREEN, cv.WINDOW_NORMAL)
                cv.setWindowProperty("feed", cv.WND_PROP_TOPMOST, 1)
                cv.waitKey(1)

    def draw_debug_text(self, frame) -> None:
        """Draw debug text on the given frame."""
        debug_info = [
            (f"ToX: {self.tox} ToY: {self.toy}", 5, 20),
            (f"X-Diff: {self.dx} Y-Diff: {self.dy}", 5, 40),
            (f"Steady Aim: {'Enabled' if self.steady_aim else 'Disabled'}", 5, 60),
            (f"Aim Down Site: {'Enabled' if self.aim else 'Disabled'}", 5, 80),
            (f"Mode: {self.mode}", 5, 100),
        ]

        for text, x, y in debug_info:
            cv.putText(
                frame,
                text,
                (x, y),
                cv.FONT_HERSHEY_COMPLEX_SMALL,
                1,
                (0, 255, 0),
                1,
                1,
            )

    def draw_debug_arrows(self, frame) -> None:
        """Draw the arrow indicating the movement direction."""
        arrow_end_x = (self.fov // 2) + int(self.tox)
        arrow_end_y = (self.fov // 2) + int(self.toy)
        cv.arrowedLine(
            frame,
            (self.fov // 2, self.fov // 2),
            (arrow_end_x, arrow_end_y),
            (0, 0, 255),
            2,
        )

    def draw_detected_positions(self, frame) -> None:
        """Draw rectangles around detected positions."""
        for x, y, w, h in self.positions:
            cv.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    def toggle_mode(self) -> None:
        """Toggle bot mode between Idle and Scan."""
        while not self.stop_event.is_set():
            if kb.is_pressed("f1"):
                self.mode = "Idle" if self.mode != "Idle" else "Scan"
                print(f"Mode changed to: {self.mode}")
                time.sleep(0.3)  # Debounce the key press
            if kb.is_pressed("f2"):
                print("Stopping bot...")
                self.stop_event.set()

    def start_threads(self) -> None:
        """Start all necessary threads."""
        threads = [
            Thread(target=self.screenshot_loop),
            Thread(target=self.detect_positions),
            Thread(target=self.move_aim),
            Thread(target=self.display_debug_info),
            Thread(target=self.toggle_mode),  # New thread for mode toggling
        ]
        for thread in threads:
            thread.start()

    def run(self) -> None:
        """Main function to start the bot."""
        self.start_threads()
        try:
            while not self.stop_event.is_set():
                time.sleep(0.1)
        finally:
            self.stop_event.set()
            time.sleep(1)
            cv.destroyAllWindows()
            print("Bot stopped successfully.")


if __name__ == "__main__":
    bot = Bot()
    bot.run()
