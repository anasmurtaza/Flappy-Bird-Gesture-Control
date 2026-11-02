"""Flappy Bird gesture game. Run locally: python main.py
Controls: upward motion, Space, Up arrow or click. --no-camera disables webcam.
Motion detection is frame-difference based; it does not identify hands specifically.
"""
import tkinter as tk
import random
import threading
import time
import argparse

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
    CAM_OK = True
except ImportError:
    CAM_OK = False

W, H = 360, 540
GRAV, FLAP, GAP, PW, SPD, GROUND = 0.42, -7.2, 150, 56, 2.4, 60


class Gesture(threading.Thread):
    """Background webcam thread: detects an upward hand flick."""

    def __init__(self, camera_index=0):
        super().__init__(daemon=True)
        self.camera_index = camera_index
        self.flap_event = threading.Event()
        self.running = True
        self.sens = 5
        self.status = "Starting camera..."
        self.preview = None
        self.level = 0.0

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.status = "Camera unavailable - use Space / click"
            cap.release()
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        failures = 0
        prev, prev_y, cool = None, None, 0
        while self.running:
            ok, frame = cap.read()
            if not ok:
                failures += 1
                self.status = "No camera frames - use Space / click"
                if failures >= 40:
                    break
                time.sleep(0.05)
                continue
            failures = 0
            frame = cv2.flip(frame, 1)
            small = cv2.resize(frame, (64, 48))
            gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (3, 3), 0)
            s = self.sens
            mask = np.zeros((48, 64), dtype=bool)
            if prev is not None:
                diff = cv2.absdiff(gray, prev)
                mask = diff > (34 - s * 2.5)
                cnt = int(mask.sum())
                self.level = min(1.0, cnt / (64 * 48) * 4)
                if cnt > 150 - s * 10:
                    y = np.nonzero(mask)[0].mean()
                    if prev_y is not None and prev_y - y > 1.6 - s * 0.1 and cool <= 0:
                        self.flap_event.set()
                        cool = 6
                        self.status = "Flap!"
                    prev_y = y
                else:
                    prev_y = None
                    if cool <= 0:
                        self.status = "Camera on - flick hand up"
            prev = gray
            cool -= 1
            # preview with motion overlay
            vis = cv2.resize(frame, (240, 180))
            m = cv2.resize(mask.astype(np.uint8) * 255, (240, 180), interpolation=cv2.INTER_NEAREST) > 0
            vis[m] = (0.4 * vis[m] + 0.6 * np.array([120, 220, 60])).astype(np.uint8)
            self.preview = Image.fromarray(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
            time.sleep(0.02)
        cap.release()


class Game:
    def __init__(self, root, camera_index=0, use_camera=True):
        self.root = root
        self.closed = False
        root.title("Flappy Bird - Gesture Control")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=W, height=H, bg="#70c5ce", highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=8, pady=8)

        side = tk.Frame(root)
        side.grid(row=0, column=1, padx=8, pady=8, sticky="n")
        # Label width/height are text units until an image is assigned: use a fixed frame.
        preview_frame = tk.Frame(side, width=240, height=180, bg="black")
        preview_frame.pack()
        preview_frame.pack_propagate(False)
        self.cam_label = tk.Label(preview_frame, bg="black", text="No camera", fg="white")
        self.cam_label.pack(fill="both", expand=True)
        self.status = tk.Label(side, text="", font=("Segoe UI", 10, "bold"))
        self.status.pack(pady=4)
        tk.Label(side, text="Sensitivity").pack()
        self.sens = tk.Scale(side, from_=1, to=10, orient="horizontal", length=240)
        self.sens.set(5)
        self.sens.pack()
        self.meter = tk.Canvas(side, width=240, height=10, bg="#ccc", highlightthickness=0)
        self.meter.pack(pady=4)
        self.bar = self.meter.create_rectangle(0, 0, 0, 10, fill="#2a7de1", width=0)
        tk.Label(side, justify="left", fg="#555",
                 text="Flick hand UP to flap\nSpace / Up / Click also work").pack(pady=6)

        self.best = 0
        self.gesture = None
        if CAM_OK and use_camera:
            self.gesture = Gesture(camera_index)
            self.gesture.start()
        else:
            self.status.config(text="Camera disabled - use Space / click" if not use_camera else "Install camera packages; Space / click work")

        root.bind("<space>", lambda e: self.flap())
        root.bind("<Up>", lambda e: self.flap())
        self.canvas.bind("<Button-1>", lambda e: self.flap())
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.reset()
        self.state = "ready"
        self.over_at = 0
        self.tick()
        self.update_side()

    def reset(self):
        self.by, self.bv, self.bx, self.br = H / 2 - 30, 0.0, 90, 13
        self.pipes, self.score, self.frame = [], 0, 0

    def flap(self):
        if self.state == "ready":
            self.state = "play"
        if self.state == "play":
            self.bv = FLAP
        elif self.state == "over" and time.time() - self.over_at > 0.5:
            self.reset()
            self.state = "ready"

    def die(self):
        self.state = "over"
        self.over_at = time.time()
        self.best = max(self.best, self.score)

    def tick(self):
        if self.closed:
            return
        g = self.gesture
        if g:
            g.sens = self.sens.get()
            if g.flap_event.is_set():
                g.flap_event.clear()
                self.flap()
        if self.state == "ready":
            import math
            self.by = H / 2 - 30 + math.sin(time.time() * 5) * 8
        elif self.state == "play":
            self.frame += 1
            self.bv += GRAV
            self.by += self.bv
            if self.frame % 88 == 1:
                self.pipes.append([W, random.randint(60, H - GROUND - GAP - 60), False])
            for p in self.pipes:
                p[0] -= SPD
                if not p[2] and p[0] + PW < self.bx:
                    p[2] = True
                    self.score += 1
                if (self.bx + self.br > p[0] and self.bx - self.br < p[0] + PW and
                        (self.by - self.br < p[1] or self.by + self.br > p[1] + GAP)):
                    self.die()
            self.pipes = [p for p in self.pipes if p[0] > -PW]
            if self.by + self.br > H - GROUND or self.by < -30:
                self.die()
        self.draw()
        self.root.after(16, self.tick)

    def draw(self):
        c = self.canvas
        c.delete("all")
        for p in self.pipes:
            x, t = p[0], p[1]
            c.create_rectangle(x, 0, x + PW, t, fill="#4caf50", outline="#2e7d32", width=3)
            c.create_rectangle(x - 4, t - 18, x + PW + 4, t, fill="#4caf50", outline="#2e7d32", width=3)
            c.create_rectangle(x, t + GAP, x + PW, H, fill="#4caf50", outline="#2e7d32", width=3)
            c.create_rectangle(x - 4, t + GAP, x + PW + 4, t + GAP + 18, fill="#4caf50", outline="#2e7d32", width=3)
        c.create_rectangle(0, H - GROUND, W, H, fill="#ded895", outline="")
        c.create_rectangle(0, H - GROUND, W, H - GROUND + 10, fill="#8bc34a", outline="")
        x, y, r = self.bx, self.by, self.br
        c.create_oval(x - r, y - r, x + r, y + r, fill="#ffd23f", outline="#b8860b", width=2)
        c.create_oval(x + 1, y - 9, x + 11, y + 1, fill="white", outline="")
        c.create_oval(x + 5, y - 6, x + 9, y - 2, fill="black", outline="")
        c.create_polygon(x + 11, y, x + 20, y + 3, x + 11, y + 7, fill="#ff7043", outline="")
        c.create_text(W / 2, 60, text=str(self.score), font=("Segoe UI", 34, "bold"), fill="white")
        if self.state == "ready":
            c.create_text(W / 2, H / 2 + 50, text="Flick up or press Space",
                          font=("Segoe UI", 14, "bold"), fill="white")
        if self.state == "over":
            c.create_rectangle(40, H / 2 - 90, W - 40, H / 2 + 80, fill="#222", stipple="gray50", outline="")
            c.create_text(W / 2, H / 2 - 45, text="Game over", font=("Segoe UI", 24, "bold"), fill="white")
            c.create_text(W / 2, H / 2 - 10, text=f"Score {self.score}   Best {self.best}",
                          font=("Segoe UI", 14), fill="white")
            c.create_text(W / 2, H / 2 + 30, text="Flick up to retry", font=("Segoe UI", 12), fill="white")

    def update_side(self):
        if self.closed:
            return
        g = self.gesture
        if g:
            self.status.config(text=g.status)
            self.meter.coords(self.bar, 0, 0, 240 * g.level, 10)
            if g.preview is not None:
                self.photo = ImageTk.PhotoImage(g.preview)
                self.cam_label.config(image=self.photo, text="")
        self.root.after(60, self.update_side)

    def close(self):
        self.closed = True
        if self.gesture:
            self.gesture.running = False
            self.gesture.join(timeout=0.5)
        self.root.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flappy Bird webcam motion game")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index (default: 0)")
    parser.add_argument("--no-camera", action="store_true", help="Keyboard/mouse only")
    args = parser.parse_args()
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise SystemExit(f"Cannot open desktop window: {exc}. Run locally on a desktop, not Kaggle/Colab.")
    Game(root, camera_index=args.camera, use_camera=not args.no_camera)
    root.mainloop()
