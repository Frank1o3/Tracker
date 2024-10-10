import math
import time
from random import uniform
from threading import Event, Thread, Lock
import cv2
import keyboard as kb
import numpy as np
from mss import mss
from Libs.Controller import VirtualKeyboard, VirtualMouse


class Bot:
    """Main Class"""

    def __init__(
        self,
        fov=500,
        threshold=0.5,
        sensitivity=7.5,
        steady_aim_range=25,
        debug=True,
        aim=True,
        steady_aim=False,
        auto_shoot=True
    ) -> None:
        self.template_image = cv2.imread(
            "images/point.png", cv2.IMREAD_GRAYSCALE)
        self.steady_aim_range = steady_aim_range
        self.point_color = (179, 255, 255)
        self.sensitivity = sensitivity
        self.steady_aim = steady_aim
        self.auto_shoot = auto_shoot
        self.vk = VirtualKeyboard()
        self.threshold = threshold
        self.stop_event = Event()
        self.vm = VirtualMouse()
        self.positions = []
        self.lock = Lock()
        self.debug = debug
        self.mode = "Offline"
        self.threads = list[Thread]
        self.frame = None
        self.aim = aim
        self.fov = fov
        self.tox, self.toy = 0, 0
        self.dx, self.dy = 0, 0
        if self.debug == True and self.fov != 400:
            self.fov = 400
        sct = mss()
        monitor = sct.monitors[0]
        x = (monitor["width"] - self.fov) // 2
        y = (monitor["height"] - self.fov) // 2
        self.monitor_area = {"left": x, "top": y,
                             "width": self.fov, "height": self.fov}
        self.sct = sct

    def calculate(self, current, target) -> int:
        """Calculate the delta to reach the target."""
        return math.ceil((target - current) / self.sensitivity)

    def screenshot(self) -> None:
        """Capture screenshots from the specified monitor area."""
        sct = mss()
        monitor = sct.monitors[0]
        x = (monitor["width"] - self.fov) // 2
        y = (monitor["height"] - self.fov) // 2
        monitor_area = {"left": x, "top": y,
                        "width": self.fov, "height": self.fov}

        while not self.stop_event.is_set():
            img = np.array(sct.grab(monitor_area))

            # Convert BGRA to BGR
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            lower_bound = np.array(self.point_color) - np.array([30, 30, 30])
            upper_bound = np.array(self.point_color) + np.array([30, 30, 30])

            # Use inRange on BGR image
            mask = cv2.inRange(img, lower_bound, upper_bound)
            self.frame = cv2.bitwise_and(img, img, mask=mask)

    def detect(self) -> None:
        """Detect target positions using template matching."""
        if self.template_image is None:
            print("Failed to load template image.")
            return

        while not self.stop_event.is_set():
            if self.frame is None:
                continue

            gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(
                gray_frame, self.template_image, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)

            boxes = [
                (x, y, self.template_image.shape[1],
                 self.template_image.shape[0])
                for x, y in zip(*loc[::-1])
            ]
            boxes = np.array(boxes, dtype=np.int64)
            boxes, _ = cv2.groupRectangles(
                boxes.tolist(), groupThreshold=1, eps=0.3)

            with self.lock:
                self.positions = [(x, y, w, h) for x, y, w, h in boxes]

    def move_aim(self) -> None:
        """Control the cursor movement based on detected positions."""
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        top = (monitor["height"] - self.fov) // 2
        move_x = 0
        move_y = 0
        while not self.stop_event.is_set():
            if self.mode not in {"Tracking"} or not self.positions:
                kb.release("shift")
                time.sleep(0.1)
                continue

            cursor_x, cursor_y = self.vm.get_cursor_position()
            with self.lock:
                if not self.positions:
                    continue
                x, y, w, h = self.positions.pop(0)

            # Calculate relative movement
            target_x, target_y = (left + x) + (w // 3), (top + y) + (h // 3)
            self.dx, self.dy = target_x - cursor_x, target_y - cursor_y
            self.tox = min(self.calculate(cursor_x, target_x), abs(self.dx))
            self.toy = min(self.calculate(cursor_y, target_y), abs(self.dy))
            if self.steady_aim:
                if abs(self.tox) < self.steady_aim_range and abs(self.toy) < self.steady_aim_range:
                    kb.press("shift")
                else:
                    kb.release("shift")
            if abs(self.tox) < 1 and abs(self.toy) < 1 and self.auto_shoot:
                self.vm.left_down()
                time.sleep(0.5)
                if self.aim:
                    self.vm.right_up()
                self.vm.left_up()
                time.sleep(0.5)
                if self.aim:
                    self.vm.right_down()
                    time.sleep(0.5)
                self.tox, self.toy = uniform(-3, 3), uniform(-3, 3)
            else:
                move_x = self.tox
                move_y = self.toy

            # Move the mouse cursor
            self.vm.move_relative(int(move_x), int(move_y))
            time.sleep(0.05)  # Control movement rate

    def display(self) -> None:
        """Takes care of showing the user data"""
        while not self.stop_event.is_set():
            try:
                if self.frame is not None:
                    copy = self.frame.copy()
                    debug_info = [
                        (f"ToX: {self.tox} ToY: {self.toy}", 5, 20),
                        (f"X-Diff: {self.dx} Y-Diff: {self.dy}", 5, 40),
                        (
                            f"Steady Aim: {
                                'Enabled' if self.steady_aim else 'Disabled'}",
                            5,
                            60,
                        ),
                        (f"Aim Down Site: {'Enabled' if self.aim else 'Disabled'}", 5, 80),
                        (f"Mode: {self.mode}", 5, 100),
                    ]
                    for text, x, y in debug_info:
                        cv2.putText(
                            copy,
                            text,
                            (x, y),
                            cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            1,
                            (0, 255, 0),
                            1,
                            1,
                        )
                    arrow_end_x = (self.fov // 2) + int(self.tox)
                    arrow_end_y = (self.fov // 2) + int(self.toy)
                    cv2.arrowedLine(
                        copy,
                        (self.fov // 2, self.fov // 2),
                        (arrow_end_x, arrow_end_y),
                        (50, 50, 255),
                        5,
                        1,
                    )
                    for x, y, w, h in self.positions:
                        cv2.rectangle(
                            copy, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)

                    cv2.imshow("feed", copy)
                    cv2.setWindowProperty(
                        "feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                    cv2.setWindowProperty(
                        "feed", cv2.WINDOW_FULLSCREEN, cv2.WINDOW_NORMAL)
                    cv2.setWindowProperty("feed", cv2.WND_PROP_TOPMOST, 1)
                    cv2.waitKey(1)
            except Exception:
                pass

    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
        """Handles keyboard events"""
        if event.name == "f1" and event.event_type == "down":
            self.stop_event.set()
            self.vm.left_up()
            self.vm.right_up()
            kb.release("shift")
            return
        elif event.name == "f2" and event.event_type == "down":
            if self.mode == "Offline":
                self.mode = "Tracking"
            else:
                self.mode = "Offline"
            return

    def start(self) -> None:
        """Starts the scaning and key event handling"""
        kb.hook_key("f1", self.keyboard_event, suppress=True)
        kb.hook_key("f2", self.keyboard_event, suppress=True)
        if self.debug:
            self.threads = [
                Thread(target=self.screenshot),
                Thread(target=self.detect),
                Thread(target=self.move_aim),
                Thread(target=self.display),
            ]
        else:
            self.threads = [
                Thread(target=self.screenshot),
                Thread(target=self.detect),
                Thread(target=self.move_aim),
            ]
        for t in self.threads:
            t.start()
        self.stop_event.wait()
        for t in self.threads:
            t.join()
        kb.unhook_all()


if __name__ == "__main__":
    aimbot = Bot(700, 0.75, 8.5, 25, True, True, False, True)
    aimbot.start()
