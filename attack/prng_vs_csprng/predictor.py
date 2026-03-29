import sys, os, random
import tkinter as tk

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


class PredictorWindow:
    def __init__(self, root: tk.Tk, shared: dict):
        self.root = root
        self.shared = shared
        self._shadow = random.Random(42)  # mirrors PRNG generator exactly
        self._shadow_pos = 0  # how many values shadow has consumed
        self._correct = 0
        self._attempts = 0

        apply_window_style(root, "PREDICTOR", role="red")
        W, H = 380, 500
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw-780)//2 + 400}+{(sh-H)//2}")
        self._build()

        # Register callbacks
        shared["on_emit"] = self._on_emit
        shared["on_reset"] = self._on_reset

    def _build(self):
        role_header(
            self.root,
            "◈  PREDICTOR",
            "Watches the stream · attempts to guess next value",
            accent="accent_red",
        )

        body = make_frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="x", padx=14, pady=10)

        # Score row
        score_row = make_frame(body, bg=COLORS["bg_dark"])
        score_row.pack(fill="x", pady=(0, 10))
        make_label(
            score_row,
            "Score:",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(side="left", padx=(0, 6))
        self.score_lbl = tk.Label(
            score_row,
            text="0 / 0",
            font=FONTS["mono"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_accent"],
        )
        self.score_lbl.pack(side="left")

        # Predict button
        self.predict_btn = make_button(
            body, "🔮  PREDICT NEXT", command=self._predict, color="accent_red"
        )
        self.predict_btn.pack(fill="x", ipady=8, pady=(0, 10))

        # Waiting label
        self.wait_lbl = tk.Label(
            body,
            text=f"Observing stream… need {self.shared['threshold']} outputs first",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            wraplength=340,
        )
        self.wait_lbl.pack(anchor="w", pady=(0, 8))

        # Log
        make_label(
            body,
            "Prediction Log",
            style="label",
            color="text_secondary",
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")
        self.log = make_text_area(body, height=14)
        self.log.pack(fill="x", pady=(3, 0))

        # Verdict
        self.verdict = tk.Label(
            self.root,
            text="",
            font=FONTS["subhead"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        )
        self.verdict.pack(anchor="w", padx=14, pady=(6, 0))

    # ── Callbacks from generator ──────────────────────────────────────────────

    def _on_reset(self):
        """Generator was re-initialised — resync shadow."""
        seed = self.shared.get("seed", 42)
        self._shadow = random.Random(seed) if seed is not None else None
        self._shadow_pos = 0
        self._correct = 0
        self._attempts = 0
        self.score_lbl.configure(text="0 / 0")
        self.verdict.configure(text="", fg=COLORS["text_secondary"])
        text_write(self.log, "[reset — watching new stream]\n")
        self._update_wait_lbl()

    def _on_emit(self):
        """Generator emitted a value — advance shadow to stay in sync."""
        if self.shared["mode"] == "prng" and self._shadow is not None:
            # Shadow must consume the same value the generator just produced
            self._shadow.randint(0, 999999)
            self._shadow_pos += 1
        self._update_wait_lbl()

    def _update_wait_lbl(self):
        n = len(self.shared["outputs"])
        thr = self.shared["threshold"]
        if self.shared["mode"] == "csprng":
            self.wait_lbl.configure(
                text="CSPRNG mode — no pattern to exploit", fg=COLORS["accent_green"]
            )
        elif n < thr:
            self.wait_lbl.configure(
                text=f"Observing… {n}/{thr} outputs collected",
                fg=COLORS["text_secondary"],
            )
        else:
            self.wait_lbl.configure(
                text=f"✅ {n} outputs observed — shadow RNG is synchronised",
                fg=COLORS["success"],
            )

    # ── Prediction ────────────────────────────────────────────────────────────

    def _predict(self):
        n = len(self.shared["outputs"])
        thr = self.shared["threshold"]
        mode = self.shared["mode"]

        self._attempts += 1

        if mode == "prng":
            if n < thr:
                self.log.configure(state="normal")
                self.log.insert(
                    "end",
                    f"[attempt {self._attempts}] Need {thr-n} more outputs first.\n",
                )
                self.log.configure(state="disabled")
                return

            # Shadow has been kept in sync — predict next value
            predicted = self._shadow.randint(0, 999999)

            # Ask generator to emit the actual next value
            # We reveal it by re-deriving from the shadow's position
            # (In the real demo the user clicks EMIT NEXT in the generator window,
            #  but we show the prediction here first, then compare on next emit)
            self.shared["pending_prediction"] = predicted

            self.log.configure(state="normal")
            self.log.insert(
                "end",
                f"[attempt {self._attempts}] Predicted: {predicted:>6}\n"
                f"            → now click EMIT NEXT in Generator\n"
                f"            → and watch it match.\n",
            )
            self.log.configure(state="disabled")
            self.log.see("end")

            self.verdict.configure(
                text=f"🔮 prediction made: {predicted}", fg=COLORS["accent_yellow"]
            )

            # Override on_emit to verify this prediction
            original_emit = self.shared.get("on_emit")

            def verify_and_restore():
                actual = self.shared.get("latest")
                correct = actual == predicted
                if correct:
                    self._correct += 1
                self.score_lbl.configure(text=f"{self._correct} / {self._attempts}")

                self.log.configure(state="normal")
                self.log.insert(
                    "end",
                    f"            actual:    {actual:>6}  "
                    f"{'✅ CORRECT' if correct else '❌ wrong'}\n\n",
                )
                self.log.configure(state="disabled")
                self.log.see("end")

                self.verdict.configure(
                    text=f"{'✅ CORRECT — shadow RNG predicted it exactly!' if correct else '❌ Out of sync'}",
                    fg=COLORS["success"] if correct else COLORS["danger"],
                )

                # Restore normal emit handler
                self.shared["on_emit"] = original_emit
                if original_emit:
                    original_emit()

            self.shared["on_emit"] = verify_and_restore

        else:
            # CSPRNG — blind guess
            guess = self.shared.get(
                "latest", 0
            )  # attacker's "best" guess: last seen value
            self.shared["pending_prediction"] = guess

            self.log.configure(state="normal")
            self.log.insert(
                "end",
                f"[attempt {self._attempts}] Best guess:  {guess:>6}\n"
                f"            (repeating last value — no better strategy)\n"
                f"            → click EMIT NEXT to see actual\n",
            )
            self.log.configure(state="disabled")
            self.log.see("end")

            self.verdict.configure(
                text=f"🔮 guess: {guess}", fg=COLORS["accent_yellow"]
            )

            original_emit = self.shared.get("on_emit")

            def verify_csprng_and_restore():
                actual = self.shared.get("latest")
                correct = actual == guess
                if correct:
                    self._correct += 1

                self.score_lbl.configure(text=f"{self._correct} / {self._attempts}")
                self.log.configure(state="normal")
                self.log.insert(
                    "end",
                    f"            actual:    {actual:>6}  "
                    f"{'✅ lucky!' if correct else '❌ wrong (expected)'}\n\n",
                )
                self.log.configure(state="disabled")
                self.log.see("end")

                self.verdict.configure(
                    text=f"{'✅ Lucky guess!' if correct else '❌ Wrong — 1-in-1,000,000 odds'}",
                    fg=COLORS["success"] if correct else COLORS["danger"],
                )

                self.shared["on_emit"] = original_emit
                if original_emit:
                    original_emit()

            self.shared["on_emit"] = verify_csprng_and_restore
