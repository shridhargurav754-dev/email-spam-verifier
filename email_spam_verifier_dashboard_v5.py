#!/usr/bin/env python3
"""Email Spam Verifier Dashboard (Tkinter) - Neon + Menu (V4)

Adds menu + more interactivity:
- Top Menu bar (File / View / Help)
- Toggle: Dark/Neon theme accent color
- Toggle: Show detailed breakdown
- Button to auto-fill sample
- Keyboard shortcuts: Ctrl+Enter to Analyze, Ctrl+L to Clear

Heuristic scoring is same as V3.

Run:
  python email_spam_verifier_dashboard_v4.py
"""

from __future__ import annotations

import re
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox


# ---------------- Heuristic Rules ----------------
SPAM_KEYWORDS = {
    "winner",
    "congratulations",
    "prize",
    "free",
    "urgent",
    "act now",
    "limited offer",
    "limited time",
    "cash",
    "reward",
    "exclusive",
    "buy now",
    "investment",
    "million",
    "selected",
    "verify your account",
    "password",
    "confirm your",
    "account suspended",
    "security alert",
    "click here",
    "unauthorized",
    "urgent action",
}

URGENCY_PATTERNS = {
    "act now",
    "limited time",
    "today only",
    "final notice",
    "ending soon",
    "last chance",
    "urgent",
}

URL_RE = re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-z]+")

RULE_LABELS = {
    "word_count_gt_threshold": "Word Count",
    "keyword_hits": "Spam Keywords",
    "suspicious_links": "Suspicious Links",
    "exclamation_marks": "Exclamation Marks",
    "all_caps_ratio": "ALL CAPS Ratio",
    "urgency_phrases": "Urgency Phrases",
    "repeated_char_spam": "Repeated Characters",
}


def normalize_email(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", text.strip())


def count_words(text: str) -> int:
    t = normalize_email(text)
    return 0 if not t else len(t.split(" "))


def all_caps_word_count(text: str) -> int:
    words = WORD_RE.findall(text)
    return sum(1 for w in words if len(w) >= 2 and w.isupper())


def spam_keyword_hits(text: str) -> int:
    t = text.lower()
    return sum(1 for kw in SPAM_KEYWORDS if kw in t)


def matched_spam_keywords(text: str) -> list[str]:
    t = text.lower()
    return sorted(kw for kw in SPAM_KEYWORDS if kw in t)


def matched_urgency_phrases(text: str) -> list[str]:
    t = text.lower()
    return sorted(p for p in URGENCY_PATTERNS if p in t)


def top_words(text: str, limit: int = 8) -> list[tuple[str, int]]:
    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "if",
        "in", "is", "it", "let", "me", "of", "on", "or", "please", "the",
        "this", "to", "we", "with", "you", "your",
    }
    counts: dict[str, int] = {}
    for raw in WORD_RE.findall(text.lower()):
        if len(raw) <= 2 or raw in stop_words:
            continue
        counts[raw] = counts.get(raw, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]


def suspicious_link_count(text: str) -> int:
    return len(URL_RE.findall(text))


def repeated_character_points(text: str) -> int:
    return 1 if re.search(r"([A-Za-z])\1{2,}", text) else 0


def exclamation_points(text: str) -> int:
    return 1 if text.count("!") >= 5 else 0


def urgency_points(text: str) -> int:
    t = text.lower()
    return 1 if any(p in t for p in URGENCY_PATTERNS) else 0


@dataclass
class Verdict:
    classification: str
    score: int
    breakdown: dict[str, int]
    word_count: int
    caps_ratio: float
    link_count: int
    keyword_hits: int
    total_points: int


BREAKDOWN_KEYS = [
    "word_count_gt_threshold",
    "keyword_hits",
    "suspicious_links",
    "exclamation_marks",
    "all_caps_ratio",
    "urgency_phrases",
    "repeated_char_spam",
]


def classify_email(
    text: str,
    *,
    word_threshold: int,
    spam_score_threshold: int,
    exclamation_threshold: int,
    caps_ratio_threshold: float,
    enabled: dict[str, bool],
) -> Verdict:
    word_count = count_words(text)
    link_count = suspicious_link_count(text)
    kw_hits = spam_keyword_hits(text)
    caps_count = all_caps_word_count(text)
    caps_ratio = (caps_count / word_count) if word_count else 0.0
    exclam_count = text.count("!")

    breakdown: dict[str, int] = {}

    def add(key: str, on: bool, points: int) -> None:
        breakdown[key] = points if on else 0

    add(
        "word_count_gt_threshold",
        enabled.get("word_count", True),
        2 if word_count > word_threshold else 0,
    )

    add(
        "keyword_hits",
        enabled.get("keywords", True),
        2 if kw_hits >= 1 else 0,
    )

    if enabled.get("links", True):
        if link_count >= 3:
            breakdown["suspicious_links"] = 2
        elif link_count >= 1:
            breakdown["suspicious_links"] = 1
        else:
            breakdown["suspicious_links"] = 0
    else:
        breakdown["suspicious_links"] = 0

    if enabled.get("exclamations", True):
        breakdown["exclamation_marks"] = 1 if exclam_count >= exclamation_threshold else 0
    else:
        breakdown["exclamation_marks"] = 0

    if enabled.get("caps", True):
        breakdown["all_caps_ratio"] = 1 if caps_ratio >= caps_ratio_threshold else 0
    else:
        breakdown["all_caps_ratio"] = 0

    if enabled.get("urgency", True):
        breakdown["urgency_phrases"] = urgency_points(text)
    else:
        breakdown["urgency_phrases"] = 0

    if enabled.get("repeated_chars", True):
        breakdown["repeated_char_spam"] = repeated_character_points(text)
    else:
        breakdown["repeated_char_spam"] = 0

    score = sum(breakdown.get(k, 0) for k in BREAKDOWN_KEYS)
    classification = "SPAM" if score >= spam_score_threshold else "NOT SPAM"
    total_points = 2 + 2 + 2 + 1 + 1 + 1 + 1

    return Verdict(
        classification=classification,
        score=score,
        breakdown=breakdown,
        word_count=word_count,
        caps_ratio=caps_ratio,
        link_count=link_count,
        keyword_hits=kw_hits,
        total_points=total_points,
    )


def clamp(n: float, a: float, b: float) -> float:
    return max(a, min(b, n))


class Chip(tk.Frame):
    def __init__(self, master, label: str, key: str, **kwargs):
        super().__init__(master, **kwargs)
        self.key = key

        self.canvas = tk.Canvas(self, width=26, height=26, highlightthickness=0, bg=kwargs.get("bg", "#0b1020"))
        self.canvas.pack(side="left", padx=(6, 6))

        self.text = tk.Label(self, text=label, fg="#c7d2fe", bg=kwargs.get("bg", "#0b1020"), font=("Segoe UI", 10, "bold"))
        self.text.pack(side="left", padx=(0, 8))

        self.set_active(False)

    def set_active(self, active: bool) -> None:
        self.canvas.delete("all")
        bg = self.text.cget("bg")
        self.canvas.config(bg=bg)
        if active:
            self.canvas.create_oval(4, 4, 22, 22, fill="#ff2bd6", outline="#ff2bd6")
            self.text.config(fg="#ffd1fa")
        else:
            self.canvas.create_oval(4, 4, 22, 22, fill="#1f2a44", outline="#1f2a44")
            self.text.config(fg="#c7d2fe")


class Gauge(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#0b1020")
        self.pack_propagate(False)

        tk.Label(self, text="Risk Gauge", bg="#0b1020", fg="#7dd3fc", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(6, 0))
        self.value_label = tk.Label(self, text="0%", bg="#0b1020", fg="#e9d5ff", font=("Segoe UI", 22, "bold"))
        self.value_label.pack(anchor="w", padx=8, pady=(2, 6))

        self.bar = tk.Canvas(self, height=16, bg="#0b1020", highlightthickness=0)
        self.bar.pack(fill="x", padx=8, pady=(0, 10))

        self.spark = tk.Canvas(self, height=30, bg="#0b1020", highlightthickness=0)
        self.spark.pack(fill="x", padx=8, pady=(0, 10))

        self.current = 0
        self.redraw(0)

    def redraw(self, percent: int) -> None:
        percent = int(clamp(percent, 0, 100))
        self.bar.delete("all")
        w = 320

        self.bar.create_rectangle(0, 0, w, 16, fill="#111a33", outline="#111a33")

        if percent >= 70:
            col = "#ff2b2b"
        elif percent >= 40:
            col = "#ffb020"
        else:
            col = "#22c55e"

        fill_w = int(w * (percent / 100))
        self.bar.create_rectangle(0, 0, fill_w, 16, fill=col, outline=col)
        self.value_label.config(text=f"{percent}%")

        self.spark.delete("all")
        self.spark.config(width=w)

        bars = 12
        gap = 4
        bar_w = (w - (bars - 1) * gap) / bars
        for i in range(bars):
            t = (i + 1) / bars
            height_factor = clamp((percent / 100) * 1.05 - abs(t - 0.6) * 0.8, 0.1, 1.0)
            h = int(26 * height_factor)
            x0 = int(i * (bar_w + gap))
            y0 = 28 - h
            self.spark.create_rectangle(x0, y0, x0 + bar_w, 28, fill=col, outline=col)

    def animate_to(self, target: int) -> None:
        target = int(clamp(target, 0, 100))
        start = self.current
        if target == start:
            return
        step = 1 if target > start else -1

        def _tick():
            nonlocal start
            start += step
            self.current = start
            self.redraw(self.current)
            if start == target:
                return
            self.after(8, _tick)

        _tick()


class DashboardV4(tk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root = root

        self.root.title("Spam Verifier - Neon Dashboard (V4)")
        self.root.geometry("1250x800")
        self.pack(fill="both", expand=True)

        self.accent_var = tk.StringVar(value="#7c3aed")
        self.show_breakdown_var = tk.BooleanVar(value=True)

        # Keyboard shortcuts
        self.root.bind_all("<Control-Return>", lambda e: self.on_analyze())
        self.root.bind_all("<Control-l>", lambda e: self.on_clear())

        self.build_menu()
        self.build_ui()

        # Load default sample
        self.load_spam_sample()

    def build_menu(self) -> None:

        menubar = tk.Menu(self.root)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=filem)

        viewm = tk.Menu(menubar, tearoff=0)
        viewm.add_checkbutton(label="Show Breakdown", variable=self.show_breakdown_var, command=self.refresh_breakdown_visibility)
        menubar.add_cascade(label="View", menu=viewm)

        helpm = tk.Menu(menubar, tearoff=0)
        helpm.add_command(label="How to Use", command=self.show_help)
        menubar.add_cascade(label="Help", menu=helpm)

        self.root.config(menu=menubar)

    def show_help(self) -> None:
        messagebox.showinfo(
            "How to use",
            "Paste email in the box and click Analyze.\n\nShortcuts:\n- Ctrl+Enter = Analyze\n- Ctrl+L = Clear\n\nRule-based detector: word/keyword/link/exclamation/CAPS/urgency/repeated-chars scoring."
        )

    def refresh_breakdown_visibility(self) -> None:
        if self.show_breakdown_var.get():
            self.breakdown_text.pack(fill="both", expand=True)
            self.breakdown_frame.pack(fill="both", expand=True)
        else:
            self.breakdown_frame.pack_forget()

    def build_ui(self) -> None:
        # Background layers (depth + shadow)
        # Using stacked frames to simulate a shadow/gradient depth without external libs.
        tk.Frame(self, bg="#070a14").place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Frame(self, bg="#0a1433").place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        tk.Frame(self, bg="#0b1020").place(relx=0.02, rely=0.02, relwidth=0.96, relheight=0.96)

        self.content = tk.Frame(self, bg="#0b1020")

        self.content.pack(fill="both", expand=True, padx=14, pady=14)

        # Header
        header = tk.Frame(self.content, bg="#0b1020")
        header.pack(fill="x")

        tk.Label(header, text="Email Spam Verifier", bg="#0b1020", fg="#a78bfa", font=("Segoe UI", 26, "bold")).pack(side="left")
        tk.Label(header, text="Neon + Menu + Shortcuts", bg="#0b1020", fg="#7dd3fc", font=("Segoe UI", 12, "bold")).pack(side="left", padx=14, pady=10)

        # Main split
        main = tk.Frame(self.content, bg="#0b1020")
        main.pack(fill="both", expand=True, pady=10)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=2)
        main.grid_columnconfigure(1, weight=1)

        # Left
        left = tk.Frame(main, bg="#0b1020")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_rowconfigure(1, weight=1)

        # Input
        input_box = tk.LabelFrame(left, text="Paste Email Content", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        input_box.pack(fill="both", expand=False)

        # Scrollable input (vertical scrollbar)
        self.text_input = tk.Text(input_box, height=18, wrap="word", bg="#070a14", fg="#e5e7eb", insertbackground="#e5e7eb")
        self.text_input.pack(side="left", fill="both", expand=True)

        text_scroll = tk.Scrollbar(input_box, command=self.text_input.yview)
        text_scroll.pack(side="right", fill="y")
        self.text_input.configure(yscrollcommand=text_scroll.set)

        # Buttons (with external glow/shadow)
        # We draw a soft glow behind the button row using a Canvas placed behind the container.
        btn_card = tk.Frame(left, bg="#0b1020")
        btn_card.pack(fill="x", pady=10)

        self.btn_glow_canvas = tk.Canvas(btn_card, height=54, bg="#0b1020", highlightthickness=0, bd=0)
        self.btn_glow_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Inner container above the glow canvas
        btns = tk.Frame(btn_card, bg="#0b1020")
        btns.place(relx=0, rely=0, relwidth=1, relheight=1)

        def redraw_btn_glow(active: str | None = None) -> None:
            self.btn_glow_canvas.delete("all")
            w = self.btn_glow_canvas.winfo_width()
            h = self.btn_glow_canvas.winfo_height()
            if w <= 1 or h <= 1:
                return

            # Rounded rectangle helper (approx)
            def rrect(x1, y1, x2, y2, rad, **kw):
                self.btn_glow_canvas.create_rectangle(x1+rad, y1, x2-rad, y2, **kw)
                self.btn_glow_canvas.create_rectangle(x1, y1+rad, x2, y2-rad, **kw)
                self.btn_glow_canvas.create_oval(x1, y1, x1+2*rad, y1+2*rad, **kw)
                self.btn_glow_canvas.create_oval(x2-2*rad, y1, x2, y1+2*rad, **kw)
                self.btn_glow_canvas.create_oval(x1, y2-2*rad, x1+2*rad, y2, **kw)
                self.btn_glow_canvas.create_oval(x2-2*rad, y2-2*rad, x2, y2, **kw)

            # Base shadow layers
            base_col = "#7c3aed"
            if active == "SPAM":
                base_col = "#ef4444"
            elif active == "NOT SPAM":
                base_col = "#10b981"

            # Soft outer glow (multiple layers)
            for i, alpha in enumerate(["#000000", base_col, base_col]):
                # alpha isn't directly supported; simulate with different fills by varying color intensity using fixed palette
                # layer 0: dark shadow
                if i == 0:
                    col = "#000000"
                elif i == 1:
                    col = base_col
                else:
                    col = base_col

                pad = 6 + i * 3
                rad = 18
                x1 = pad
                y1 = 6
                x2 = w - pad
                y2 = h - 6
                # Use semi-transparent-like feel via stipple-style not available; instead thicker outline/width
                self.btn_glow_canvas.create_rectangle(x1, y1, x2, y2, outline=col, width=6-i*2)

            # Neon border line
            rrect(10, 8, w-10, h-8, rad=18, outline=base_col, width=2)

        # Redraw on resize and whenever we set SPAM/NOT state
        btn_card.bind("<Configure>", lambda e: redraw_btn_glow(None))
        self._redraw_btn_glow = redraw_btn_glow

        # Buttons styled to sit above the row glow, each with its own outside shadow.
        def shadow_button(parent, text, command, bg, active_bg, width, padx):
            shell = tk.Frame(parent, bg="#020617")
            shell.pack(side="left", padx=padx, pady=(4, 8))

            shadow = tk.Frame(shell, bg="#000000")
            shadow.place(x=4, y=5, relwidth=1, relheight=1)

            btn = tk.Button(
                shell,
                text=text,
                command=command,
                bg=bg,
                fg="white",
                activebackground=active_bg,
                activeforeground="white",
                bd=0,
                relief="flat",
                highlightthickness=0,
                width=width,
                height=2,
                font=("Segoe UI", 10, "bold"),
                cursor="hand2",
            )
            btn.pack(padx=(0, 4), pady=(0, 5))
            return btn

        self.btn_analyze = shadow_button(
            btns, "[!] Analyze", self.on_analyze, "#7c3aed", "#6d28d9", 14, (6, 10)
        )
        shadow_button(btns, "[X] Clear", self.on_clear, "#111827", "#0b1220", 12, 10)
        shadow_button(btns, "[SPAM] Sample", self.load_spam_sample, "#ef4444", "#dc2626", 15, 10)
        shadow_button(btns, "[OK] Sample", self.load_not_spam_sample, "#10b981", "#059669", 15, 10)


        # Controls
        controls = tk.LabelFrame(left, text="Conditions & Thresholds", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        controls.pack(fill="x", pady=(10, 0))

        thr = tk.Frame(controls, bg="#0b1020")
        thr.pack(fill="x")

        self.word_threshold_var = tk.IntVar(value=100)
        self.spam_score_threshold_var = tk.IntVar(value=3)
        self.exclamation_threshold_var = tk.IntVar(value=5)
        self.caps_ratio_threshold_var = tk.DoubleVar(value=0.10)

        def add_spin(parent, text, var, from_, to_, inc_, width=12):
            row = tk.Frame(parent, bg="#0b1020")
            row.pack(side="left", padx=8)
            tk.Label(row, text=text, bg="#0b1020", fg="#c7d2fe", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Spinbox(row, from_=from_, to=to_, increment=inc_, textvariable=var, width=width,
                       bg="#070a14", fg="#e5e7eb", insertbackground="#e5e7eb").pack(anchor="w")

        add_spin(thr, "Word >", self.word_threshold_var, 10, 3000, 1)
        add_spin(thr, "Score >=", self.spam_score_threshold_var, 1, 20, 1)
        add_spin(thr, "Exclam >=", self.exclamation_threshold_var, 1, 50, 1)
        add_spin(thr, "Caps >=", self.caps_ratio_threshold_var, 0.00, 1.00, 0.01, width=10)

        chips_frame = tk.Frame(controls, bg="#0b1020")
        chips_frame.pack(fill="x", pady=10)

        self.enabled_vars: dict[str, tk.BooleanVar] = {
            "word_count": tk.BooleanVar(value=True),
            "keywords": tk.BooleanVar(value=True),
            "links": tk.BooleanVar(value=True),
            "exclamations": tk.BooleanVar(value=True),
            "caps": tk.BooleanVar(value=True),
            "urgency": tk.BooleanVar(value=True),
            "repeated_chars": tk.BooleanVar(value=True),
        }

        chip_titles = [
            ("word_count", "Word Count"),
            ("keywords", "Spam Keywords"),
            ("links", "Suspicious Links"),
            ("exclamations", "Exclamation Marks"),
            ("caps", "ALL CAPS Ratio"),
            ("urgency", "Urgency Phrases"),
            ("repeated_chars", "Repeated Characters"),
        ]

        for idx, (key, label) in enumerate(chip_titles):
            tk.Checkbutton(
                chips_frame,
                text=label,
                variable=self.enabled_vars[key],
                bg="#0b1020",
                fg="#e5e7eb",
                activebackground="#0b1020",
                font=("Segoe UI", 10, "bold"),
                selectcolor="#1d4ed8",
            ).grid(row=idx // 2, column=idx % 2, sticky="w", padx=8, pady=6)

        # Right
        right = tk.Frame(main, bg="#0b1020")
        right.grid(row=0, column=1, sticky="nsew")

        badge = tk.Frame(right, bg="#0b1020")
        badge.pack(fill="x")

        self.badge_icon = tk.Label(badge, text="[?]", bg="#0b1020", fg="#93c5fd", font=("Segoe UI", 18, "bold"))
        self.badge_icon.pack(side="left")

        self.badge_label = tk.Label(badge, text="Classification: -", bg="#0b1020", fg="#e5e7eb", font=("Segoe UI", 18, "bold"))
        self.badge_label.pack(side="left", padx=10)

        card = tk.LabelFrame(right, text="Live Risk", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        card.pack(fill="x", pady=12)
        self.gauge = Gauge(card)
        self.gauge.pack(fill="x")

        # Accuracy + Spam content circle
        circle_row = tk.Frame(right, bg="#0b1020")
        circle_row.pack(fill="x", pady=(0, 8))

        self.circle_canvas = tk.Canvas(circle_row, width=86, height=86, bg="#0b1020", highlightthickness=0)
        self.circle_canvas.pack(side="left", padx=(10, 0))

        self.accuracy_label = tk.Label(circle_row, text="Confidence: -", bg="#0b1020", fg="#e5e7eb", font=("Segoe UI", 12, "bold"))
        self.accuracy_label.pack(anchor="w", padx=12, pady=6)

        self.content_label = tk.Label(circle_row, text="Spam Content: -", bg="#0b1020", fg="#93c5fd", font=("Segoe UI", 11, "bold"))
        self.content_label.pack(anchor="w", padx=12)


        expl = tk.LabelFrame(right, text="Triggered Conditions", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        expl.pack(fill="x", pady=12)

        self.display_chips_frame = tk.Frame(expl, bg="#0b1020")
        self.display_chips_frame.pack(fill="x")

        chip_map = {
            "word_count_gt_threshold": ("Word Count", "word_count"),
            "keyword_hits": ("Keywords", "keywords"),
            "suspicious_links": ("Links", "links"),
            "exclamation_marks": ("Exclamations", "exclamations"),
            "all_caps_ratio": ("ALL CAPS", "caps"),
            "urgency_phrases": ("Urgency", "urgency"),
            "repeated_char_spam": ("Repeated", "repeated_chars"),
        }
        self.display_chips: dict[str, Chip] = {}
        for i, bkey in enumerate(BREAKDOWN_KEYS):
            lbl, _ = chip_map[bkey]
            c = Chip(self.display_chips_frame, label=lbl, key=bkey, bg="#0b1020")
            c.grid(row=i, column=0, sticky="w", pady=3)
            self.display_chips[bkey] = c

        self.breakdown_frame = tk.LabelFrame(right, text="Breakdown", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        self.breakdown_frame.pack(fill="both", expand=True, pady=(0, 0))

        self.breakdown_text = tk.Text(self.breakdown_frame, height=16, wrap="word", bg="#070a14", fg="#e5e7eb", insertbackground="#e5e7eb", relief="flat")
        self.breakdown_text.pack(side="left", fill="both", expand=True)
        self.breakdown_scroll = tk.Scrollbar(self.breakdown_frame, command=self.breakdown_text.yview)
        self.breakdown_scroll.pack(side="right", fill="y")
        self.breakdown_text.configure(yscrollcommand=self.breakdown_scroll.set, state="disabled")


        if not self.show_breakdown_var.get():
            self.breakdown_frame.pack_forget()

        # --- Additional attractor UI content (kept simple/label-based) ---
        # Benefits (short, converts well)
        benefits_frame = tk.LabelFrame(right, text="Why this helps", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        benefits_frame.pack(fill="x", pady=(10, 0))

        self.benefits_lines = tk.Label(
            benefits_frame,
            text=(
                "* Fast rule-based check with adjustable rules\n"
                "* Shows the exact words, links, and patterns that pushed risk up\n"
                "* Gives a practical next step after each analysis"
            ),
            bg="#0b1020",
            fg="#93c5fd",
            justify="left",
            font=("Segoe UI", 10),
            wraplength=460,
        )
        self.benefits_lines.pack(anchor="w")

        # How to read results
        how_frame = tk.LabelFrame(right, text="How to read the result", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        how_frame.pack(fill="x", pady=(10, 0))

        self.how_lines = tk.Label(
            how_frame,
            text=(
                "1) Risk Gauge = overall rule score from 0-100\n"
                "2) Triggered chips show the exact rules that fired\n"
                "3) Word explainer lists the matched phrases and repeated terms"
            ),
            bg="#0b1020",
            fg="#c7d2fe",
            justify="left",
            font=("Segoe UI", 10),
            wraplength=460,
        )
        self.how_lines.pack(anchor="w")

        # Next-step CTA (will update after Analyze)
        self.cta_frame = tk.LabelFrame(right, text="Next step", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        self.cta_frame.pack(fill="x", pady=(10, 0))

        self.cta_title = tk.Label(self.cta_frame, text="Ready? Run an analysis to get your recommendation", bg="#0b1020", fg="#7dd3fc", font=("Segoe UI", 10, "bold"))
        self.cta_title.pack(anchor="w")

        self.cta_body = tk.Label(self.cta_frame, text="Then follow the safest action based on the classification.", bg="#0b1020", fg="#c7d2fe", font=("Segoe UI", 10), justify="left", wraplength=460)
        self.cta_body.pack(anchor="w", pady=(6, 0))

        # Word-level explainer (scrollable)
        word_frame = tk.LabelFrame(right, text="Word Level Explainer", padx=10, pady=10, bg="#0b1020", fg="#e5e7eb")
        word_frame.pack(fill="both", expand=False, pady=(10, 0))


        word_text_row = tk.Frame(word_frame, bg="#0b1020")
        word_text_row.pack(fill="both", expand=True)

        self.word_explainer_text = tk.Text(
            word_text_row,
            height=10,
            wrap="word",
            bg="#070a14",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            relief="flat",
        )
        self.word_explainer_text.pack(side="left", fill="both", expand=True)
        self.word_explainer_text.configure(state="disabled")

        sb = tk.Scrollbar(word_text_row, command=self.word_explainer_text.yview)
        sb.pack(side="right", fill="y")
        self.word_explainer_text.configure(yscrollcommand=sb.set)

        perf_frame = tk.LabelFrame(word_frame, text="Performance Insights", padx=8, pady=8, bg="#0b1020", fg="#e5e7eb")
        perf_frame.pack(fill="x", pady=(8, 0))

        self.word_perf_label = tk.Label(perf_frame, text="Waiting for analysis", bg="#0b1020", fg="#93c5fd", font=("Segoe UI", 10, "bold"))
        self.word_perf_label.pack(anchor="w")

        self.word_perf_details = tk.Label(perf_frame, text="Paste an email to see score density, strongest rule, and matched-word coverage.", bg="#0b1020", fg="#c7d2fe", font=("Segoe UI", 9), justify="left", wraplength=440)
        self.word_perf_details.pack(anchor="w", pady=(4, 0))


    def get_enabled(self) -> dict[str, bool]:
        return {k: v.get() for k, v in self.enabled_vars.items()}

    def risk_percent(self, score: int, total_points: int) -> int:
        return int(clamp((score / total_points) * 100, 0, 100)) if total_points else 0

    def set_default_ui(self) -> None:
        self.badge_icon.config(text="[?]")
        self.badge_label.config(text="Classification: -", fg="#e5e7eb")
        self.accuracy_label.config(text="Confidence: -")
        self.content_label.config(text="Spam Content: -")
        self.circle_canvas.delete("all")
        self.gauge.current = 0
        self.gauge.redraw(0)
        if hasattr(self, "_redraw_btn_glow"):
            self._redraw_btn_glow(None)
        for chip in self.display_chips.values():
            chip.set_active(False)
        self.breakdown_text.configure(state="normal")
        self.breakdown_text.delete("1.0", "end")
        self.breakdown_text.configure(state="disabled")
        self.word_explainer_text.configure(state="normal")
        self.word_explainer_text.delete("1.0", "end")
        self.word_explainer_text.configure(state="disabled")
        self.word_perf_label.config(text="Waiting for analysis")
        self.word_perf_details.config(text="Paste an email to see score density, strongest rule, and matched-word coverage.")

    def on_clear(self) -> None:
        self.text_input.delete("1.0", "end")
        self.set_default_ui()

    def draw_spam_circle(self, risk: int) -> None:
        # Draw a glowing circle with risk percent fill
        self.circle_canvas.delete("all")
        r = 35
        cx = 43
        cy = 43
        x0 = cx - r
        y0 = cy - r
        x1 = cx + r
        y1 = cy + r

        # Background circle
        self.circle_canvas.create_oval(x0, y0, x1, y1, outline="#1f2a44", width=4)

        # Color based on risk
        if risk >= 70:
            col = "#ff2b2b"
            label_col = "#ffd1d1"
        elif risk >= 40:
            col = "#ffb020"
            label_col = "#ffe8c2"
        else:
            col = "#22c55e"
            label_col = "#c7f9d3"

        # Fill using a filled arc
        # Tk supports arc; using extent 0..359 by mapping risk
        extent = int(3.6 * clamp(risk, 0, 100))
        self.circle_canvas.create_arc(x0, y0, x1, y1, start=90, extent=extent, style="pieslice", fill=col, outline=col)

        # Center text
        self.circle_canvas.create_text(cx, cy, text=f"{int(risk)}%", fill=label_col, font=("Segoe UI", 14, "bold"))

    def on_analyze(self) -> None:

        content = self.text_input.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Input missing", "Paste email content first.")
            return

        v = classify_email(
            content,
            word_threshold=self.word_threshold_var.get(),
            spam_score_threshold=self.spam_score_threshold_var.get(),
            exclamation_threshold=self.exclamation_threshold_var.get(),
            caps_ratio_threshold=float(self.caps_ratio_threshold_var.get()),
            enabled=self.get_enabled(),
        )

        risk = self.risk_percent(v.score, v.total_points)
        confidence = risk if v.classification == "SPAM" else 100 - risk

        if v.classification == "SPAM":
            self.badge_icon.config(text="[!]")
            self.badge_label.config(text="Classification: SPAM", fg="#ff2b2b")
            self.cta_title.config(text="SPAM detected - protect yourself")
            self.cta_body.config(text="Avoid clicking links or downloading attachments. Mark as spam and verify the sender through official channels.")
        else:
            self.badge_icon.config(text="[OK]")
            self.badge_label.config(text="Classification: NOT SPAM", fg="#22c55e")
            self.cta_title.config(text="Looks safe - still verify")
            self.cta_body.config(text="No major spam signals found. Still double-check the sender and links before taking action.")

        if hasattr(self, "_redraw_btn_glow"):
            self._redraw_btn_glow(v.classification)

        self.gauge.animate_to(risk)
        self.accuracy_label.config(text=f"Confidence: {confidence}%")
        self.draw_spam_circle(risk)

        spam_content_hint = "HIGH" if v.classification == "SPAM" else "LOW"
        self.content_label.config(text=f"Spam Content: {spam_content_hint} (risk {risk}%)")

        for bkey, chip in self.display_chips.items():
            chip.set_active(v.breakdown.get(bkey, 0) > 0)

        enabled = self.get_enabled()
        triggered_keys = [k for k in BREAKDOWN_KEYS if v.breakdown.get(k, 0) > 0]
        disabled_rules = [key for key, is_on in enabled.items() if not is_on]
        keywords = matched_spam_keywords(content)
        urgencies = matched_urgency_phrases(content)
        frequent_words = top_words(content)
        keyword_text = ", ".join(keywords) if keywords else "none"
        urgency_text = ", ".join(urgencies) if urgencies else "none"
        exclam_count = content.count("!")
        score_density = (v.score / max(v.word_count, 1)) * 100

        if triggered_keys:
            strongest_key = max(triggered_keys, key=lambda key: v.breakdown.get(key, 0))
            strongest = f"{RULE_LABELS[strongest_key]} (+{v.breakdown.get(strongest_key, 0)})"
        else:
            strongest = "None"

        expl_lines = [
            f"Triggered conditions ({len(triggered_keys)}):",
        ]
        if triggered_keys:
            for key in triggered_keys:
                expl_lines.append(f"- {RULE_LABELS[key]} => +{v.breakdown.get(key, 0)}")
        else:
            expl_lines.append("- None. No enabled rule added risk points.")

        expl_lines.extend([
            "",
            "Matched spam words / phrases:",
            "- " + (", ".join(keywords) if keywords else "No spam keyword phrases found."),
            "",
            "Matched urgency phrases:",
            "- " + (", ".join(urgencies) if urgencies else "No urgency phrase found."),
            "",
            "Most repeated meaningful words:",
            "- " + (", ".join(f"{word} ({count})" for word, count in frequent_words) if frequent_words else "No repeated meaningful words found."),
            "",
            "Quick interpretation:",
        ])
        if v.classification == "SPAM":
            expl_lines.append("- Multiple spam signals fired; treat links, attachments, and account requests as suspicious.")
        else:
            expl_lines.append("- Not enough risk signals fired; still verify the sender and links before acting.")

        rule_notes: dict[str, str] = {
            "word_count_gt_threshold": f"Word count is {v.word_count}; threshold is {self.word_threshold_var.get()}.",
            "keyword_hits": f"Detected {v.keyword_hits} spam keyword phrase(s): {keyword_text}.",
            "suspicious_links": f"Found {v.link_count} URL(s); one link adds risk and three or more links add higher risk.",
            "exclamation_marks": f"Exclamation mark count is {exclam_count}; threshold is {self.exclamation_threshold_var.get()}.",
            "all_caps_ratio": f"ALL-CAPS word ratio is {v.caps_ratio:.3f}; threshold is {self.caps_ratio_threshold_var.get():.2f}.",
            "urgency_phrases": f"Matched urgency phrase(s): {urgency_text}.",
            "repeated_char_spam": "Repeated character pattern detected." if v.breakdown.get("repeated_char_spam", 0) else "No repeated-character pattern detected.",
        }

        rationale_lines = []
        for key in BREAKDOWN_KEYS:
            status = "ON" if v.breakdown.get(key, 0) > 0 else "off"
            rationale_lines.append(f"* {RULE_LABELS[key]} [{status}]: {rule_notes[key]}")

        disabled_text = ", ".join(disabled_rules) if disabled_rules else "None"
        perf_detail = (
            f"Risk {risk}% | confidence {confidence}% | score density {score_density:.2f} points per 100 words\n"
            f"Strongest signal: {strongest} | disabled rules: {disabled_text}\n"
            f"Matched keywords: {len(keywords)} | links: {v.link_count} | exclamations: {exclam_count}"
        )

        self.word_explainer_text.configure(state="normal")
        self.word_explainer_text.delete("1.0", "end")
        self.word_explainer_text.insert(
            "end",
            "\n".join(expl_lines) + "\n\nRationale by rule:\n" + "\n".join(rationale_lines),
        )
        self.word_explainer_text.configure(state="disabled")

        self.word_perf_label.config(text=f"Performance Insights: {v.classification}")
        self.word_perf_details.config(text=perf_detail)

        lines = []
        lines.append(f"Score: {v.score}/{v.total_points} | Word Count: {v.word_count}")
        lines.append(f"Links: {v.link_count} | Keyword hits: {v.keyword_hits} | ALL-CAPS ratio: {v.caps_ratio:.3f}")
        lines.append(f"Matched keywords: {keyword_text}")
        lines.append(f"Urgency phrases: {urgency_text}")
        lines.append("")
        lines.append("Condition -> Points")
        for key in BREAKDOWN_KEYS:
            points = v.breakdown.get(key, 0)
            marker = "TRIGGERED" if points > 0 else "-"
            lines.append(f"{RULE_LABELS[key]}: {points}  {marker}")
        self.breakdown_text.configure(state="normal")
        self.breakdown_text.delete("1.0", "end")
        self.breakdown_text.insert("end", "\n".join(lines))
        self.breakdown_text.configure(state="disabled")

    def load_spam_sample(self) -> None:
        sample = (
            "CONGRATULATIONS!!! You are a WINNER. Claim your FREE prize now.\n"
            "Visit http://example.com/claim and verify your account.\n"
            "This is a limited time offer!!! Act now!!!"
        )
        self.text_input.delete("1.0", "end")
        self.text_input.insert("end", sample)
        self.on_analyze()

    def load_not_spam_sample(self) -> None:
        sample = (
            "Hello John,\n\n"
            "Just checking in regarding the meeting schedule next week.\n"
            "Please let me know if you can attend.\n\n"
            "Thanks,\n"
            "Support Team"
        )
        self.text_input.delete("1.0", "end")
        self.text_input.insert("end", sample)
        self.on_analyze()


def main() -> None:
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.1)
    except Exception:
        pass
    app = DashboardV4(root)
    root.mainloop()


if __name__ == "__main__":
    main()

