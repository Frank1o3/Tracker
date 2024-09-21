from Scripts.XboxController import PhantomForcesController
from Scripts.Controller import VirtualMouse
from threading import Thread, Event
from PIL import ImageGrab
import keyboard as kb
from mss import mss
import numpy as np
import cv2 as cv
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
        cutoff_limit=0.25,
    ) -> None:
        try:
            self.template_image = cv.imread("images\\point.png", cv.IMREAD_GRAYSCALE)
            if self.template_image is None:
                raise ValueError("Failed to load template image.")
        except Exception as e:
            print(f"Error loading template image: {e}")
            return

        self.sensitivity_reciprocal = 1 / sensitivity
        self.steady_aim_range = steady_aim_range
        self.vc = PhantomForcesController()
        self.point_color = (179, 255, 255)
        self.sensitivity = sensitivity
        self.steady_aim = steady_aim
        self.threshold = threshold
        self.stop_event = Event()
        self.vm = VirtualMouse()
        self.reverse = False
        self.positions = []
        self.debug = debug
        self.mode = "Idle"
        self.threads = []
        self.frame = None
        self.ads = False
        self.aim = aim
        self.fov = fov
        self.moved = 0
        self.tox = 0
        self.toy = 0
        self.dx = 0
        self.dy = 0
        self.cutoff_limit = cutoff_limit

    def calculate(self, x, to) -> float:
        distance = abs(to - x)
        adjusted_sensitivity = self.sensitivity_reciprocal * (distance / self.fov)
        result = (to - x) * adjusted_sensitivity

        clamped_result = round(
            max(min(result, self.cutoff_limit), -self.cutoff_limit), 3
        )

        if abs(clamped_result) < 0.05:
            clamped_result = 0.0

        return clamped_result

    def screenshot(self) -> None:
        sct = mss()
        monitor = sct.monitors[0]
        x = (monitor["width"] - self.fov) // 2
        y = (monitor["height"] - self.fov) // 2
        monitor_area = {"left": x, "top": y, "width": self.fov, "height": self.fov}

        while not self.stop_event.is_set():
            try:
                sct_img = sct.grab(monitor_area)
                img = np.array(sct_img)
                img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)

                lower_bound = np.array(self.point_color) - np.array([20, 20, 20])
                upper_bound = np.array(self.point_color) + np.array([20, 20, 20])
                mask = cv.inRange(img, lower_bound, upper_bound)
                self.frame = cv.bitwise_and(img, img, mask=mask)
            except Exception as e:
                print(f"Error in screenshot function: {e}")
                self.stop_event.set()

    def detect(self) -> None:
        while not self.stop_event.is_set():
            if self.frame is None:
                continue

            try:
                gray_frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
                res = cv.matchTemplate(
                    gray_frame, self.template_image, cv.TM_CCOEFF_NORMED
                )
                loc = np.where(res >= self.threshold)

                boxes = [
                    (x, y, self.template_image.shape[1], self.template_image.shape[0])
                    for x, y in zip(*loc[::-1])
                ]

                boxes = np.array(
                    [(x, y, x + w, y + h) for x, y, w, h in boxes], dtype=np.int32
                )
                boxes, weights = cv.groupRectangles(
                    boxes.tolist(), groupThreshold=1, eps=0.2
                )

                self.positions = [(x, y, w - x, h - y) for (x, y, w, h) in boxes]

                if self.mode in ["Offline", "Shooting"]:
                    continue

                self.mode = "Tracking" if self.positions else "Idle"

            except Exception as e:
                print(f"Error in detect function: {e}")
                self.stop_event.set()

    def move_aim(self) -> None:
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        bottom = (monitor["height"] - self.fov) // 2

        while not self.stop_event.is_set():
            try:
                if self.mode == "Offline":
                    self.ads = False
                    continue
                elif self.mode == "Idle":
                    if not self.ads:
                        self.vc.aim_down_sights()
                        self.ads = True

                if not self.positions:
                    self.vc.look_around_float(0.0, 0.0)
                    continue

                cursor_x, cursor_y = self.vm.get_cursor_position()

                x, y, w, h = self.positions.pop(0)
                target_x = x + left + (w // 2)
                target_y = y + bottom + (h // 2)
                self.dx = self.calculate(cursor_x, target_x)
                self.dy = self.calculate(cursor_y, target_y)

                self.vc.look_around_float(self.dx, -self.dy)

                if (
                    abs(self.dx) <= self.steady_aim_range
                    and abs(self.dy) <= self.steady_aim_range
                    and self.steady_aim
                ):
                    self.vc.start_steady_aim()
                else:
                    self.vc.stop_steady_aim()

                if abs(self.dx) <= 0.05 and abs(self.dy) <= 0.05:
                    self.mode = "Shooting"
                    self.vc.fire_weapon()
                    if self.aim:
                        self.vc.stop_aiming_down_sights()
                        self.ads = False
                        time.sleep(3.25)
                        self.vc.aim_down_sights()
                        self.ads = True
                    time.sleep(0.25)
                    if self.mode == "Offline":
                        return
                    self.mode = "Tracking"

            except IndexError:
                continue
            except Exception as e:
                print(f"Error in move_aim function: {e}")
                self.stop_event.set()

    def display(self) -> None:
        while not self.stop_event.is_set():
            if not self.debug:
                time.sleep(0.1)
                continue
            if self.frame is not None:
                try:
                    copy = self.frame.copy()
                    debug_info = [
                        (f"ToX: {self.tox} ToY: {self.toy}", 5, 20),
                        (f"X-Diff: {self.dx} Y-Diff: {self.dy}", 5, 40),
                        (
                            f"Steady Aim: {'Enabled' if self.steady_aim else 'Disabled'}",
                            5,
                            60,
                        ),
                        (
                            f"Aim Down Sights: {'Enabled' if self.aim else 'Disabled'}",
                            5,
                            80,
                        ),
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
                    cv.setWindowProperty(
                        "feed", cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL
                    )
                    cv.setWindowProperty("feed", cv.WINDOW_FULLSCREEN, cv.WINDOW_NORMAL)
                    cv.setWindowProperty("feed", cv.WND_PROP_TOPMOST, 1)
                    cv.waitKey(1)
                except Exception as e:
                    print(f"Error in display function: {e}")
                    self.stop_event.set()

    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
        if event.name == "f1" and event.event_type == "down":
            self.stop_event.set()
            return
        elif event.name == "f2" and event.event_type == "down":
            self.mode = "Idle" if self.mode == "Offline" else "Offline"
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

        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()


if __name__ == "__main__":
    aimbot = Bot(500, 0.5, 85, 25, True, True, False)
    time.sleep(3)
    kb.send("f11")
    time.sleep(3)
    aimbot.start()
