import sys, os, secrets, random, string, time
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
    role_header,
)


class GeneratorWindow:
    def __init__(self, root: tk.Tk, shared: dict):
        self.root = root
        self.shared = shared
        self.mode_var = tk.StringVar(value="prng")
        self.seed_var = tk.StringVar(value="42")
        self._rng = random.Random(42)
        self._count = 0

        apply_window_style(root, "GENERATOR", role="blue")
        W, H = 380, 500
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw-780)//2}+{(sh-H)//2}")
        self._build()
        self._init_rng()

    def _build(self):
        role_header(
            self.root,
            "◈  GENERATOR",
            "Produces a stream of numbers",
            accent="accent_blue",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=14, pady=10)

        # Mode toggle
        mode_row = make_frame(body, bg=COLORS["bg_dark"])
        mode_row.pack(fill="x", pady=(0, 8))
        for text, val, col in [
            ("PRNG  (random)", "prng", "accent_yellow"),
            ("CSPRNG  (secrets)", "csprng", "accent_green"),
        ]:
            tk.Radiobutton(
                mode_row,
                text=text,
                variable=self.mode_var,
                value=val,
                command=self._on_mode_change,
                font=FONTS["mono_sm"],
                bg=COLORS["bg_dark"],
                fg=COLORS[col],
                selectcolor=COLORS["bg_input"],
                activebackground=COLORS["bg_dark"],
                activeforeground=COLORS[col],
                cursor="hand2",
            ).pack(side="left", padx=(0, 14))

        # Seed row (only visible for PRNG)
        self.seed_row = make_frame(body, bg=COLORS["bg_dark"])
        self.seed_row.pack(fill="x", pady=(0, 10))
        make_label(
            self.seed_row,
            "Seed:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 6))
        make_entry(self.seed_row, textvariable=self.seed_var, width=10).pack(
            side="left", ipady=5, padx=(0, 8)
        )
        make_button(
            self.seed_row, "INIT", command=self._init_rng, color="accent_yellow"
        ).pack(side="left", ipady=3)

        # Generate button
        make_button(
            body, "▶  EMIT NEXT NUMBER", command=self._emit, color="accent_blue"
        ).pack(fill="x", ipady=8, pady=(0, 10))

        # Stream output
        make_label(
            body, "Stream", style="label", color="text_secondary", bg=COLORS["bg_dark"]
        ).pack(anchor="w")
        self.stream = make_text_area(body, height=16)
        self.stream.pack(fill="x", pady=(3, 0))

        # Status
        self.status = tk.Label(
            self.root,
            text="",
            font=FONTS["tiny"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.status.pack(anchor="w", padx=14, pady=(6, 0))

    def _on_mode_change(self):
        if self.mode_var.get() == "prng":
            self.seed_row.pack(fill="x", pady=(0, 10))
        else:
            self.seed_row.pack_forget()
        self._init_rng()

    def _init_rng(self):
        self._count = 0
        self.shared["outputs"].clear()
        self.shared["mode"] = self.mode_var.get()

        if self.mode_var.get() == "prng":
            try:
                seed = int(self.seed_var.get().strip())
            except ValueError:
                seed = 42
            self._rng = random.Random(seed)
            self.shared["seed"] = seed
            self.status.configure(
                text=f"PRNG seeded with {seed} — attacker can predict after {self.shared['threshold']} outputs"
            )
        else:
            self.shared["seed"] = None
            self.status.configure(text="CSPRNG — OS entropy — no seed to exploit")

        self.stream.configure(state="normal")
        self.stream.delete("1.0", "end")
        mode = self.mode_var.get().upper()
        self.stream.insert("end", f"[{mode} initialised]\n")
        self.stream.configure(state="disabled")

        if cb := self.shared.get("on_reset"):
            cb()

    def _emit(self):
        self._count += 1
        mode = self.mode_var.get()

        if mode == "prng":
            value = self._rng.randint(0, 999999)
        else:
            value = secrets.randbelow(1000000)

        self.shared["outputs"].append(value)
        self.shared["latest"] = value

        self.stream.configure(state="normal")
        self.stream.insert("end", f"  [{self._count:>3}]  {value:>6}\n")
        self.stream.configure(state="disabled")
        self.stream.see("end")

        self.status.configure(
            text=f"{self._count} emitted  ·  mode={mode.upper()}  ·  latest={value}"
        )

        if cb := self.shared.get("on_emit"):
            cb()
