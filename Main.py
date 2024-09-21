"""Import's"""
import math
import time
from threading import Event, Thread
from typing import Any

import cv2
import keyboard as kb
import numpy as np
from mss import mss
from PIL import ImageGrab

from Scripts.Controller import VirtualKeyboard, VirtualMouse


class Bot:
    """Main Class"""
    def __init__(
        self,
        Aim=True,
        fov=500,
        threshold=0.5,
        sensitivity=7.5,
        Steady_Aim_Range=25,
        debug=True,
        Steady_Aim=False,
    ) -> None:
        self.template_image = cv2.imread("images/point.png",cv2.IMREAD_GRAYSCALE)
        self.Steady_Aim_Range = Steady_Aim_Range
        self.point_color = (179, 255, 255)
        self.sensitivity = sensitivity
        self.Steady_Aim = Steady_Aim
        self.vk = VirtualKeyboard()
        self.threshold = threshold
        self.stop_event = Event()
        self.vm = VirtualMouse()
        self.reverse = False
        self.positions = Any
        self.debug = debug
        self.mode = "Offline"
        self.threads = list[Thread]
        self.frame = Any
        self.toggle = 0
        self.Aim = Aim
        self.fov = fov
        self.moved = 0
        self.tox = 0
        self.toy = 0
        self.dx = 0
        self.dy = 0

    def calculate(self, x, to) -> int:
        """Calculate the amount needed to get to the target"""
        return math.ceil((to - x) / self.sensitivity)

    def screenshot(self) -> None:
        """Takes the Screenshot"""
        sct = mss()
        monitor = sct.monitors[0]
        while not self.stop_event.is_set():
            try:
                x = (monitor["width"] - self.fov) // 2
                y = (monitor["height"] - self.fov) // 2
                monitor_area = (x, y, x + self.fov, y + self.fov)
                img = ImageGrab.grab(monitor_area)
                i = np.array(img)
                i = cv2.cvtColor(i, cv2.COLOR_RGB2BGR)
                lower_bound = np.array(self.point_color) - np.array([20, 20, 20])
                upper_bound = np.array(self.point_color) + np.array([20, 20, 20])
                mask = cv2.inRange(i, lower_bound, upper_bound)
                self.frame = cv2.bitwise_and(i, i, mask=mask)
            except Exception as e:
                print(f"Error in screenshot function: {e}")

    def detect(self) -> None:
        """Takes care of finding the target"""
        if self.template_image is None:
            print("Failed to load template image")
            return

        while not self.stop_event.is_set():
            if self.frame is None:
                continue

            gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(gray_frame, self.template_image, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)

            # Collect bounding boxes
            boxes = [
                (x, y, self.template_image.shape[1], self.template_image.shape[0])
                for x, y in zip(*loc[::-1])
            ]

            # Convert to the format required by groupRectangles
            boxes = np.array(
                [(x, y, x + w, y + h) for x, y, w, h in boxes], dtype=np.int32
            )
            boxes, weights = cv2.groupRectangles(
                boxes.tolist(), groupThreshold=1, eps=0.2
            )

            self.positions = [(x, y, w - x, h - y) for (x, y, w, h) in boxes]

            if self.mode == "Offline" or self.mode == "Shotting":
                time.sleep(0.1)
                continue

            if self.positions:
                self.mode = "Tracking"
            else:
                self.mode = "Idle"

    def move_aim(self) -> None:
        """Moves the cursor"""
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        bottom = (monitor["height"] - self.fov) // 2

        while not self.stop_event.is_set():
            if self.mode == "Offline" or self.mode == "Idle":
                continue

            if not self.positions:
                if kb.is_pressed("shift") and self.toggle <= 15:
                    kb.release("shift")
                    self.toggle += 1
                continue

            self.toggle = 0

            cursor_x, cursor_y = self.vm.get_cursor_position()
            try:
                x, y, w, h = self.positions.pop(0)
                target_x = x + (left + (w // 2))
                target_y = y + (bottom + (h // 2))
                self.dx = target_x - cursor_x
                self.dy = target_y - cursor_y

                x = self.calculate(cursor_x, target_x)
                y = self.calculate(cursor_y, target_y)

                move_x = min(x, abs(self.dx)) if self.dx >= 0 else max(x, -abs(self.dx))
                move_y = min(y, abs(self.dy)) if self.dy >= 0 else max(y, -abs(self.dy))
                self.tox = move_x
                self.toy = move_y

                self.vm.move_relative(int(move_x), int(move_y))

                if (
                    (abs(move_x) <= self.Steady_Aim_Range)
                    and (abs(move_y) <= self.Steady_Aim_Range)
                ) and self.Steady_Aim == True:
                    kb.press("shift")
                else:
                    kb.release("shift")

                # if abs(move_x) == 0 and abs(move_y) == 0:
                #     self.mode = "Shotting"
                #     self.vm.left_down()
                #     if self.Aim == True:
                #         self.vm.right_up()
                #         time.sleep(5)
                #         self.vm.right_down()
                #     if self.mode == "Offline": return
                #     self.mode = "Tracking"
                # else:
                #     self.vm.left_up()
            except IndexError:
                pass
            time.sleep(0.1)

    def display(self) -> None:
        """Takes care of showing the user data"""
        while not self.stop_event.is_set():
            if self.debug is False:
                time.sleep(0.1)
                continue
            if self.frame is not None:
                copy = self.frame.copy()
                debug_info = [
                    (f"ToX: {self.tox} ToY: {self.toy}", 5, 20),
                    (f"X-Diff: {self.dx} Y-Diff: {self.dy}", 5, 40),
                    (
                        f"Steady Aim: {'Enabled' if self.Steady_Aim else 'Disabled'}",
                        5,
                        60,
                    ),
                    (f"Aim Down Site: {'Enabled' if self.Aim else 'Disabled'}", 5, 80),
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
                    cv2.rectangle(copy, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)

                cv2.imshow("feed", copy)
                cv2.setWindowProperty("feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                cv2.setWindowProperty("feed", cv2.WINDOW_FULLSCREEN, cv2.WINDOW_NORMAL)
                cv2.setWindowProperty("feed", cv2.WND_PROP_TOPMOST, 1)
                cv2.waitKey(1)

    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
        """Handles keyboard events"""
        if event.name == "f1" and event.event_type == "down":
            self.stop_event.set()
            return
        elif event.name == "f2" and event.event_type == "down":
            if self.mode == "Offline":
                self.mode = "Idle"
            else:
                self.mode = "Offline"
            return

    def start(self) -> None:
        """Starts the scaning and key event handling"""
        kb.hook_key("f1", self.keyboard_event, suppress=True)
        kb.hook_key("f2", self.keyboard_event, suppress=True)

        self.threads = [
            Thread(target=self.screenshot),
            Thread(target=self.detect),
            Thread(target=self.move_aim),
            Thread(target=self.display),
        ]
        for t in self.threads:
            t.start()
        self.stop_event.wait()
        for t in self.threads:
            t.join()
        kb.unhook_all()


if __name__ == "__main__":
    aimbot = Bot(500, 0.5, 7, 25, True, False, False)
    aimbot.start()
