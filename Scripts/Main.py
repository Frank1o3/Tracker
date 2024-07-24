from Controller import VirtualMouse, VirtualKeyboard
from threading import Thread, Event
from PIL import ImageGrab
import keyboard as kb
from mss import mss
import numpy as np
import cv2 as cv
import math
import time


class Aimbot:
    def __init__(
        self, fov=500, threshold=0.5, sensitivity=7.5, debug=True, Steady_Aim=False
    ) -> None:
        self.template_image = cv.imread("images\\point.png", cv.IMREAD_GRAYSCALE)
        self.point_color = (179, 255, 255)
        self.sensitivity = sensitivity
        self.Steady_Aim = Steady_Aim
        self.vk = VirtualKeyboard()
        self.threshold = threshold
        self.Steady_Aim_Range = 15
        self.stop_event = Event()
        self.vm = VirtualMouse()
        self.positions = []
        self.debug = debug
        self.threads = []
        self.frame = None
        self.fov = fov
        self.tox = 0
        self.toy = 0
        self.dx = 0
        self.dy = 0

    def calculate(self, x, to) -> None:
        return math.ceil((to - x) / self.sensitivity)

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
            self.positions = [
                (x, y, self.template_image.shape[1], self.template_image.shape[0])
                for x, y in zip(*loc[::-1])
            ]

    def move_aim(self) -> None:
        sct = mss()
        monitor = sct.monitors[0]
        left = (monitor["width"] - self.fov) // 2
        top = (monitor["height"] - self.fov) // 2
        while not self.stop_event.is_set():
            cursor_x, cursor_y = self.vm.get_cursor_position()
            if not self.positions:
                if kb.is_pressed("shift"):
                    kb.release("shift")
                continue
            try:
                x, y, w, h = self.positions.pop(0)
                target_x = x + left + w // 2
                target_y = y + top + h // 2
                self.dx = target_x - cursor_x
                self.dy = target_y - cursor_y
                self.tox = self.calculate(cursor_x, target_x)
                self.toy = self.calculate(cursor_y, target_y)
                move_x = (
                    min(self.tox, abs(self.dx))
                    if self.dx >= 0
                    else max(self.tox, -abs(self.dx))
                )
                move_y = (
                    min(self.toy, abs(self.dy))
                    if self.dy >= 0
                    else max(self.toy, -abs(self.dy))
                )
                self.vm.move_relative(int(move_x), int(move_y))
                if (
                    (abs(move_x) < self.Steady_Aim_Range)
                    and (abs(move_y) < self.Steady_Aim_Range)
                    and self.Steady_Aim == True
                ):
                    kb.press("shift")
                else:
                    kb.release("shift")
                if abs(move_x) == 0 and abs(move_y) == 0:
                    self.vm.left_click()
                    self.vm.right_up()
                    time.sleep(3)
                    self.vm.right_down()
            except IndexError:
                pass
            time.sleep(0.1)

    def display(self) -> None:
        while not self.stop_event.is_set():
            if self.debug == False:
                try:
                    cv.destroyWindow("feed")
                except:
                    pass
                continue
            if self.frame is not None:
                copy = self.frame.copy()
                cv.putText(
                    copy,
                    f"ToX: {self.tox} ToY: {self.toy} X-Diff: {self.dx} Y-Diff: {self.dy}",
                    (5, 35),
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
                    cv.rectangle(copy, (x, y), (x + w, y + h), (255, 0, 0), 2, 1)
                cv.imshow("feed", copy)
                cv.setWindowProperty("feed", cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL)
                cv.setWindowProperty("feed", cv.WINDOW_FULLSCREEN, cv.WINDOW_NORMAL)
                cv.setWindowProperty("feed", cv.WND_PROP_TOPMOST, 1)
                cv.waitKey(1)

    def keyboard_event(self, event: kb.KeyboardEvent) -> None:
        if event.name == "f1" and event.event_type == "down":
            self.stop_event.set()
        elif event.name == "f2" and event.event_type == "down":
            self.Steady_Aim = not (self.Steady_Aim)

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
        kb.unhook_all()


if __name__ == "__main__":
    aimbot = Aimbot(500, 0.5, 6.5,True,False)
    aimbot.start()
