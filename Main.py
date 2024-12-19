"""Import's"""

import math
import time
from threading import Event, Thread

import cv2
import keyboard as kb
import numpy as np
from mss import mss

from Libs.Aim import get_future_position_nl, get_vel
from Libs.Controller import VirtualMouse


class Bot:
    """Main Class"""

    def __init__(
        self,
        fov=500,
        threshold=0.5,
        sensitivity=7.5,
        debug=True,
    ) -> None:
        self.template_image = cv2.imread("images/point.png", cv2.IMREAD_GRAYSCALE)
        self.point_color = (179, 255, 255)
        self.sensitivity = sensitivity
        self.threshold = threshold
        self.stop_event = Event()
        self.vm = VirtualMouse()
        self.positions = None
        self.debug = debug
        self.mode = "Offline"
        self.threads = list[Thread]
        self.predicted_X = 0
        self.predicted_Y = 0
        self.frame = None
        self.fov = fov
        self.tox = 0
        self.toy = 0
        self.dx = 0
        self.dy = 0
        self.t2 = 0
        self.t = 0

    def calculate(self, x, to) -> int:
        """Calculate the amount needed to get to the target"""
        return math.ceil((to - x) / self.sensitivity)

    def screenshot(self) -> None:
        """Takes the Screenshot"""
        sct = mss()
        monitor = sct.monitors[0]
        x = (monitor["width"] - self.fov) // 2
        y = (monitor["height"] - self.fov) // 2
        monitor_area = (x, y, x + self.fov, y + self.fov)
        while not self.stop_event.is_set():
            start_time = time.perf_counter()  # Start timing

            try:
                img = np.array(sct.grab(monitor_area))
                i = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Use BGRA to BGR
                lower_bound = np.array(self.point_color) - np.array([35, 35, 35])
                upper_bound = np.array(self.point_color) + np.array([35, 35, 35])
                mask = cv2.inRange(i, lower_bound, upper_bound)
                self.frame = cv2.bitwise_and(i, i, mask=mask)
            except Exception as e:
                print(f"Error in screenshot function: {e}")

            end_time = time.perf_counter()  # End timing
            # Calculate detection duration
            self.t2 = end_time - start_time


    def detect(self) -> None:
        """Takes care of finding the target and calculates detection time"""
        if self.template_image is None:
            print("Failed to load template image")
            return

        while not self.stop_event.is_set():
            if self.frame is None:
                continue

            start_time = time.perf_counter()  # Start timing

            gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(
                gray_frame, self.template_image, cv2.TM_CCOEFF_NORMED
            )
            loc = np.where(res >= self.threshold)

            # Collect bounding boxes
            boxes = [
                (x, y, self.template_image.shape[1], self.template_image.shape[0])
                for x, y in zip(*loc[::-1])
            ]

            # Convert to the format required by groupRectangles
            boxes = np.array(
                [(x, y, x + w, y + h) for x, y, w, h in boxes], dtype=np.int64
            )
            boxes, weights = cv2.groupRectangles(
                boxes.tolist(), groupThreshold=1, eps=0.2
            )

            self.positions = [(x, y, w - x, h - y) for (x, y, w, h) in boxes]

            if self.mode == "Offline":
                continue

            if self.positions:
                self.mode = "Tracking"
            else:
                self.mode = "Idle"
            
            end_time = time.perf_counter()  # End timing
            # Calculate detection duration
            self.t = end_time - start_time

    def move_aim(self) -> None:
        """Moves the cursor"""
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        bottom = (monitor["height"] - self.fov) // 2
        oldX = 0
        oldY = 0
        oldVX = 0
        oldVY = 0
        fire = False
        while not self.stop_event.is_set():
            if self.mode == "Offline" or self.mode == "Idle":
                self.tox = 0
                self.toy = 0
                time.sleep(0.1)
                fire = False
                continue

            cursor_x, cursor_y = self.vm.get_cursor_position()
            try:

                x, y, w, h = self.positions.pop(0)
                vx, vy = get_vel(x, y, oldX, oldY)
                target_x = math.ceil(left + (w // 3))
                target_y = math.ceil(bottom + (h // 3))

                # self.vm.move_to(int(target_x), int(target_y))

                self.predicted_X, self.predicted_Y = get_future_position_nl(
                    oldX,
                    oldY,
                    math.ceil(x),
                    math.ceil(y),
                    oldVX,
                    oldVY,
                    sum((self.t,self.t2)),
                )

                oldX = x if oldX != x else oldX
                oldY = y if oldY != y else oldY

                oldVX = vx if oldX != vx else oldVX
                oldVY = vy if oldY != vy else oldVY

                target_x = target_x + (self.predicted_X)
                target_y = target_y + (self.predicted_Y)

                self.dx = target_x - cursor_x
                self.dy = target_y - cursor_y

                x = self.calculate(cursor_x, target_x)
                y = self.calculate(cursor_y, target_y)

                self.tox = (
                    min(x, abs(self.dx)) if self.dx > 0 else max(x, -abs(self.dx))
                )
                self.toy = (
                    min(y, abs(self.dy)) if self.dy > 0 else max(y, -abs(self.dy))
                )

                if abs(self.tox) < 1 and abs(self.toy) < 1 and fire == True:
                    self.vm.left_down()
                    time.sleep(0.1)
                    self.vm.left_up()
                    time.sleep(0.1)

                if (abs(self.tox) < 20 and abs(self.toy) < 20):
                    self.vm.move_relative(int(self.tox), int(self.toy))
                else:
                    self.vm.move_in_steps(int(self.tox), int(self.toy))
                fire = True
            except Exception:
                pass
            time.sleep(0.1)
            

    def display(self) -> None:
        """Takes care of showing the user data"""
        while not self.stop_event.is_set():
            try:
                if self.frame is not None:
                    copy = self.frame.copy()
                    arrow_end_x = (self.fov // 2) + int(self.tox)
                    arrow_end_y = (self.fov // 2) + int(self.toy)
                    cv2.arrowedLine(
                        copy,
                        (self.fov // 2, self.fov // 2),
                        (self.predicted_X, self.predicted_Y),
                        (255, 50, 50),
                        5,
                        1,
                    )
                    cv2.arrowedLine(
                        copy,
                        (self.fov // 2, self.fov // 2),
                        (arrow_end_x, arrow_end_y),
                        (50, 50, 255),
                        5,
                        1,
                    )
                    for x, y, w, h in self.positions:
                        cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 0, 0), 1, 1)
                    debug_info = [
                        (f"ToX: {self.tox} ToY: {self.toy}", 5, 20),
                        (f"X-Diff: {self.dx} Y-Diff: {self.dy}", 5, 40),
                        (
                            f"PredictedX: {self.predicted_X} PredictedY: {self.predicted_Y}",
                            5,
                            60,
                        ),
                        (f"Mode: {self.mode}", 5, 80),
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

                    cv2.imshow("feed", copy)
                    cv2.setWindowProperty(
                        "feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL
                    )
                    cv2.setWindowProperty(
                        "feed", cv2.WINDOW_FULLSCREEN, cv2.WINDOW_NORMAL
                    )
                    cv2.setWindowProperty("feed", cv2.WND_PROP_TOPMOST, 1)
                    cv2.waitKey(1)
            except Exception:
                pass

    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
        """Handles keyboard events"""
        if event.name == "f2" and event.event_type == "down":
            self.stop_event.set()
            return
        elif event.name == "f1" and event.event_type == "down":
            if self.mode == "Offline":
                self.mode = "Idle"
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
    aimbot = Bot(500, 0.5, 7.2, False)
    aimbot.start()
