import sys, os, time, threading
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
    make_text_area,
    text_write,
    role_header,
)
from attack.seed_image_generator.perlin import render_cells, image_fingerprint

CANVAS_SIZE = 300
CELLS = 75
CELL_PX = CANVAS_SIZE // CELLS


def _heat_color(t: float) -> str:
    if t < 0.5:
        s = t * 2
        r = int(0 + s * 120)
        g = 0
        b = 180
    else:
        s = (t - 0.5) * 2
        r = int(120 + s * 100)
        g = int(s * 30)
        b = int(180 - s * 150)
    return f"#{r:02x}{g:02x}{b:02x}"


class AttackerWindow:
    def __init__(self, root: tk.Tk, shared: dict):
        self.root = root
        self.shared = shared
        self._running = False

        apply_window_style(root, "SEED ATTACKER", role="red")
        W, H = 400, 520
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw - 820)//2 + 420}+{(sh - H)//2}")
        self._build()

        shared["on_generate"] = self._on_generate

    def _build(self):
        role_header(
            self.root,
            "◈  SEED ATTACKER",
            "Brute-forces the seed from the image fingerprint",
            accent="accent_red",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=14, pady=10)

        # Intercepted fingerprint display
        make_label(
            body,
            "Intercepted fingerprint:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")
        self.fp_lbl = tk.Label(
            body,
            text="— waiting for generator —",
            font=FONTS["mono"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_red"],
        )
        self.fp_lbl.pack(anchor="w", pady=(2, 10))

        # Search range row
        range_row = make_frame(body, bg=COLORS["bg_dark"])
        range_row.pack(fill="x", pady=(0, 8))
        make_label(
            range_row,
            "Search:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 6))
        self.from_var = tk.StringVar(value="0")
        self.to_var = tk.StringVar(value="200")
        make_entry(range_row, textvariable=self.from_var, width=7).pack(
            side="left", ipady=4, padx=(0, 4)
        )
        make_label(
            range_row,
            "→",
            style="mono_sm",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 4))
        make_entry(range_row, textvariable=self.to_var, width=7).pack(
            side="left", ipady=4, padx=(0, 8)
        )
        make_button(
            range_row, "⚡  ATTACK", command=self._start_attack, color="accent_red"
        ).pack(side="left", ipady=4)

        # Progress
        self.progress_lbl = tk.Label(
            body,
            text="Status: idle",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.progress_lbl.pack(anchor="w", pady=(0, 8))

        # Recovered image canvas
        make_label(
            body,
            "Recovered image:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")
        self.canvas = tk.Canvas(
            body,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg=COLORS["bg_panel"],
            highlightthickness=1,
            highlightbackground=COLORS["accent_red"],
        )
        self.canvas.pack(pady=(3, 8))

        self.result_lbl = tk.Label(
            body,
            text="",
            font=FONTS["mono"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.result_lbl.pack(anchor="w")

    def _on_generate(self):
        fp = self.shared.get("fingerprint", "")
        self.fp_lbl.configure(text=fp)
        self.progress_lbl.configure(
            text="Status: fingerprint intercepted — ready to attack",
            fg=COLORS["accent_yellow"],
        )
        # Clear previous result
        self.canvas.delete("all")
        self.result_lbl.configure(text="")

    def _start_attack(self):
        if self._running:
            return
        fp = self.shared.get("fingerprint")
        if not fp:
            return

        try:
            lo = int(self.from_var.get())
            hi = int(self.to_var.get())
        except ValueError:
            return

        self._running = True
        self.progress_lbl.configure(
            text=f"Status: attacking seeds {lo}–{hi}…", fg=COLORS["accent_red"]
        )
        threading.Thread(
            target=self._attack_thread, args=(fp, lo, hi), daemon=True
        ).start()

    def _attack_thread(self, target_fp: str, lo: int, hi: int):
        total = hi - lo + 1
        t0 = time.perf_counter()

        for i, seed in enumerate(range(lo, hi + 1)):
            # Update progress every 20 seeds
            if i % 20 == 0:
                self.root.after(
                    0,
                    self.progress_lbl.configure,
                    {
                        "text": f"Status: trying {seed}…  ({i}/{total})",
                        "fg": COLORS["accent_red"],
                    },
                )

            if image_fingerprint(seed) == target_fp:
                elapsed = time.perf_counter() - t0
                self.root.after(0, self._on_found, seed, i + 1, elapsed)
                return

        elapsed = time.perf_counter() - t0
        self.root.after(0, self._on_not_found, total, elapsed)

    def _on_found(self, seed: int, attempts: int, elapsed: float):
        self._running = False
        self.progress_lbl.configure(
            text=f"Status: ✅ cracked in {attempts} attempts ({elapsed:.3f}s)",
            fg=COLORS["success"],
        )
        self.result_lbl.configure(
            text=f"Recovered seed: {seed}   fingerprint: {image_fingerprint(seed)}",
            fg=COLORS["success"],
        )
        # Render the recovered image
        grid = render_cells(seed, CELLS)
        self._draw(grid)

    def _on_not_found(self, total: int, elapsed: float):
        self._running = False
        self.progress_lbl.configure(
            text=f"Status: ❌ not found in {total} attempts ({elapsed:.3f}s)",
            fg=COLORS["warning"],
        )
        self.result_lbl.configure(
            text="Seed not in range — widen the search window.",
            fg=COLORS["warning"],
        )

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
