import cv2
import pyautogui
import numpy as np
import time

STABILIZE_TIME = 1
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


def find_image(template_path, screenshot, threshold=0.5):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"ОШИБКА: Не удалось загрузить шаблон: {template_path}")
        return None

    h, w = template.shape[:2]

    if screenshot.shape[0] < h or screenshot.shape[1] < w:
        print("ОШИБКА: Скриншот меньше шаблона.")
        return None

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        x, y = max_loc
        return x, y, w, h
    return None


def track_poplavok(template_path, threshold=0.5, click_offset_ratio=0.2):
    global roi

    SPLASH_PADDING = 100
    SPLASH_CHANGE_THRESHOLD = 10
    SPLASH_PIXEL_THRESHOLD = 280


    prev_frame_gray = None
    stabilize_timer = None
    x = y = w = h = None
    fail_count = 0

    template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template_img is None:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не могу загрузить {template_path}. Выход.")
        return
    template_h, template_w = template_img.shape[:2]

    while True:
        screenshot_full = pyautogui.screenshot()
        screenshot_full = cv2.cvtColor(np.array(screenshot_full), cv2.COLOR_RGB2BGR)

        if roi is not None:
            rx, ry, rw, rh = roi
            rx, ry = max(0, rx), max(0, ry)
            rw, rh = min(rw, screenshot_full.shape[1] - rx), min(rh, screenshot_full.shape[0] - ry)
            search_area = screenshot_full[ry:ry + rh, rx:rx + rw]
        else:
            rx, ry = 0, 0
            search_area = screenshot_full

        if x is None or y is None:
            coords = find_image(template_path, search_area, threshold)
            if coords:
                cx, cy, w, h = coords

                x = rx + cx
                y = ry + cy
                prev_frame_gray = None
                stabilize_timer = time.time()
                print(f"✅ Поплавок найден: {x},{y},{w},{h} — жду стабилизации...")
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
                time.sleep(0.5)
                continue



        roi_x1 = max(0, x - SPLASH_PADDING)
        roi_y1 = max(0, y - SPLASH_PADDING)
        roi_x2 = min(screenshot_full.shape[1], x + w + SPLASH_PADDING)
        roi_y2 = min(screenshot_full.shape[0], y + h + SPLASH_PADDING)


        try:
            splash_roi_bgr = screenshot_full[roi_y1:roi_y2, roi_x1:roi_x2]
            current_frame_gray = cv2.cvtColor(splash_roi_bgr, cv2.COLOR_BGR2GRAY)
        except cv2.error:
            print("⚠️ Ошибка вырезания области, поплавок у края экрана? Ищу заново...")
            x = y = w = h = None
            stabilize_timer = None
            prev_frame_gray = None
            continue


        if stabilize_timer is None or (time.time() - stabilize_timer) < STABILIZE_TIME:

            prev_frame_gray = current_frame_gray
            print(f"Stabilizing... {int(STABILIZE_TIME - (time.time() - stabilize_timer))}s left")
            time.sleep(0.1)
            continue


        if prev_frame_gray is not None and prev_frame_gray.shape == current_frame_gray.shape:

            frame_diff = cv2.absdiff(prev_frame_gray, current_frame_gray)


            bobber_x_rel = SPLASH_PADDING
            bobber_y_rel = SPLASH_PADDING

            bobber_x_end = min(bobber_x_rel + w, frame_diff.shape[1])
            bobber_y_end = min(bobber_y_rel + h, frame_diff.shape[0])


            frame_diff[bobber_y_rel:bobber_y_end, bobber_x_rel:bobber_x_end] = 0


            _, diff_thresh = cv2.threshold(frame_diff, SPLASH_CHANGE_THRESHOLD, 255, cv2.THRESH_BINARY)


            changed_pixels = cv2.countNonZero(diff_thresh)


            if changed_pixels > SPLASH_PIXEL_THRESHOLD:
                print(f"🎣 ПОКЛЁВКА! (Всплеск: {changed_pixels} пикселей)")

                time.sleep(1)

                if roi is not None:

                    click_x = rx + rw // 2
                    click_y = ry + rh // 2 - int(rh * click_offset_ratio)
                else:

                    click_x = x + w // 2
                    click_y = y + h // 2 - int(h * click_offset_ratio)

                pyautogui.click(click_x, click_y)
                print(f"🖱️ Клик в точке ({click_x}, {click_y})")
                time.sleep(1)
                pyautogui.click(click_x, click_y)


                x = y = w = h = None
                stabilize_timer = None
                prev_frame_gray = None
                print("--- Сброс, ищу новый поплавок ---")
                time.sleep(2)
                continue


        prev_frame_gray = current_frame_gray


        time.sleep(0.05)


if __name__ == "__main__":
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    height, width = screenshot.shape[:2]
    small = cv2.resize(screenshot, (int(width * scale), int(height * scale)))

    cv2.namedWindow("Выберите область")
    cv2.setMouseCallback("Выберите область", select_roi)

    while True:
        temp = small.copy()
        if selecting:
            cv2.rectangle(temp, (int(x0 * scale), int(y0 * scale)), (int(x1 * scale), int(y1 * scale)), (0, 0, 255), 2)
        cv2.imshow("Выберите область", temp)
        key = cv2.waitKey(1) & 0xFF
        if roi is not None and not selecting:
            break
        if key == 27:
            print("Выбор отменен.")
            exit()

    cv2.destroyAllWindows()
    print("Запуск отслеживания...")

    track_poplavok("poplavok.png", click_offset_ratio=0)