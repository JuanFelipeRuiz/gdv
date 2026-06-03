"""
Evaluation tool for GDV usability study.
Runs a guided session, collects answers + think-aloud notes, appends a
LaTeX block to docs/evaluation/evaluation_notes.tex.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk

REPO_ROOT   = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "docs" / "evaluation" / "evaluation_notes.tex"
PLOTS_DIR   = REPO_ROOT / "docs" / "graphic_own"

# ---------- Modern theme ----------------------------------------------------

THEME = {
    "bg":            "#faf6f4",
    "surface":       "#ffffff",
    "border":        "#f0eae7",
    "border_strong": "#e6dcd6",
    "text":          "#1f232b",
    "text_muted":    "#5b6472",
    "text_subtle":   "#9a9290",
    "accent":        "#67000D",
    "accent_hover":  "#8a0a17",
    "accent_soft":   "#f6e6e6",
    "success":       "#1b9968",
    "success_soft":  "#dff2ea",
    "danger":        "#C1151B",
    "chip":          "#f3edea",
}

FONT_FAMILY = "Segoe UI"


def _font(size=10, weight="normal", slant="roman"):
    return (FONT_FAMILY, size, weight) if slant == "roman" else (FONT_FAMILY, size, weight, slant)


# ---------- Questions -------------------------------------------------------

RQ_TITLES = {
    "Plot A — RQ1: Fuel types over time":            "How have different fuel types developed over time?",
    "Plot B — RQ2: Fuel types across Swiss cantons": "How do different fuel types vary across Swiss cantons?",
    "Plot C — RQ3: Aargau vs. other cantons":        "How does Aargau compare to other cantons?",
}


QUESTIONS = [
    {
        "label":   "Plot A — RQ1: Fuel types over time",
        "images":  ["vis_a_area_pct_3.png", "vis_a_area_1.png"],
        "warmups": [
            "Looking at the chart you chose: which fuel type grew the most between 2015 and 2023?",
        ],
        "choice":  "Which of these charts would you use to answer 'How have different fuel types developed over time?' and why?",
        "evals":   [],
        "feedback": "Feedback",
    },
    {
        "label":   "Plot B — RQ2: Fuel types across Swiss cantons",
        "images":  ["vis_b_bar_2.png", "vis_b_bar_3.png"],
        "warmups": [
            "Can you compare two cantons of your choice — what do you observe?",
            "Which canton has the highest Hybrid share?",
        ],
        "choice":  "Which one is more intuitive to you and why?",
        "evals":   [
            "Do the number of labels overwhelm you?",
        ],
        "feedback": "Feedback",
    },
    {
        "label":   "Plot C — RQ3: Aargau vs. other cantons",
        "images":  ["vis_c_bar_bev_2.png", "vis_c_lollipop_bev_delta_1.png"],
        "warmups": [
            "How big is the difference between Aargau and the canton with the highest share?",
            "Can you compare Aargau to Basel-Landschaft — how big is the delta, and how high is the other canton's share?",
        ],
        "choice":  "Which of these two charts did you prefer and why?",
        "evals":   [],
        "feedback": "Feedback",
    },
]


# ---------- LaTeX output ----------------------------------------------------

def escape_latex(text: str) -> str:
    replacements = {
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}", "\\": r"\textbackslash{}",
    }
    return "".join(replacements.get(c, c) for c in text)


TABLE_COL_SPEC = r"""{@{}
  p{0.8cm}   % A: Plot
  p{6cm}     % A: Notes
  p{0.8cm}   % B: Plot
  p{6cm}     % B: Notes
  p{0.8cm}   % C: Plot
  p{6cm}     % C: Notes
@{}}"""

TABLE_HEADER_ROW = "\n".join([
    r"\toprule",
    r"\multicolumn{2}{c}{\textbf{Plot A}} &",
    r"\multicolumn{2}{c}{\textbf{Plot B}} &",
    r"\multicolumn{2}{c}{\textbf{Plot C}} \\",
    r"\cmidrule(lr){1-2}\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
    r"\textbf{Plot} & \textbf{Notes} &",
    r"\textbf{Plot} & \textbf{Notes} &",
    r"\textbf{Plot} & \textbf{Notes} \\",
    r"\midrule",
])


def _cell(text: str) -> str:
    return escape_latex(text.strip()) if text.strip() else "---"


def build_latex_block(nickname: str, beruf: str, dataviz_exp: bool,
                      answers: list[dict], general_notes: str) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    exp_str = "Yes" if dataviz_exp else "No"

    by_key: dict[tuple[str, str], dict] = {}
    for a in answers:
        by_key[(a["plot"], a["question"])] = a

    def get(plot_label: str, q_text: str, field: str = "notes") -> str:
        entry = by_key.get((plot_label, q_text), {})
        return entry.get("answer", "") if field == "answer" else entry.get("notes", "")

    rq = QUESTIONS

    def notes_cell(why: str, fb: str, overwhelm: str = "") -> str:
        parts = []
        if why != "---":
            parts.append(r"\textit{\textbf{Why:}} \newline " + why)
        if overwhelm and overwhelm != "---":
            parts.append(r"\textit{\textbf{Overwhelm:}} \newline " + overwhelm)
        if fb != "---":
            parts.append(r"\textit{\textbf{Feedback:}} \newline " + fb)
        return (r" \newline ").join(parts) if parts else "---"

    a_plot  = _cell(get(rq[0]["label"], rq[0]["choice"], "answer"))
    a_notes = notes_cell(
        _cell(get(rq[0]["label"], rq[0]["choice"])),
        _cell(get(rq[0]["label"], rq[0]["feedback"])),
    )

    b_plot  = _cell(get(rq[1]["label"], rq[1]["choice"], "answer"))
    b_notes = notes_cell(
        _cell(get(rq[1]["label"], rq[1]["choice"])),
        _cell(get(rq[1]["label"], rq[1]["feedback"])),
        _cell(get(rq[1]["label"], rq[1]["evals"][0])),
    )

    c_plot  = _cell(get(rq[2]["label"], rq[2]["choice"], "answer"))
    c_notes = notes_cell(
        _cell(get(rq[2]["label"], rq[2]["choice"])),
        _cell(get(rq[2]["label"], rq[2]["feedback"])),
    )

    data_row = (
        f"  {a_plot} & {a_notes} &\n"
        f"  {b_plot} & {b_notes} &\n"
        f"  {c_plot} & {c_notes} \\\\"
    )

    general_line = ""
    if general_notes.strip():
        general_line = (
            "\n" + r"\multicolumn{6}{l}{\textit{General: "
            + escape_latex(general_notes.strip()) + r"}} \\"
        )

    label_key = escape_latex(nickname).lower().replace(" ", "-")

    lines = [
        f"% ── {escape_latex(nickname)} " + ("─" * 60),
        (r"\noindent\textbf{" + escape_latex(nickname) + r"}"
         r" \quad " + escape_latex(beruf)
         + r" \quad DV experience: " + exp_str
         + r" \quad " + ts
         + r"\label{eval:" + label_key + r"}"),
        "",
        r"\smallskip",
        r"{\small",
        r"\begin{tabular}" + TABLE_COL_SPEC,
        TABLE_HEADER_ROW,
        data_row,
        general_line,
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        "",
        r"\bigskip",
        "",
    ]
    return "\n".join(lines)


# ---------- App -------------------------------------------------------------

class EvalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GDV Evaluation")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(bg=THEME["bg"])

        # fall back to Helvetica when Segoe UI is not installed
        global FONT_FAMILY
        if FONT_FAMILY not in tkfont.families():
            FONT_FAMILY = "Helvetica"

        self._init_styles()

        self.nickname    = tk.StringVar()
        self.beruf       = tk.StringVar()
        self.dataviz_exp = tk.BooleanVar(value=False)
        self.answers     = []
        self.current_q   = 0
        self._img_refs      = []
        self._plot_win      = None
        self._plot_win_refs = []

        self._show_welcome()
        self._show_plot_win_welcome()

    # -- theming ------------------------------------------------------------

    def _init_styles(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass

        s.configure(".", background=THEME["bg"], foreground=THEME["text"],
                    font=_font(11))

        s.configure("Primary.TButton",
                    font=_font(11, "bold"),
                    foreground="#ffffff",
                    background=THEME["accent"],
                    bordercolor=THEME["accent"],
                    focusthickness=0,
                    padding=(18, 10))
        s.map("Primary.TButton",
              background=[("active", THEME["accent_hover"]),
                          ("pressed", THEME["accent_hover"])],
              foreground=[("disabled", "#ffffffaa")])

        s.configure("Ghost.TButton",
                    font=_font(11),
                    foreground=THEME["text"],
                    background=THEME["surface"],
                    bordercolor=THEME["border_strong"],
                    focusthickness=0,
                    padding=(14, 8))
        s.map("Ghost.TButton",
              background=[("active", THEME["chip"]),
                          ("pressed", THEME["chip"])])

        s.configure("Modern.TEntry",
                    fieldbackground=THEME["surface"],
                    bordercolor=THEME["border_strong"],
                    lightcolor=THEME["border_strong"],
                    darkcolor=THEME["border_strong"],
                    padding=8,
                    relief="flat")

        s.configure("Modern.Horizontal.TProgressbar",
                    troughcolor=THEME["border"],
                    background=THEME["accent"],
                    bordercolor=THEME["bg"],
                    lightcolor=THEME["accent"],
                    darkcolor=THEME["accent"],
                    thickness=6)

        s.configure("Modern.Vertical.TScrollbar",
                    background=THEME["border"],
                    troughcolor=THEME["bg"],
                    bordercolor=THEME["bg"],
                    arrowcolor=THEME["text_muted"])

    # -- helpers ------------------------------------------------------------

    def _clear(self):
        for w in self.winfo_children():
            if w is not self._plot_win:
                w.destroy()

    def _card(self, parent, **kwargs):
        return tk.Frame(parent, bg=THEME["surface"], bd=0,
                        highlightthickness=0, **kwargs)

    def _heading(self, parent, text, size=22):
        return tk.Label(parent, text=text, font=_font(size, "bold"),
                        bg=parent["bg"], fg=THEME["text"])

    def _muted(self, parent, text, size=11):
        return tk.Label(parent, text=text, font=_font(size),
                        bg=parent["bg"], fg=THEME["text_muted"],
                        justify="left")

    def _img_paths(self, img_field) -> list[Path]:
        if isinstance(img_field, list):
            return [PLOTS_DIR / f for f in img_field]
        return [PLOTS_DIR / img_field]

    # -- screens ------------------------------------------------------------

    def _show_welcome(self):
        self._clear()
        wrapper = tk.Frame(self, bg=THEME["bg"])
        wrapper.pack(expand=True, fill="both")

        card = self._card(wrapper)
        card.place(relx=0.5, rely=0.5, anchor="center", width=620)

        inner = tk.Frame(card, bg=THEME["surface"], padx=44, pady=40)
        inner.pack(fill="both", expand=True)

        tk.Frame(inner, bg=THEME["accent"], height=3, width=48).pack(
            anchor="w", pady=(0, 16))
        self._heading(inner, "GDV Evaluation", size=26).pack(anchor="w")
        tk.Label(inner, text="Usability study · vehicle registrations in Switzerland",
                 font=_font(11), bg=THEME["surface"],
                 fg=THEME["text_subtle"]).pack(anchor="w", pady=(2, 22))

        body = (
            "Thank you for taking part in this study.\n\n"
            "You will be shown three data visualizations about Swiss vehicle "
            "registrations. For each one, please describe what you see and "
            "answer a few short questions.\n\n"
            "There are no right or wrong answers — we are interested in how "
            "the charts communicate, not in your prior knowledge."
        )
        tk.Label(inner, text=body, font=_font(11), bg=THEME["surface"],
                 fg=THEME["text"], justify="left", wraplength=540).pack(
                 anchor="w")

        btn_row = tk.Frame(inner, bg=THEME["surface"])
        btn_row.pack(fill="x", pady=(28, 0))
        ttk.Button(btn_row, text="Start →", style="Primary.TButton",
                   command=self._show_name).pack(side="right")

    def _show_name(self):
        self._clear()
        wrapper = tk.Frame(self, bg=THEME["bg"])
        wrapper.pack(expand=True, fill="both")

        card = self._card(wrapper)
        card.place(relx=0.5, rely=0.5, anchor="center", width=560)

        inner = tk.Frame(card, bg=THEME["surface"], padx=40, pady=36)
        inner.pack(fill="both", expand=True)

        tk.Frame(inner, bg=THEME["accent"], height=3, width=48).pack(
            anchor="w", pady=(0, 14))
        self._heading(inner, "About you").pack(anchor="w")
        self._muted(inner,
                    "Used only to label this session's responses — pick any nickname.",
                    size=10).pack(anchor="w", pady=(4, 20))

        tk.Label(inner, text="Nickname", font=_font(10, "bold"),
                 bg=THEME["surface"], fg=THEME["text_muted"]).pack(anchor="w")
        entry = ttk.Entry(inner, textvariable=self.nickname,
                          style="Modern.TEntry", font=_font(12), width=30)
        entry.pack(anchor="w", pady=(4, 16), fill="x")
        entry.focus()

        tk.Label(inner, text="Job / Profession", font=_font(10, "bold"),
                 bg=THEME["surface"], fg=THEME["text_muted"]).pack(anchor="w")
        ttk.Entry(inner, textvariable=self.beruf,
                  style="Modern.TEntry", font=_font(11), width=34
                  ).pack(anchor="w", pady=(4, 16), fill="x")

        tk.Label(inner, text="Prior experience with data visualizations",
                 font=_font(10, "bold"), bg=THEME["surface"],
                 fg=THEME["text_muted"]).pack(anchor="w")

        seg = tk.Frame(inner, bg=THEME["surface"])
        seg.pack(anchor="w", pady=(6, 0))

        yes_btn = tk.Button(seg, text="Yes", font=_font(11, "bold"),
                            relief="flat", bd=0, padx=22, pady=8,
                            cursor="hand2")
        no_btn  = tk.Button(seg, text="No", font=_font(11, "bold"),
                            relief="flat", bd=0, padx=22, pady=8,
                            cursor="hand2")

        def paint(val):
            self.dataviz_exp.set(val)
            if val:
                yes_btn.config(bg=THEME["accent"], fg="#ffffff",
                               activebackground=THEME["accent_hover"])
                no_btn.config(bg=THEME["chip"], fg=THEME["text_muted"],
                              activebackground=THEME["chip"])
            else:
                yes_btn.config(bg=THEME["chip"], fg=THEME["text_muted"],
                               activebackground=THEME["chip"])
                no_btn.config(bg=THEME["accent"], fg="#ffffff",
                              activebackground=THEME["accent_hover"])

        yes_btn.config(command=lambda: paint(True))
        no_btn.config(command=lambda: paint(False))
        yes_btn.pack(side="left", padx=(0, 6))
        no_btn.pack(side="left")
        paint(False)

        nav = tk.Frame(inner, bg=THEME["surface"])
        nav.pack(fill="x", pady=(28, 0))

        def proceed():
            if not self.nickname.get().strip():
                messagebox.showwarning("Nickname missing",
                                       "Please enter a nickname to continue.")
                return
            self._show_question()

        self.bind("<Return>", lambda _: proceed())
        ttk.Button(nav, text="Continue →", style="Primary.TButton",
                   command=proceed).pack(side="right")

    def _show_question(self):
        self._clear()

        rq = QUESTIONS[self.current_q]
        plot_label = rq["label"]
        img_paths  = self._img_paths(rq["images"])
        multi_img  = len(img_paths) > 1

        top = tk.Frame(self, bg=THEME["bg"], padx=28, pady=18)
        top.pack(fill="x")

        top_left = tk.Frame(top, bg=THEME["bg"])
        top_left.pack(side="left")
        tk.Label(top_left, text=plot_label.split(" — ")[0],
                 font=_font(10, "bold"), bg=THEME["bg"],
                 fg=THEME["accent"]).pack(anchor="w")
        tk.Label(top_left, text=RQ_TITLES.get(plot_label, plot_label),
                 font=_font(16, "bold"), bg=THEME["bg"],
                 fg=THEME["text"]).pack(anchor="w", pady=(2, 0))

        top_right = tk.Frame(top, bg=THEME["bg"])
        top_right.pack(side="right")
        tk.Label(top_right,
                 text=f"Step {self.current_q + 1} of {len(QUESTIONS)}",
                 font=_font(10), bg=THEME["bg"],
                 fg=THEME["text_subtle"]).pack(anchor="e")
        pb = ttk.Progressbar(top_right,
                             style="Modern.Horizontal.TProgressbar",
                             value=((self.current_q + 1) / len(QUESTIONS)) * 100,
                             length=240)
        pb.pack(pady=(6, 0))

        body = tk.Frame(self, bg=THEME["bg"])
        body.pack(expand=True, fill="both", padx=28, pady=20)

        left_card = self._card(body)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 16))

        left = tk.Frame(left_card, bg=THEME["surface"], padx=18, pady=18)
        left.pack(fill="both", expand=True)

        tk.Label(left, text="Showing on viewer screen",
                 font=_font(9, "bold"), bg=THEME["surface"],
                 fg=THEME["text_subtle"]).pack(anchor="w", pady=(0, 10))

        self._img_refs = []
        if multi_img:
            grid = tk.Frame(left, bg=THEME["surface"])
            grid.pack(fill="both", expand=True)
            cols = 2
            for idx, path in enumerate(img_paths):
                row, col = divmod(idx, cols)
                cell = tk.Frame(grid, bg=THEME["surface"])
                cell.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                grid.grid_rowconfigure(row, weight=1)
                grid.grid_columnconfigure(col, weight=1)

                badge = tk.Frame(cell, bg=THEME["accent_soft"])
                badge.pack(anchor="w", pady=(0, 6))
                tk.Label(badge, text=f"  Plot {idx + 1}  ",
                         font=_font(10, "bold"),
                         bg=THEME["accent_soft"],
                         fg=THEME["accent"]).pack()

                if path.exists():
                    img = Image.open(path)
                    img.thumbnail((280, 280), Image.LANCZOS)
                    ref = ImageTk.PhotoImage(img)
                    self._img_refs.append(ref)
                    tk.Label(cell, image=ref, bg=THEME["surface"]
                             ).pack(expand=True)
                else:
                    tk.Label(cell, text=f"[not found]\n{path.name}",
                             bg=THEME["surface"], fg=THEME["text_subtle"],
                             font=_font(9)).pack(expand=True)
            self._update_plot_window_multi(
                img_paths, rq_label=RQ_TITLES.get(plot_label, plot_label))
        else:
            path = img_paths[0]
            if path.exists():
                img = Image.open(path)
                img.thumbnail((560, 560), Image.LANCZOS)
                ref = ImageTk.PhotoImage(img)
                self._img_refs = [ref]
                tk.Label(left, image=ref, bg=THEME["surface"]
                         ).pack(expand=True, pady=8)
                self._update_plot_window_single(
                    path, rq_label=RQ_TITLES.get(plot_label, plot_label))
            else:
                tk.Label(left, text=f"[image not found]\n{path.name}",
                         bg=THEME["surface"], fg=THEME["text_subtle"],
                         font=_font(10)).pack(expand=True)

        right_card = self._card(body)
        right_card.pack(side="left", fill="both")
        right_card.config(width=480)
        right_card.pack_propagate(False)

        right = tk.Frame(right_card, bg=THEME["surface"])
        right.pack(fill="both", expand=True)

        footer = tk.Frame(right, bg=THEME["surface"])
        footer.pack(side="bottom", fill="x")
        footer_inner = tk.Frame(footer, bg=THEME["surface"], padx=18,
                                pady=14)
        footer_inner.pack(fill="x")

        scroll_wrap = tk.Frame(right, bg=THEME["surface"])
        scroll_wrap.pack(side="top", fill="both", expand=True)
        canvas = tk.Canvas(scroll_wrap, bg=THEME["surface"],
                           highlightthickness=0, bd=0)
        vbar = ttk.Scrollbar(scroll_wrap, orient="vertical",
                             style="Modern.Vertical.TScrollbar",
                             command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=THEME["surface"])
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_config(_):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_config(e):
            canvas.itemconfigure(inner_id, width=e.width)
        inner.bind("<Configure>", _on_inner_config)
        canvas.bind("<Configure>", _on_canvas_config)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        inner_pad = tk.Frame(inner, bg=THEME["surface"], padx=18, pady=18)
        inner_pad.pack(fill="both", expand=True)

        warmups  = rq.get("warmups", [])
        choice_q = rq.get("choice", "")
        evals    = rq.get("evals", [])
        feedback = rq.get("feedback", "")

        notes_boxes = []

        def add_notes_question(parent, q_text, height, with_choice=False):
            tk.Label(parent, text=q_text, font=_font(12, "bold"),
                     bg=THEME["surface"], fg=THEME["text"],
                     wraplength=400, justify="left"
                     ).pack(anchor="w", pady=(0, 4))

            choice_var = None
            if with_choice:
                btn_row = tk.Frame(parent, bg=THEME["surface"])
                btn_row.pack(anchor="w", pady=(8, 4))

                p1 = tk.Button(btn_row, text="Plot 1",
                               font=_font(11, "bold"),
                               relief="flat", bd=0, padx=22, pady=10,
                               cursor="hand2")
                p2 = tk.Button(btn_row, text="Plot 2",
                               font=_font(11, "bold"),
                               relief="flat", bd=0, padx=22, pady=10,
                               cursor="hand2")
                choice_var = tk.StringVar(value="")

                def _set_choice(val, var=choice_var, b1=p1, b2=p2):
                    var.set(val)
                    chosen = THEME["accent"]
                    unchosen_bg = THEME["chip"]
                    if val == "Plot 1":
                        b1.config(bg=chosen, fg="#ffffff",
                                  activebackground=THEME["accent_hover"])
                        b2.config(bg=unchosen_bg, fg=THEME["text_muted"],
                                  activebackground=unchosen_bg)
                    else:
                        b1.config(bg=unchosen_bg, fg=THEME["text_muted"],
                                  activebackground=unchosen_bg)
                        b2.config(bg=chosen, fg="#ffffff",
                                  activebackground=THEME["accent_hover"])

                p1.config(command=lambda: _set_choice("Plot 1"),
                          bg=THEME["chip"], fg=THEME["text_muted"],
                          activebackground=THEME["chip"])
                p2.config(command=lambda: _set_choice("Plot 2"),
                          bg=THEME["chip"], fg=THEME["text_muted"],
                          activebackground=THEME["chip"])
                p1.pack(side="left", padx=(0, 8))
                p2.pack(side="left")

            tk.Label(parent, text="Notes",
                     font=_font(9, "bold"), bg=THEME["surface"],
                     fg=THEME["text_subtle"]
                     ).pack(anchor="w", pady=(12, 4))

            nb = scrolledtext.ScrolledText(
                parent, height=height, font=_font(11), wrap=tk.WORD,
                bd=0, relief="flat", padx=10, pady=8,
                bg="#fafbfd", highlightthickness=1,
                highlightcolor=THEME["accent"],
                highlightbackground=THEME["border_strong"])
            nb.pack(fill="x")
            notes_boxes.append((q_text, nb, choice_var))

        first_section = True
        def section_frame():
            nonlocal first_section
            f = tk.Frame(inner_pad, bg=THEME["surface"])
            f.pack(fill="x", pady=(0 if first_section else 22, 0))
            first_section = False
            return f

        if warmups:
            section = section_frame()
            list_inner = tk.Frame(section, bg=THEME["chip"],
                                  padx=14, pady=12)
            list_inner.pack(fill="x")
            for i, text in enumerate(warmups, start=1):
                row = tk.Frame(list_inner, bg=THEME["chip"])
                row.pack(fill="x", pady=(0 if i == 1 else 8, 0))
                tk.Label(row, text=f"{i}.",
                         font=_font(11, "bold"),
                         bg=THEME["chip"], fg=THEME["text_muted"],
                         width=2, anchor="nw"
                         ).pack(side="left")
                tk.Label(row, text=text,
                         font=_font(11), bg=THEME["chip"],
                         fg=THEME["text"], wraplength=360,
                         justify="left"
                         ).pack(side="left", fill="x", expand=True)
                # warm-ups are think-aloud only — not saved to transcript

        if choice_q or evals:
            section = section_frame()
            if choice_q:
                add_notes_question(section, choice_q, height=6,
                                   with_choice=True)
            for i, q_text in enumerate(evals):
                wrap = tk.Frame(section, bg=THEME["surface"])
                wrap.pack(fill="x", pady=(14 if (choice_q or i > 0) else 0, 0))
                add_notes_question(wrap, q_text, height=5)

        if feedback:
            section = section_frame()
            add_notes_question(section, feedback, height=10)

        for _, nb, _ in notes_boxes:
            if nb is not None:
                nb.focus()
                break

        def next_question():
            for q_text, nb, cv in notes_boxes:
                self.answers.append({
                    "plot": plot_label,
                    "question": q_text,
                    "answer": cv.get() if cv is not None else "",
                    "notes": nb.get("1.0", tk.END).strip() if nb is not None else "",
                })
            canvas.unbind_all("<MouseWheel>")
            self.current_q += 1
            if self.current_q < len(QUESTIONS):
                self._show_question()
            else:
                self._show_general_notes()

        tk.Label(footer_inner,
                 text=f"{self.current_q + 1} / {len(QUESTIONS)}",
                 font=_font(10), bg=THEME["surface"],
                 fg=THEME["text_subtle"]).pack(side="left")
        ttk.Button(footer_inner, text="Next →", style="Primary.TButton",
                   command=next_question).pack(side="right")

    # -- viewer window helpers ---------------------------------------------

    # Shared image-area rectangle so a plot is sized the same whether shown
    # solo, side-by-side, or zoomed.
    VIEWER_HEADER_H = 130
    VIEWER_CHROME_H = 90
    VIEWER_SIDE_PAD = 80

    def _viewer_image_box(self) -> tuple[int, int]:
        screen_w = self._plot_win.winfo_screenwidth()
        screen_h = self._plot_win.winfo_screenheight()
        box_w = screen_w - self.VIEWER_SIDE_PAD
        box_h = screen_h - self.VIEWER_HEADER_H - self.VIEWER_CHROME_H
        return box_w, box_h

    def _open_zoom(self, img_path: Path, plot_number: int | None):
        if not img_path.exists():
            return
        if self._plot_win is None or not self._plot_win.winfo_exists():
            return

        for w in self._plot_win.winfo_children():
            w.destroy()
        self._plot_win.configure(bg=THEME["surface"])

        screen_w = self._plot_win.winfo_screenwidth()
        screen_h = self._plot_win.winfo_screenheight()

        header = tk.Frame(self._plot_win, bg=THEME["surface"], height=44)
        header.pack(fill="x", pady=(8, 0), padx=12)
        header.pack_propagate(False)

        tk.Button(header, text="←  Back",
                  font=_font(13, "bold"),
                  bg=THEME["chip"], fg=THEME["text"],
                  activebackground=THEME["border_strong"],
                  relief="flat", bd=0, padx=16, pady=6,
                  cursor="hand2",
                  command=self._restore_plot_window).pack(side="left")

        if plot_number is not None:
            badge = tk.Frame(header, bg=THEME["accent_soft"])
            badge.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(badge, text=f"  Plot {plot_number}  ",
                     font=_font(18, "bold"),
                     bg=THEME["accent_soft"], fg=THEME["accent"]
                     ).pack(padx=4, pady=2)

        avail_w, avail_h = self._viewer_image_box()
        img = Image.open(img_path)
        img.thumbnail((avail_w, avail_h), Image.LANCZOS)
        ref = ImageTk.PhotoImage(img)
        self._plot_win_refs = [ref]
        tk.Label(self._plot_win, image=ref, bg=THEME["surface"]
                 ).pack(expand=True, fill="both", padx=12, pady=(6, 12))

        self._plot_win.title(
            f"Plot {plot_number} — {img_path.name}"
            if plot_number else img_path.name)

    def _restore_plot_window(self):
        state = getattr(self, "_plot_win_current", None)
        if not state:
            return
        kind, payload, rq_label = state
        if kind == "single":
            self._update_plot_window_single(payload, rq_label=rq_label)
        elif kind == "multi":
            self._update_plot_window_multi(payload, rq_label=rq_label)

    def _show_plot_win_welcome(self):
        if self._plot_win is None or not self._plot_win.winfo_exists():
            self._plot_win = tk.Toplevel(self)
            self._plot_win.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            for w in self._plot_win.winfo_children():
                w.destroy()
        self._plot_win.configure(bg=THEME["surface"])
        screen_w = self._plot_win.winfo_screenwidth()
        screen_h = self._plot_win.winfo_screenheight()
        self._plot_win.geometry(f"{screen_w}x{screen_h}")
        self._plot_win.title("GDV Evaluation")

        center = tk.Frame(self._plot_win, bg=THEME["surface"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Frame(center, bg=THEME["accent"], height=4, width=80).pack(
            pady=(0, 24))
        tk.Label(center, text="GDV Evaluation",
                 font=_font(46, "bold"),
                 bg=THEME["surface"], fg=THEME["text"]).pack()
        tk.Label(center,
                 text="Thank you for taking part in this study.",
                 font=_font(20),
                 bg=THEME["surface"], fg=THEME["text_muted"]).pack(
                 pady=(16, 6))
        tk.Label(center,
                 text="The session will start shortly.",
                 font=_font(16),
                 bg=THEME["surface"], fg=THEME["text_subtle"]).pack()

    def _ensure_plot_win(self):
        if self._plot_win is None or not self._plot_win.winfo_exists():
            self._plot_win = tk.Toplevel(self)
            self._plot_win.protocol("WM_DELETE_WINDOW", lambda: None)
        else:
            for w in self._plot_win.winfo_children():
                w.destroy()
        self._plot_win.configure(bg=THEME["surface"])

    def _update_plot_window_single(self, img_path: Path, rq_label: str = ""):
        self._ensure_plot_win()
        self._plot_win_current = ("single", img_path, rq_label)

        screen_w = self._plot_win.winfo_screenwidth()
        screen_h = self._plot_win.winfo_screenheight()
        self._plot_win.geometry(f"{screen_w}x{screen_h}")

        if rq_label:
            head = tk.Frame(self._plot_win, bg=THEME["surface"])
            head.pack(fill="x", pady=(24, 12))
            tk.Frame(head, bg=THEME["accent"], height=4, width=72).pack(
                pady=(0, 10))
            tk.Label(head, text=rq_label,
                     font=_font(28, "bold"),
                     bg=THEME["surface"], fg=THEME["text"],
                     justify="center").pack()

        box_w, box_h = self._viewer_image_box()
        img = Image.open(img_path)
        img.thumbnail((box_w, box_h), Image.LANCZOS)
        ref = ImageTk.PhotoImage(img)
        self._plot_win_refs = [ref]
        tk.Label(self._plot_win, image=ref, bg=THEME["surface"]
                 ).pack(expand=True, fill="both", padx=40, pady=12)

        self._plot_win.title(img_path.stem)

    def _update_plot_window_multi(self, img_paths: list[Path],
                                  rq_label: str = ""):
        self._ensure_plot_win()
        self._plot_win_current = ("multi", img_paths, rq_label)

        screen_w = self._plot_win.winfo_screenwidth()
        screen_h = self._plot_win.winfo_screenheight()
        self._plot_win.geometry(f"{screen_w}x{screen_h}")

        head_h = 0
        if rq_label:
            head = tk.Frame(self._plot_win, bg=THEME["surface"])
            head.pack(fill="x", pady=(14, 4))
            tk.Frame(head, bg=THEME["accent"], height=4, width=72).pack(
                pady=(0, 6))
            tk.Label(head, text=rq_label,
                     font=_font(24, "bold"),
                     bg=THEME["surface"], fg=THEME["text"],
                     justify="center").pack()
            tk.Label(head, text="Click to zoom into plot",
                     font=_font(11, slant="italic"),
                     bg=THEME["surface"], fg=THEME["text_subtle"]
                     ).pack(pady=(4, 0))
            head_h = 116

        grid = tk.Frame(self._plot_win, bg=THEME["surface"])
        grid.pack(expand=True, fill="both", padx=24, pady=(0, 8))

        cols = 2
        n = len(img_paths)
        rows = (n + cols - 1) // cols

        box_w, box_h = self._viewer_image_box()
        per_cell_overhead = 40
        thumb_w = box_w // cols - 30
        thumb_h = box_h // rows - per_cell_overhead

        self._plot_win_refs = []
        for idx, path in enumerate(img_paths):
            row, col = divmod(idx, cols)
            if not path.exists():
                continue

            cell_card = tk.Frame(grid, bg=THEME["surface"])
            cell_card.grid(row=row, column=col, padx=14, pady=4,
                           sticky="nsew")
            grid.grid_rowconfigure(row, weight=1)
            grid.grid_columnconfigure(col, weight=1)

            cell = tk.Frame(cell_card, bg=THEME["surface"], padx=12, pady=4)
            cell.pack(fill="both", expand=True)

            img = Image.open(path)
            img.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
            ref = ImageTk.PhotoImage(img)
            self._plot_win_refs.append(ref)

            img_lbl = tk.Label(cell, image=ref, bg=THEME["surface"],
                               cursor="hand2")
            img_lbl.pack(expand=True)
            img_lbl.bind("<Button-1>",
                         lambda _, p=path, n=idx + 1:
                             self._open_zoom(p, n))

            badge = tk.Frame(cell, bg=THEME["accent_soft"])
            badge.pack(anchor="center", pady=(4, 0))
            tk.Label(badge, text=f"  Plot {idx + 1}  ",
                     font=_font(11, "bold"),
                     bg=THEME["accent_soft"], fg=THEME["accent"]
                     ).pack(padx=2, pady=1)

        self._plot_win.title(
            " | ".join(p.stem for p in img_paths if p.exists()))

    # -- remaining screens --------------------------------------------------

    def _show_general_notes(self):
        self._clear()

        wrapper = tk.Frame(self, bg=THEME["bg"])
        wrapper.pack(expand=True, fill="both")

        card = self._card(wrapper)
        card.place(relx=0.5, rely=0.5, anchor="center", width=720)

        inner = tk.Frame(card, bg=THEME["surface"], padx=40, pady=36)
        inner.pack(fill="both", expand=True)

        tk.Frame(inner, bg=THEME["accent"], height=3, width=48).pack(
            anchor="w", pady=(0, 14))
        self._heading(inner, "General observations").pack(anchor="w")
        self._muted(inner,
                    "Any additional think-aloud notes, reactions, or comments from this session.",
                    size=11).pack(anchor="w", pady=(4, 16))

        notes_box = scrolledtext.ScrolledText(
            inner, height=12, font=_font(11), wrap=tk.WORD,
            bd=0, relief="flat", padx=12, pady=10,
            bg="#fafbfd", highlightthickness=1,
            highlightcolor=THEME["accent"],
            highlightbackground=THEME["border_strong"])
        notes_box.pack(fill="both", expand=True)
        notes_box.focus()

        def finish():
            general = notes_box.get("1.0", tk.END).strip()
            self._save(general)
            self._show_viewer_thankyou()
            self._show_thankyou()

        nav = tk.Frame(inner, bg=THEME["surface"])
        nav.pack(fill="x", pady=(22, 0))
        ttk.Button(nav, text="Finish session →", style="Primary.TButton",
                   command=finish).pack(side="right")

    def _show_viewer_thankyou(self):
        if self._plot_win is None or not self._plot_win.winfo_exists():
            return
        for w in self._plot_win.winfo_children():
            w.destroy()
        self._plot_win.configure(bg=THEME["surface"])

        center = tk.Frame(self._plot_win, bg=THEME["surface"])
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Frame(center, bg=THEME["accent"], height=4, width=80).pack(
            pady=(0, 24))
        tk.Label(center, text="Thank you!",
                 font=_font(52, "bold"),
                 bg=THEME["surface"], fg=THEME["text"]).pack()
        tk.Label(center,
                 text="Your feedback was very helpful.",
                 font=_font(20),
                 bg=THEME["surface"], fg=THEME["text_muted"]).pack(
                 pady=(16, 6))
        tk.Label(center,
                 text="The session is now complete.",
                 font=_font(16),
                 bg=THEME["surface"], fg=THEME["text_subtle"]).pack()

    def _show_thankyou(self):
        self._clear()

        wrapper = tk.Frame(self, bg=THEME["bg"])
        wrapper.pack(expand=True, fill="both")

        card = self._card(wrapper)
        card.place(relx=0.5, rely=0.5, anchor="center", width=560)

        inner = tk.Frame(card, bg=THEME["surface"], padx=44, pady=44)
        inner.pack(fill="both", expand=True)

        tk.Frame(inner, bg=THEME["accent"], height=3, width=48).pack(
            anchor="w", pady=(0, 14))
        self._heading(inner, "Thanks — all saved.", size=24).pack(anchor="w")
        tk.Label(inner,
                 text=f"Output: {OUTPUT_FILE}",
                 font=_font(10),
                 bg=THEME["surface"], fg=THEME["text_subtle"],
                 wraplength=460, justify="left").pack(anchor="w",
                                                       pady=(10, 22))

        btn_row = tk.Frame(inner, bg=THEME["surface"])
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Quit", style="Ghost.TButton",
                   command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(btn_row, text="New session", style="Primary.TButton",
                   command=self._reset).pack(side="right")

    # -- persistence --------------------------------------------------------

    def _save(self, general_notes: str):
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        block = build_latex_block(
            self.nickname.get().strip(),
            self.beruf.get().strip(),
            self.dataviz_exp.get(),
            self.answers,
            general_notes,
        )
        with open(OUTPUT_FILE, "a", encoding="utf-8") as fh:
            fh.write(block)

    def _close_plot_window(self):
        if self._plot_win and self._plot_win.winfo_exists():
            self._plot_win.protocol("WM_DELETE_WINDOW",
                                    self._plot_win.destroy)
            self._plot_win.destroy()
            self._plot_win = None

    def _reset(self):
        self.answers = []
        self.current_q = 0
        self.nickname.set("")
        self.beruf.set("")
        self.dataviz_exp.set(False)
        self._show_welcome()
        self._show_plot_win_welcome()


if __name__ == "__main__":
    app = EvalApp()
    app.mainloop()
