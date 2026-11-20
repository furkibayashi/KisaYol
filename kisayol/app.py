"""KısaYol arayüzü: kalıp düzenleyici, ayarlar, tepsi ve arama penceresi.

Kanca ve işçi iş parçacıkları Tk'ye asla doğrudan dokunmaz; arayüze yalnızca post(event) ile mesaj gönderir.
"""
from __future__ import annotations

import dataclasses
import os
import queue
import sys
import tkinter as tk
import traceback
import webbrowser
from datetime import datetime
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk

from . import APP_NAME, VERSION, themes, winutil
from .config import Config, config_dir
from .expander import Expander
from .hook import ExpansionWorker, KeyboardSink, KeyHook, altgr_char, hotkey_problem, pretty_combo
from .i18n import LANGUAGES, T, detect_language, set_language
from .matcher import Match, Matcher
from .search import filter_snippets
from .snippets import (DEFAULT_GROUP, Snippet, SnippetStore, find_conflict, is_symbol_trigger,
                       validate_trigger)
from .tray import Tray

REPO_URL = "https://github.com/furkibayashi/KisaYol"
PAGES = [("snippets", "✎"), ("settings", "⚙"), ("about", "ⓘ")]
VARIABLES = [("var_date", "{tarih}"), ("var_time", "{saat}"), ("var_clipboard", "{pano}"), ("var_cursor", "{imleç}")]
HOTKEY_ACTIONS = (("pause", "pause_hotkey"), ("search", "search_hotkey"))


class Seg(ctk.CTkFrame):
    """Tema renklerine uyumlu segment seçici (OtoTık'tan)."""

    def __init__(self, master, app, options, value, command=None, height=30):
        super().__init__(master, fg_color=app.p["card2"], corner_radius=9)
        self.app, self.command, self.value = app, command, value
        self.btns = {}
        for i, (val, label) in enumerate(options):
            b = ctk.CTkButton(self, text=label, height=height, width=20, corner_radius=7,
                              font=app.font(12, "bold"), command=lambda v=val: self.select(v, True))
            b.grid(row=0, column=i, padx=3, pady=3, sticky="ew")
            self.grid_columnconfigure(i, weight=1, uniform="seg")
            self.btns[val] = b
        self.select(value)

    def select(self, v, user=False):
        p = self.app.p
        self.value = v
        for val, b in self.btns.items():
            on = val == v
            b.configure(fg_color=p["accent"] if on else "transparent",
                        text_color=p["accent_text"] if on else p["text"],
                        hover_color=p["accent_hover"] if on else p["hover"])
        if user and self.command:
            self.command(v)


class NavItem(ctk.CTkFrame):
    """Yan menü öğesi (OtoTık'tan, sadeleştirildi)."""

    def __init__(self, master, app, icon, text, command):
        super().__init__(master, fg_color=app.p["side"], corner_radius=8)
        self.app, self.active, self.hover = app, False, False
        self.icon = ctk.CTkLabel(self, text=icon, width=26, font=app.font(15))
        self.icon.pack(side="left", padx=(12, 6), pady=6)
        self.text = ctk.CTkLabel(self, text=text, font=app.font(13, "bold"), anchor="w")
        self.text.pack(side="left", fill="x", expand=True, pady=6)
        for w in (self, self.icon, self.text):
            w.bind("<Button-1>", lambda e=None: command())
            w.bind("<Enter>", lambda e=None: self._set_hover(True))
            w.bind("<Leave>", lambda e=None: self._set_hover(False))
        self._paint()

    def _set_hover(self, v):
        if v != self.hover:
            self.hover = v
            self._paint()

    def set_active(self, v):
        self.active = v
        self._paint()

    def _paint(self):
        p = self.app.p
        bg = p["accent_soft"] if self.active else (p["hover"] if self.hover else p["side"])
        fg = p["accent"] if self.active else p["text"]
        self.configure(fg_color=bg)
        self.icon.configure(text_color=fg)
        self.text.configure(text_color=fg)


class App:
    def __init__(self, instance: winutil.SingleInstance, start_hidden: bool = False):
        self.instance = instance
        d = config_dir()
        self.cfg = Config(os.path.join(d, "settings.json"))
        a = self.cfg["app"]
        if not a["language"]:
            a["language"] = detect_language()
        set_language(a["language"])

        self.store = SnippetStore(os.path.join(d, "snippets.json"))
        self.store.load()
        self.store.save()

        self.q: "queue.Queue" = queue.Queue()
        self.post = self.q.put
        self.p = themes.apply(a["theme"], a["accent"])
        ctk.set_widget_scaling(a["ui_scale"])

        self.matcher = Matcher()
        self.matcher.set_snippets(self.store.active())
        self.hook = KeyHook(self.matcher, on_match=lambda m: self.worker.submit(m), post=self.post)
        self.hook.set_hotkeys(a["pause_hotkey"], a["search_hotkey"])
        self.hook.paused = bool(a["paused"])
        self.expander = Expander(KeyboardSink(), settings=a)
        self.worker = ExpansionWorker(self.hook, self.expander, on_done=lambda m: self.post(("expanded",)))
        self.store.on_change = self._snippets_changed

        self.root = ctk.CTk()
        self.root.title(APP_NAME)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self._set_icon()

        self.page = "snippets"
        self.selected_id = None
        self.draft = None
        self.group_filter = None
        self.query = ""
        self.capturing = None
        self._save_job = None
        self._osd_win = None
        self._search_win = None
        self._tray_hint_shown = False

        self.build()
        geo = a["geometry"]
        if geo:
            try:
                self.root.geometry(geo)
            except Exception:
                pass
        if start_hidden:
            self.root.withdraw()

        self.hook.start()
        self.tray = Tray(self.post, self.p["accent"], self.hook.paused)
        self.tray.start()
        self.root.after(100, self.tick)

    # ------------------------------------------------------------------ yardımcılar
    def font(self, size=13, weight="normal"):
        return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)

    def _set_icon(self):
        for base in (getattr(sys, "_MEIPASS", ""), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
            ico = os.path.join(base, "assets", "icon.ico")
            if base and os.path.exists(ico):
                try:
                    self.root.iconbitmap(ico)
                    self.root.after(250, lambda i=ico: self.root.iconbitmap(i))
                except Exception:
                    pass
                return

    def osd(self, text):
        """Ekranın üst ortasında kısa bildirim (pencere gizliyken de görünür). OtoTık'tan."""
        if not self.cfg["app"].get("osd", True):
            return
        try:
            if self._osd_win is not None:
                self._osd_win.destroy()
        except Exception:
            pass
        p = self.p
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        try:
            w.attributes("-alpha", 0.92)
        except Exception:
            pass
        w.configure(bg=p["accent"])
        tk.Label(w, text=text, bg=p["card"], fg=p["text"], font=("Segoe UI", 12, "bold"),
                 padx=18, pady=8).pack(padx=2, pady=2)
        w.update_idletasks()
        w.geometry(f"+{(w.winfo_screenwidth() - w.winfo_reqwidth()) // 2}+40")
        self._osd_win = w
        w.after(1400, lambda: w.destroy() if w.winfo_exists() else None)

    def card(self, parent, title=None, hint=None):
        p = self.p
        outer = ctk.CTkFrame(parent, fg_color=p["card"], corner_radius=12, border_width=1, border_color=p["border"])
        outer.pack(fill="x", padx=12, pady=7)
        if title:
            ctk.CTkLabel(outer, text=title, font=self.font(14, "bold"), anchor="w").pack(anchor="w", padx=16, pady=(12, 0))
        if hint:
            ctk.CTkLabel(outer, text=hint, font=self.font(11), text_color=p["sub"], anchor="w", justify="left",
                         wraplength=560).pack(anchor="w", padx=16)
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(8, 14))
        return inner

    def row(self, parent, pady=4):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", pady=pady)
        return r

    def lbl(self, parent, text, sub=False, size=13, bold=False, **kw):
        return ctk.CTkLabel(parent, text=text, font=self.font(size, "bold" if bold else "normal"),
                            text_color=self.p["sub"] if sub else self.p["text"], **kw)

    def button(self, parent, text, command, primary=False, danger=False, width=120, **kw):
        p = self.p
        if primary:
            colors = dict(fg_color=p["accent"], hover_color=p["accent_hover"], text_color=p["accent_text"])
        elif danger:
            colors = dict(fg_color="transparent", hover_color=p["err"], text_color=p["err"], border_width=1,
                          border_color=p["err"])
        else:
            colors = dict(fg_color=p["card2"], hover_color=p["hover"], text_color=p["text"])
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=30,
                             font=self.font(12, "bold"), **colors, **kw)

    # ------------------------------------------------------------------ inşa
    def build(self):
        for child in self.root.winfo_children():
            if not isinstance(child, tk.Toplevel):
                child.destroy()
        p = self.p
        self.root.configure(fg_color=p["bg"])
        self.root.minsize(860, 580)
        if not self.cfg["app"]["geometry"]:
            self.root.geometry("980x660")

        side = ctk.CTkFrame(self.root, fg_color=p["side"], corner_radius=0, width=210)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        logo = ctk.CTkFrame(side, fg_color="transparent")
        logo.pack(fill="x", padx=18, pady=(20, 18))
        ctk.CTkLabel(logo, text="⌁", text_color=p["accent"], font=self.font(26, "bold")).pack(side="left")
        ctk.CTkLabel(logo, text=" " + APP_NAME, font=self.font(22, "bold")).pack(side="left")

        self.nav = {}
        for key, icon in PAGES:
            item = NavItem(side, self, icon, T("nav_" + key), lambda k=key: self.show_page(k))
            item.pack(fill="x", padx=10, pady=2)
            self.nav[key] = item

        bottom = ctk.CTkFrame(side, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=10, pady=12)
        self.w_state = ctk.CTkLabel(bottom, text="", font=self.font(13, "bold"))
        self.w_state.pack(anchor="w", padx=4)
        self.w_stats = ctk.CTkLabel(bottom, text="", text_color=p["sub"], font=self.font(11))
        self.w_stats.pack(anchor="w", padx=4, pady=(0, 6))
        self.w_pause = ctk.CTkButton(bottom, text="", height=34, font=self.font(12, "bold"), command=self.toggle_pause)
        self.w_pause.pack(fill="x")
        ctk.CTkLabel(bottom, text=f"v{VERSION}", text_color=p["sub"], font=self.font(11)).pack(pady=(8, 0))

        self.content = ctk.CTkFrame(self.root, fg_color=p["bg"], corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)
        self.update_state_widgets()
        self.show_page(self.page)

    def rebuild(self):
        a = self.cfg["app"]
        self.p = themes.apply(a["theme"], a["accent"])
        ctk.set_widget_scaling(a["ui_scale"])
        set_language(a["language"])
        self.build()
        self.tray.refresh_language()

    def update_state_widgets(self):
        p = self.p
        paused = self.hook.paused
        self.w_state.configure(text="● " + (T("status_paused") if paused else T("status_active")),
                               text_color=p["warn"] if paused else p["ok"])
        self.w_stats.configure(text=T("snippet_count", n=len(self.store.active())) + " · " +
                               T("expansions", n=self.cfg["stats"]["expansions"]))
        hk = pretty_combo(self.cfg["app"]["pause_hotkey"])
        self.w_pause.configure(text=(T("btn_resume") if paused else T("btn_pause")) + f"  ({hk})",
                               fg_color=p["accent"] if paused else p["card"],
                               hover_color=p["accent_hover"] if paused else p["hover"],
                               text_color=p["accent_text"] if paused else p["text"])

    def show_page(self, key):
        p = self.p
        if key != "settings":
            self.cancel_capture()   # yakalama açık kalırsa başka bir uygulamada basılan tuş kısayol olur
        self.page = key
        for k, item in self.nav.items():
            item.set_active(k == key)
        for child in self.content.winfo_children():
            child.destroy()
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(header, text=T("nav_" + key), font=self.font(24, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(header, text=T("desc_" + key), text_color=p["sub"], font=self.font(12), anchor="w").pack(anchor="w")
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        getattr(self, "page_" + key)(body)

    # ------------------------------------------------------------------ Kalıplar sayfası
    def page_snippets(self, body):
        p = self.p
        body.grid_columnconfigure(0, weight=0, minsize=300)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(body, fg_color=p["card"], corner_radius=12, border_width=1, border_color=p["border"],
                            width=300)
        left.grid(row=0, column=0, sticky="nsw", padx=(12, 6), pady=6)
        left.grid_propagate(False)
        left.pack_propagate(False)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(10, 4))
        search = ctk.CTkEntry(top, placeholder_text=T("search_placeholder"))
        if self.query:
            search.insert(0, self.query)
        search.pack(side="left", fill="x", expand=True)
        self.button(top, T("btn_new"), self.new_snippet, primary=True, width=80).pack(side="left", padx=(6, 0))

        grow = ctk.CTkFrame(left, fg_color="transparent")
        grow.pack(fill="x", padx=10, pady=(0, 6))
        options = [T("group_all")] + list(self.store.groups)
        gmenu = ctk.CTkOptionMenu(grow, values=options, dynamic_resizing=False, width=200,
                                  command=lambda v: self._set_group_filter(None if v == T("group_all") else v))
        gmenu.set(self.group_filter if self.group_filter in self.store.groups else T("group_all"))
        gmenu.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(grow, text="⋯", width=34, height=28, fg_color=p["card2"], hover_color=p["hover"],
                      text_color=p["text"], command=lambda: self._group_menu(gbtn)).pack(side="left", padx=(6, 0))
        gbtn = grow.winfo_children()[-1]

        self.w_list = ctk.CTkScrollableFrame(left, fg_color="transparent", scrollbar_button_color=p["muted"],
                                             scrollbar_button_hover_color=p["accent"])
        self.w_list.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        def on_query(_=None):
            if search.get() != self.query:
                self.query = search.get()
                self.render_list()
        search.bind("<KeyRelease>", on_query)

        self.w_editor = ctk.CTkFrame(body, fg_color=p["card"], corner_radius=12, border_width=1,
                                     border_color=p["border"])
        self.w_editor.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=6)
        self.render_list()
        self.render_editor()

    def _visible_snippets(self):
        items = self.store.snippets
        if self.group_filter:
            items = [s for s in items if s.group == self.group_filter]
        return filter_snippets(items, self.query)

    def render_list(self):
        p = self.p
        try:
            if not self.w_list.winfo_exists():
                return
        except Exception:
            return
        for child in self.w_list.winfo_children():
            child.destroy()
        for s in self._visible_snippets():
            sel = s.id == self.selected_id
            preview = s.text.replace("\n", " ⏎ ")
            preview = preview[:34] + "…" if len(preview) > 34 else preview
            bg = p["accent_soft"] if sel else p["card"]
            item = ctk.CTkFrame(self.w_list, fg_color=bg, corner_radius=8)
            item.pack(fill="x", pady=1)
            head = ctk.CTkLabel(item, text=s.trigger, anchor="w", font=self.font(13, "bold"),
                                text_color=(p["accent"] if sel else p["text"]) if s.enabled else p["sub"])
            head.pack(fill="x", padx=10, pady=(6, 0))
            body = ctk.CTkLabel(item, text=preview, anchor="w", font=self.font(11), text_color=p["sub"])
            body.pack(fill="x", padx=10, pady=(0, 6))
            for w in (item, head, body):
                w.bind("<Button-1>", lambda e, i=s.id: self.select_snippet(i))
                if not sel:
                    w.bind("<Enter>", lambda e, f=item: f.configure(fg_color=p["hover"]))
                    w.bind("<Leave>", lambda e, f=item: f.configure(fg_color=p["card"]))

    def _current(self):
        if self.draft is not None:
            return self.draft
        for s in self.store.snippets:
            if s.id == self.selected_id:
                return s
        return None

    def select_snippet(self, sid):
        self.draft = None
        self.selected_id = sid
        self.render_list()
        self.render_editor()

    def new_snippet(self):
        group = self.group_filter or DEFAULT_GROUP
        self.draft = Snippet("", "", group=group)
        self.selected_id = None
        self.render_list()
        self.render_editor()
        try:
            self._w_trigger.focus_set()
        except Exception:
            pass

    def render_editor(self):
        p = self.p
        ed = self.w_editor
        for child in ed.winfo_children():
            child.destroy()
        s = self._current()
        if s is None:
            ctk.CTkLabel(ed, text=T("no_selection"), text_color=p["sub"], font=self.font(13)).pack(expand=True)
            return
        is_draft = self.draft is not None
        wrap = ctk.CTkFrame(ed, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=18, pady=14)
        if is_draft:
            self.lbl(wrap, T("new_snippet"), bold=True, size=15).pack(anchor="w", pady=(0, 6))

        r = self.row(wrap)
        self.lbl(r, T("field_trigger"), width=110, anchor="w").pack(side="left")
        tv = tk.StringVar(value=s.trigger)
        self._w_trigger = ctk.CTkEntry(r, textvariable=tv, width=200, font=self.font(14, "bold"))
        self._w_trigger.pack(side="left")
        info = ctk.CTkLabel(wrap, text="", font=self.font(11), anchor="w", justify="left", wraplength=340)
        info.pack(anchor="w", padx=(110, 0))

        r = self.row(wrap)
        self.lbl(r, T("field_group"), width=110, anchor="w").pack(side="left")
        gm = ctk.CTkOptionMenu(r, values=list(self.store.groups), width=200, dynamic_resizing=False,
                               command=lambda v: self._edit(group=v))
        gm.set(s.group)
        gm.pack(side="left")

        r = self.row(wrap)
        self.lbl(r, T("field_method"), width=110, anchor="w").pack(side="left")
        Seg(r, self, [("paste", T("method_paste")), ("type", T("method_type"))], s.method,
            lambda v: self._edit(method=v)).pack(side="left")

        r = self.row(wrap, pady=(10, 2))
        self.lbl(r, T("field_text"), anchor="w").pack(side="left")
        var_labels = [f"{T(k)}  {tok}" for k, tok in VARIABLES]
        vm = ctk.CTkOptionMenu(r, values=var_labels, width=190, dynamic_resizing=False,
                               fg_color=p["card2"], button_color=p["card2"], button_hover_color=p["hover"],
                               text_color=p["text"])
        vm.set(T("insert_variable"))
        vm.pack(side="right")
        text = ctk.CTkTextbox(wrap, height=200, font=ctk.CTkFont(family="Consolas", size=13), wrap="word",
                              border_width=1, border_color=p["border"])
        text.pack(fill="both", expand=True, pady=(2, 8))
        text.insert("1.0", s.text)

        def insert_var(label):
            tok = dict(zip(var_labels, [t for _, t in VARIABLES]))[label]
            text.insert("insert", tok)
            vm.set(T("insert_variable"))
            on_text()
            text.focus_set()
        vm.configure(command=insert_var)

        r = self.row(wrap)
        ev = tk.BooleanVar(value=s.enabled)
        ctk.CTkSwitch(r, text=T("enabled"), variable=ev, onvalue=True, offvalue=False,
                      command=lambda: self._edit(enabled=bool(ev.get())), font=self.font(13)).pack(side="left")
        if not is_draft:
            self.button(r, T("delete"), lambda: self.delete_snippet(s.id), danger=True).pack(side="right")

        def show_info(err):
            trig = tv.get()
            if err:
                msg = T(err)
                if err == "err_prefix_conflict":
                    cur_s = self._current()
                    other = find_conflict(trig, self.store.snippets, cur_s.id if cur_s else None)
                    if other:
                        msg += f"  → {other}"
                info.configure(text="⚠ " + msg, text_color=p["err"])
                self._w_trigger.configure(border_color=p["err"])
            else:
                hint = "trigger_hint_symbol" if is_symbol_trigger(trig) else "trigger_hint_bare"
                info.configure(text=T(hint), text_color=p["sub"])
                self._w_trigger.configure(border_color=p["border"])

        def on_trigger(*_):
            show_info(self._edit(trigger=tv.get()))

        def on_text(*_):
            self._edit(text=text.get("1.0", "end-1c"))

        tv.trace_add("write", on_trigger)
        text.bind("<KeyRelease>", on_text)
        text.bind("<<Paste>>", lambda e: self.root.after(10, on_text))
        cur = self._current()
        show_info(validate_trigger(cur.trigger, self.store.snippets, self_id=cur.id) if cur.trigger or not is_draft
                  else None)

    def _edit(self, **changes):
        """Seçili kalıba değişiklik uygular. Tetikleyici geçersizse hata anahtarını döner ve kaydetmez."""
        s = self._current()
        if s is None:
            return None
        new = dataclasses.replace(s, **changes)
        err = validate_trigger(new.trigger, self.store.snippets, self_id=new.id)
        if self.draft is not None:
            self.draft = new
            if err is None:
                self.draft = None
                self.selected_id = new.id
                self.store.add(new)
            return err
        if err is not None and "trigger" in changes:
            return err
        if err is not None:
            new = dataclasses.replace(new, trigger=s.trigger)
        if new != s:
            self.store.update(new)
        return err if "trigger" in changes else None

    def delete_snippet(self, sid):
        s = next((x for x in self.store.snippets if x.id == sid), None)
        if s and messagebox.askyesno(APP_NAME, T("confirm_delete", t=s.trigger), parent=self.root):
            self.store.remove(sid)
            self.selected_id = None
            self.render_list()
            self.render_editor()

    def _set_group_filter(self, g):
        self.group_filter = g
        self.render_list()

    def _group_menu(self, anchor):
        p = self.p
        m = tk.Menu(self.root, tearoff=0, bg=p["card"], fg=p["text"], activebackground=p["accent"],
                    activeforeground=p["accent_text"])
        m.add_command(label=T("group_new"), command=self.group_new)
        if self.group_filter and self.group_filter != DEFAULT_GROUP:
            m.add_command(label=T("group_rename"), command=self.group_rename)
            m.add_command(label=T("group_delete"), command=self.group_delete)
        m.tk_popup(anchor.winfo_rootx(), anchor.winfo_rooty() + anchor.winfo_height())

    def _ask_name(self, title, initial=""):
        d = ctk.CTkInputDialog(text=T("group_name_prompt"), title=title)
        name = (d.get_input() or "").strip()
        return name or None

    def group_new(self):
        name = self._ask_name(T("group_new"))
        if name and name not in self.store.groups:
            self.store.groups.append(name)
            self.group_filter = name
            self._snippets_changed()
            self.show_page("snippets")

    def group_rename(self):
        old = self.group_filter
        name = self._ask_name(T("group_rename"), old)
        if not name or name == old or name in self.store.groups:
            return
        self.store.groups[self.store.groups.index(old)] = name
        for s in self.store.snippets:
            if s.group == old:
                s.group = name
        self.group_filter = name
        self._snippets_changed()
        self.show_page("snippets")

    def group_delete(self):
        old = self.group_filter
        if not messagebox.askyesno(APP_NAME, T("confirm_group_delete", g=old, d=DEFAULT_GROUP), parent=self.root):
            return
        for s in self.store.snippets:
            if s.group == old:
                s.group = DEFAULT_GROUP
        self.store.groups.remove(old)
        self.group_filter = None
        self._snippets_changed()
        self.show_page("snippets")

    def _snippets_changed(self):
        self.matcher.set_snippets(self.store.active())
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(1000, self._save_snippets)
        self.render_list()
        self.update_state_widgets()

    def _save_snippets(self):
        self._save_job = None
        try:
            self.store.save()
        except Exception as ex:
            messagebox.showerror(APP_NAME, str(ex), parent=self.root)

    # ------------------------------------------------------------------ Ayarlar sayfası
    def page_settings(self, body):
        p = self.p
        a = self.cfg["app"]
        scroll = ctk.CTkScrollableFrame(body, fg_color="transparent", scrollbar_button_color=p["muted"],
                                        scrollbar_button_hover_color=p["accent"])
        scroll.pack(fill="both", expand=True)

        k = self.card(scroll, T("card_appearance"))
        r = self.row(k)
        self.lbl(r, T("language"), width=190, anchor="w").pack(side="left")
        lm = ctk.CTkOptionMenu(r, values=[n for _, n in LANGUAGES], width=200, dynamic_resizing=False,
                               command=lambda name: self._set("language", {n: c for c, n in LANGUAGES}[name], True))
        lm.set(dict(LANGUAGES).get(a["language"], "English"))
        lm.pack(side="left")
        self.lbl(k, T("theme"), anchor="w").pack(anchor="w", pady=(10, 4))
        grid = ctk.CTkFrame(k, fg_color="transparent")
        grid.pack(fill="x")
        for i, name in enumerate(themes.THEME_ORDER):
            tp = themes.palette(name)
            on = name == a["theme"]
            ctk.CTkButton(grid, text=("✓ " if on else "") + T("theme_" + name), height=42, fg_color=tp["card"],
                          hover_color=tp["card2"], text_color=tp["text"], border_width=3 if on else 2,
                          border_color=tp["accent"], corner_radius=10, font=self.font(12, "bold"),
                          command=lambda n=name: self._set("theme", n, True)).grid(
                row=i // 4, column=i % 4, padx=4, pady=4, sticky="ew")
            grid.grid_columnconfigure(i % 4, weight=1, uniform="th")
        r = self.row(k, pady=(10, 4))
        self.lbl(r, T("accent_color"), width=190, anchor="w").pack(side="left")
        ctk.CTkButton(r, text="", width=34, height=28, fg_color=p["accent"], hover_color=p["accent_hover"],
                      command=self.pick_accent).pack(side="left")
        self.button(r, "🎨 " + T("choose"), self.pick_accent, width=100).pack(side="left", padx=6)
        if a["accent"]:
            self.button(r, T("reset"), lambda: self._set("accent", "", True), width=80).pack(side="left")

        k = self.card(scroll, T("card_hotkeys"), T("hint_hotkeys"))
        for action, key in HOTKEY_ACTIONS:
            rr = ctk.CTkFrame(k, fg_color=p["card2"], corner_radius=8)
            rr.pack(fill="x", pady=2)
            self.lbl(rr, T("hk_" + action), anchor="w").pack(side="left", padx=12, pady=6)
            text = T("press_key") if self.capturing == action else pretty_combo(a[key])
            hb = ctk.CTkButton(rr, text=text, width=170, height=28, font=self.font(12, "bold"), fg_color=p["bg"],
                               text_color=p["warn"] if self.capturing == action else p["accent"],
                               hover_color=p["hover"], border_width=1, border_color=p["border"],
                               command=lambda ac=action: self.capture_hotkey(ac))
            hb.pack(side="right", padx=6, pady=4)

        k = self.card(scroll, T("card_expansion"))
        now = datetime.now()
        for key, label in (("date_fmt", "date_fmt"), ("time_fmt", "time_fmt")):
            r = self.row(k)
            self.lbl(r, T(label), width=190, anchor="w").pack(side="left")
            v = tk.StringVar(value=a[key])
            ctk.CTkEntry(r, textvariable=v, width=140).pack(side="left")
            prev = self.lbl(r, "", sub=True, size=12)
            prev.pack(side="left", padx=10)

            def upd(*_, key=key, v=v, prev=prev):
                fmt = v.get()
                try:
                    shown = now.strftime(fmt) if fmt.strip() else "—"
                except Exception:
                    shown = "—"
                prev.configure(text=T("preview", v=shown))
                if fmt.strip():
                    a[key] = fmt
                    self.cfg.save_later()
            v.trace_add("write", upd)
            upd()
        for key, label, lo, hi in (("type_delay_ms", "type_delay", 0, 200), ("restore_delay_ms", "restore_delay", 50, 3000)):
            r = self.row(k)
            self.lbl(r, T(label), width=190, anchor="w").pack(side="left")
            v = tk.StringVar(value=str(a[key]))
            ent = ctk.CTkEntry(r, textvariable=v, width=80, justify="center")
            ent.pack(side="left")

            def upd_num(*_, key=key, v=v, ent=ent, lo=lo, hi=hi):
                try:
                    n = int(v.get().strip())
                    if not lo <= n <= hi:
                        raise ValueError
                    a[key] = n
                    self.cfg.save_later()
                    ent.configure(border_color=p["border"])
                except ValueError:
                    ent.configure(border_color=p["err"])
            v.trace_add("write", upd_num)

        k = self.card(scroll, T("card_general"))
        r = self.row(k)
        ov = tk.BooleanVar(value=bool(a["osd"]))
        ctk.CTkSwitch(r, text=T("osd"), variable=ov, command=lambda: self._set("osd", bool(ov.get())),
                      font=self.font(13)).pack(side="left")
        r = self.row(k)
        av = tk.BooleanVar(value=winutil.autostart_enabled())
        sw = ctk.CTkSwitch(r, text=T("autostart"), variable=av, font=self.font(13),
                           command=lambda: self._set_autostart(bool(av.get()), av))
        sw.pack(side="left")
        if not winutil.autostart_supported():
            sw.configure(state="disabled")
            self.lbl(r, T("autostart_dev"), sub=True, size=11).pack(side="left", padx=8)
        r = self.row(k, pady=(10, 4))
        self.button(r, T("export_snippets"), self.export_snippets, width=180).pack(side="left")
        self.button(r, T("import_snippets"), self.import_snippets, width=180).pack(side="left", padx=8)
        if not winutil.is_admin():
            r = self.row(k, pady=(10, 0))
            self.button(r, "🛡 " + T("admin_restart"), self.run_as_admin, width=240).pack(side="left")
            self.lbl(r, T("admin_hint"), sub=True, size=11).pack(side="left", padx=8)

    def _set(self, key, value, rebuild=False):
        self.cfg["app"][key] = value
        self.cfg.save_later()
        if rebuild:
            self.rebuild()

    def _set_autostart(self, enabled, var):
        if not winutil.set_autostart(enabled):
            var.set(winutil.autostart_enabled())

    def pick_accent(self):
        c = colorchooser.askcolor(color=self.p["accent"], parent=self.root)
        if c and c[1]:
            self._set("accent", c[1], True)

    def capture_hotkey(self, action):
        if self.capturing:
            return
        self.capturing = action
        self.hook.start_capture(lambda combo: self.post(("captured", action, combo)))
        self.show_page("settings")

    def cancel_capture(self):
        if self.capturing:
            self.capturing = None
            self.hook.cancel_capture()

    def set_hotkey(self, action, combo):
        a = self.cfg["app"]
        key = dict(HOTKEY_ACTIONS)[action]
        if combo:
            problem = hotkey_problem(combo, altgr_char)
            if problem:
                parsed_key = combo.split("+")[-1]
                messagebox.showwarning(APP_NAME, T(problem, c=altgr_char(parsed_key)), parent=self.root)
                return
            for other, okey in HOTKEY_ACTIONS:
                if other != action and a[okey] == combo:
                    a[okey] = ""
            a[key] = combo
        self.cfg.save_later()
        self.hook.set_hotkeys(a["pause_hotkey"], a["search_hotkey"])
        self.update_state_widgets()

    def export_snippets(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", initialfile="kisayol-kaliplar.json",
                                            filetypes=[("JSON", "*.json")], parent=self.root)
        if path:
            self.store.export_to(path)

    def import_snippets(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], parent=self.root)
        if not path:
            return
        before = len(self.store.snippets)
        try:
            flagged = self.store.import_from(path)
        except Exception as ex:
            messagebox.showerror(APP_NAME, T("file_error", e=ex), parent=self.root)
            return
        msg = T("import_done", n=len(self.store.snippets) - before)
        if flagged:
            msg += "\n\n" + T("import_flagged", list=", ".join(flagged))
        messagebox.showinfo(APP_NAME, msg, parent=self.root)

    def run_as_admin(self):
        self.instance.release()
        if winutil.relaunch_as_admin():
            self.quit()
        else:
            self.instance.acquire()

    # ------------------------------------------------------------------ Hakkında
    def page_about(self, body):
        p = self.p
        k = self.card(body, f"{APP_NAME} {VERSION}")
        self.lbl(k, T("about_text"), anchor="w", justify="left", wraplength=560).pack(anchor="w")
        self.lbl(k, T("license_line") + " · © 2026 furkibayashi", sub=True, size=12).pack(anchor="w", pady=(6, 0))
        self.button(k, T("github"), lambda: webbrowser.open(REPO_URL), primary=True, width=200).pack(
            anchor="w", pady=(10, 0))
        k = self.card(body, "🔒 " + T("privacy_title"))
        self.lbl(k, T("privacy_text"), anchor="w", justify="left", wraplength=600).pack(anchor="w")

    # ------------------------------------------------------------------ duraklatma, tepsi, arama
    def toggle_pause(self):
        self.hook.paused = not self.hook.paused
        self.matcher.reset()
        self.cfg["app"]["paused"] = self.hook.paused
        self.cfg.save_later()
        self.tray.set_paused(self.hook.paused)
        self.update_state_widgets()
        self.osd(T("osd_paused") if self.hook.paused else T("osd_resumed"))

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        try:
            winutil.force_foreground(winutil.root_hwnd(self.root.winfo_id()))
        except Exception:
            pass

    def hide_to_tray(self):
        self.cancel_capture()
        self.cfg["app"]["geometry"] = self.root.geometry()
        self.cfg.save_later()
        self.root.withdraw()
        if not self._tray_hint_shown:
            self._tray_hint_shown = True
            self.osd(T("osd_tray"))

    def open_search(self):
        if self._search_win is not None:
            return
        p = self.p
        prev, prev_focus = winutil.capture_focus()
        w = tk.Toplevel(self.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=p["accent"])
        frame = tk.Frame(w, bg=p["card"])
        frame.pack(padx=2, pady=2)
        qv = tk.StringVar()
        entry = tk.Entry(frame, textvariable=qv, font=("Segoe UI", 13), bg=p["bg"], fg=p["text"],
                         insertbackground=p["text"], relief="flat", width=40)
        entry.pack(fill="x", padx=8, pady=(8, 4), ipady=4)
        lb = tk.Listbox(frame, font=("Segoe UI", 11), bg=p["card"], fg=p["text"], selectbackground=p["accent"],
                        selectforeground=p["accent_text"], relief="flat", highlightthickness=0, height=8,
                        activestyle="none")
        lb.pack(fill="both", padx=8, pady=(0, 8))
        results = []

        def refresh(*_):
            results[:] = filter_snippets(self.store.active(), qv.get())[:50]
            lb.delete(0, "end")
            for s in results:
                lb.insert("end", f"{s.trigger}   —   {s.text.replace(chr(10), ' ⏎ ')[:60]}")
            if not results:
                lb.insert("end", T("search_empty"))
            else:
                lb.selection_set(0)

        def move(delta):
            if not results:
                return "break"
            cur = (lb.curselection() or (0,))[0]
            nxt = max(0, min(len(results) - 1, cur + delta))
            lb.selection_clear(0, "end")
            lb.selection_set(nxt)
            lb.see(nxt)
            return "break"

        def close(_=None):
            if self._search_win is not None:
                self._search_win = None
                try:
                    w.destroy()
                except Exception:
                    pass

        def choose(_=None):
            sel = lb.curselection()
            if not results or not sel:
                return "break"
            snippet = results[sel[0]]
            # Pencereyi kapat, sonra hedefi öne al ve gerçekten öne gelene kadar dene
            # (Windows odağı bir an KısaYol'un ana penceresine verebilir).
            close()
            winutil.restore_focus(prev, prev_focus)
            self._submit_when_foreground(prev, prev_focus, Match(snippet, 0, ""))
            return "break"

        qv.trace_add("write", refresh)
        entry.bind("<Down>", lambda e: move(1))
        entry.bind("<Up>", lambda e: move(-1))
        entry.bind("<Return>", choose)
        entry.bind("<Escape>", close)
        lb.bind("<Double-Button-1>", choose)
        w.bind("<FocusOut>", lambda e: self.root.after(150, lambda: close() if self._search_win is w and
                                                        w.focus_displayof() is None else None))
        refresh()
        w.update_idletasks()
        px, py = w.winfo_pointerxy()
        area = winutil.work_area_at(px, py) or (0, 0, w.winfo_screenwidth(), w.winfo_screenheight() - 48)
        left, top, right, bottom = area
        x = max(left, min(px + 12, right - w.winfo_reqwidth() - 8))
        y = max(top, min(py + 12, bottom - w.winfo_reqheight() - 8))
        w.geometry(f"+{x}+{y}")
        self._search_win = w
        winutil.force_foreground(winutil.root_hwnd(w.winfo_id()))
        entry.focus_force()

    def _submit_when_foreground(self, hwnd, focus, match, tries=12):
        """Hedef pencere gerçekten öne gelince genişletir (en çok ~0.6 sn dener)."""
        if winutil.foreground_window() == hwnd:
            self.root.after(80, lambda: self.worker.submit(match))
            return
        if tries <= 0:
            return
        winutil.restore_focus(hwnd, focus)
        self.root.after(50, lambda: self._submit_when_foreground(hwnd, focus, match, tries - 1))

    # ------------------------------------------------------------------ olay döngüsü
    def tick(self):
        try:
            while True:
                ev = self.q.get_nowait()
                kind = ev[0]
                if kind == "hotkey":
                    if self.capturing:
                        pass   # yeni kısayol kaydedilirken eski kısayolun eylemi çalışmasın
                    elif ev[1] == "pause":
                        self.toggle_pause()
                    elif ev[1] == "search" and not self.hook.paused:
                        self.open_search()
                elif kind == "expanded":
                    self.cfg["stats"]["expansions"] += 1
                    self.cfg.save_later()
                    self.update_state_widgets()
                elif kind == "captured":
                    action, self.capturing = self.capturing, None
                    if ev[2]:
                        self.set_hotkey(ev[1], ev[2])
                    if action and self.page == "settings":
                        self.show_page("settings")
                elif kind == "tray":
                    if ev[1] == "open":
                        self.show_window()
                    elif ev[1] == "pause":
                        self.toggle_pause()
                    elif ev[1] == "quit":
                        self.quit()
                        return
        except queue.Empty:
            pass
        except Exception:
            traceback.print_exc()
        if self.instance.show_requested():
            self.show_window()
        self.root.after(100, self.tick)

    def quit(self):
        try:
            if self.root.state() != "withdrawn":
                self.cfg["app"]["geometry"] = self.root.geometry()
            if self._save_job:
                self.root.after_cancel(self._save_job)
            self.store.save()
            self.cfg.save()
            self.hook.close()
            self.worker.stop()
            self.tray.stop()
        finally:
            self.instance.release()
            self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    instance = winutil.SingleInstance()
    if not instance.acquire():
        if "--elevated" in sys.argv:
            import time
            for _ in range(24):
                time.sleep(0.25)
                if instance.acquire():
                    break
            else:
                return
        else:
            winutil.SingleInstance.signal_show()
            return
    App(instance, start_hidden="--tray" in sys.argv).run()
