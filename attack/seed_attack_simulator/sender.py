"""
Sender Window — uses current time as seed, generates artefacts, transmits.
"""

import sys, os, time
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
    generate_password,
    generate_key,
    generate_session_token,
    current_time_seed,
)


class SenderWindow:
    def __init__(self, root: tk.Tk, shared_state: dict):
        self.root = root
        self.state = shared_state
        apply_window_style(root, "SENDER", role="blue")
        self._build()

    def _build(self):
        role_header(
            self.root,
            "◈  SENDER",
            "Generates artefacts from the current time as seed",
            accent="accent_blue",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=SIZES["pad_x"], pady=12)

        make_button(
            body, "⚡  GENERATE & TRANSMIT", command=self._transmit, color="accent_blue"
        ).pack(fill="x", ipady=8, pady=(0, 12))

        make_label(
            body,
            "Transmitted",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")
        self.out = make_text_area(body, height=5)
        self.out.pack(fill="x", pady=(3, 0))

    def _transmit(self):
        seed = current_time_seed()
        pw = generate_password(seed)
        key = generate_key(seed)
        token = generate_session_token(seed)

        self.state.update(
            seed=seed, password=pw, key=key, token=token, transmitted=True
        )

        text_write(
            self.out,
            f"seed     : {seed}\n"
            f"password : {pw}\n"
            f"key      : {key[:24]}...\n"
            f"token    : {token}\n",
        )

        if cb := self.state.get("on_transmit"):
            cb()
