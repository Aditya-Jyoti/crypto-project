import sys, os, secrets, hashlib, time, string, random, math
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config.theme import (
    COLORS,
    FONTS,
    make_frame,
    make_entry,
    make_button,
    make_text_area,
    text_write,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def weak_token():
    rng = random.Random(int(time.time()))
    return "".join(rng.choice(string.hexdigits[:16]) for _ in range(16))


def secure_token():
    return secrets.token_hex(8)


def estimate_crack_time(iters: int) -> str:
    seconds = (26**8) / (1_000_000_000 / iters)
    if seconds < 60:
        return f"~{seconds:.0f} sec"
    if seconds < 3600:
        return f"~{seconds/60:.0f} min"
    if seconds < 86400:
        return f"~{seconds/3600:.0f} hrs"
    if seconds < 2.6e6:
        return f"~{seconds/86400:.0f} days"
    if seconds < 3.15e7:
        return f"~{seconds/2.6e6:.0f} months"
    return f"~{seconds/3.15e7:.0f} years"


def crack_color(est: str) -> str:
    if "year" in est:
        return COLORS["success"]
    if "month" in est:
        return COLORS["accent_green"]
    if "day" in est:
        return COLORS["accent_yellow"]
    return COLORS["danger"]


# ── Card widget helpers ───────────────────────────────────────────────────────


def card(parent, accent: str, padx=10, pady=10) -> tk.Frame:
    """A raised panel with a coloured left border."""
    outer = tk.Frame(
        parent,
        bg=COLORS["bg_panel"],
        highlightthickness=1,
        highlightbackground=COLORS["border"],
    )
    outer.pack(fill="x", padx=0, pady=(0, 8))
    # Left accent bar
    tk.Frame(outer, bg=COLORS[accent], width=3).pack(side="left", fill="y")
    inner = tk.Frame(outer, bg=COLORS["bg_panel"])
    inner.pack(side="left", fill="both", expand=True, padx=padx, pady=pady)
    return inner


def card_label(parent, text: str, color="text_secondary", font="label") -> tk.Label:
    lbl = tk.Label(
        parent,
        text=text,
        font=FONTS[font],
        bg=COLORS["bg_panel"],
        fg=COLORS[color],
        anchor="w",
    )
    lbl.pack(fill="x")
    return lbl


def card_text(parent, height=4) -> tk.Text:
    t = tk.Text(
        parent,
        font=FONTS["mono_sm"],
        bg=COLORS["bg_input"],
        fg=COLORS["text_accent"],
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["border_bright"],
        height=height,
        state="disabled",
        wrap="word",
    )
    t.pack(fill="x", pady=(4, 0))
    return t


def section_title(parent, text: str, color: str):
    tk.Label(
        parent,
        text=text,
        font=FONTS["label"],
        bg=COLORS["bg_dark"],
        fg=COLORS[color],
        anchor="w",
    ).pack(fill="x", pady=(0, 4))


def divider(parent):
    tk.Frame(parent, bg=COLORS["border"], height=1).pack(fill="x", pady=8)


# ── Main app ──────────────────────────────────────────────────────────────────


class DefenseDashboard:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("⬡ DEFENSE DASHBOARD")
        root.configure(bg=COLORS["bg_dark"])
        root.resizable(False, False)
        W, H = 960, 640
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self._build()

    def _build(self):
        # ── Header ──
        tk.Frame(self.root, bg=COLORS["accent_green"], height=3).pack(fill="x")

        hdr = tk.Frame(self.root, bg=COLORS["bg_panel"])
        hdr.pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=COLORS["bg_panel"])
        inner_hdr.pack(fill="x", padx=20, pady=12)
        tk.Label(
            inner_hdr,
            text="◈  DEFENSE DASHBOARD",
            font=FONTS["title"],
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_green"],
        ).pack(side="left")
        for pill_text, pill_col in [
            ("secure seeds", "accent_blue"),
            ("salting", "accent_yellow"),
            ("key stretching", "accent_purple"),
        ]:
            pill = tk.Label(
                inner_hdr,
                text=f"  {pill_text}  ",
                font=FONTS["tiny"],
                bg=COLORS["bg_input"],
                fg=COLORS[pill_col],
                padx=6,
                pady=3,
            )
            pill.pack(side="left", padx=(8, 0))

        tk.Frame(self.root, bg=COLORS["border"], height=1).pack(fill="x")

        # ── Three columns ──
        body = tk.Frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=16, pady=14)
        body.grid_columnconfigure(0, weight=1, uniform="col")
        body.grid_columnconfigure(1, weight=1, uniform="col")
        body.grid_columnconfigure(2, weight=1, uniform="col")

        self._build_seed_col(body, 0)
        self._build_salt_col(body, 1)
        self._build_pbkdf2_col(body, 2)

    def _col(self, parent, col: int) -> tk.Frame:
        f = tk.Frame(parent, bg=COLORS["bg_dark"])
        f.grid(row=0, column=col, sticky="nsew", padx=(0, 12 if col < 2 else 0))
        return f

    # ── Column 1: Secure Seed ─────────────────────────────────────────────────

    def _build_seed_col(self, parent, col):
        p = self._col(parent, col)

        # Column header
        tk.Frame(p, bg=COLORS["accent_blue"], height=2).pack(fill="x", pady=(0, 8))
        tk.Label(
            p,
            text="① Secure Seed Generation",
            font=FONTS["subhead"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_blue"],
        ).pack(anchor="w")
        tk.Label(
            p,
            text="os.urandom  vs  time-based seed",
            font=FONTS["tiny"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, 10))

        # Weak card
        section_title(p, "⚠  WEAK — time seed", "accent_red")
        weak_card = card(p, "accent_red")
        self.weak_seed_out = card_text(weak_card, height=5)
        make_button(
            p, "Generate weak tokens", command=self._gen_weak_seeds, color="accent_red"
        ).pack(fill="x", ipady=6, pady=(6, 0))

        divider(p)

        # Strong card
        section_title(p, "✅  STRONG — os.urandom", "accent_green")
        strong_card = card(p, "accent_green")
        self.strong_seed_out = card_text(strong_card, height=5)
        make_button(
            p,
            "Generate secure tokens",
            command=self._gen_secure_seeds,
            color="accent_green",
        ).pack(fill="x", ipady=6, pady=(6, 0))

        divider(p)

        self.seed_verdict = tk.Label(
            p,
            text="Click a button above to compare",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            wraplength=280,
            justify="left",
        )
        self.seed_verdict.pack(anchor="w")

    def _gen_weak_seeds(self):
        lines = []
        for i in range(4):
            seed = int(time.time()) + i
            tok = weak_token()
            lines.append(f"seed={seed}\n→ {tok}")
        text_write(self.weak_seed_out, "\n".join(lines))
        self.seed_verdict.configure(
            text="⚠  Attacker brute-forces nearby timestamps — cracks in < 1s",
            fg=COLORS["danger"],
        )

    def _gen_secure_seeds(self):
        lines = []
        for _ in range(4):
            raw = os.urandom(32)
            lines.append(f"entropy: {raw.hex()[:16]}…\n→ {raw.hex()[16:32]}…")
        text_write(self.strong_seed_out, "\n".join(lines))
        self.seed_verdict.configure(
            text="✅  2²⁵⁶ possible seeds — computationally impossible to brute-force",
            fg=COLORS["success"],
        )

    # ── Column 2: Salt + Hashing ──────────────────────────────────────────────

    def _build_salt_col(self, parent, col):
        p = self._col(parent, col)

        tk.Frame(p, bg=COLORS["accent_yellow"], height=2).pack(fill="x", pady=(0, 8))
        tk.Label(
            p,
            text="② Salt + Hashing",
            font=FONTS["subhead"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_yellow"],
        ).pack(anchor="w")
        tk.Label(
            p,
            text="same password → different hash every time",
            font=FONTS["tiny"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, 10))

        # Password input card
        pw_card = card(p, "border", pady=8)
        tk.Label(
            pw_card,
            text="PASSWORD",
            font=FONTS["label"],
            bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")
        self.salt_pw_var = tk.StringVar(value="hunter2")
        e = make_entry(pw_card, textvariable=self.salt_pw_var)
        e.configure(bg=COLORS["bg_dark"])
        e.pack(fill="x", ipady=6, pady=(3, 0))

        # No salt
        section_title(p, "⚠  WITHOUT SALT  (SHA-256)", "accent_red")
        nosalt_card = card(p, "accent_red")
        self.nosalt_out = card_text(nosalt_card, height=4)
        make_button(
            p, "Hash ×3 (no salt)", command=self._hash_nosalt, color="accent_red"
        ).pack(fill="x", ipady=6, pady=(6, 0))

        divider(p)

        # With salt
        section_title(p, "✅  WITH SALT  (PBKDF2 + os.urandom)", "accent_green")
        salted_card = card(p, "accent_green")
        self.salted_out = card_text(salted_card, height=4)
        make_button(
            p, "Hash ×3 (with salt)", command=self._hash_salted, color="accent_green"
        ).pack(fill="x", ipady=6, pady=(6, 0))

        divider(p)

        self.salt_verdict = tk.Label(
            p,
            text="Click a button above to compare",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            wraplength=280,
            justify="left",
        )
        self.salt_verdict.pack(anchor="w")

    def _hash_nosalt(self):
        pw = self.salt_pw_var.get() or "hunter2"
        lines = [
            f"run {i+1}: {hashlib.sha256(pw.encode()).hexdigest()[:32]}…"
            for i in range(3)
        ]
        text_write(self.nosalt_out, "\n".join(lines))
        self.salt_verdict.configure(
            text="⚠  All three hashes are identical — one rainbow table cracks every account with this password",
            fg=COLORS["danger"],
        )

    def _hash_salted(self):
        pw = self.salt_pw_var.get() or "hunter2"
        lines = []
        for i in range(3):
            salt = os.urandom(16)
            h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 1, dklen=32)
            lines.append(f"salt: {salt.hex()[:12]}…\nhash: {h.hex()[:24]}…")
        text_write(self.salted_out, "\n".join(lines))
        self.salt_verdict.configure(
            text="✅  Every hash is unique — rainbow tables are useless",
            fg=COLORS["success"],
        )

    # ── Column 3: Key Stretching ──────────────────────────────────────────────

    def _build_pbkdf2_col(self, parent, col):
        p = self._col(parent, col)

        tk.Frame(p, bg=COLORS["accent_purple"], height=2).pack(fill="x", pady=(0, 8))
        tk.Label(
            p,
            text="③ Key Stretching (PBKDF2)",
            font=FONTS["subhead"],
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_purple"],
        ).pack(anchor="w")
        tk.Label(
            p,
            text="more iterations = slower to crack",
            font=FONTS["tiny"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(0, 10))

        # Password input
        pw_card = card(p, "border", pady=8)
        tk.Label(
            pw_card,
            text="PASSWORD",
            font=FONTS["label"],
            bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")
        self.pbkdf2_pw_var = tk.StringVar(value="mysecret")
        e = make_entry(pw_card, textvariable=self.pbkdf2_pw_var)
        e.configure(bg=COLORS["bg_dark"])
        e.pack(fill="x", ipady=6, pady=(3, 0))

        # Iterations
        section_title(p, "ITERATIONS", "text_secondary")
        iter_card = card(p, "accent_purple", pady=10)

        iter_top = tk.Frame(iter_card, bg=COLORS["bg_panel"])
        iter_top.pack(fill="x", pady=(0, 6))
        self.iter_lbl = tk.Label(
            iter_top,
            text="100,000",
            font=FONTS["heading"],
            bg=COLORS["bg_panel"],
            fg=COLORS["accent_purple"],
        )
        self.iter_lbl.pack(side="left")
        tk.Label(
            iter_top,
            text=" iterations",
            font=FONTS["mono_sm"],
            bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", pady=(4, 0))

        self.iters_var = tk.IntVar(value=100_000)
        tk.Scale(
            iter_card,
            from_=1_000,
            to=600_000,
            resolution=1_000,
            orient="horizontal",
            variable=self.iters_var,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"],
            troughcolor=COLORS["bg_input"],
            activebackground=COLORS["accent_purple"],
            highlightthickness=0,
            sliderlength=14,
            showvalue=False,
            command=self._on_iter_change,
        ).pack(fill="x")

        # Preset buttons
        presets = tk.Frame(iter_card, bg=COLORS["bg_panel"])
        presets.pack(fill="x", pady=(6, 0))
        for lbl, val in [
            ("1k", 1_000),
            ("10k", 10_000),
            ("100k", 100_000),
            ("500k", 500_000),
        ]:
            b = tk.Button(
                presets,
                text=lbl,
                font=FONTS["tiny"],
                bg=COLORS["bg_input"],
                fg=COLORS["accent_purple"],
                activebackground=COLORS["bg_hover"],
                activeforeground=COLORS["accent_purple"],
                relief="flat",
                bd=0,
                cursor="hand2",
                padx=8,
                pady=4,
                command=lambda v=val: self._set_iters(v),
            )
            b.pack(side="left", padx=(0, 4))

        make_button(
            p, "⚡  HASH & TIME IT", command=self._run_pbkdf2, color="accent_purple"
        ).pack(fill="x", ipady=6, pady=(8, 0))

        divider(p)

        # Output
        section_title(p, "RESULT", "text_secondary")
        out_card = card(p, "accent_purple")
        self.pbkdf2_out = card_text(out_card, height=4)

        divider(p)

        # Crack time meter
        section_title(p, "GPU CRACK TIME  (8-char lowercase)", "text_secondary")
        meter_card = card(p, "border", pady=10)

        self.crack_bar_canvas = tk.Canvas(
            meter_card, height=14, bg=COLORS["bg_input"], highlightthickness=0
        )
        self.crack_bar_canvas.pack(fill="x")

        self.crack_time_lbl = tk.Label(
            meter_card,
            text="—",
            font=FONTS["mono"],
            bg=COLORS["bg_panel"],
            fg=COLORS["text_secondary"],
        )
        self.crack_time_lbl.pack(anchor="w", pady=(6, 0))

        self._on_iter_change()

    def _on_iter_change(self, _=None):
        v = self.iters_var.get()
        self.iter_lbl.configure(text=f"{v:,}")
        self._update_crack_meter(v)

    def _set_iters(self, val):
        self.iters_var.set(val)
        self._on_iter_change()

    def _update_crack_meter(self, iters: int):
        est = estimate_crack_time(iters)
        col = crack_color(est)
        self.crack_time_lbl.configure(text=est, fg=col)

        ratio = min(1.0, (math.log10(iters) - 3) / (math.log10(600_000) - 3))
        self.crack_bar_canvas.update_idletasks()
        w = self.crack_bar_canvas.winfo_width() or 240
        self.crack_bar_canvas.delete("all")
        # Track background
        self.crack_bar_canvas.create_rectangle(
            0, 0, w, 14, fill=COLORS["bg_input"], outline=""
        )
        # Fill
        self.crack_bar_canvas.create_rectangle(
            0, 0, int(w * ratio), 14, fill=col, outline=""
        )

    def _run_pbkdf2(self):
        pw = self.pbkdf2_pw_var.get() or "mysecret"
        iters = self.iters_var.get()
        salt = os.urandom(16)
        t0 = time.perf_counter()
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, iters, dklen=32)
        ms = (time.perf_counter() - t0) * 1000
        text_write(
            self.pbkdf2_out,
            f"password   : {pw}\n"
            f"salt       : {salt.hex()[:16]}…\n"
            f"iterations : {iters:,}\n"
            f"hash       : {dk.hex()[:28]}…\n"
            f"time/hash  : {ms:.0f}ms\n",
        )
        self._update_crack_meter(iters)
