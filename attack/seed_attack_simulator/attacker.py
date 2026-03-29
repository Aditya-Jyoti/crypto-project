"""
Attacker Window — intercepts token, brute-forces seed, recovers all artefacts.
"""

import sys, os, time, threading
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.theme import (
    COLORS,
    FONTS,
    SIZES,
    apply_window_style,
    make_frame,
    make_label,
    make_button,
    make_text_area,
    text_write,
    role_header,
)
from attack.seed_attack_simulator.utils import (
    generate_session_token,
    derive_all_from_seed,
    time_seed_range,
)


class AttackerWindow:
    def __init__(self, root: tk.Tk, shared_state: dict):
        self.root = root
        self.state = shared_state
        self._attacking = False
        apply_window_style(root, "ATTACKER", role="red")
        self._build()

    def _build(self):
        role_header(
            self.root,
            "◈  ATTACKER",
            "Brute-forces the seed from an intercepted token",
            accent="accent_red",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=SIZES["pad_x"], pady=12)

        make_label(
            body,
            "Search window (seconds back)",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")
        self.window_var = tk.IntVar(value=60)
        tk.Scale(
            body,
            from_=10,
            to=300,
            orient="horizontal",
            variable=self.window_var,
            font=FONTS["tiny"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            troughcolor=COLORS["bg_input"],
            activebackground=COLORS["accent_red"],
            highlightthickness=0,
            sliderlength=16,
        ).pack(fill="x", pady=(3, 10))

        make_button(
            body, "⚡  INTERCEPT & ATTACK", command=self._start, color="accent_red"
        ).pack(fill="x", ipady=8, pady=(0, 8))

        self.status_lbl = make_label(
            body,
            "Status: idle",
            style="mono_sm",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        )
        self.status_lbl.pack(anchor="w", pady=(0, 10))

        make_label(
            body,
            "Recovered",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")
        self.out = make_text_area(body, height=5)
        self.out.pack(fill="x", pady=(3, 0))

    def _start(self):
        if self._attacking:
            return
        if not self.state.get("transmitted"):
            messagebox.showinfo("Nothing intercepted", "Sender hasn't transmitted yet.")
            return
        self._attacking = True
        self.status_lbl.configure(text="Status: attacking…", fg=COLORS["accent_red"])
        token = self.state["token"]
        window = self.window_var.get()
        threading.Thread(target=self._attack, args=(token, window), daemon=True).start()

    def _attack(self, token: str, window: int):
        candidates = list(time_seed_range(window))
        t0 = time.time()
        for i, seed in enumerate(candidates):
            if generate_session_token(seed) == token:
                elapsed = time.time() - t0
                self.root.after(0, self._success, seed, i + 1, elapsed)
                return
        elapsed = time.time() - t0
        self.root.after(0, self._fail, len(candidates), elapsed)

    def _success(self, seed, attempts, elapsed):
        self._attacking = False
        self.status_lbl.configure(
            text=f"Status: ✅ cracked in {attempts} attempts ({elapsed:.3f}s)",
            fg=COLORS["success"],
        )
        art = derive_all_from_seed(seed)
        text_write(
            self.out,
            f"seed     : {art['seed']}\n"
            f"password : {art['password']}\n"
            f"key      : {art['key'][:24]}...\n"
            f"token    : {art['token']}\n",
        )

    def _fail(self, total, elapsed):
        self._attacking = False
        self.status_lbl.configure(
            text=f"Status: ❌ not found in {total} attempts ({elapsed:.3f}s)",
            fg=COLORS["warning"],
        )
        text_write(
            self.out,
            "Seed not found in window.\n" "Try increasing the search window.\n",
        )
