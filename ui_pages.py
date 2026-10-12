# -*- coding: utf-8 -*-
"""
Internet Doctor - Knowledge / History / Settings tabs.
دکتر اینترنت - تب‌های پایگاه دانش، تاریخچه و تنظیمات
"""
import tkinter.messagebox as mb

import customtkinter as ctk

PANEL2 = "#182136"; BORDER = "#26324D"
TXT = "#E6EDF6"; MUT = "#8CA0BF"
GREEN = "#34D399"; RED = "#F87171"; AMBER = "#FBBF24"; BLUE = "#60A5FA"; TEAL = "#2DD4BF"

CAT_COLORS = {"DNS": BLUE, "IP": TEAL, "Wi-Fi": AMBER, "Modem": RED,
              "Proxy": "#C084FC", "Security": RED, "Adapter": GREEN}

RESULT_FA = {"fixed": ("رفع شد", GREEN), "unresolved": ("حل نشد", RED),
             "needs_reboot": ("نیاز به ری‌استارت", AMBER),
             "no_fix_needed": ("بدون نیاز", BLUE)}


def build_kb_tab(app, parent):
    scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=8, pady=8)
    ctk.CTkLabel(
        scroll,
        text=("این پایگاه دانش مجموعه راه‌حل‌های رایج قطعی اینترنت (برگرفته از مستندات مایکروسافت و انجمن‌های تخصصی) است "
              "که برنامه به‌صورت خودکار اجرا می‌کند.\n"
              "This knowledge base contains common fixes compiled from Microsoft docs and tech communities; "
              "the repair engine applies them automatically."),
        font=app.f(12), text_color=MUT, justify="left",
        wraplength=860).pack(anchor="w", pady=(4, 10))
    for e in app.ctrl.kb:
        card = ctk.CTkFrame(scroll, fg_color=PANEL2, corner_radius=12)
        card.pack(fill="x", pady=6)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(top, text="%s  |  %s" % (e["fa"]["title"], e["en"]["title"]),
                     font=app.f(14, True), text_color=TXT,
                     justify="left").pack(side="left")
        chip = ctk.CTkLabel(top, text=e["category"], font=app.f(10, True),
                            text_color="#0B0F1A",
                            fg_color=CAT_COLORS.get(e["category"], MUT),
                            corner_radius=999)
        chip.pack(side="right", padx=8, ipadx=10)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(6, 12))
        ctk.CTkLabel(body, text="علت: %s" % e["fa"]["cause"], font=app.f(12),
                     text_color=TXT, justify="left",
                     wraplength=840).pack(anchor="w")
        ctk.CTkLabel(body, text="Cause: %s" % e["en"]["cause"], font=app.f(11),
                     text_color=MUT, justify="left",
                     wraplength=840).pack(anchor="w", pady=(0, 4))
        steps_fa = "\n".join("• " + s for s in e["fa"]["steps"])
        ctk.CTkLabel(body, text=steps_fa, font=app.f(12), text_color=TEAL,
                     justify="left").pack(anchor="w")
        steps_en = "\n".join("• " + s for s in e["en"]["steps"])
        ctk.CTkLabel(body, text=steps_en, font=app.f(11), text_color=MUT,
                     justify="left").pack(anchor="w", pady=(0, 4))
        if e.get("commands"):
            cmds = "\n".join(e["commands"])
            ctk.CTkLabel(body, text=cmds,
                         font=ctk.CTkFont(family="Consolas", size=11),
                         text_color=AMBER, justify="left").pack(anchor="w", pady=(2, 2))
        badges = []
        if e.get("admin"):
            badges.append("نیاز به دسترسی مدیر | needs admin")
        if e.get("reboot"):
            badges.append("نیاز به ری‌استارت | needs reboot")
        if badges:
            ctk.CTkLabel(body, text=" - ".join(badges), font=app.f(10, True),
                         text_color=RED, justify="left").pack(anchor="w")


def build_history_tab(app, parent):
    bar = ctk.CTkFrame(parent, fg_color="transparent")
    bar.pack(fill="x", padx=10, pady=(10, 2))
    ctk.CTkButton(bar, text="به‌روزرسانی | Refresh", width=130,
                  command=lambda: refresh_history(app),
                  fg_color="#2A3A57", hover_color="#354A6E").pack(side="left", padx=4)
    ctk.CTkButton(bar, text="پوشه لاگ | Logs", width=120,
                  command=app.open_logs,
                  fg_color="#2A3A57", hover_color="#354A6E").pack(side="left", padx=4)
    ctk.CTkButton(bar, text="پاک‌کردن تاریخچه | Clear", width=150,
                  command=lambda: _clear_history(app),
                  fg_color="#7F1D1D", hover_color="#991B1B").pack(side="left", padx=4)
    app.hist_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    app.hist_scroll.pack(fill="both", expand=True, padx=8, pady=(4, 8))
    refresh_history(app)


def refresh_history(app):
    scroll = getattr(app, "hist_scroll", None)
    if scroll is None:
        return
    for w in scroll.winfo_children():
        w.destroy()
    records = app.ctrl.history.all()
    if not records:
        ctk.CTkLabel(scroll, text="هنوز اتفاقی ثبت نشده | Nothing recorded yet",
                     font=app.f(12), text_color=MUT).pack(pady=20)
        return
    for r in records:
        label, color = RESULT_FA.get(r.get("result", ""), ("؟", MUT))
        trig = "(خودکار | auto)" if r.get("trigger") == "auto" else "(دستی | manual)"
        card = ctk.CTkFrame(scroll, fg_color=PANEL2, corner_radius=10)
        card.pack(fill="x", pady=4)
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(top, text="%s   %s" % (r.get("time", ""), trig),
                     font=app.f(11), text_color=MUT).pack(side="left")
        ctk.CTkLabel(top, text=label, font=app.f(11, True),
                     text_color=color).pack(side="right")
        fa_f = "؛ ".join(f.get("fa", f.get("id", "")) for f in r.get("findings", [])) \
            or "مشکل مشخصی شناسایی نشد"
        ctk.CTkLabel(card, text="مشکل: %s" % fa_f, font=app.f(11),
                     text_color=TXT, justify="left",
                     wraplength=840).pack(anchor="w", padx=12)
        fixes = r.get("fixes", [])
        fx = "؛ ".join("%s [%s]" % (s.get("fa", s.get("id", "")),
                                    s.get("status", "")) for s in fixes) or "-"
        web = r.get("web_count", 0)
        extra = "   (%d نتیجه وب | web results)" % web if web else ""
        ctk.CTkLabel(card, text="اقدامات: %s%s" % (fx, extra), font=app.f(11),
                     text_color=MUT, justify="left",
                     wraplength=840).pack(anchor="w", padx=12, pady=(0, 8))


def _clear_history(app):
    if mb.askyesno("Internet Doctor",
                   "تاریخچه پاک شود؟ | Clear the history?"):
        app.ctrl.history.clear()
        refresh_history(app)


def build_settings_tab(app, parent):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=16, pady=12)
    s = app.ctrl.settings

    ctk.CTkLabel(frame, text="فاصله بررسی اتصال (ثانیه) | Check interval (seconds): 5 - 120",
                 font=app.f(13, True), text_color=TXT,
                 justify="left").pack(anchor="w", pady=(6, 0))
    app.int_slider = ctk.CTkSlider(frame, from_=5, to=120, number_of_steps=23,
                                   progress_color=TEAL)
    app.int_slider.set(int(s.get("interval_seconds", 12)))
    app.int_slider.pack(fill="x", pady=4)
    app.int_value = ctk.CTkLabel(frame, text="%d ثانیه | seconds" % int(s.get("interval_seconds", 12)),
                                 font=app.f(11), text_color=TEAL)
    app.int_value.pack(anchor="w")
    app.int_slider.configure(
        command=lambda v: app.int_value.configure(text="%d ثانیه | seconds" % int(float(v))))

    ctk.CTkLabel(frame, text="چند بررسی ناموفق پشت‌سرهم قبل از تعمیر خودکار | Failed checks before auto-repair: 1 - 10",
                 font=app.f(13, True), text_color=TXT,
                 justify="left").pack(anchor="w", pady=(14, 0))
    app.thr_slider = ctk.CTkSlider(frame, from_=1, to=10, number_of_steps=9,
                                   progress_color=TEAL)
    app.thr_slider.set(int(s.get("fail_threshold", 3)))
    app.thr_slider.pack(fill="x", pady=4)
    app.thr_value = ctk.CTkLabel(frame, text="%d بررسی | checks" % int(s.get("fail_threshold", 3)),
                                 font=app.f(11), text_color=TEAL)
    app.thr_value.pack(anchor="w")
    app.thr_slider.configure(
        command=lambda v: app.thr_value.configure(text="%d بررسی | checks" % int(float(v))))

    app.sw_autofix = ctk.CTkSwitch(frame, text="رفع خودکار مشکل | Auto-fix enabled",
                                   font=app.f(12), progress_color=TEAL)
    if s.get("autofix", True):
        app.sw_autofix.select()
    app.sw_autofix.pack(anchor="w", pady=(16, 2))

    app.sw_online = ctk.CTkSwitch(
        frame, text="جستجوی راه‌حل در وب وقتی حل نشد | Search the web when unresolved",
        font=app.f(12), progress_color=TEAL)
    if s.get("online_help", True):
        app.sw_online.select()
    app.sw_online.pack(anchor="w", pady=2)

    app.sw_tray = ctk.CTkSwitch(
        frame, text="آیکون کنار ساعت (System Tray) | System tray icon",
        font=app.f(12), progress_color=TEAL)
    if s.get("enable_tray", True):
        app.sw_tray.select()
    app.sw_tray.pack(anchor="w", pady=(10, 2))

    app.sw_close_tray = ctk.CTkSwitch(
        frame, text="بستن پنجره = کمینه‌سازی به کنار ساعت | Close button hides to tray",
        font=app.f(12), progress_color=TEAL)
    if s.get("close_to_tray", True):
        app.sw_close_tray.select()
    app.sw_close_tray.pack(anchor="w", pady=2)

    ctk.CTkLabel(frame, text="DNS جایگزین (وقتی DNS خراب است) | Fallback DNS:",
                 font=app.f(13, True), text_color=TXT,
                 justify="left").pack(anchor="w", pady=(16, 2))
    app.dns_menu = ctk.CTkOptionMenu(frame, values=["8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222"],
                                     fg_color=PANEL2, button_color="#2A3A57",
                                     button_hover_color="#354A6E")
    app.dns_menu.set(s.get("preferred_dns", "8.8.8.8"))
    app.dns_menu.pack(anchor="w", pady=2)

    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(anchor="w", pady=(20, 0))

    def save():
        s.set("interval_seconds", int(float(app.int_slider.get())))
        s.set("fail_threshold", int(float(app.thr_slider.get())))
        s.set("autofix", bool(app.sw_autofix.get()))
        s.set("online_help", bool(app.sw_online.get()))
        s.set("enable_tray", bool(app.sw_tray.get()))
        s.set("close_to_tray", bool(app.sw_close_tray.get()))
        s.set("preferred_dns", app.dns_menu.get())
        app.ctrl._log("ok", "تنظیمات ذخیره شد (تغییر تری با اجرای مجدد اعمال می‌شود)",
                      "Settings saved (tray change applies after restart)")

    ctk.CTkButton(row, text="ذخیره تنظیمات | Save", command=save,
                  fg_color=TEAL, hover_color="#14B8A6", text_color="#06251F",
                  font=app.f(12, True)).pack(side="left", padx=(0, 8))
    ctk.CTkButton(row, text="بازگرداندن DNS خودکار (DHCP) | Restore auto DNS",
                  command=lambda: app.ctrl.restore_dns(),
                  fg_color="#2A3A57", hover_color="#354A6E").pack(side="left", padx=8)

    ctk.CTkLabel(frame,
                 text=("نکته: برنامه برای اجرای بعضی تعمیرها (مثل تغییر DNS و ریست Winsock) به دسترسی مدیر نیاز دارد.\n"
                       "Note: some repairs (DNS change, Winsock reset) require administrator rights."),
                 font=app.f(11), text_color=MUT, justify="left",
                 wraplength=760).pack(anchor="w", pady=(18, 0))
