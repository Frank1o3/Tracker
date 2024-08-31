from Scripts.XboxController import PhantomForcesController
from Scripts.Controller import VirtualMouse
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
        Steady_Aim_Range=25,
        debug=True,
        Aim=True,
        Steady_Aim=False,
    ) -> None:
        self.template_image = cv.imread("images\\point.png", cv.IMREAD_GRAYSCALE)
        self.Steady_Aim_Range = Steady_Aim_Range
        self.vc = PhantomForcesController()
        self.point_color = (179, 255, 255)
        self.sensitivity = sensitivity
        self.Steady_Aim = Steady_Aim
        self.threshold = threshold
        self.stop_event = Event()
        self.vm = VirtualMouse()
        self.reverse = False
        self.positions = []
        self.debug = debug
        self.mode = "Offline"
        self.threads = []
        self.frame = None
        self.Aim = Aim
        self.fov = fov
        self.moved = 0
        self.tox = 0
        self.toy = 0
        self.dx = 0
        self.dy = 0

    def calculate(self, x, to) -> None:
        return (to - x) / self.sensitivity

    def screenshot(self) -> None:
        sct = mss()
        monitor = sct.monitors[0]
        while not self.stop_event.is_set():
            try:
                x = (monitor["width"] - self.fov) // 2
                y = (monitor["height"] - self.fov) // 2
                monitor_area = (x, y, x + self.fov, y + self.fov)
                img = ImageGrab.grab(monitor_area)
                i = np.array(img)
                i = cv.cvtColor(i, cv.COLOR_RGB2BGR)
                lower_bound = np.array(self.point_color) - np.array([20, 20, 20])
                upper_bound = np.array(self.point_color) + np.array([20, 20, 20])
                mask = cv.inRange(i, lower_bound, upper_bound)
                self.frame = cv.bitwise_and(i, i, mask=mask)
            except Exception as e:
                print(f"Error in screenshot function: {e}")

    def detect(self) -> None:
        if self.template_image is None:
            print("Failed to load template image")
            return

        while not self.stop_event.is_set():
            if self.frame is None:
                continue

            gray_frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
            res = cv.matchTemplate(gray_frame, self.template_image, cv.TM_CCOEFF_NORMED)
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
            boxes, weights = cv.groupRectangles(
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
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        bottom = (monitor["height"] - self.fov) // 2

        while not self.stop_event.is_set():
            if self.mode == "Offline" or self.mode == "Idle":
                continue

            if not self.positions:
                continue

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
                
                self.tox = max(-1.0, min(move_x, 1.0))
                self.toy = max(-1.0, min(move_y, 1.0))

                self.vc.look_around(int(self.tox), int(self.toy))

                if (
                    (abs(move_x) <= self.Steady_Aim_Range)
                    and (abs(move_y) <= self.Steady_Aim_Range)
                ) and self.Steady_Aim == True:
                    self.vc.start_steady_aim()
                else:
                    self.vc.stop_steady_aim("shift")

                if abs(move_x) == 0 and abs(move_y) == 0:
                    self.mode = "Shotting"
                    self.vc.fire_weapon()
                    if self.Aim == True:
                        self.vc.stop_aiming_down_sights()
                        time.sleep(3.25)
                        self.vc.aim_down_sights()
                    time.sleep(0.25)
                    if self.mode == "Offline":
                        return
                    self.mode = "Tracking"
            except IndexError:
                pass
            time.sleep(0.1)

    def display(self) -> None:
        while not self.stop_event.is_set():
            if self.debug == False:
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
                    cv.putText(
                        copy,
                        text,
                        (x, y),
                        cv.FONT_HERSHEY_COMPLEX_SMALL,
                        1,
                        (0, 255, 0),
                        1,
                        1,
                    )
                arrow_end_x = (self.fov // 2) + int(self.tox)
                arrow_end_y = (self.fov // 2) + int(self.toy)
                cv.arrowedLine(
                    copy,
                    (self.fov // 2, self.fov // 2),
                    (arrow_end_x, arrow_end_y),
                    (50, 50, 255),
                    5,
                    1,
                )
                for x, y, w, h in self.positions:
                    cv.rectangle(copy, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)

                cv.imshow("feed", copy)
                cv.setWindowProperty("feed", cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL)
                cv.setWindowProperty("feed", cv.WINDOW_FULLSCREEN, cv.WINDOW_NORMAL)
                cv.setWindowProperty("feed", cv.WND_PROP_TOPMOST, 1)
                cv.waitKey(1)

    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
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
        self.vc.close()
        kb.unhook_all()


if __name__ == "__main__":
    aimbot = Bot(500, 0.5, 7, 25, True, True, False)
    aimbot.start()
