import sys, os, random, secrets
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

WALK_W, WALK_H = 300, 300
STEPS = 500
ANIM_DELAY = 10  # ms per frame


def lerp(a, b, t):
    return int(a + (b - a) * t)


def lerp_color(t, c1, c2):
    return "#{:02x}{:02x}{:02x}".format(
        lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)
    )


def hex_rgb(h):
    h = h.lstrip("#")
    return int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16)


def make_walk(seed: int) -> list:
    """Deterministic walk — same seed always gives the same list of points."""
    rng = random.Random(seed)
    x, y = WALK_W // 2, WALK_H // 2
    pts = [(x, y)]
    for _ in range(STEPS):
        x = max(4, min(WALK_W - 4, x + rng.randint(-7, 7)))
        y = max(4, min(WALK_H - 4, y + rng.randint(-7, 7)))
        pts.append((x, y))
    return pts


# ── Per-window walk viewer ────────────────────────────────────────────────────


class WalkWindow:
    """One independent window that generates its own walk from a seed."""

    ACCENT_COLORS = ["accent_blue", "accent_green", "accent_purple"]
    LABELS = ["Instance A", "Instance B", "Instance C"]

    def __init__(self, root: tk.Tk, instance: int, shared: dict):
        self.root = root
        self.instance = instance  # 0, 1, 2
        self.shared = shared  # {'seed': int, 'on_generate': fn}
        self.accent = self.ACCENT_COLORS[instance]
        self.label = self.LABELS[instance]
        self._pts = []
        self._anim_id = None
        self._step = 0

        apply_window_style(root, self.label, role=["blue", "green", "blue"][instance])
        # Override position so three windows sit side by side
        W, H = 360, 420
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        offsets = [0, 380, 760]
        x = (sw - 1140) // 2 + offsets[instance]
        y = (sh - H) // 2
        root.geometry(f"{W}x{H}+{x}+{y}")

        self._build()

    def _build(self):
        role_header(
            self.root,
            f"◈  {self.label}",
            "random.Random(seed) — independent instance",
            accent=self.accent,
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=12, pady=10)

        # Seed display (read-only, shared)
        seed_row = make_frame(body, bg=COLORS["bg_dark"])
        seed_row.pack(fill="x", pady=(0, 8))
        make_label(
            seed_row,
            "Seed:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 6))
        self.seed_lbl = tk.Label(
            seed_row,
            text="—",
            font=FONTS["mono"],
            bg=COLORS["bg_dark"],
            fg=COLORS[self.accent],
        )
        self.seed_lbl.pack(side="left")

        # Buttons
        btn_row = make_frame(body, bg=COLORS["bg_dark"])
        btn_row.pack(fill="x", pady=(0, 8))
        make_button(
            btn_row, "▶  GENERATE", command=self._generate, color=self.accent
        ).pack(side="left", ipady=5, padx=(0, 6))
        make_button(
            btn_row, "⚡  ANIMATE", command=self._animate, color="accent_yellow"
        ).pack(side="left", ipady=5)

        # Canvas
        self.canvas = tk.Canvas(
            body,
            width=WALK_W,
            height=WALK_H,
            bg=COLORS["bg_panel"],
            highlightthickness=1,
            highlightbackground=COLORS[self.accent],
        )
        self.canvas.pack()

        # Match label
        self.match_lbl = tk.Label(
            body,
            text="",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.match_lbl.pack(anchor="w", pady=(6, 0))

    # ── Actions ──────────────────────────────────────────────────────────────

    def _get_seed(self):
        return self.shared.get("seed", 42)

    def _generate(self):
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
        seed = self._get_seed()
        self._pts = make_walk(seed)
        self.seed_lbl.configure(text=str(seed))
        self._draw_full()
        self._check_match()
        if cb := self.shared.get("on_generate"):
            cb(self.instance, self._pts)

    def _animate(self):
        if self._anim_id:
            self.root.after_cancel(self._anim_id)
            self._anim_id = None
        seed = self._get_seed()
        self._pts = make_walk(seed)
        self.seed_lbl.configure(text=str(seed))
        self.canvas.delete("all")
        self._step = 1
        self._tick()
        if cb := self.shared.get("on_generate"):
            cb(self.instance, self._pts)

    def _tick(self):
        i = self._step
        if i >= len(self._pts):
            ex, ey = self._pts[-1]
            self.canvas.create_oval(
                ex - 4, ey - 4, ex + 4, ey + 4, fill=COLORS["accent_red"], outline=""
            )
            self._check_match()
            return
        t = i / len(self._pts)
        c1 = hex_rgb(COLORS[self.accent])
        c2 = hex_rgb(COLORS["accent_red"])
        col = lerp_color(t, c1, c2)
        x0, y0 = self._pts[i - 1]
        x1, y1 = self._pts[i]
        self.canvas.create_line(x0, y0, x1, y1, fill=col, width=1)
        if i == 1:
            self.canvas.create_oval(
                x0 - 4, y0 - 4, x0 + 4, y0 + 4, fill=COLORS["accent_blue"], outline=""
            )
        self._step += 1
        self._anim_id = self.root.after(ANIM_DELAY, self._tick)

    def _draw_full(self):
        self.canvas.delete("all")
        pts = self._pts
        c1 = hex_rgb(COLORS[self.accent])
        c2 = hex_rgb(COLORS["accent_red"])
        n = len(pts)
        for i in range(1, n):
            col = lerp_color(i / n, c1, c2)
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            self.canvas.create_line(x0, y0, x1, y1, fill=col, width=1)
        sx, sy = pts[0]
        ex, ey = pts[-1]
        self.canvas.create_oval(
            sx - 4, sy - 4, sx + 4, sy + 4, fill=COLORS["accent_blue"], outline=""
        )
        self.canvas.create_oval(
            ex - 4, ey - 4, ex + 4, ey + 4, fill=COLORS["accent_red"], outline=""
        )

    def _check_match(self):
        walks = self.shared.get("walks", {})
        if len(walks) < 2:
            self.match_lbl.configure(
                text="waiting for other instances…", fg=COLORS["text_secondary"]
            )
            return
        others = [v for k, v in walks.items() if k != self.instance]
        my_pts = self._pts
        all_match = all(o == my_pts for o in others)
        if all_match:
            self.match_lbl.configure(
                text="✅ identical to all other instances", fg=COLORS["success"]
            )
        else:
            self.match_lbl.configure(text="❌ paths differ", fg=COLORS["danger"])


# ── Launcher ─────────────────────────────────────────────────────────────────


class RandomnessVisualizer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.seed_var = tk.StringVar(value="42")

        # Shared state between all three walk windows
        self.shared = {
            "seed": 42,
            "walks": {},  # instance_index → pts list
            "on_generate": self._on_generate,
        }

        self._build_control(root)
        self._spawn_walkers(root)

    def _build_control(self, root: tk.Tk):
        """Small floating control panel attached to the main root window."""
        W, H = 340, 110
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2 - 260}")
        root.title("⬡ RANDOMNESS VISUALIZER — Control")
        root.configure(bg=COLORS["bg_dark"])
        root.resizable(False, False)

        tk.Frame(root, bg=COLORS["accent_purple"], height=3).pack(fill="x")

        body = make_frame(root, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(
            body,
            text="◈  RANDOMNESS VISUALIZER",
            font=FONTS["heading"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_purple"],
        ).pack(anchor="w", pady=(0, 8))

        row = make_frame(body, bg=COLORS["bg_dark"])
        row.pack(fill="x")
        make_label(
            row,
            "Shared seed:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 6))
        e = make_entry(row, textvariable=self.seed_var, width=10)
        e.pack(side="left", ipady=5, padx=(0, 10))
        e.bind("<Return>", lambda _: self._broadcast_seed())
        make_button(
            row, "BROADCAST SEED →", command=self._broadcast_seed, color="accent_purple"
        ).pack(side="left", ipady=4)

    def _spawn_walkers(self, root: tk.Tk):
        self.windows = []
        for i in range(3):
            top = tk.Toplevel(root)
            w = WalkWindow(top, i, self.shared)
            self.windows.append(w)

    def _broadcast_seed(self):
        raw = self.seed_var.get().strip()
        try:
            seed = int(raw)
        except ValueError:
            seed = int.from_bytes(raw.encode()[:8], "big") if raw else 42
        self.shared["seed"] = seed
        self.shared["walks"] = {}
        # Trigger generate on all three
        for w in self.windows:
            w._generate()

    def _on_generate(self, instance: int, pts: list):
        self.shared["walks"][instance] = pts
