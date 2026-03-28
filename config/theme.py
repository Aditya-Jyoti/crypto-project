import tkinter as tk
from tkinter import ttk, font
import tkinter.font as tkfont

# ── Colour Palette ──────────────────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg_dark":        "#0a0e1a",   # main window background
    "bg_panel":       "#111827",   # card / panel background
    "bg_input":       "#1a2235",   # entry / text widget background
    "bg_hover":       "#1e2d45",   # button hover

    # Accents
    "accent_blue":    "#3b82f6",   # sender / primary
    "accent_green":   "#10b981",   # receiver / success
    "accent_red":     "#ef4444",   # attacker / danger
    "accent_yellow":  "#f59e0b",   # warning / highlight
    "accent_purple":  "#8b5cf6",   # neutral info

    # Text
    "text_primary":   "#f1f5f9",   # main readable text
    "text_secondary": "#64748b",   # muted / labels
    "text_accent":    "#38bdf8",   # highlighted values

    # Borders
    "border":         "#1e3a5f",   # subtle border
    "border_bright":  "#3b82f6",   # focused border

    # Status colours
    "success":        "#10b981",
    "danger":         "#ef4444",
    "warning":        "#f59e0b",
    "info":           "#3b82f6",
}

# ── Typography ───────────────────────────────────────────────────────────────
FONTS = {
    "title":    ("Courier New", 18, "bold"),
    "heading":  ("Courier New", 13, "bold"),
    "subhead":  ("Courier New", 11, "bold"),
    "body":     ("Courier New", 10),
    "mono":     ("Courier New", 10),
    "mono_sm":  ("Courier New", 9),
    "label":    ("Courier New", 9, "bold"),
    "tiny":     ("Courier New", 8),
}

# ── Dimensions ───────────────────────────────────────────────────────────────
SIZES = {
    "window_width":   520,
    "window_height":  680,
    "pad_x":          16,
    "pad_y":          12,
    "corner":         8,    # not directly usable in tk but kept for reference
    "entry_height":   32,
    "btn_height":     36,
}

# ── Widget style helpers ─────────────────────────────────────────────────────

def apply_window_style(root: tk.Tk, title: str, role: str = "blue"):
    """Configure a top-level window with the global dark theme."""
    root.configure(bg=COLORS["bg_dark"])
    root.title(f"⬡ {title}")
    root.resizable(False, False)

    w, h = SIZES["window_width"], SIZES["window_height"]
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    # Offset each role so windows don't stack exactly
    offsets = {"blue": 0, "green": 540, "red": 1080}
    x_off = offsets.get(role, 0)
    x = max(0, min((screen_w - w) // 2 + x_off - 540, screen_w - w))
    y = (screen_h - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")


def make_frame(parent, **kwargs) -> tk.Frame:
    return tk.Frame(
        parent,
        bg=kwargs.pop("bg", COLORS["bg_panel"]),
        **kwargs
    )


def make_label(parent, text: str, style: str = "body",
               color: str = "text_primary", **kwargs) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=FONTS[style],
        bg=kwargs.pop("bg", COLORS["bg_panel"]),
        fg=COLORS[color],
        **kwargs
    )


def make_entry(parent, textvariable=None, show=None, **kwargs) -> tk.Entry:
    e = tk.Entry(
        parent,
        font=FONTS["mono"],
        bg=COLORS["bg_input"],
        fg=COLORS["text_primary"],
        insertbackground=COLORS["accent_blue"],
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightcolor=COLORS["border_bright"],
        highlightbackground=COLORS["border"],
        textvariable=textvariable,
        **kwargs
    )
    if show:
        e.configure(show=show)
    return e


def make_button(parent, text: str, command=None,
                color: str = "accent_blue", **kwargs) -> tk.Button:
    fg_col = COLORS[color]
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        font=FONTS["subhead"],
        bg=COLORS["bg_input"],
        fg=fg_col,
        activebackground=COLORS["bg_hover"],
        activeforeground=fg_col,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=12,
        pady=6,
        **kwargs
    )
    # Hover effect
    btn.bind("<Enter>", lambda e: btn.configure(bg=COLORS["bg_hover"]))
    btn.bind("<Leave>", lambda e: btn.configure(bg=COLORS["bg_input"]))
    return btn


def make_text_area(parent, height: int = 6, **kwargs) -> tk.Text:
    return tk.Text(
        parent,
        font=FONTS["mono_sm"],
        bg=COLORS["bg_input"],
        fg=COLORS["text_accent"],
        insertbackground=COLORS["accent_blue"],
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightcolor=COLORS["border_bright"],
        highlightbackground=COLORS["border"],
        height=height,
        state="disabled",
        wrap="word",
        **kwargs
    )


def text_write(widget: tk.Text, content: str, clear: bool = True):
    """Helper to write into a read-only Text widget."""
    widget.configure(state="normal")
    if clear:
        widget.delete("1.0", "end")
    widget.insert("end", content)
    widget.configure(state="disabled")
    widget.see("end")


def make_separator(parent) -> tk.Frame:
    return tk.Frame(parent, bg=COLORS["border"], height=1)


def make_badge(parent, text: str, color: str = "accent_blue") -> tk.Label:
    """Small coloured tag label."""
    return tk.Label(
        parent,
        text=f"  {text}  ",
        font=FONTS["tiny"],
        bg=COLORS[color],
        fg=COLORS["bg_dark"],
        padx=4,
        pady=2,
    )


def role_header(parent, title: str, subtitle: str,
                accent: str = "accent_blue") -> tk.Frame:
    """Render a consistent role header (icon + title + subtitle)."""
    frm = make_frame(parent, bg=COLORS["bg_dark"])
    frm.pack(fill="x", padx=0, pady=0)

    bar = tk.Frame(frm, bg=COLORS[accent], height=3)
    bar.pack(fill="x")

    inner = make_frame(frm, bg=COLORS["bg_dark"])
    inner.pack(fill="x", padx=SIZES["pad_x"], pady=(10, 6))

    tk.Label(inner, text=title, font=FONTS["title"],
             bg=COLORS["bg_dark"], fg=COLORS[accent]).pack(anchor="w")
    tk.Label(inner, text=subtitle, font=FONTS["mono_sm"],
             bg=COLORS["bg_dark"], fg=COLORS["text_secondary"]).pack(anchor="w")

    return frm


def section_card(parent, label: str) -> tk.Frame:
    """A labelled card section."""
    outer = make_frame(parent, bg=COLORS["bg_panel"])
    outer.pack(fill="x", padx=SIZES["pad_x"], pady=(0, 10))

    lbl_row = make_frame(outer, bg=COLORS["bg_panel"])
    lbl_row.pack(fill="x", padx=10, pady=(8, 4))
    tk.Label(lbl_row, text=label.upper(), font=FONTS["label"],
             bg=COLORS["bg_panel"], fg=COLORS["text_secondary"]).pack(anchor="w")

    make_separator(outer).pack(fill="x", padx=10, pady=(0, 8))
    return outer
