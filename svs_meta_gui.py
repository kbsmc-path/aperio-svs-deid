"""
GUI for SVS metadata de-identification (scan date, scanner IDs, slide label image).

Scans a folder, shows what each slide currently carries, lets you pick what to change,
previews the result (dry run) and then applies it. All the actual work is done by
svs_meta.py, which edits the TIFF metadata in place - pixel data of the pyramid is never
touched and a 1.6 GB slide is processed in milliseconds.

    python svs_meta_gui.py [folder]

Safety
    - "미리보기" (preview) never writes anything.
    - "적용" (apply) asks for confirmation and can make a .bak copy of each file first.
    - Removing the label image zeroes its pixel bytes, so it cannot be recovered.

Requirements: Python 3.8+ with tkinter - no third-party packages. svs_meta.py and i18n.py must
sit in the same folder. A missing piece is reported with install instructions.
"""
import os
import queue
import sys
import threading
import time

MIN_PYTHON = (3, 8)


def _missing(problem, fix):
    """A requirement is missing: say what and how to install it (console + message box), then exit.

    The message box matters when the .py was started by double-click - the console closes at once.
    """
    msg = f"{problem}\n\n{fix}"
    print("\n[!] " + msg.replace("\n", "\n    ") + "\n", file=sys.stderr, flush=True)
    try:
        import tkinter
        from tkinter import messagebox as mb
        root = tkinter.Tk()
        root.withdraw()
        mb.showerror("SVS De-identification", msg)
        root.destroy()
    except Exception:  # noqa - no tkinter either: the console text has to do
        pass
    sys.exit(1)


if sys.version_info < MIN_PYTHON:
    _missing(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required (this is {sys.version.split()[0]}).\n"
             f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} 이상이 필요합니다.",
             "https://www.python.org/downloads/  (Windows: tick 'Add python.exe to PATH')")
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter import font as tkfont
except ImportError as e:
    _missing(f"tkinter (Python's GUI library) is not available: {e}\n"
             "tkinter(파이썬 GUI 모듈)가 없습니다.",
             "Windows / macOS: install Python from https://www.python.org/downloads/ (tkinter is included)\n"
             "Ubuntu / Debian:  sudo apt install python3-tk\n"
             "Fedora:           sudo dnf install python3-tkinter\n"
             "macOS Homebrew:   brew install python-tk")
try:
    import i18n
    import svs_meta
    from i18n import t
except ImportError as e:
    _missing(f"A file of this program is missing: {e}\n"
             "svs_meta_gui.py 와 같은 폴더에 svs_meta.py / i18n.py 가 없습니다.",
             "Download the whole repository (GitHub: Code > Download ZIP) and keep all files together.\n"
             "저장소 전체를 받아서(GitHub: Code > Download ZIP) 파일들을 한 폴더에 두세요.")


def app_dir():
    """Folder the program lives in (the .exe's folder when frozen, not the temp unpack dir)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


LOG_FILE = os.path.join(app_dir(), "svs_deid.log")
_log_fh = None


def console(text=""):
    """Print to the console window and append to the log file."""
    global _log_fh
    try:
        print(text, flush=True)
    except Exception:  # noqa - no console attached
        pass
    if _log_fh is None:
        try:
            _log_fh = open(LOG_FILE, "a", encoding="utf-8")
        except OSError:
            _log_fh = False
    if _log_fh:
        try:
            _log_fh.write(text + "\n")
            _log_fh.flush()
        except OSError:
            pass


BANNER_KO = """\
============================================================
  SVS 메타데이터 비식별 도구  (SVS_Deid)
============================================================
  이 검은 창은 프로그램의 '기록 창'입니다. 정상입니다.
  작업 내용이 여기에 그대로 남으므로, 나중에 무엇을 바꿨는지
  확인할 수 있습니다. 창을 닫지 마세요.

  [ 사용 순서 ]
    1. 함께 열린 'SVS 메타데이터 비식별 도구' 창에서
       폴더를 고르고 [스캔]
    2. 오른쪽에서 바꿀 항목 선택
    3. [미리보기] - 파일을 건드리지 않고 결과만 확인
    4. [적용]     - 확인 후 실제로 수정

  [ 주의 ]
    * [적용]은 되돌릴 수 없습니다. Label 이미지 제거는
      픽셀을 0으로 덮어쓰므로 복구가 불가능합니다.
    * 처음에는 반드시 '버려도 되는 복사본 폴더'에서
      시험해 보세요.
    * 슬라이드 본 이미지(병리 이미지)는 수정하지 않습니다.
    * 대상 파일을 ImageScope 등에서 열어 두면 쓰기가
      실패합니다. 먼저 닫아 주세요.

  [ 종료 방법 ]
    'SVS 메타데이터 비식별 도구' 창을 닫으면 이 창도 닫힙니다.
    (이 창만 먼저 닫으면 프로그램이 강제 종료됩니다)

  기록 파일: {log}
============================================================
"""

BANNER_EN = """\
============================================================
  SVS Metadata De-identification  (SVS_Deid)
============================================================
  This black window is the program's LOG WINDOW. It is normal.
  Everything you do is recorded here, so you can check later
  what was changed. Do not close it.

  [ How to use ]
    1. In the 'SVS Metadata De-identification' window that
       opened alongside, choose a folder and press [Scan]
    2. Pick what to change on the right
    3. [Preview] - shows the result, touches no file
    4. [Apply]   - writes, after a confirmation

  [ Warnings ]
    * [Apply] cannot be undone. Deleting the label image
      overwrites its pixels with zeros - unrecoverable.
    * Try it on a throw-away copy of a folder first.
    * The pathology image itself is never modified.
    * Writing fails while a file is open in ImageScope.
      Close it first.

  [ How to quit ]
    Close the 'SVS Metadata De-identification' window and
    this one closes with it.
    (Closing this one first kills the program.)

  Log file: {log}
============================================================
"""


def banner():
    return BANNER_EN if i18n.get_lang() == "en" else BANNER_KO

# Date presets: i18n key -> (strftime format or None, remove Date entirely?)
# The radio value is the KEY, not the label, so the choice survives a language switch.
DATE_CHOICES = [
    ("date_ym", "%Y-%m", False),
    ("date_ymd", "%Y-%m-%d", False),
    ("date_yymd", "%y-%m-%d", False),
    ("date_y", "%Y", False),
    ("date_drop", None, True),
    ("date_keep", None, False),
]

# Sizes below are in pixels at 100 % Windows scaling; App._px() scales them to the screen.
OPTIONS_W = 360           # minimum width of the options panel on the right
WIN_W, WIN_H = 1500, 950  # preferred window size when the screen has room
LOG_LINES = 12            # log pane height ...
LOG_LINES_COMPACT = 4     # ... shrinks to this before the spacing is tightened ...
LOG_LINES_MIN = 2         # ... and at most to this, so the options still fit on screen

# Run box colours - the box that actually does something has to stand out from the options
RUN_ACCENT = "#1565c0"    # border / title
RUN_BG = "#e8f1fc"        # box background
PREVIEW_BG, PREVIEW_HOVER = "#1565c0", "#0d47a1"
APPLY_BG, APPLY_HOVER = "#c62828", "#8e0000"     # red: this one writes to the files
BTN_DISABLED_BG = "#9e9e9e"


class App(tk.Tk):
    def __init__(self, folder):
        super().__init__()
        # Fonts follow Windows display scaling (150 % -> 1.5x) but pixel sizes do not, so every
        # fixed size goes through _px(), or text gets clipped on a high-DPI screen.
        self.scale = max(1.0, self.winfo_fpixels("1i") / 96.0)
        self.title(t("deid_title"))
        self.rows = {}            # path -> treeview item id
        self.files = []
        self.q = queue.Queue()
        self.busy = False
        self.rows_data = {}        # path -> (values, tag)  kept so a rebuild is instant
        self.log_lines = LOG_LINES
        self._setup_style()
        self._build_ui()
        self._fit_to_screen(first=True)
        self.after(100, self._poll)
        if folder and os.path.isdir(folder):
            self.folder_var.set(folder)
            self.after(200, self.scan)

    # ------------------------------------------------------------------ language
    def _change_language(self, label):
        code = i18n.code_for(label)
        if code == i18n.get_lang():
            return
        keep = {
            "folder": self.folder_var.get(),
            "date": self.date_var.get(),
            "rm_time": self.rm_time.get(), "rm_ids": self.rm_ids.get(),
            "rm_label": self.rm_label.get(), "rm_macro": self.rm_macro.get(),
            "extra": self.extra_var.get(),
            "backup": self.backup_var.get(), "sel_only": self.sel_only.get(),
            "log": self.log.get("1.0", "end").rstrip("\n"),
        }
        i18n.set_lang(code)
        for w in self.winfo_children():
            w.destroy()
        self.title(t("deid_title"))
        self._build_ui()
        self._fit_to_screen()                   # labels differ in length between languages
        self.folder_var.set(keep["folder"])
        self.date_var.set(keep["date"])
        self.rm_time.set(keep["rm_time"]); self.rm_ids.set(keep["rm_ids"])
        self.rm_label.set(keep["rm_label"]); self.rm_macro.set(keep["rm_macro"])
        self.extra_var.set(keep["extra"])
        self.backup_var.set(keep["backup"]); self.sel_only.set(keep["sel_only"])
        if keep["log"]:
            self.log.insert("end", keep["log"] + "\n")
            self.log.see("end")
        self.rows.clear()                       # rebuild the table from the cached rows
        for path in self.files:
            vals, tag = self.rows_data.get(path, (("...", "", "", "", "", ""), None))
            self.rows[path] = self.tree.insert("", "end", text=os.path.basename(path),
                                               values=self._shown_values(vals),
                                               tags=(tag,) if tag else ())
        self._update_sample()
        console("")
        console(f"language -> {code}")

    # ------------------------------------------------------------------ layout / screen size
    def _px(self, n):
        """Pixels at 100 % scaling -> pixels on this screen."""
        return int(round(n * self.scale))

    def _setup_style(self):
        style = ttk.Style(self)
        # Tk 8.6 keeps a fixed Treeview row height, which cuts off scaled-up text
        line = tkfont.nametofont("TkDefaultFont").metrics("linespace")
        style.configure("Treeview", rowheight=int(line * 1.4))
        style.configure("Run.TCheckbutton", background=RUN_BG)
        self.run_font = tkfont.nametofont("TkDefaultFont").copy()      # kept on self: a Font
        size = self.run_font.cget("size")                               # dies with its object
        self.run_font.configure(weight="bold", size=size + 1 if size > 0 else size - 1)

    def _run_button(self, parent, text, command, bg, hover):
        """Coloured, bold button - ttk buttons cannot be coloured with the native Windows theme."""
        b = tk.Button(parent, text=text, command=command, font=self.run_font,
                      bg=bg, fg="white", activebackground=hover, activeforeground="white",
                      disabledforeground="#eeeeee", relief=tk.FLAT, borderwidth=0,
                      cursor="hand2", padx=self._px(6), pady=self._px(6))
        b.normal_bg = bg
        b.bind("<Enter>", lambda e: b.cget("state") == tk.NORMAL and b.configure(bg=hover))
        b.bind("<Leave>", lambda e: b.cget("state") == tk.NORMAL and b.configure(bg=bg))
        return b

    def _set_apply_enabled(self, on):
        b = self.apply_btn
        b.configure(state=tk.NORMAL if on else tk.DISABLED,
                    bg=b.normal_bg if on else BTN_DISABLED_BG,
                    cursor="hand2" if on else "arrow")

    def _work_area(self):
        """(x, y, w, h) of the primary screen minus the taskbar, in the pixels Tk uses."""
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes
                r = wintypes.RECT()
                if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
                    return r.left, r.top, r.right - r.left, r.bottom - r.top
            except Exception:  # noqa
                pass
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight() - self._px(60)

    def _fit_to_screen(self, first=False):
        """Size the window so every control is visible, whatever the resolution and scaling.

        Sizes are measured from the built widgets, then clamped to the work area. On a short
        screen the log pane gives up lines, then the spacing tightens, then the log shrinks
        further; if the options still do not fit, they get a scrollbar (the Run box with
        Preview / Apply stays pinned below them) instead of being silently cut off.
        """
        ax, ay, aw, ah = self._work_area()
        frame_w, frame_h = self._px(16), self._px(40)      # borders and title bar
        max_w, max_h = aw - frame_w, ah - frame_h

        def too_tall():
            self.update_idletasks()
            self._sync_options()
            self.update_idletasks()
            return self.winfo_reqheight() > max_h

        def shrink_log(down_to):
            while self.log_lines > down_to and too_tall():
                self.log_lines -= 1
                self.log.configure(height=self.log_lines)

        self.log_lines = LOG_LINES
        self.log.configure(height=self.log_lines)
        shrink_log(LOG_LINES_COMPACT)
        if too_tall():
            for b in self.option_boxes:
                b.configure(padding=(self._px(6), self._px(1)))
                b.pack_configure(pady=self._px(1))
            self.run_box.pack_configure(pady=self._px(1))
            self.sample_label.pack_configure(pady=0)
            self.run_title.pack_forget()             # the coloured box says "run" well enough
            self.run_first_check.pack_configure(pady=(self._px(4), 0))
            self.run_btns.pack_configure(pady=(self._px(3), self._px(4)))
            for b in self.run_buttons:
                b.configure(pady=self._px(3))
            self.log_box.configure(padding=self._px(1))
            self.log_box.pack_configure(pady=self._px(1))
            self.top_bar.configure(padding=(self._px(6), self._px(2)))
            shrink_log(LOG_LINES_MIN)
        too_tall()
        req_h = self.winfo_reqheight()
        min_w = min(self.options_holder.winfo_reqwidth() + self._px(450), max_w)
        min_h = min(req_h, max_h)
        self.minsize(min_w, min_h)

        if first:
            w = min(max(min(self._px(WIN_W), int(aw * 0.9)), min_w), max_w)
            h = min(max(min(self._px(WIN_H), int(ah * 0.9)), req_h), max_h)
            x = ax + max(0, (aw - w - frame_w) // 2)
            y = ay + max(0, (ah - h - frame_h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        elif self.state() == "normal":
            w, h = self.winfo_width(), self.winfo_height()
            if w < min_w or h < min_h:
                self.geometry(f"{max(w, min_w)}x{max(h, min_h)}")

    def _build_options_panel(self, parent):
        """Right-hand options column, inside a canvas that scrolls only when it does not fit.

        Returns (inner, run_area): the options go in `inner`; `run_area` is pinned below the
        scrolling part, so the Run box (Preview / Apply) is always on screen.
        """
        holder = ttk.Frame(parent)
        holder.pack(side=tk.RIGHT, fill=tk.Y)
        self.options_holder = holder
        run_area = ttk.Frame(holder, padding=(self._px(8), 0))
        run_area.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_area = ttk.Frame(holder)
        scroll_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        bg = ttk.Style(self).lookup("TFrame", "background") or self.cget("background")
        canvas = tk.Canvas(scroll_area, highlightthickness=0, borderwidth=0, background=bg,
                           yscrollincrement=self._px(20))
        sb = ttk.Scrollbar(scroll_area, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.Y)
        inner = ttk.Frame(canvas, padding=(self._px(8), 0))
        ttk.Frame(inner, width=self._px(OPTIONS_W - 16), height=1).pack()   # minimum width
        canvas.create_window(0, 0, window=inner, anchor="nw")

        def sync(_=None):
            w, h = inner.winfo_reqwidth(), inner.winfo_reqheight()
            canvas.configure(width=w, height=h, scrollregion=(0, 0, w, h))

        def resized(e):
            need = inner.winfo_reqheight() > e.height + self._px(6)     # ignore the last box's margin
            if need and not sb.winfo_ismapped():
                sb.pack(side=tk.RIGHT, fill=tk.Y)
            elif not need and sb.winfo_ismapped():
                sb.pack_forget()
                canvas.yview_moveto(0)

        def wheel(e):
            try:
                w = str(self.winfo_containing(e.x_root, e.y_root))
            except (KeyError, tk.TclError):
                return
            area = str(scroll_area)
            if (w == area or w.startswith(area + ".")) and sb.winfo_ismapped():
                canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

        inner.bind("<Configure>", sync)
        canvas.bind("<Configure>", resized)
        self.bind_all("<MouseWheel>", wheel)
        self._sync_options = sync
        return inner, run_area

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        top = self.top_bar = ttk.Frame(self, padding=self._px(6))
        top.pack(fill=tk.X)
        ttk.Label(top, text=t("folder") + ":").pack(side=tk.LEFT)
        self.folder_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(top, text=t("browse"), command=self._pick).pack(side=tk.LEFT)
        ttk.Button(top, text=t("scan"), command=self.scan).pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="   " + t("language")).pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value=i18n.lang_label())
        lang_cb = ttk.Combobox(top, textvariable=self.lang_var, width=9, state="readonly",
                               values=[lb for lb, _ in i18n.LANGS])
        lang_cb.pack(side=tk.LEFT, padx=(4, 0))
        lang_cb.bind("<<ComboboxSelected>>", lambda e: self._change_language(self.lang_var.get()))

        # ---------------- status bar + log: packed before the middle part, so when the window is
        # short it is the middle (table / scrollable options) that gives way, not these
        self.status = tk.StringVar(value=t("deid_start_hint"))
        ttk.Label(self, textvariable=self.status, anchor="w", padding=(8, 3)).pack(side=tk.BOTTOM, fill=tk.X)
        bottom = self.log_box = ttk.LabelFrame(self, text=t("log"), padding=self._px(4))
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=self._px(4))
        self.log = tk.Text(bottom, height=self.log_lines, wrap="none", bg="#1e1e1e", fg="#dcdcdc",
                           font=("Consolas", 9))
        lsb = ttk.Scrollbar(bottom, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=lsb.set)
        lsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log.tag_configure("err", foreground="#ff8080")
        self.log.tag_configure("hdr", foreground="#7ec8ff")

        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=6)

        # ---------------- options (packed first so the table, not the options, gets squeezed) ----
        right, run_area = self._build_options_panel(main)

        # ---------------- file table ----------------
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cols = ("date", "time", "scanner", "label", "pages", "status")
        self.tree = ttk.Treeview(left, columns=cols, show="tree headings", selectmode="extended",
                                 height=5)
        self.tree.heading("#0", text=t("col_file"))
        self.tree.column("#0", width=self._px(300), anchor="w")
        for c, head, w in (("date", "Date", 90), ("time", "Time", 80),
                           ("scanner", "ScanScope ID", 100), ("label", t("col_label"), 60),
                           ("pages", t("col_pages"), 55), ("status", t("col_result"), 220)):
            self.tree.heading(c, text=head)
            self.tree.column(c, width=self._px(w), anchor="w")
        vsb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.tag_configure("err", foreground="#c00000")
        self.tree.tag_configure("done", foreground="#006000")

        box = ttk.LabelFrame(right, text=t("box_date"), padding=self._px(6))
        box.pack(fill=tk.X, pady=self._px(4))
        self.date_var = tk.StringVar(value=DATE_CHOICES[0][0])
        for key, _, _ in DATE_CHOICES:
            ttk.Radiobutton(box, text=t(key), value=key, variable=self.date_var).pack(anchor="w")
        self.sample_var = tk.StringVar(value="")
        self.sample_label = ttk.Label(box, textvariable=self.sample_var, foreground="#0050a0")
        self.sample_label.pack(anchor="w", pady=(4, 0))
        self.date_var.trace_add("write", lambda *a: self._update_sample())

        box2 = ttk.LabelFrame(right, text=t("box_remove"), padding=self._px(6))
        box2.pack(fill=tk.X, pady=self._px(4))
        self.rm_time = tk.BooleanVar(value=True)
        self.rm_ids = tk.BooleanVar(value=True)
        self.rm_label = tk.BooleanVar(value=True)
        self.rm_macro = tk.BooleanVar(value=True)   # the macro photo often shows the label too
        ttk.Checkbutton(box2, text=t("rm_time"), variable=self.rm_time).pack(anchor="w")
        ttk.Checkbutton(box2, text=t("rm_ids"), variable=self.rm_ids).pack(anchor="w")
        ttk.Checkbutton(box2, text=t("rm_label"), variable=self.rm_label).pack(anchor="w")
        ttk.Checkbutton(box2, text=t("rm_macro"), variable=self.rm_macro).pack(anchor="w")

        box3 = ttk.LabelFrame(right, text=t("box_extra"), padding=self._px(6))
        box3.pack(fill=tk.X, pady=self._px(4))
        self.extra_var = tk.StringVar()
        ttk.Entry(box3, textvariable=self.extra_var).pack(fill=tk.X)

        # ---------------- Run box: coloured so it stands out from the option boxes above
        pad = self._px(8)
        run = self.run_box = tk.Frame(run_area, bg=RUN_BG, highlightthickness=self._px(2),
                                      highlightbackground=RUN_ACCENT, highlightcolor=RUN_ACCENT)
        run.pack(fill=tk.X, pady=self._px(4))
        self.run_title = tk.Label(run, text="▶ " + t("box_run"), font=self.run_font,
                                  fg=RUN_ACCENT, bg=RUN_BG)
        self.run_title.pack(anchor="w", padx=pad, pady=(self._px(6), self._px(2)))
        self.backup_var = tk.BooleanVar(value=False)
        self.run_first_check = ttk.Checkbutton(run, text=t("backup"), variable=self.backup_var,
                                               style="Run.TCheckbutton")
        self.run_first_check.pack(anchor="w", padx=pad)
        self.sel_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(run, text=t("sel_only"), variable=self.sel_only,
                        style="Run.TCheckbutton").pack(anchor="w", padx=pad)
        btns = self.run_btns = tk.Frame(run, bg=RUN_BG)   # side by side: one row less on short screens
        btns.pack(fill=tk.X, padx=pad, pady=(self._px(6), pad))
        btns.columnconfigure((0, 1), weight=1, uniform="run")
        preview_btn = self._run_button(btns, t("preview_btn"), lambda: self.run(False),
                                       PREVIEW_BG, PREVIEW_HOVER)
        preview_btn.grid(row=0, column=0, sticky="ew", padx=(0, self._px(3)))
        self.apply_btn = self._run_button(btns, t("apply_btn"), lambda: self.run(True),
                                          APPLY_BG, APPLY_HOVER)
        self.apply_btn.grid(row=0, column=1, sticky="ew", padx=(self._px(3), 0))
        self.run_buttons = (preview_btn, self.apply_btn)
        self._set_apply_enabled(not self.busy)

        self.option_boxes = (box, box2, box3)

        self.bind("<F5>", lambda e: self.scan())
        self._update_sample()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self.busy and not messagebox.askyesno(
                t("close_confirm_title"), t("deid_close_busy"), parent=self, icon="warning"):
            return
        console("")
        console("=" * 60)
        console(t("con_quit"))
        console(f"   {LOG_FILE}")
        self.destroy()

    def _pick(self):
        d = filedialog.askdirectory(parent=self, title=t("folder"),
                                    initialdir=self.folder_var.get() or os.getcwd())
        if d:
            self.folder_var.set(os.path.normpath(d))
            self.scan()

    def _date_choice(self):
        for key, fmt, drop in DATE_CHOICES:
            if key == self.date_var.get():
                return fmt, drop
        return None, False

    def _date_label(self):
        return t(self.date_var.get())

    def _update_sample(self):
        fmt, drop = self._date_choice()
        sample = "04/11/2023"
        if drop:
            self.sample_var.set(t("sample_drop", s=sample))
        elif fmt:
            dt, _ = svs_meta.parse_date(sample, svs_meta.DEFAULT_IN_FORMATS)
            self.sample_var.set(t("sample_fmt", s=sample, out=dt.strftime(fmt)))
        else:
            self.sample_var.set(t("sample_keep", s=sample))

    # ------------------------------------------------------------------ log
    def _log(self, text, tag=None):
        self.log.insert("end", text + "\n", tag or ())
        self.log.see("end")
        console(f"[{time.strftime('%H:%M:%S')}] {text}")

    @staticmethod
    def _shown_values(values):
        """Translate the boolean Label column right before it is displayed."""
        v = list(values)
        if len(v) > 3 and isinstance(v[3], bool):
            v[3] = t("yes_have") if v[3] else t("none")
        return v

    def _poll(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    text, tag = payload
                    self._log(text, tag)
                elif kind == "row":
                    path, values, tag = payload
                    self.rows_data[path] = (values, tag)
                    item = self.rows.get(path)
                    if item:
                        self.tree.item(item, values=self._shown_values(values),
                                       tags=(tag,) if tag else ())
                elif kind == "rowstatus":
                    path, text = payload
                    item = self.rows.get(path)
                    if item:
                        vals = list(self.tree.item(item, "values"))
                        while len(vals) < 6:
                            vals.append("")
                        vals[5] = text
                        self.tree.item(item, values=vals)
                elif kind == "status":
                    self.status.set(payload)
                elif kind == "done":
                    self.busy = False
                    self._set_apply_enabled(True)
        except queue.Empty:
            pass
        except tk.TclError:
            return
        self.after(60, self._poll)

    # ------------------------------------------------------------------ scan
    def scan(self):
        folder = self.folder_var.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror(t("error"), t("deid_no_folder", path=folder), parent=self)
            return
        if self.busy:
            return
        self.tree.delete(*self.tree.get_children())
        self.rows.clear()
        self.log.delete("1.0", "end")
        self.files = svs_meta.iter_files(folder)
        for path in self.files:
            item = self.tree.insert("", "end", text=os.path.basename(path),
                                    values=("...", "", "", "", "", ""))
            self.rows[path] = item
        self.rows_data.clear()
        self._log(t("deid_scan_head", path=folder, n=len(self.files)), "hdr")
        self.busy = True
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        n_label = 0
        for path in self.files:
            try:
                _, _, entries = svs_meta.read_descriptions(path)
                if not entries:
                    raise ValueError(t("deid_no_desc"))
                if not svs_meta.is_aperio(entries):
                    raise ValueError(svs_meta.NOT_APERIO)
                _, items = svs_meta.split_desc(entries[0].value)
                kv = {k.lower(): v for k, v, _ in items if k}
                _, _, _, kinds = svs_meta.classify_pages(path)
                has_label = "label" in kinds.values()
                n_label += bool(has_label)
                self.q.put(("row", (path, (kv.get("date", "-"), kv.get("time", "-"),
                                           kv.get("scanscope id", "-"),
                                           bool(has_label),          # 언어 전환 시 다시 번역
                                           len(kinds), ""), None)))
            except Exception as e:  # noqa
                self.q.put(("row", (path, ("ERROR", "", "", "", "", str(e)), "err")))
                self.q.put(("log", (f"ERROR  {os.path.basename(path)}: {e}", "err")))
        self.q.put(("status", t("deid_scan_status", n=len(self.files), label=n_label)))
        self.q.put(("log", (t("deid_scan_done", n=len(self.files), label=n_label), "hdr")))
        self.q.put(("done", None))

    # ------------------------------------------------------------------ run
    def _targets(self):
        if self.sel_only.get():
            sel = set(self.tree.selection())
            return [p for p in self.files if self.rows.get(p) in sel]
        return list(self.files)

    def run(self, apply):
        if self.busy:
            return
        targets = self._targets()
        if not targets:
            messagebox.showinfo(t("deid_notice"), t("deid_no_files"), parent=self)
            return
        fmt, drop = self._date_choice()
        removes = []
        if drop:
            removes.append("Date")
        if self.rm_time.get():
            removes += svs_meta.DEID_REMOVE_TIME
        if self.rm_ids.get():
            removes += svs_meta.DEID_REMOVE_IDS
        removes += [r.strip() for r in self.extra_var.get().split(",") if r.strip()]
        rm_label, rm_macro = self.rm_label.get(), self.rm_macro.get()
        if not removes and not fmt and not rm_label and not rm_macro:
            messagebox.showinfo(t("deid_notice"), t("deid_pick_items"), parent=self)
            return

        if apply:
            lines = [t("deid_confirm_head", n=len(targets))]
            lines.append(t("deid_confirm_date", v=self._date_label()))
            if removes:
                lines.append(t("deid_confirm_remove", v=", ".join(removes)))
            if rm_label:
                lines.append(t("deid_confirm_label"))
            if rm_macro:
                lines.append(t("deid_confirm_macro"))
            lines.append(t("deid_confirm_backup",
                           v=t("deid_backup_on") if self.backup_var.get() else t("deid_backup_off")))
            if not messagebox.askyesno(t("deid_confirm_title"), "\n".join(lines),
                                       parent=self, icon="warning"):
                return

        self.busy = True
        self._set_apply_enabled(False)
        self.log.delete("1.0", "end")
        mode = t("deid_mode_apply") if apply else t("deid_mode_preview")
        self._log(t("deid_run_head", mode=mode, n=len(targets)), "hdr")
        self._log(t("deid_opt_date", v=self._date_label()))
        self._log(t("deid_opt_remove", v=", ".join(removes) if removes else t("deid_none")))
        self._log(t("deid_opt_images",
                    label=t("deid_removed") if rm_label else t("deid_kept"),
                    macro=t("deid_removed") if rm_macro else t("deid_kept")))
        self._log(t("deid_opt_backup",
                    v=t("deid_backup_on") if self.backup_var.get() else t("deid_backup_off")))
        threading.Thread(target=self._run_worker,
                         args=(targets, removes, fmt, rm_label, rm_macro, apply), daemon=True).start()

    def _run_worker(self, targets, removes, fmt, rm_label, rm_macro, apply):
        changed = 0
        failed = 0
        for path in targets:
            notes_out = []

            def out(line, _n=notes_out):
                _n.append(line)
                self.q.put(("log", (line, "err" if "ERROR" in line or "FAILED" in line else None)))

            try:
                ok, notes = svs_meta.plan_and_apply(
                    path, removes, [], fmt, svs_meta.DEFAULT_IN_FORMATS,
                    remove_label=rm_label, remove_macro=rm_macro,
                    backup=self.backup_var.get(), apply=apply, out=out)
            except Exception as e:  # noqa
                self.q.put(("log", (f"ERROR {os.path.basename(path)}: {e}", "err")))
                self.q.put(("row", (path, ("ERROR", "", "", "", "", str(e)), "err")))
                failed += 1
                continue
            if ok:
                changed += 1
            if apply and ok:
                try:
                    _, _, entries = svs_meta.read_descriptions(path)
                    _, items = svs_meta.split_desc(entries[0].value)
                    kv = {k.lower(): v for k, v, _ in items if k}
                    _, _, _, kinds = svs_meta.classify_pages(path)
                    self.q.put(("row", (path, (kv.get("date", "-"), kv.get("time", "-"),
                                               kv.get("scanscope id", "-"),
                                               "label" in kinds.values(),
                                               len(kinds), t("deid_complete")), "done")))
                except Exception as e:  # noqa
                    self.q.put(("row", (path, ("?", "", "", "", "",
                                               t("deid_recheck_fail", e=e)), "err")))
            elif not apply:
                summary = "; ".join(n for n in notes if not n.startswith("note:"))[:120]
                self.q.put(("rowstatus", (path, summary or t("deid_row_nochange"))))
        msg = (t("deid_done", mode=t("deid_mode_apply_s") if apply else t("deid_mode_preview_s"), n=changed)
               + (t("deid_done_fail", n=failed) if failed else "")
               + ("" if apply else t("deid_done_dry")))
        self.q.put(("log", (msg, "hdr")))
        self.q.put(("status", msg))
        self.q.put(("done", None))


def setup_console():
    """Title the console window and widen it so long paths stay readable."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(
            "SVS_Deid - log window (do not close)" if i18n.get_lang() == "en"
            else "SVS_Deid - 기록 창 (닫지 마세요)")
    except Exception:  # noqa
        pass
    try:
        os.system("mode con: cols=100 lines=3000 >nul 2>&1")
    except Exception:  # noqa
        pass


def main():
    setup_console()
    console("")
    console(banner().format(log=LOG_FILE))
    console(t("con_start_time", v=time.strftime("%Y-%m-%d %H:%M:%S")))

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa - Windows 7 / 8.0
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:  # noqa
                pass
    folder = sys.argv[1] if len(sys.argv) > 1 else ""
    if folder:
        console(t("con_start_folder", v=folder))
    else:
        console(t("con_no_folder"))
    console("")
    try:
        App(folder).mainloop()
    except Exception:  # noqa - keep the traceback readable in the console
        import traceback
        console("")
        console(t("con_unexpected"))
        console(traceback.format_exc())
        console(t("con_report"))
        try:
            input(t("con_press_enter"))
        except EOFError:
            pass
        raise


if __name__ == "__main__":
    main()
