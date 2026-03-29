"""
Receiver Window — re-derives artefacts from the shared seed and verifies.
"""

import sys, os
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
)


class ReceiverWindow:
    def __init__(self, root: tk.Tk, shared_state: dict):
        self.root = root
        self.state = shared_state
        apply_window_style(root, "RECEIVER", role="green")
        self._build()
        self.state["on_transmit"] = self._on_transmit

    def _build(self):
        role_header(
            self.root,
            "◈  RECEIVER",
            "Re-derives artefacts from the shared seed & verifies",
            accent="accent_green",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=SIZES["pad_x"], pady=12)

        make_button(
            body, "📩  RECEIVE & VERIFY", command=self._verify, color="accent_green"
        ).pack(fill="x", ipady=8, pady=(0, 12))

        make_label(
            body, "Result", style="label", color="text_secondary", bg=COLORS["bg_dark"]
        ).pack(anchor="w")
        self.out = make_text_area(body, height=6)
        self.out.pack(fill="x", pady=(3, 0))

    def _on_transmit(self):
        text_write(self.out, "[ signal received — click RECEIVE & VERIFY ]\n")

    def _verify(self):
        s = self.state
        if not s.get("transmitted"):
            messagebox.showinfo("Nothing Yet", "Sender hasn't transmitted.")
            return

        seed = s["seed"]
        pw = generate_password(seed)
        key = generate_key(seed)
        token = generate_session_token(seed)

        ok_pw = "✅" if pw == s["password"] else "❌"
        ok_key = "✅" if key == s["key"] else "❌"
        ok_token = "✅" if token == s["token"] else "❌"

        text_write(
            self.out,
            f"seed     : {seed}\n\n"
            f"{ok_pw}  password : {pw}\n"
            f"{ok_key}  key      : {key[:24]}...\n"
            f"{ok_token}  token    : {token}\n",
        )
