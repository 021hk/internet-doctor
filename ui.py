# -*- coding: utf-8 -*-
"""
Internet Doctor - GUI shell & dashboard (CustomTkinter dark theme, bilingual FA/EN).
دکتر اینترنت - پوسته گرافیکی و داشبورد (تم تیره، دوزبانه)
"""
import datetime
import math
import os
import queue
import subprocess
import webbrowser

import customtkinter as ctk

import engine.fixes as fixengine
from ui_pages import build_kb_tab, build_history_tab, build_settings_tab, refresh_history

BG = "#0B0F1A"; PANEL = "#121826"; PANEL2 = "#182136"; DEEP = "#0D1322"; BORDER = "#26324D"
TXT = "#E6EDF6"; MUT = "#8CA0BF"
GREEN = "#34D399"; RED = "#F87171"; AMBER = "#FBBF24"; BLUE = "#60A5FA"; TEAL = "#2DD4BF"

STATE_META = {
    "online": ("آنلاین", "Online", GREEN),
    "dns": ("مشکل DNS", "DNS problem", AMBER),
    "captive": ("نیاز به لاگین", "Captive portal", AMBER),
    "offline": ("قطع", "Offline", RED),
    "adapter_down": ("کارت شبکه خاموش", "Adapter down", RED),
    "unknown": ("نامشخص", "Unknown", MUT),
}
LEVEL_COLOR = {"ok": GREEN, "fail": RED, "warn": AMBER, "info": BLUE}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class InternetDoctorApp(ctk.CTk):
    def __init__(self, ctrl):
        super().__init__()
        self.ctrl = ctrl
        self._busy = False
        self._phase = 0.0
        self.title("Internet Doctor | دکتر اینترنت")
        self.geometry("1000x700")
        self.minsize(900, 620)
        self.configure(fg_color=BG)
        self._build_header()
        self._build_action_bar()
        self._build_tabs()
        self._build_footer()
        self.after(150, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def f(self, size=13, bold=False):
        return ctk.CTkFont(family="Segoe UI", size=size,
                           weight="bold" if bold else "normal")

    # ---------- header
    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=14)
        h.pack(fill="x", padx=14, pady=(12, 6))
        left = ctk.CTkFrame(h, fg_color="transparent")
        left.pack(side="left", padx=18, pady=10)
        ctk.CTkLabel(left, text="دکتر اینترنت", font=self.f(22, True),
                     text_color=TXT, justify="left").pack(anchor="w")
        ctk.CTkLabel(left, text="Internet Doctor - automatic diagnosis & repair",
                     font=self.f(11), text_color=MUT, justify="left").pack(anchor="w")

        mid = ctk.CTkFrame(h, fg_color="transparent")
        mid.pack(side="left", expand=True)
        pill = ctk.CTkFrame(mid, fg_color=PANEL2, corner_radius=999,
                            border_width=1, border_color=BORDER)
        pill.pack(padx=8, pady=8)
        self.pill_label = ctk.CTkLabel(pill, text="●  در حال شروع... | Starting...",
                                       font=self.f(14, True), text_color=MUT)
        self.pill_label.pack(padx=20, pady=9)

        right = ctk.CTkFrame(h, fg_color="transparent")
        right.pack(side="right", padx=14)
        self.admin_badge = ctk.CTkLabel(right, text="", font=self.f(11, True),
                                        justify="right")
        self.admin_badge.pack(anchor="e", pady=(8, 2))
        self.admin_btn = ctk.CTkButton(
            right, text="اجرای مجدد به‌صورت مدیر | Run as Admin", width=210,
            height=26, font=self.f(11), command=self._elevate,
            fg_color="#2A3A57", hover_color="#354A6E")
        self.admin_btn.pack(anchor="e")
        self._refresh_admin_badge()

    def _refresh_admin_badge(self):
        if fixengine.is_admin():
            self.admin_badge.configure(text="دسترسی مدیر: فعال | Administrator: yes",
                                       text_color=GREEN)
            self.admin_btn.configure(state="disabled")
        else:
            self.admin_badge.configure(text="دسترسی مدیر: ندارد | Administrator: no",
                                       text_color=AMBER)
            self.admin_btn.configure(state="normal")

    def _elevate(self):
        ok = self.ctrl.relaunch_as_admin()
        if ok:
            self._really_quit()
        else:
            self.ctrl._log("warn", "اجرای مجدد با دسترسی مدیر انجام نشد",
                           "Elevation failed")

    # ---------- action bar
    def _build_action_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(2, 2))
        self.btn_toggle = ctk.CTkButton(
            bar, text="توقف مانیتورینگ | Pause", width=175, font=self.f(12, True),
            command=self.ctrl.toggle_monitoring,
            fg_color="#2A3A57", hover_color="#354A6E")
        self.btn_toggle.pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar, text="بررسی و رفع مشکل | Diagnose & Fix", width=200,
                      font=self.f(12, True), command=self.ctrl.diagnose_now,
                      fg_color=TEAL, hover_color="#14B8A6",
                      text_color="#06251F").pack(side="left", padx=8)
        ctk.CTkButton(bar, text="توقف اضطراری | Emergency Stop", width=175,
                      font=self.f(12, True), command=self.ctrl.emergency_stop,
                      fg_color="#7F1D1D", hover_color="#991B1B").pack(side="left", padx=8)
        ctk.CTkButton(bar, text="جستجو در وب | Web Search", width=155,
                      font=self.f(12), command=self.ctrl.run_web_search,
                      fg_color="#2A3A57", hover_color="#354A6E").pack(side="left", padx=8)
        ctk.CTkButton(bar, text="پوشه لاگ | Logs", width=110, font=self.f(12),
                      command=self.open_logs,
                      fg_color="#2A3A57", hover_color="#354A6E").pack(side="right", padx=8)

    # ---------- tabs
    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(
            self, fg_color=PANEL, corner_radius=14,
            segmented_button_selected_color=PANEL2,
            segmented_button_selected_hover_color=PANEL2,
            segmented_button_unselected_color=DEEP)
        try:
            self.tabs._segmented_button.configure(font=self.f(12, True))
        except Exception:
            pass
        self.tabs.pack(fill="both", expand=True, padx=14, pady=8)
        d = self.tabs.add("داشبورد | Dashboard")
        k = self.tabs.add("پایگاه دانش | Knowledge")
        hh = self.tabs.add("تاریخچه | History")
        s = self.tabs.add("تنظیمات | Settings")
        self._build_dashboard(d)
        build_kb_tab(self, k)
        build_history_tab(self, hh)
        build_settings_tab(self, s)

    def _build_dashboard(self, d):
        card = ctk.CTkFrame(d, fg_color=PANEL2, corner_radius=12)
        card.pack(fill="x", padx=10, pady=(10, 6))
        self.state_label = ctk.CTkLabel(card, text="در حال بررسی...",
                                        font=self.f(24, True), text_color=MUT)
        self.state_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))
        self.detail_label = ctk.CTkLabel(card, text="", font=self.f(12), text_color=MUT)
        self.detail_label.grid(row=0, column=1, sticky="e", padx=16, pady=(12, 2))
        self.net_label = ctk.CTkLabel(card, text="", font=self.f(12),
                                      text_color=TXT, anchor="w", justify="left")
        self.net_label.grid(row=1, column=0, columnspan=2, sticky="we",
                            padx=16, pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)

        act = ctk.CTkFrame(d, fg_color="transparent")
        act.pack(fill="x", padx=12, pady=2)
        self.activity_label = ctk.CTkLabel(act, text="آماده | Idle",
                                           font=self.f(12, True), text_color=TEAL,
                                           anchor="w")
        self.activity_label.pack(side="left", padx=(2, 10))
        self.progress = ctk.CTkProgressBar(act, progress_color=TEAL, height=8)
        self.progress.pack(side="left", fill="x", expand=True, padx=10)
        self.progress.set(0)

        self.result_box = ctk.CTkTextbox(d, height=190, fg_color=PANEL2,
                                         font=self.f(12), wrap="word")
        self.result_box.pack(fill="x", padx=10, pady=(8, 4))
        self.result_box.configure(state="disabled")
        self._tag(self.result_box, "good", GREEN)
        self._tag(self.result_box, "bad", RED)
        self._tag(self.result_box, "warn", AMBER)
        self._tag(self.result_box, "dim", MUT)

        self.web_frame = ctk.CTkFrame(d, fg_color="transparent")
        self.web_frame.pack(fill="x", padx=10, pady=(0, 2))

        self.log_box = ctk.CTkTextbox(d, fg_color=DEEP,
                                      font=ctk.CTkFont(family="Consolas", size=12),
                                      wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        for name, color in LEVEL_COLOR.items():
            self._tag(self.log_box, "lvl_%s" % name, color)

    @staticmethod
    def _tag(box, name, color):
        try:
            inner = getattr(box, "_textbox", box)
            inner.tag_config(name, foreground=color)
        except Exception:
            pass

    # ---------- footer
    def _build_footer(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(f, text="نسخه 1.1.0 - سازگار با ویندوز 10/11 | v1.1.0 - for Windows 10/11",
                     font=self.f(10), text_color=MUT).pack(side="left")
        ctk.CTkLabel(f, text="همه اقدامات در فایل لاگ ثبت می‌شود | every action is logged",
                     font=self.f(10), text_color=MUT).pack(side="right")

    # ---------- event queue
    def _poll(self):
        try:
            for _ in range(100):
                ev = self.ctrl.events.get_nowait()
                try:
                    self._handle(ev)
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(150, self._poll)

    def _handle(self, ev):
        t = ev.get("type")
        if t == "log":
            level = ev.get("level", "info")
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.log_box.insert("end", "%s  %s\n" % (ts, ev.get("fa", "")),
                                "lvl_%s" % level)
            self.log_box.insert("end", "        %s\n" % ev.get("en", ""),
                                "lvl_%s" % level)
            self.log_box.see("end")
        elif t == "status":
            self._on_status(ev["probe"])
        elif t == "activity":
            self.activity_label.configure(
                text="%s | %s" % (ev.get("fa", ""), ev.get("en", "")))
            self._set_busy(bool(ev.get("running")))
        elif t == "monitor_state":
            running = ev.get("running")
            self.btn_toggle.configure(
                text="توقف مانیتورینگ | Pause" if running else "شروع مانیتورینگ | Start")
        elif t == "diagnosis":
            self._on_diagnosis(ev)
        elif t == "fix_step":
            self._on_fix_step(ev)
        elif t == "final":
            self._on_final(ev["record"])
        elif t == "web":
            self._on_web(ev)
        elif t == "tray_show":
            self.deiconify()
            self.lift()
            self.focus_force()
        elif t == "app_exit":
            self._really_quit()

    def _on_status(self, p):
        meta = STATE_META.get(p.state, STATE_META["unknown"])
        self.state_label.configure(text="%s | %s" % (meta[0], meta[1]),
                                   text_color=meta[2])
        self.pill_label.configure(text="●  %s | %s" % (meta[0], meta[1]),
                                  text_color=meta[2])
        lat = "پینگ: - | ping: -"
        if p.ext_latency:
            lat = "پینگ: %dms | ping: %dms" % (int(p.ext_latency), int(p.ext_latency))
        self.detail_label.configure(
            text="آخرین بررسی: %s | last check: %s    %s" % (p.when, p.when, lat))
        self.net_label.configure(
            text="IF: %s    IP: %s\nGW: %s (%s)    DNS: %s" % (
                p.iface or "-", p.local_ip or "-", p.gateway or "-",
                "ok" if p.gw_ping_ok else "fail", p.dns_servers or "-"))

    # ---------- busy pulse
    def _set_busy(self, busy):
        if busy and not self._busy:
            self._busy = True
            self._pulse()
        elif not busy and self._busy:
            self._busy = False
            self.progress.set(0)

    def _pulse(self):
        if not self._busy:
            return
        self._phase += 0.09
        self.progress.set(0.5 + 0.45 * abs(math.sin(self._phase)))
        self.after(80, self._pulse)

    # ---------- result box helpers
    def _res_open(self):
        self.result_box.configure(state="normal")

    def _res_line(self, text, tag):
        self.result_box.insert("end", text + "\n", tag)

    def _res_close_see(self):
        self.result_box.configure(state="disabled")
        self.result_box.see("end")

    def _on_diagnosis(self, ev):
        self._res_open()
        self.result_box.delete("1.0", "end")
        self._res_line("نتیجه تشخیص | Diagnosis result:", "dim")
        findings = ev.get("findings", [])
        if not findings:
            self._res_line("مشکل مشخصی در سیستم پیدا نشد؛ تعمیرهای عمومی اجرا می‌شود.",
                           "warn")
            self._res_line("No specific local problem found; running generic repairs.",
                           "warn")
        for f in findings:
            self._res_line("• %s | %s" % (f.get("fa", ""), f.get("en", "")), "warn")
            if f.get("detail_fa"):
                self._res_line("  %s" % f["detail_fa"], "dim")
            if f.get("detail_en"):
                self._res_line("  %s" % f["detail_en"], "dim")
        if ev.get("modem_hint"):
            self._res_line("توصیه: مودم/روتر را خاموش کنید، 30 ثانیه صبر کنید و روشن کنید.",
                           "bad")
            self._res_line("Tip: power-cycle the modem/router (off, wait 30s, on).",
                           "bad")
        self._res_close_see()

    def _on_fix_step(self, ev):
        i, n = ev.get("i", 0), ev.get("n", 0)
        title = "%s | %s" % (ev.get("fa", ""), ev.get("en", ""))
        status = ev.get("status")
        self._res_open()
        if status == "start":
            self._res_line("[%d/%d] اجرا: %s" % (i, n, title), "dim")
        elif status == "fixed":
            self._res_line("[%d/%d] موفق - اتصال برقرار شد: %s" % (i, n, title), "good")
        elif status == "ran":
            self._res_line("[%d/%d] انجام شد (اتصال برنگشت): %s" % (i, n, title), "warn")
        elif status == "skip":
            self._res_line("[%d/%d] رد شد (دسترسی مدیر لازم است): %s" % (i, n, title), "warn")
        elif status == "reboot":
            self._res_line("[%d/%d] نیاز به ری‌استارت ویندوز: %s" % (i, n, title), "bad")
        self._res_close_see()

    def _on_final(self, rec):
        res = rec.get("result", "unresolved")
        color = {"fixed": "good", "needs_reboot": "warn",
                 "unresolved": "bad", "no_fix_needed": "dim"}.get(res, "dim")
        fa_map = {
            "fixed": "مشکل رفع شد",
            "needs_reboot": "برای تکمیل تعمیر ویندوز را ری‌استارت کنید",
            "unresolved": "مشکل حل نشد؛ راه‌حل‌های وب را ببینید",
            "no_fix_needed": "مشکلی نیاز به تعمیر نداشت",
        }
        en_map = {
            "fixed": "Problem fixed",
            "needs_reboot": "Restart Windows to finish the repair",
            "unresolved": "Not fixed yet; check the web suggestions",
            "no_fix_needed": "Nothing needed repair",
        }
        self._res_open()
        self._res_line("----------------------------------------", "dim")
        self._res_line("نتیجه نهایی: %s | Final: %s" % (fa_map[res], en_map[res]), color)
        self._res_close_see()
        refresh_history(self)

    def _on_web(self, ev):
        for w in self.web_frame.winfo_children():
            w.destroy()
        q = ev.get("query", "")
        ctk.CTkLabel(self.web_frame,
                     text="راه‌حل‌های پیدا شده از وب برای «%s» | Web results:" % q,
                     font=self.f(11), text_color=MUT,
                     justify="left").pack(anchor="w", pady=(2, 2))
        for i, r in enumerate(ev.get("results", [])[:5], 1):
            title = r.get("title", r.get("url", ""))[:90]
            b = ctk.CTkButton(self.web_frame, text="%d. %s" % (i, title),
                              anchor="w", height=26, font=self.f(11),
                              fg_color=PANEL2, hover_color=BORDER, text_color=BLUE,
                              command=lambda u=r.get("url"): webbrowser.open(u))
            b.pack(fill="x", pady=1)

    # ---------- misc
    def open_logs(self):
        try:
            from engine import store
            path = store.LOG_DIR
        except Exception:
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        try:
            if os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _on_close(self):
        """Window close: hide to tray (default) or really exit."""
        if bool(self.ctrl.settings.get("close_to_tray", True)) and \
                getattr(self.ctrl, "tray", None) is not None:
            self.withdraw()
            self.ctrl.tray.notify(
                "برنامه کنار ساعت به کار خود ادامه می‌دهد | "
                "Still running in the system tray")
            return
        self._really_quit()

    def _really_quit(self):
        try:
            self.ctrl.shutdown()
        finally:
            self.destroy()
