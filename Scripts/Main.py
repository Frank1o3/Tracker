from Controller import VirtualMouse, VirtualKeyboard
from threading import Thread, Event, Lock
from PIL import ImageGrab
import keyboard as kb
from mss import mss
import numpy as np
import cv2 as cv
import math
import time

TOX = 0
TOY = 0
FOV = 500
SHOOT = False
STOP = False
FRAME = None
POSITIONS = []
THRESHOLD = 0.74
SENSITIVITY = 5
FRAME_LOCK = Lock()
VM = VirtualMouse()
VK = VirtualKeyboard()


TEMPLATE_IMAGE = cv.imread(
    "C:/Users/jahdy/OneDrive/Desktop/Tracker/images/point.png", cv.IMREAD_GRAYSCALE
)


def calculate(x: int, to: int, sensitivity: int) -> int:
    return math.ceil((to - x) // sensitivity)


def screenshot(event: Event):
    sct = mss()
    monitor = sct.monitors[0]
    global FRAME
    while not event.is_set():
        x = (monitor["width"] - FOV) // 2
        y = (monitor["height"] - FOV) // 2
        monitor_area = (x, y, x + FOV, y + FOV)
        img = ImageGrab.grab(monitor_area)
        i = np.array(img)
        with FRAME_LOCK:
            FRAME = cv.cvtColor(i, cv.COLOR_RGB2BGR)


def detect(event: Event):
    if TEMPLATE_IMAGE is None:
        print("Failed to load template image")
        return
    TEMPLATE_IMAGE[TEMPLATE_IMAGE == 255] = 0
    global POSITIONS
    while not event.is_set():
        with FRAME_LOCK:
            if FRAME is None:
                continue
            gray_frame = cv.cvtColor(FRAME, cv.COLOR_BGR2GRAY)
        res = cv.matchTemplate(gray_frame, TEMPLATE_IMAGE, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= THRESHOLD)
        POSITIONS = list(zip(*loc[::-1]))


def move_aim(event: Event):
    if TEMPLATE_IMAGE is None:
        print("Failed to load template image")
        return
    w, h = TEMPLATE_IMAGE.shape[::-1]
    sct = mss()
    monitor = sct.monitors[0]
    left = (monitor["width"] - FOV) // 2
    top = (monitor["height"] - FOV) // 2
    global TOX, TOY, SHOOT
    while not event.is_set():
        if not POSITIONS:
            continue
        x, y = POSITIONS[0]
        x += left + (w // 2) + 4
        y += top + (h // 2) + 4
        cursor_x, cursor_y = VM.get_cursor_position()
        TOX = calculate(cursor_x, x, SENSITIVITY)
        TOY = calculate(cursor_y, y, SENSITIVITY)
        if (abs(x - cursor_x) <= 5 and abs(y - cursor_y) <= 5):
            SHOOT = True
            VM.left_click()
        else:
            SHOOT = False
        VM.move_mouse_relative(TOX, TOY)
        try:
            POSITIONS.pop(0)
        except:
            pass
        time.sleep(0.05)

def display(event: Event):
    while not event.is_set():
        if FRAME is not None:
            cv.putText(FRAME, f"Shoot: {SHOOT}", (5,35),cv.FONT_ITALIC,1,(0,255,0),2,1)
            cv.arrowedLine(
                FRAME,
                ((FOV // 2), (FOV // 2)),
                ((FOV // 2) + TOX, (FOV // 2) + TOY),
                (0, 0, 0),
                5,
                1,
            )
            for x, y in POSITIONS:
                cv.rectangle(FRAME, (x, y), (x + 15, y + 15), (255, 0, 0), 3, 1)
            cv.imshow("feed", FRAME)
            cv.setWindowProperty("feed", cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL)
            cv.setWindowProperty("feed", cv.WND_PROP_TOPMOST, 1)
            cv.waitKey(1)


def keyboard_event(event: kb.KeyboardEvent):
    global stop_event
    stop_event.set()


if __name__ == "__main__":
    stop_event = Event()
    kb.hook_key("q", keyboard_event, suppress=True)
    threads = [
        Thread(target=screenshot, args=(stop_event,)),
        Thread(target=detect, args=(stop_event,)),
        Thread(target=move_aim, args=(stop_event,)),
        Thread(target=display, args=(stop_event,)),
    ]

    for t in threads:
        t.start()

    stop_event.wait()
    for t in threads:
        t.join()
    kb.unhook_all()
