# 🎣 OpenCV Fishing Bot

A **lightweight and customizable automated fishing bot** written in Python. The script utilizes Computer Vision (OpenCV) to locate the fishing float on the screen and track bites by analyzing pixel changes (water splashes).

> **💾 Download Executable**
> You can download the compiled `.exe` version of this macro here:  
> [Google Drive](https://drive.google.com/drive/folders/1aUl9aK7EBgviW1OmlUNMsSpTBK_7TMVl?usp=drive_link) or in **release page in this github repository**

## ✨ Features

  * **🎯 ROI Selection:** Manually select the fishing zone at startup to eliminate false positives from the UI.
  * **🖼️ Template Matching:** Locates the float using your custom template image (`poplavok.png`).
  * **🌊 Bite Detection:** Analyzes frame differences. If the number of changed pixels exceeds the threshold (splash), the bot hooks the fish.
  * **⏳ Stabilization:** Ignores water ripples immediately after casting.
  * **🔄 Auto-Recast:** Automatically recasts if the float is lost or if there is no bite for a specified time.

## 🛠️ Requirements

To run the script, you need **Python 3** and the following libraries:

  * `opencv-python` (cv2)
  * `pyautogui`
  * `numpy`

## 🚀 Installation & Setup

### 1\. Clone and Install Dependencies

Download the project and install the required libraries:

```bash
pip install opencv-python pyautogui numpy
```

### 2\. Prepare the Template (Important\!)

The script needs to know what your float looks like.

1.  Take a screenshot of the game.
2.  Crop **only the float** using any image editor (try to keep the surrounding water to a minimum).
3.  Save the image as `poplavok.png` in the script's folder.
4.  **Important:** The game scale/resolution when taking the screenshot must match the scale when running the bot.

### 3\. Run

Execute the script:

```bash
python main.py
```

## 🎮 How to Use

1.  Upon launching, a window showing a stream of your screen (scaled down) will appear.
2.  **Draw a rectangular box** with your mouse to define the fishing area (water + float).
3.  Release the mouse button — the script will lock onto this area.
4.  The bot will start working:
      * Finds float -\> Waits for stabilization -\> Waits for splash -\> Clicks (hooks).

## ⚙️ Configuration

You can adjust variables at the beginning of `main.py` (or inside the `track_poplavok` function) to fit your specific game:

| Variable | Value | Description |
| :--- | :--- | :--- |
| `STABILIZE_TIME` | `1` | Time (in sec) to ignore movement after finding the float (allows ripples from casting to settle). |
| `threshold` | `0.6` | Image matching accuracy (0.1 - 1.0). If it fails to find the float, decrease to `0.4`. |
| `SPLASH_PIXEL_THRESHOLD` | `30` | How many pixels need to change to register as a bite. Lower = more sensitive. |
| `SPLASH_CHANGE_THRESHOLD` | `10` | How drastically a pixel's color must change to be considered movement. |
| `click_offset_ratio` | `0.2` | Click offset from the center of the float (useful if you need to click slightly above/below). |

## ⚠️ Troubleshooting

  * **"ERROR: Screenshot smaller than template"**: You likely saved `poplavok.png` in a resolution that is too high or captured it on a different monitor.
  * **Float found, but bot clicks immediately**: Increase `STABILIZE_TIME` or `SPLASH_PIXEL_THRESHOLD`. There might be too much background movement/ripples in the water.
  * **Float is not found**: Decrease `threshold` (e.g., to `0.4`) or create a new, clearer screenshot for `poplavok.png`.
