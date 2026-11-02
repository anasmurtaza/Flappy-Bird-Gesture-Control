# Flappy Bird — VS Code desktop edition

Your original Tkinter game adapted into a normal Python project. No browser, localhost server, or notebook is needed. Run on your own computer so the desktop window and webcam are accessible.

## Windows / VS Code setup
1. Install Python 3.11 or 3.12, including Tkinter (standard Python Windows installer) and Python launcher.
2. Extract the ZIP. In VS Code choose File > Open Folder > `Flappy_Gesture_VSCode` (the folder containing main.py).
3. Install the recommended Microsoft Python and Python Debugger extensions.
4. Open Terminal > New Terminal and run:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

5. Ctrl+Shift+P > Python: Select Interpreter > choose `.venv\Scripts\python.exe`.
6. Press F5 and select **Flappy: Webcam**, or run:

```bat
.venv\Scripts\python.exe main.py
```

Alternative: double-click `start_windows.bat` to install dependencies and start the desktop game.

## Play
- Flick your hand UP in front of the webcam to flap.
- Space / Up arrow / click the game canvas also flap.
- After game over, wait half a second then press/click to reset; press again to start.
- Adjust Sensitivity (1–10); use a steady camera and stable lighting.
- This is simple upward-motion detection, not an AI hand-landmark model. Other movement can trigger flaps.

## Without webcam
Select **Flappy: Keyboard only** in Run and Debug, or:

```bat
.venv\Scripts\python.exe main.py --no-camera
```

Try a second camera:

```bat
.venv\Scripts\python.exe main.py --camera 1
```

If webcam unavailable, the game remains usable with keyboard/mouse. Close Teams/Zoom or other apps using the webcam and allow desktop-app camera access in Windows settings.

## macOS / Linux
```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```
Tkinter must be installed with your Python. On Ubuntu/Debian it commonly requires the `python3-tk` OS package. macOS may ask for camera permission for VS Code/Terminal. Remote/headless environments cannot display this local Tk window without a desktop display.

## Changes
- Renamed the notebook-style script to main.py, with a clear entry point.
- Added VS Code F5 configurations and Windows launcher.
- Fixed webcam panel sizing (original text-unit Label sizes created an oversized window).
- Added camera index and keyboard-only launch options.
- Replaced the shared flap boolean with a threading Event.
- Added camera read-failure status and callback guards during window shutdown.
- No external images/assets required; graphics are drawn on Tkinter canvas.

Verification: syntax, imports and keyboard game state logic can be checked without a webcam. A real camera and graphical desktop are required to verify preview and gesture behavior. Full webcam/desktop testing was not available in the delivery environment.

## 👨‍💻 Developer

**Muhammad Anas Murtaza**

GitHub: https://github.com/anasmurtaza

Linkedin: https://www.linkedin.com/in/m-anas-murtaza