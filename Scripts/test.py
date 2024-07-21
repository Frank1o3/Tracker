from threading import Thread, Event, Lock
from PIL import ImageGrab
import keyboard as kb
from mss import mss
import numpy as np
import cv2 as cv

FOV = 500
FRAME = None
FRAME_LOCK = Lock()
Path = str(__file__).replace("Scripts\\test.py", "images\\Background.png")
BACKGROUND = cv.imread(Path)
BACKGROUND = cv.resize(BACKGROUND, (500, 500))

# Variables to control the position of the circle image
x_pos = 120
y_pos = 170


def screenshot(event: Event):
    sct = mss()
    monitor = sct.monitors[0]
    global FRAME
    while not event.is_set():
        x = (monitor["width"] - FOV) // 2
        y = (monitor["height"] - FOV) // 2
        monitor_area = (x, y, x + FOV, y + FOV)
        img = ImageGrab.grab(bbox=monitor_area)  # Correct the bbox assignment
        i = np.array(img)
        with FRAME_LOCK:
            FRAME = cv.cvtColor(i, cv.COLOR_RGB2BGR)
            FRAME = cv.resize(FRAME, (220, 220))
            radius = min(FRAME.shape[1], FRAME.shape[0]) // 2
            mask = np.zeros(FRAME.shape[:2], dtype=np.uint8)
            center = (FRAME.shape[1] // 2, FRAME.shape[0] // 2)
            cv.circle(mask, center, radius, (255), thickness=-1)
            FRAME = cv.bitwise_and(FRAME, FRAME, mask=mask)
            border_color = (0, 0, 0)
            border_thickness = 10
            cv.circle(FRAME, center, radius, border_color, border_thickness)


def display(event: Event):
    while not event.is_set():
        with FRAME_LOCK:
            if FRAME is None:
                continue

            display_image = BACKGROUND.copy()
            cv.putText(
                display_image,
                "Target: (x,y)",
                (5, 45),
                cv.FONT_ITALIC,
                1,
                (0, 255, 0),
                2,
                1,
            )

            # Calculate offsets and mask parameters
            frame_height, frame_width = FRAME.shape[:2]
            x_offset = x_pos - frame_width // 2
            y_offset = y_pos - frame_height // 2
            x_offset = max(0, min(display_image.shape[1] - frame_width, x_offset))
            y_offset = max(0, min(display_image.shape[0] - frame_height, y_offset))

            # Region of Interest (ROI)
            roi = display_image[
                y_offset : y_offset + frame_height, x_offset : x_offset + frame_width
            ]

            # Create mask and apply
            radius = min(frame_width, frame_height) // 2
            mask = np.zeros((frame_height, frame_width), dtype=np.uint8)
            center = (frame_width // 2, frame_height // 2)
            cv.circle(mask, center, radius, (255), thickness=-1)
            mask_inv = cv.bitwise_not(mask)
            background_part = cv.bitwise_and(roi, roi, mask=mask_inv)
            frame_part = cv.bitwise_and(FRAME, FRAME, mask=mask)
            dst = cv.add(background_part, frame_part)
            display_image[
                y_offset : y_offset + frame_height, x_offset : x_offset + frame_width
            ] = dst

            # Arrow line centered on the mask
            arrow_start = (x_pos, y_pos)
            # Calculate maximum valid length of the arrow line within the circle
            length = min(
                radius,
                np.linalg.norm(
                    np.array((x_pos, y_pos)) - np.array((x_pos, y_pos - radius))
                ),
            )
            # Adjust the end of the arrow line to be within the circle
            direction = np.array([0, -1])  # Straight up direction
            arrow_end = np.array(arrow_start) + direction * length
            arrow_end = tuple(map(int, arrow_end))

            # Create an overlay for transparency
            overlay = display_image.copy()
            cv.arrowedLine(
                overlay, arrow_start, arrow_end, (255, 0, 0), 5, tipLength=0.1
            )

            # Apply transparency
            alpha = 0.5
            display_image = cv.addWeighted(overlay, alpha, display_image, 1 - alpha, 0)

            # Show the image
            cv.imshow("feed", display_image)
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
        Thread(target=display, args=(stop_event,)),
    ]

    for t in threads:
        t.start()

    stop_event.wait()
    for t in threads:
        t.join()
    kb.unhook_all()
