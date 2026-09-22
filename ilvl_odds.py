"""iLvl Upgrade Odds - check the upgrade and failure chance for one upgrade attempt.

Data comes from the Weapons / Armor / Accessory Data tabs of the upgrade spreadsheet.
Probabilities are stored in basis points (10000 = 100%) for a jump of +0..+5 levels.
A +0 result is a failure (the item stays at its current level); items never lose levels.
"""

import csv
import io
import threading
import tkinter as tk
import urllib.request
from tkinter import ttk

SHEET_ID = "1vwajieBpz1aG5w9Bowha_bi0FKsclHv6GOT3r0qvzps"
# Armor shares the Accessory Data tab: the sheet's Armor Data tab has the wrong odds.
SHEET_TABS = {"weapon": "1739045732", "accessory": "526687631"}
TYPES = [("weapon", "Weapon"), ("armor", "Armor"), ("accessory", "Accessory")]
MIN_LVL, MAX_LVL = 51, 90

# Snapshot of the sheet, used offline and until "Update from sheet" is pressed.
# level: [+0 (fail), +1, +2, +3, +4, +5] in basis points
DATA = {"weapon":{"51":[0,2975,2380,1904,1523,1218],"52":[0,5113,2585,1307,661,334],"53":[0,5716,2501,1094,479,210],"54":[0,6149,2402,939,367,143],"55":[0,6498,2299,813,288,102],"56":[0,6795,2194,708,229,74],"57":[0,7056,2089,618,183,54],"58":[0,7289,1984,540,147,40],"59":[0,7501,1880,471,118,30],"60":[0,7696,1777,410,95,22],"61":[0,7877,1675,356,76,16],"62":[0,8046,1574,308,60,12],"63":[0,8205,1473,265,48,9],"64":[0,8357,1374,226,37,6],"65":[0,8499,1276,192,29,4],"66":[0,8634,1180,161,22,3],"67":[0,8763,1084,134,17,2],"68":[0,8888,989,110,12,1],"69":[0,9006,895,89,9,1],"70":[0,9122,801,70,6,1],"71":[0,9233,709,54,4,0],"72":[0,9338,618,41,3,0],"73":[0,9442,527,29,2,0],"74":[0,9542,437,20,1,0],"75":[0,9639,348,13,0,0],"76":[0,9733,260,7,0,0],"77":[0,9824,173,3,0,0],"78":[1,9912,86,1,0,0],"79":[3,9997,0,0,0,0],"80":[8,9992,0,0,0,0],"81":[21,9979,0,0,0,0],"82":[49,9951,0,0,0,0],"83":[110,9890,0,0,0,0],"84":[243,9757,0,0,0,0],"85":[516,9484,0,0,0,0],"86":[1064,8936,0,0,0,0],"87":[2137,7863,0,0,0,0],"88":[4184,5816,0,0,0,0],"89":[8000,2000,0,0,0,0],"90":[10000,0,0,0,0,0]},"accessory":{"51":[0,2975,2380,1904,1523,1218],"52":[0,5113,2585,1307,661,334],"53":[0,5716,2501,1094,479,210],"54":[0,6149,2402,939,367,143],"55":[0,6498,2299,813,288,102],"56":[0,6795,2194,708,229,74],"57":[0,7056,2089,618,183,54],"58":[0,7289,1984,540,147,40],"59":[0,7501,1880,471,118,30],"60":[0,7696,1777,410,95,22],"61":[0,7877,1675,356,76,16],"62":[3,8044,1573,308,60,12],"63":[11,8197,1472,264,47,9],"64":[25,8335,1371,226,37,6],"65":[48,8458,1270,191,29,4],"66":[82,8563,1170,160,22,3],"67":[128,8652,1070,132,16,2],"68":[190,8719,970,108,12,1],"69":[270,8764,870,86,9,1],"70":[368,8785,772,68,6,1],"71":[487,8782,675,52,4,0],"72":[630,8750,579,38,3,0],"73":[797,8689,485,27,2,0],"74":[992,8595,394,18,1,0],"75":[1216,8467,306,11,0,0],"76":[1471,8301,222,6,0,0],"77":[1759,8096,142,3,0,0],"78":[2082,7849,68,1,0,0],"79":[2442,7558,0,0,0,0],"80":[2841,7159,0,0,0,0],"81":[3281,6719,0,0,0,0],"82":[3763,6237,0,0,0,0],"83":[4290,5710,0,0,0,0],"84":[4864,5136,0,0,0,0],"85":[5487,4513,0,0,0,0],"86":[6159,3841,0,0,0,0],"87":[6885,3115,0,0,0,0],"88":[7664,2336,0,0,0,0],"89":[8500,1500,0,0,0,0],"90":[10000,0,0,0,0,0]}}
DATA = {t: {int(lvl): probs for lvl, probs in levels.items()} for t, levels in DATA.items()}
DATA["armor"] = DATA["accessory"]  # armor uses the same odds as accessories

# Palette
BG = "#12151B"
SURFACE = "#1A1F27"
SUNKEN = "#0D1015"
LINE = "#2B313B"
INK = "#E8EBF0"
MUTED = "#97A0AE"
FAINT = "#56606E"
ACCENT = "#E8A93F"
GOOD = "#4CC48B"
BAD = "#F0735F"
TYPE_COLOR = {"weapon": ACCENT, "armor": GOOD, "accessory": BAD}

FONT = "Segoe UI"
MONO = "Consolas"


def fetch_sheet():
    """Download the three Data tabs from the Google Sheet and parse them."""
    fresh = {}
    for item_type, gid in SHEET_TABS.items():
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        with urllib.request.urlopen(url, timeout=15) as resp:
            text = resp.read().decode("utf-8")
        levels = {}
        for row in csv.DictReader(io.StringIO(text)):
            delta = int(row["delta"])
            if delta < 0:
                continue
            lvl = int(row["current_level"])
            levels.setdefault(lvl, [0] * 6)[delta] = int(row["probability"])
        missing = [lvl for lvl in range(MIN_LVL, MAX_LVL + 1) if lvl not in levels]
        if missing:
            raise ValueError(f"{item_type} tab is missing iLvl {missing[0]}")
        fresh[item_type] = levels
    fresh["armor"] = fresh["accessory"]
    return fresh


def pct(bp):
    return f"{bp / 100:.2f}%"


def num(x):
    return f"{x:.2f}" if x != float("inf") else "—"


def calc(data, item_type, lvl):
    p = data[item_type][lvl]
    fail = p[0]
    up = 10000 - fail
    gain = sum(d * v for d, v in enumerate(p)) / 10000
    return {
        "p": p,
        "fail": fail,
        "up": up,
        "gain": gain,
        "per_lvl": 1 / gain if gain > 0 else float("inf"),
        "until_any": 10000 / up if up > 0 else float("inf"),
    }


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.data = DATA
        self.title("iLvl Upgrade Odds")
        self.configure(bg=BG)
        self.minsize(720, 760)

        self.type_var = tk.StringVar(value="weapon")
        self.lvl_var = tk.IntVar(value=75)
        self._syncing = False

        self._style()
        self._build()
        self.render()

    # ---------- layout ----------
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame", background=BG)
        s.configure("Card.TFrame", background=SURFACE)
        s.configure("TLabel", background=BG, foreground=INK, font=(FONT, 10))
        s.configure("Card.TLabel", background=SURFACE, foreground=INK, font=(FONT, 10))
        s.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=(FONT, 9))
        s.configure("TButton", background=LINE, foreground=INK, font=(FONT, 9), borderwidth=0, padding=(10, 5))
        s.map("TButton", background=[("active", FAINT), ("disabled", SURFACE)], foreground=[("disabled", FAINT)])
        s.configure("Horizontal.TScale", background=SURFACE, troughcolor=SUNKEN)
        s.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=INK,
                    font=(MONO, 10), rowheight=26, borderwidth=0)
        s.configure("Treeview.Heading", background=SUNKEN, foreground=MUTED, font=(FONT, 9, "bold"), borderwidth=0)
        s.map("Treeview", background=[("selected", LINE)], foreground=[("selected", INK)])
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])  # drop the light border

    def _card(self, parent, **grid):
        f = tk.Frame(parent, bg=SURFACE, highlightbackground=LINE, highlightthickness=1, padx=16, pady=14)
        f.grid(sticky="nsew", pady=(0, 12), **grid)
        return f

    def _build(self):
        root = ttk.Frame(self, padding=(20, 16, 20, 8))
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)

        head = ttk.Frame(root)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        tk.Label(head, text="iLvl Upgrade Odds", bg=BG, fg=INK, font=(FONT, 20, "bold")).pack(anchor="w")
        tk.Label(head, text="Pick your item type and current item level to see what one upgrade attempt will do.",
                 bg=BG, fg=MUTED, font=(FONT, 10)).pack(anchor="w")

        # Controls
        ctrl = self._card(root, row=1, column=0, columnspan=2)
        ctrl.columnconfigure(1, weight=1)
        tk.Label(ctrl, text="ITEM TYPE", bg=SURFACE, fg=MUTED, font=(FONT, 8, "bold")).grid(row=0, column=0, sticky="w")
        types = tk.Frame(ctrl, bg=SUNKEN, padx=3, pady=3)
        types.grid(row=1, column=0, sticky="w", padx=(0, 24))
        for item_type, name in TYPES:
            tk.Radiobutton(types, text=name, value=item_type, variable=self.type_var, command=self.render,
                           indicatoron=False, font=(FONT, 10, "bold"), padx=12, pady=5, bd=0,
                           relief="flat", offrelief="flat", cursor="hand2",
                           bg=SUNKEN, fg=MUTED, activebackground=LINE, activeforeground=INK,
                           selectcolor=LINE).pack(side="left", padx=1)

        tk.Label(ctrl, text="CURRENT ITEM LEVEL", bg=SURFACE, fg=MUTED, font=(FONT, 8, "bold")).grid(row=0, column=1, sticky="w")
        lvlrow = tk.Frame(ctrl, bg=SURFACE)
        lvlrow.grid(row=1, column=1, sticky="ew")
        lvlrow.columnconfigure(3, weight=1)
        self.dec_btn = ttk.Button(lvlrow, text="−", width=3, command=lambda: self.set_lvl(self.lvl_var.get() - 1))
        self.dec_btn.grid(row=0, column=0)
        self.spin = tk.Spinbox(lvlrow, from_=MIN_LVL, to=MAX_LVL, width=4, textvariable=self.lvl_var,
                               font=(MONO, 16, "bold"), justify="center", bg=SUNKEN, fg=INK,
                               insertbackground=INK, buttonbackground=SURFACE, relief="flat",
                               command=lambda: self.set_lvl(self.spin.get()))
        self.spin.grid(row=0, column=1, padx=4)
        self.spin.bind("<Return>", lambda e: self.set_lvl(self.spin.get()))
        self.spin.bind("<FocusOut>", lambda e: self.set_lvl(self.spin.get()))
        self.inc_btn = ttk.Button(lvlrow, text="+", width=3, command=lambda: self.set_lvl(self.lvl_var.get() + 1))
        self.inc_btn.grid(row=0, column=2)
        self.scale = ttk.Scale(lvlrow, from_=MIN_LVL, to=MAX_LVL, orient="horizontal",
                               command=lambda v: None if self._syncing else self.set_lvl(float(v)))
        self.scale.grid(row=0, column=3, sticky="ew", padx=(14, 0))

        # Verdict
        v = self._card(root, row=2, column=0, columnspan=2)
        v.columnconfigure(0, weight=1)
        v.columnconfigure(1, weight=1)
        top = tk.Frame(v, bg=SURFACE)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.v_title = tk.Label(top, bg=SURFACE, fg=INK, font=(FONT, 13, "bold"))
        self.v_title.pack(side="left")
        self.v_pill = tk.Label(top, font=(FONT, 9, "bold"), padx=10, pady=3)
        self.v_pill.pack(side="right")

        self.up_box = self._odd_box(v, "UPGRADE CHANCE", GOOD, "#13301F", 0)
        self.fail_box = self._odd_box(v, "FAILURE CHANCE", BAD, "#3A1A15", 1)

        self.split = tk.Canvas(v, height=10, bg=SUNKEN, highlightthickness=0)
        self.split.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 12))
        self.split.bind("<Configure>", lambda e: self.render())

        stats = tk.Frame(v, bg=SURFACE)
        stats.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.stat_labels = {}
        for i, (key, label) in enumerate([("gain", "Avg levels gained per attempt"),
                                          ("per_lvl", "Avg attempts per +1 level"),
                                          ("until_any", "Avg attempts until any upgrade")]):
            stats.columnconfigure(i, weight=1)
            tk.Label(stats, text=label, bg=SURFACE, fg=MUTED, font=(FONT, 9)).grid(row=0, column=i, sticky="w")
            lbl = tk.Label(stats, bg=SURFACE, fg=INK, font=(MONO, 14, "bold"))
            lbl.grid(row=1, column=i, sticky="w")
            self.stat_labels[key] = lbl

        # Outcomes
        out = self._card(root, row=3, column=0, padx=(0, 6))
        tk.Label(out, text="Every possible result", bg=SURFACE, fg=INK, font=(FONT, 11, "bold")).pack(anchor="w")
        self.out_sub = tk.Label(out, bg=SURFACE, fg=MUTED, font=(FONT, 9))
        self.out_sub.pack(anchor="w", pady=(0, 6))
        self.out_canvas = tk.Canvas(out, height=190, bg=SURFACE, highlightthickness=0)
        self.out_canvas.pack(fill="both", expand=True)
        self.out_canvas.bind("<Configure>", lambda e: self.draw_outcomes())

        # Compare
        cmp_card = self._card(root, row=3, column=1, padx=(6, 0))
        tk.Label(cmp_card, text="Same level, other item types", bg=SURFACE, fg=INK, font=(FONT, 11, "bold")).pack(anchor="w")
        self.cmp_sub = tk.Label(cmp_card, bg=SURFACE, fg=MUTED, font=(FONT, 9))
        self.cmp_sub.pack(anchor="w", pady=(0, 6))
        cols = ("type", "up", "fail", "gain")
        self.tree = ttk.Treeview(cmp_card, columns=cols, show="headings", height=3, selectmode="none")
        for c, name, w, anchor in [("type", "Type", 110, "w"), ("up", "Upgrade", 76, "e"),
                                   ("fail", "Failure", 76, "e"), ("gain", "Avg gain", 72, "e")]:
            self.tree.heading(c, text=name, anchor=anchor)
            self.tree.column(c, width=w, anchor=anchor, stretch=True)
        self.tree.tag_configure("cur", foreground=ACCENT)
        self.tree.pack(fill="x")

        # Chart
        ch = self._card(root, row=4, column=0, columnspan=2)
        tk.Label(ch, text="Failure chance by item level", bg=SURFACE, fg=INK, font=(FONT, 11, "bold")).pack(anchor="w")
        tk.Label(ch, text="Click a level on the chart to jump to it.", bg=SURFACE, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
        self.chart = tk.Canvas(ch, height=200, bg=SURFACE, highlightthickness=0)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))
        self.chart.bind("<Configure>", lambda e: self.draw_chart())
        self.chart.bind("<Button-1>", self.chart_click)
        legend = tk.Frame(ch, bg=SURFACE)
        legend.pack(anchor="w", pady=(6, 0))
        for item_type, name in TYPES:
            tk.Label(legend, text="━", bg=SURFACE, fg=TYPE_COLOR[item_type], font=(FONT, 11, "bold")).pack(side="left")
            tk.Label(legend, text=name, bg=SURFACE, fg=MUTED, font=(FONT, 9)).pack(side="left", padx=(2, 12))

        # Footer
        foot = ttk.Frame(root)
        foot.grid(row=5, column=0, columnspan=2, sticky="ew")
        self.status = tk.Label(foot, text="Using built-in data from the sheet.", bg=BG, fg=MUTED, font=(FONT, 9))
        self.status.pack(side="left")
        self.refresh_btn = ttk.Button(foot, text="Update from sheet", command=self.refresh)
        self.refresh_btn.pack(side="right")

        root.rowconfigure(4, weight=1)

    def _odd_box(self, parent, title, fg, bg, col):
        f = tk.Frame(parent, bg=bg, padx=14, pady=10)
        f.grid(row=1, column=col, sticky="nsew", padx=(0, 6) if col == 0 else (6, 0))
        tk.Label(f, text=title, bg=bg, fg=fg, font=(FONT, 8, "bold")).pack(anchor="w")
        value = tk.Label(f, bg=bg, fg=INK, font=(MONO, 28, "bold"))
        value.pack(anchor="w")
        sub = tk.Label(f, bg=bg, fg=MUTED, font=(FONT, 9))
        sub.pack(anchor="w")
        return value, sub

    # ---------- behaviour ----------
    def set_lvl(self, value):
        try:
            lvl = int(round(float(value)))
        except (TypeError, ValueError):
            lvl = self.current_lvl()
        lvl = max(MIN_LVL, min(MAX_LVL, lvl))
        if lvl != self.lvl_var.get() or str(self.spin.get()) != str(lvl):
            self.lvl_var.set(lvl)
        self.render()

    def current_lvl(self):
        try:
            return max(MIN_LVL, min(MAX_LVL, int(self.lvl_var.get())))
        except (tk.TclError, ValueError):
            return MIN_LVL

    def render(self):
        item_type = self.type_var.get()
        lvl = self.current_lvl()
        r = calc(self.data, item_type, lvl)
        type_name = dict(TYPES)[item_type]

        self._syncing = True
        self.scale.set(lvl)
        self._syncing = False
        self.dec_btn.state(["disabled"] if lvl <= MIN_LVL else ["!disabled"])
        self.inc_btn.state(["disabled"] if lvl >= MAX_LVL else ["!disabled"])

        self.v_title.config(text=f"{type_name} at iLvl {lvl}")
        if lvl >= MAX_LVL:
            pill = ("Max level reached", BAD, "#3A1A15")
        elif r["fail"] >= 5000:
            pill = ("Fails more often than not", BAD, "#3A1A15")
        elif r["fail"] >= 1000:
            pill = ("Noticeable failure risk", ACCENT, "#3A2C14")
        else:
            pill = ("Upgrade very likely", GOOD, "#13301F")
        self.v_pill.config(text=pill[0], fg=pill[1], bg=pill[2])

        up_val, up_sub = self.up_box
        fail_val, fail_sub = self.fail_box
        up_val.config(text=pct(r["up"]))
        up_sub.config(text="Can't go past 90" if lvl >= MAX_LVL else f"Reach iLvl {lvl + 1} or higher")
        fail_val.config(text=pct(r["fail"]))
        fail_sub.config(text=f"Stay at iLvl {lvl}")

        w = self.split.winfo_width()
        self.split.delete("all")
        split_x = w * r["up"] / 10000
        self.split.create_rectangle(0, 0, split_x, 10, fill=GOOD, width=0)
        self.split.create_rectangle(split_x, 0, w, 10, fill=BAD, width=0)

        self.stat_labels["gain"].config(text=f"+{num(r['gain'])}")
        self.stat_labels["per_lvl"].config(text=num(r["per_lvl"]))
        self.stat_labels["until_any"].config(text=num(r["until_any"]))

        self.out_sub.config(text=f"One attempt from iLvl {lvl}. The chances add up to 100%.")
        self.cmp_sub.config(text=f"Odds for each item type at iLvl {lvl}.")
        self.tree.delete(*self.tree.get_children())
        for t, name in TYPES:
            c = calc(self.data, t, lvl)
            self.tree.insert("", "end", values=(name, pct(c["up"]),
                                                pct(c["fail"]), f"+{num(c['gain'])}"),
                             tags=("cur",) if t == item_type else ())

        self.draw_outcomes()
        self.draw_chart()

    def draw_outcomes(self):
        cv = self.out_canvas
        cv.delete("all")
        lvl = self.current_lvl()
        p = self.data[self.type_var.get()][lvl]
        w = max(cv.winfo_width(), 200)
        name_w, pct_w, row_h = 90, 70, 30
        bar_x0, bar_x1 = name_w, w - pct_w
        biggest = max(p) or 1
        row = 0
        for d, v in enumerate(p):
            if d > 0 and lvl + d > MAX_LVL:
                continue
            y = row * row_h + 10
            color = BAD if d == 0 else GOOD
            text_color = FAINT if v == 0 else INK
            label = f"Stay  {lvl}" if d == 0 else f"+{d} → {lvl + d}"
            cv.create_text(0, y, text=label, anchor="w", fill=text_color, font=(MONO, 10))
            cv.create_rectangle(bar_x0, y - 4, bar_x1, y + 4, fill=SUNKEN, width=0)
            if v:
                cv.create_rectangle(bar_x0, y - 4, bar_x0 + (bar_x1 - bar_x0) * v / biggest, y + 4, fill=color, width=0)
            cv.create_text(w, y, text=pct(v), anchor="e", fill=text_color, font=(MONO, 10))
            row += 1

    def chart_geom(self):
        w = max(self.chart.winfo_width(), 300)
        h = max(self.chart.winfo_height(), 150)
        left, right, top, bottom = 44, 10, 8, 24
        x = lambda lv: left + (lv - MIN_LVL) / (MAX_LVL - MIN_LVL) * (w - left - right)
        y = lambda bp: top + (1 - bp / 10000) * (h - top - bottom)
        return w, h, left, right, top, bottom, x, y

    def draw_chart(self):
        cv = self.chart
        cv.delete("all")
        w, h, left, right, top, bottom, x, y = self.chart_geom()
        cur_type = self.type_var.get()
        lvl = self.current_lvl()
        step = (w - left - right) / (MAX_LVL - MIN_LVL)

        for v in (0, 2500, 5000, 7500, 10000):
            cv.create_line(left, y(v), w - right, y(v), fill=LINE)
            cv.create_text(left - 6, y(v), text=f"{v // 100}%", anchor="e", fill=MUTED, font=(MONO, 8))
        for lv in (51, 55, 60, 65, 70, 75, 80, 85, 90):
            cv.create_text(x(lv), h - 8, text=str(lv), fill=MUTED, font=(MONO, 8))

        cv.create_rectangle(x(lvl) - step / 2, top, x(lvl) + step / 2, h - bottom, fill=LINE, width=0)

        order = sorted((t for t, _ in TYPES), key=lambda t: t == cur_type)
        for t in order:
            pts = []
            for lv in range(MIN_LVL, MAX_LVL + 1):
                pts += [x(lv), y(self.data[t][lv][0])]
            sel = t == cur_type
            cv.create_line(*pts, fill=TYPE_COLOR[t] if sel else FAINT, width=3 if sel else 1.5,
                           dash=() if sel else (4, 3), joinstyle="round")

        cy = y(self.data[cur_type][lvl][0])
        cv.create_oval(x(lvl) - 5, cy - 5, x(lvl) + 5, cy + 5, fill=TYPE_COLOR[cur_type], outline=SURFACE, width=2)

    def chart_click(self, event):
        w, h, left, right, top, bottom, x, y = self.chart_geom()
        if left <= event.x <= w - right:
            self.set_lvl(MIN_LVL + (event.x - left) / (w - left - right) * (MAX_LVL - MIN_LVL))

    def refresh(self):
        self.refresh_btn.state(["disabled"])
        self.status.config(text="Downloading the latest odds from the sheet…", fg=MUTED)

        def work():
            try:
                fresh = fetch_sheet()
                self.after(0, lambda: self._refresh_done(fresh, None))
            except Exception as exc:  # network or parse problem
                self.after(0, lambda: self._refresh_done(None, exc))

        threading.Thread(target=work, daemon=True).start()

    def _refresh_done(self, fresh, error):
        self.refresh_btn.state(["!disabled"])
        if error:
            self.status.config(text=f"Couldn't reach the sheet ({error}). Still using the built-in data.", fg=BAD)
            return
        self.data = fresh
        self.status.config(text="Updated with the latest odds from the sheet.", fg=GOOD)
        self.render()


if __name__ == "__main__":
    App().mainloop()
