import sys, os, time
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.theme import (
    COLORS,
    FONTS,
    SIZES,
    apply_window_style,
    make_frame,
    make_label,
    make_entry,
    make_button,
    role_header,
)
from attack.seed_image_generator.perlin import render_cells, image_fingerprint

CANVAS_SIZE = 300
CELLS = 75
CELL_PX = CANVAS_SIZE // CELLS  # 4


def _heat_color(t: float) -> str:
    """Map [0..1] to a blue→purple→red heat palette."""
    # blue (0,0,180) → purple (120,0,180) → red (220,30,30)
    if t < 0.5:
        s = t * 2
        r = int(0 + s * 120)
        g = 0
        b = int(180 + s * 0)
    else:
        s = (t - 0.5) * 2
        r = int(120 + s * 100)
        g = int(0 + s * 30)
        b = int(180 - s * 150)
    return f"#{r:02x}{g:02x}{b:02x}"


class GeneratorWindow:
    def __init__(self, root: tk.Tk, shared: dict):
        self.root = root
        self.shared = shared
        self.seed_var = tk.StringVar(value="42")

        apply_window_style(root, "IMAGE GENERATOR", role="blue")
        W, H = 400, 520
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw - 820)//2}+{(sh - H)//2}")
        self._build()
        self._generate()

    def _build(self):
        role_header(
            self.root,
            "◈  IMAGE GENERATOR",
            "Perlin noise — same seed → same image",
            accent="accent_blue",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=14, pady=10)

        # Seed row
        row = make_frame(body, bg=COLORS["bg_dark"])
        row.pack(fill="x", pady=(0, 8))
        make_label(
            row, "Seed:", style="label", color="text_secondary", bg=COLORS["bg_dark"]
        ).pack(side="left", padx=(0, 6))
        self.seed_entry = make_entry(row, textvariable=self.seed_var, width=12)
        self.seed_entry.pack(side="left", ipady=5, padx=(0, 8))
        self.seed_entry.bind("<Return>", lambda _: self._generate())
        make_button(
            row, "▶  GENERATE", command=self._generate, color="accent_blue"
        ).pack(side="left", ipady=4)

        # Quick seed buttons
        quick = make_frame(body, bg=COLORS["bg_dark"])
        quick.pack(fill="x", pady=(0, 10))
        make_label(
            quick, "Try:", style="label", color="text_secondary", bg=COLORS["bg_dark"]
        ).pack(side="left", padx=(0, 6))
        for s in [42, 43, 100, 999, 12345]:
            make_button(
                quick, str(s), command=lambda v=s: self._quick(v), color="accent_purple"
            ).pack(side="left", ipady=2, padx=(0, 4))

        # Canvas
        self.canvas = tk.Canvas(
            body,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg=COLORS["bg_panel"],
            highlightthickness=1,
            highlightbackground=COLORS["accent_blue"],
        )
        self.canvas.pack(pady=(0, 8))

        # Info bar
        self.info = tk.Label(
            body,
            text="",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            anchor="w",
        )
        self.info.pack(fill="x")

        self.fp_lbl = tk.Label(
            body,
            text="",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_accent"],
            anchor="w",
        )
        self.fp_lbl.pack(fill="x")

    def _quick(self, seed: int):
        self.seed_var.set(str(seed))
        self._generate()

    def _generate(self):
        raw = self.seed_var.get().strip()
        try:
            seed = int(raw)
        except ValueError:
            seed = int.from_bytes(raw.encode()[:8], "big") if raw else 42
            self.seed_var.set(str(seed))

        t0 = time.perf_counter()
        grid = render_cells(seed, CELLS)
        fp = image_fingerprint(seed)
        elapsed = time.perf_counter() - t0

        self._draw(grid)

        self.shared.update(seed=seed, fingerprint=fp, generated=True)
        self.info.configure(
            text=f"seed={seed}   cells={CELLS}×{CELLS}   time={elapsed*1000:.0f}ms"
        )
        self.fp_lbl.configure(text=f"fingerprint: {fp}")

        if cb := self.shared.get("on_generate"):
            cb()

    def _draw(self, grid: list):
        self.canvas.delete("all")
        for cy, row in enumerate(grid):
            for cx, val in enumerate(row):
                color = _heat_color(val)
                x0 = cx * CELL_PX
                y0 = cy * CELL_PX
                self.canvas.create_rectangle(
                    x0,
                    y0,
                    x0 + CELL_PX,
                    y0 + CELL_PX,
                    fill=color,
                    outline="",
                )
