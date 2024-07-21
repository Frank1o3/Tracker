from Controller import VirtualMouse, VirtualKeyboard
from threading import Thread, Event
from PIL import ImageGrab
import keyboard as kb
from mss import mss
import numpy as np
import cv2 as cv
import math
import time
import math

TOX = 0
TOY = 0
FOV = 500
SHOOT = False
STOP = False
FRAME = None
DISTANCE = 0
POSITIONS = []
THRESHOLD = 0.35
SENSITIVITY = 8
VM = VirtualMouse()
VK = VirtualKeyboard()

POINT_COLOR = (179, 255, 255)  # BGR format for OpenCV
TEMPLATE_IMAGE = cv.imread("images\\point.png", cv.IMREAD_GRAYSCALE)


def Good(
    rect: tuple[int, int, int, int], point: tuple[int, int], range: int = 10
) -> bool:
    """
    Check if a point is within a rectangle and close to its center.

    Args:
        rect (tuple): A tuple containing the rectangle's coordinates and size (x, y, width, height).
        point (tuple): A tuple containing the point's coordinates (x, y).

    Returns:
        bool: True if the point is within the rectangle and close to its center, False otherwise.
    """
    Rx, Ry, Rw, Rh = rect
    x, y = point
    RCx = Rx + int(Rw / 2)
    RCy = Ry + int(Rh / 2)

    # Check if the point is within the rectangle
    if Rx <= x <= (Rx + Rw) and Ry <= y <= (Ry + Rh):
        # Calculate the distance from the point to the rectangle's center
        distance = math.sqrt((x - RCx) ** 2 + (y - RCy) ** 2)
        # Check if the distance is less than 10 units
        if distance < range:
            return True

    return False


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
        # Correct the color inversion by converting from RGB to BGR
        i = cv.cvtColor(i, cv.COLOR_RGB2BGR)

        # Create a binary mask where POINT_COLOR is white and all else is black
        lower_bound = np.array(POINT_COLOR) - np.array([20, 20, 20])
        upper_bound = np.array(POINT_COLOR) + np.array([20, 20, 20])
        mask = cv.inRange(i, lower_bound, upper_bound)

        # Apply the mask to filter out non-target areas
        i = cv.bitwise_and(i, i, mask=mask)
        FRAME = i


def detect(event: Event):
    if TEMPLATE_IMAGE is None:
        print("Failed to load template image")
        return
    global POSITIONS
    while not event.is_set():
        if FRAME is None:
            continue
        gray_frame = cv.cvtColor(FRAME, cv.COLOR_BGR2GRAY)
        res = cv.matchTemplate(gray_frame, TEMPLATE_IMAGE, cv.TM_CCOEFF_NORMED)
        loc = np.where(res >= THRESHOLD)
        rects = [
            (*pt, TEMPLATE_IMAGE.shape[1], TEMPLATE_IMAGE.shape[0])
            for pt in zip(*loc[::-1])
        ]
        rects, _ = cv.groupRectangles(rects, groupThreshold=5, eps=0.2)
        POSITIONS = [(x, y, w, h) for (x, y, w, h) in rects]


def move_aim(event: Event):
    global TOX, TOY, SHOOT, DISTANCE
    sct = mss()
    monitor = sct.monitors[0]
    left = (monitor["width"] - FOV) // 2
    top = (monitor["height"] - FOV) // 2
    while not event.is_set():
        cursor_x, cursor_y = VM.get_cursor_position()
        if not POSITIONS:
            CanShoot = False
            x = 0
            y = 0
            TOX = 0
            TOY = 0
            continue
        x, y, w, h = POSITIONS[0]
        if x > 0:
            x += left + int(w / 2)
        else:
            x += left - int(w / 2)
        if cursor_y > 0:
            y += top + int(h / 2)
        else:
            y += top - int(h / 2)
        TOX = calculate(cursor_x, x, SENSITIVITY)
        TOY = calculate(cursor_y, y, SENSITIVITY)
        VM.move_mouse_relative(TOX, TOY)
        if Good((x, y, w, h), (cursor_x, cursor_y), 10) and CanShoot:
            VM.left_click()
        try:
            POSITIONS.pop(0)
        except:
            pass


def display(event: Event):
    while not event.is_set():
        if FRAME is not None:
            COPY = FRAME.copy()
            cv.putText(
                COPY,
                f"ToX: {TOX} ToY: {TOY}",
                (5, 35),
                cv.FONT_ITALIC,
                1,
                (0, 255, 0),
                2,
                1,
            )
            cv.arrowedLine(
                COPY,
                ((FOV // 2), (FOV // 2)),
                ((FOV // 2) + TOX, (FOV // 2) + TOY),
                (0, 0, 255),
                5,
                1,
            )
            for x, y, w, h in POSITIONS:
                cv.rectangle(COPY, (x, y), (x + w, y + h), (255, 0, 0), 3, 1)
            cv.imshow("feed", COPY)
            cv.setWindowProperty("feed", cv.WND_PROP_FULLSCREEN, cv.WINDOW_NORMAL)
            cv.setWindowProperty("feed", cv.WND_PROP_TOPMOST, 1)
            cv.waitKey(1)


def keyboard_event(event: kb.KeyboardEvent):
    global stop_event
    stop_event.set()


if __name__ == "__main__":
    stop_event = Event()
    kb.hook_key("y", keyboard_event, suppress=True)
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
