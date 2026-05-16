import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import config

VALID_STATES = {"asleep", "idle", "listening", "thinking", "speaking", "error"}


class FaceController:
    def __init__(self, enabled: bool = config.ENABLE_GUI, state_file: Path = config.FACE_STATE_FILE):
        self.enabled = enabled
        self.state_file = Path(state_file)
        self.process: subprocess.Popen | None = None

    def start(self) -> None:
        self.set_state("idle")
        if not self.enabled:
            return
        if not os.environ.get("DISPLAY"):
            print("pi_friend GUI disabled: DISPLAY is not set.", file=sys.stderr)
            return

        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log = open(config.LOG_DIR / "robot_face.log", "ab", buffering=0)
        self.process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--state-file", str(self.state_file)],
            stdout=log,
            stderr=log,
        )
        (config.LOG_DIR / "robot_face.pid").write_text(str(self.process.pid), encoding="utf-8")

    def set_state(self, state: str) -> None:
        if state not in VALID_STATES:
            state = "idle"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"state": state, "time": time.time()}), encoding="utf-8")
        tmp.replace(self.state_file)

    def stop(self) -> None:
        self.set_state("idle")
        if self.process and self.process.poll() is None:
            self.process.terminate()


def _read_state(path: Path) -> str:
    try:
        state = json.loads(path.read_text(encoding="utf-8")).get("state", "idle")
        return state if state in VALID_STATES else "idle"
    except Exception:
        return "idle"


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(points, smooth=True, **kw)


def run_gui(state_file: Path) -> None:
    import tkinter as tk

    root = tk.Tk()
    root.title("pi_friend")
    root.configure(bg="#050607")
    root.overrideredirect(True)
    root.attributes("-fullscreen", True)

    canvas = tk.Canvas(root, bg="#050607", highlightthickness=0, bd=0)
    canvas.pack(fill="both", expand=True)

    def apply_fullscreen():
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.overrideredirect(True)
        root.attributes("-fullscreen", True)
        root.geometry(f"{sw}x{sh}+0+0")
        root.lift()
        root.focus_force()

    root.bind("<Escape>", lambda e=None: root.destroy())
    root.bind("<F11>", lambda e=None: apply_fullscreen())
    root.after(50, apply_fullscreen)
    root.after(800, apply_fullscreen)

    def draw():
        state = _read_state(state_file)
        speaking = state == "speaking"
        t = time.time()

        canvas.delete("all")
        w = max(canvas.winfo_width(), 320)
        h = max(canvas.winfo_height(), 240)
        scale = min(w / 900, h / 560)
        cx = w / 2
        cy = h / 2

        bg = "#050607"
        frame = "#46515a"
        frame_dark = "#20272d"
        screen = "#fff2df"
        ink = "#26323a"
        panel = "#d8cec0"
        button = "#f8efe2"

        canvas.create_rectangle(0, 0, w, h, fill=bg, outline="")

        head_w = min(w * 0.88, 760 * scale)
        head_h = min(h * 0.76, 430 * scale)
        x1 = cx - head_w / 2
        y1 = cy - head_h / 2
        x2 = cx + head_w / 2
        y2 = cy + head_h / 2

        _round_rect(canvas, x1 + 14 * scale, y1 + 16 * scale, x2 + 14 * scale, y2 + 16 * scale,
                    36 * scale, fill="#111417", outline="")
        _round_rect(canvas, x1, y1, x2, y2, 36 * scale,
                    fill=frame, outline=frame_dark, width=max(5, int(8 * scale)))

        margin = 46 * scale
        panel_w = 102 * scale
        sx1 = x1 + margin
        sy1 = y1 + margin
        sx2 = x2 - margin - panel_w
        sy2 = y2 - margin

        _round_rect(canvas, sx1, sy1, sx2, sy2, 24 * scale,
                    fill=screen, outline=frame_dark, width=max(4, int(6 * scale)))

        px1 = sx2 + 24 * scale
        px2 = x2 - 32 * scale
        _round_rect(canvas, px1, sy1, px2, sy2, 18 * scale,
                    fill=panel, outline=frame_dark, width=max(3, int(5 * scale)))

        bx = (px1 + px2) / 2
        gap = (sy2 - sy1) / 4
        for i in range(3):
            by = sy1 + gap * (i + 1)
            r = 18 * scale
            canvas.create_oval(bx - r, by - r, bx + r, by + r,
                               fill=button, outline=frame_dark, width=max(2, int(3 * scale)))
            canvas.create_oval(bx - r * 0.35, by - r * 0.42,
                               bx + r * 0.05, by - r * 0.08,
                               fill="#ffffff", outline="")

        sw = sx2 - sx1
        sh = sy2 - sy1
        eye_y = sy1 + sh * 0.42
        mouth_y = sy1 + sh * 0.64

        for ex in (sx1 + sw * 0.35, sx1 + sw * 0.65):
            ew = 22 * scale
            eh = 28 * scale
            canvas.create_oval(ex - ew, eye_y - eh, ex + ew, eye_y + eh, fill=ink, outline="")
            canvas.create_oval(ex + ew * 0.18, eye_y - eh * 0.48,
                               ex + ew * 0.56, eye_y - eh * 0.12,
                               fill="#ffffff", outline="")

        mx1 = sx1 + sw * 0.43
        mx2 = sx1 + sw * 0.57
        mx = (mx1 + mx2) / 2

        if speaking:
            a = math.sin(t * 8.5) * 4 * scale
            b = math.sin(t * 13.0) * 2 * scale
            canvas.create_line(
                mx1, mouth_y,
                mx1 + (mx - mx1) * 0.45, mouth_y + 4 * scale + b,
                mx, mouth_y + 7 * scale + a,
                mx + (mx2 - mx) * 0.55, mouth_y + 4 * scale - b,
                mx2, mouth_y,
                fill=ink,
                width=max(4, int(6 * scale)),
                capstyle="round",
                smooth=True,
            )
        else:
            canvas.create_line(
                mx1, mouth_y,
                mx, mouth_y + 6 * scale,
                mx2, mouth_y,
                fill=ink,
                width=max(4, int(6 * scale)),
                capstyle="round",
                smooth=True,
            )

        root.after(50, draw)

    draw()
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default=str(config.FACE_STATE_FILE))
    args = parser.parse_args()
    run_gui(Path(args.state_file))


if __name__ == "__main__":
    main()
