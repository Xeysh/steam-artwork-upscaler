"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Manual Usage: python gif_region_splitter.py <file.gif>

Controls:
  Left click + drag   → Draw rectangle
  Z                   → Undo last region
  R                   → Clear all regions
  E                   → Export all regions as GIFs
  Q / ESC             → Exit
"""

import sys
import os
import cv2
import numpy as np
from PIL import Image, ImageSequence

COLORS = [
    (0, 80, 220),    # Red
    (0, 200, 50),    # Green
    (220, 100, 0),   # Blue
    (0, 180, 220),   # Yellow
    (180, 0, 200),   # Purple
    (0, 200, 200),   # Yellow-Green
    (200, 150, 0),   # Cyan
    (100, 50, 255),  # Orange
]



def load_gif_frames(path: str):
    gif = Image.open(path)
    frames, durations = [], []
    canvas = Image.new("RGBA", gif.size, (0, 0, 0, 0))

    for raw in ImageSequence.Iterator(gif):
        dur = raw.info.get("duration", 50)
        durations.append(max(int(dur), 20))
        disposal = raw.info.get("disposal_method", 0)
        rgba = raw.convert("RGBA")

        try:
            ox, oy = raw.tile[0][1][0], raw.tile[0][1][1]
        except Exception:
            ox, oy = 0, 0

        full = canvas.copy()
        full.paste(rgba, (ox, oy), rgba)
        frames.append(full.copy())
        if disposal == 2:
            canvas = Image.new("RGBA", gif.size, (0, 0, 0, 0))
        elif disposal != 3:
            canvas = full.copy()

    return frames, durations


def export_region(frames, durations, region, out_path):
    x1, y1, x2, y2 = region
    x1, x2 = sorted([x1, x2])
    y1, y2 = sorted([y1, y2])
    crops = [f.crop((x1, y1, x2, y2)) for f in frames]
    crops[0].save(
        out_path, format="GIF",
        save_all=True,
        append_images=crops[1:],
        loop=0,
        duration=durations,
        optimize=False,
        disposal=2,
    )


class Splitter:
    def __init__(self, gif_path: str):
        self.gif_path  = gif_path
        self.frames, self.durations = load_gif_frames(gif_path)
        self.orig_w, self.orig_h = self.frames[0].size

        max_w, max_h = 1280, 720
        scale_w = max_w / self.orig_w
        scale_h = max_h / self.orig_h
        self.scale = min(1.0, scale_w, scale_h)

        self.disp_w = int(self.orig_w * self.scale)
        self.disp_h = int(self.orig_h * self.scale)

        first = self.frames[0].convert("RGB")
        arr  = np.array(first)
        self.base_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        self.base_img = cv2.resize(self.base_img, (self.disp_w, self.disp_h))

        self.regions: list[tuple[int,int,int,int]] = []
        self.drawing  = False
        self.start    = (0, 0)
        self.cur_end  = (0, 0)

    def to_orig(self, x, y):
        return int(x / self.scale), int(y / self.scale)


    def render(self) -> np.ndarray:
        img = self.base_img.copy()

        for i, (x1, y1, x2, y2) in enumerate(self.regions):
            dx1 = int(x1 * self.scale); dy1 = int(y1 * self.scale)
            dx2 = int(x2 * self.scale); dy2 = int(y2 * self.scale)
            col = COLORS[i % len(COLORS)]
            cv2.rectangle(img, (dx1, dy1), (dx2, dy2), col, 2)
            label = f"SPLIT_{i+1}"
            cv2.rectangle(img, (dx1, dy1-22), (dx1+len(label)*11+6, dy1), col, -1)
            cv2.putText(img, label, (dx1+3, dy1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

        if self.drawing:
            sx, sy = self.start
            ex, ey = self.cur_end
            cv2.rectangle(img, (sx, sy), (ex, ey), (200,200,200), 1)

        lines = [
            f"Regions: {len(self.regions)}  |  GIF: {self.orig_w}x{self.orig_h}  |  Frames: {len(self.frames)}",
            "Left click+drag: Draw region  |  Z: Undo last  |  R: Clear all  |  E: Export  |  Q: Exit",
        ]

        cv2.rectangle(img, (5, 5), (660, 55), (15, 15, 15), -1)

        for i, line in enumerate(lines):
            cv2.putText(img, line, (15, 24 + i * 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        return img


    def on_mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start   = (x, y)
            self.cur_end = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.cur_end = (x, y)

        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            sx, sy = self.start
            ex, ey = x, y
            if abs(ex - sx) > 5 and abs(ey - sy) > 5:
                ox1, oy1 = self.to_orig(min(sx, ex), min(sy, ey))
                ox2, oy2 = self.to_orig(max(sx, ex), max(sy, ey))
                ox1 = max(0, ox1); oy1 = max(0, oy1)
                ox2 = min(self.orig_w, ox2); oy2 = min(self.orig_h, oy2)
                self.regions.append((ox1, oy1, ox2, oy2))

                print(f"  + SPLIT_{len(self.regions)}: ({ox1},{oy1}) → ({ox2},{oy2})  "
                      f"[{ox2-ox1}x{oy2-oy1}px]")

    def run(self):
        win = "GIF Splitter"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, self.disp_w, self.disp_h)
        cv2.setMouseCallback(win, self.on_mouse)

        print(f"\nGIF Loaded: {self.gif_path}")
        print(f"Size: {self.orig_w}x{self.orig_h}  |  Frames: {len(self.frames)}")
        print("Left click and drag to draw a region.\n")

        while True:
            cv2.imshow(win, self.render())
            key = cv2.waitKey(30) & 0xFF

            if key in (ord('q'), 27):       # Q / ESC → Exit
                break

            elif key == ord('z') and self.regions:  # Z → Undo last region
                self.regions.pop()
                print(f"  - SPLIT_{len(self.regions)+1} removed.")

            elif key == ord('r'):           # R → Clear all
                self.regions.clear()
                print("  All regions cleared.")

            elif key == ord('e'):           # E → Export
                self.export()

        cv2.destroyAllWindows()

    def export(self):
        if not self.regions:
            print("Draw a region first.")
            return

        out_dir   = os.path.join(os.path.dirname(self.gif_path), f"output_splits")
        os.makedirs(out_dir, exist_ok=True)

        print(f"\nExporting → {out_dir}/")
        for i, region in enumerate(self.regions, start=1):
            out_path = os.path.join(out_dir, f"split_{i}.gif")
            export_region(self.frames, self.durations, region, out_path)
            kb = os.path.getsize(out_path) / 1024
            x1,y1,x2,y2 = region
            print(f"  split_{i}.gif  ({x2-x1}x{y2-y1}px, {kb:.1f} KB)")

        print(f"{len(self.regions)} GIFs saved.\n")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = sys.argv[1]

    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)

    Splitter(path).run()