import cv2
import pyautogui
import numpy as np
import time

STABILIZE_TIME = 2
roi = None
selecting = False
x0 = y0 = x1 = y1 = 0
scale = 0.5

def select_roi(event, x, y, flags, param):
    global x0, y0, x1, y1, selecting, roi, scale
    x_real, y_real = int(x / scale), int(y / scale)
    if event == cv2.EVENT_LBUTTONDOWN:
        x0, y0 = x_real, y_real
        selecting = True
    elif event == cv2.EVENT_MOUSEMOVE and selecting:
        x1, y1 = x_real, y_real
    elif event == cv2.EVENT_LBUTTONUP:
        x1, y1 = x_real, y_real
        selecting = False
        roi = (min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        print(f"✅ Выбрана область: {roi}")

def find_image(template_path, screenshot, threshold=0.6):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    h, w = template.shape[:2]
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        x, y = max_loc
        return x, y, w, h
    return None

def track_poplavok(template_path, threshold=0.6, movement_threshold=1, click_offset_ratio=0.2):
    global roi
    prev_points = None
    stabilize_timer = None
    x = y = w = h = None
    fail_count = 0

    while True:
        screenshot_full = pyautogui.screenshot()
        screenshot_full = cv2.cvtColor(np.array(screenshot_full), cv2.COLOR_RGB2BGR)

        if roi is not None:
            rx, ry, rw, rh = roi
            screenshot = screenshot_full[ry:ry+rh, rx:rx+rw]
        else:
            screenshot = screenshot_full

        if x is None or y is None:
            coords = find_image(template_path, screenshot, threshold)
            if coords:
                cx, cy, w, h = coords
                x = rx + cx if roi else cx
                y = ry + cy if roi else cy
                prev_points = None
                stabilize_timer = time.time()
                print(f"✅ Поплавок найден: {x},{y},{w},{h} — stabilizing...")
            else:
                fail_count += 1
                print(f"🔍 Ищу поплавок... (попытка {fail_count})")
                if fail_count >= 5:
                    fail_count = 0
                    if roi is not None:
                        click_x = rx + rw // 2
                        click_y = ry + rh // 2
                    else:
                        h_scr, w_scr = screenshot_full.shape[:2]
                        click_x, click_y = w_scr // 2, h_scr // 2
                    pyautogui.click(click_x, click_y)
                    print(f"🖱️ Повторный клик в точке ({click_x}, {click_y}) из-за 5 неудач")
                time.sleep(0.2)
                continue

        roi_x1 = max(0, x - 50)
        roi_y1 = max(0, y - 50)
        roi_x2 = min(screenshot_full.shape[1], x + w + 50)
        roi_y2 = min(screenshot_full.shape[0], y + h + 50)
        roi_search = screenshot_full[roi_y1:roi_y2, roi_x1:roi_x2]

        coords = find_image(template_path, roi_search, threshold)

        if coords:
            cx, cy, rw, rh = coords
            x = roi_x1 + cx
            y = roi_y1 + cy
            w, h = rw, rh
            points = [y, y, y + rh, y + rh, y + rh // 2]

            if stabilize_timer is None or (time.time() - stabilize_timer) > STABILIZE_TIME:
                if prev_points is not None:
                    triggered = any(abs(p - pp) > movement_threshold for p, pp in zip(points, prev_points))
                    if triggered:
                        print(f"🎣 ПОКЛЁВКА!")
                        if roi is not None:
                            click_x = rx + roi[2] // 2
                            click_y = ry + roi[3] // 2 - int(roi[3] * click_offset_ratio)
                        else:
                            click_x = x + w // 2
                            click_y = y + h // 2 - int(h * click_offset_ratio)
                        pyautogui.click(click_x, click_y)
                        print(f"🖱️ Клик в точке ({click_x}, {click_y})")
                        time.sleep(1)
                        pyautogui.click(click_x, click_y)
                prev_points = points
            else:
                prev_points = points
        else:
            print("⚠️ Поплавок потерян! Ищу заново...")
            x = y = w = h = None
            stabilize_timer = None

        time.sleep(0.05)

if __name__ == "__main__":
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    height, width = screenshot.shape[:2]
    small = cv2.resize(screenshot, (int(width*scale), int(height*scale)))

    cv2.namedWindow("Выберите область")
    cv2.setMouseCallback("Выберите область", select_roi)

    while True:
        temp = small.copy()
        if selecting:
            cv2.rectangle(temp, (int(x0*scale), int(y0*scale)), (int(x1*scale), int(y1*scale)), (0,0,255), 2)
        cv2.imshow("Выберите область", temp)
        key = cv2.waitKey(1) & 0xFF
        if roi is not None and not selecting:
            break
        if key == 27:
            exit()

    cv2.destroyAllWindows()
    track_poplavok("poplavok.png", click_offset_ratio=0)
