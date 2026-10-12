# -*- coding: utf-8 -*-
"""
Internet Doctor | دکتر اینترنت
Automatic internet-outage diagnosis & repair app for Windows 10/11.
برنامه تشخیص و رفع خودکار قطعی اینترنت برای ویندوز 10/11

Usage:
    python main.py              GUI (default, with system tray)
    python main.py --no-tray    GUI without the system-tray icon
    python main.py --selftest   headless engine self-test
"""
import os
import queue
import sys
import threading
import time

if getattr(sys, "frozen", False):
    # PyInstaller EXE: resources live in the temp dir (sys._MEIPASS) which
    # PyInstaller already puts on sys.path; keep cwd user-friendly.
    BASE = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    os.chdir(os.path.expanduser("~"))
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
    os.chdir(BASE)
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from engine import store, monitor, diagnostics, fixes, knowledge, online_help

VERSION = "1.2.0"


class Controller:
    """Glue between the GUI and the engine: monitoring loop + repair pipeline."""

    def __init__(self):
        self.events = queue.Queue()
        self.settings = store.Settings()
        self.history = store.History()
        self.log = store.setup_logger(self.events)
        self.kb = knowledge.load_kb()
        self.cancel = threading.Event()
        self.monitoring = False
        self.fail_count = 0
        self.last_probe = None
        self.last_search_query = "Windows 10 11 no internet connection fix troubleshoot"
        self.worker_thread = None
        self.worker_lock = threading.Lock()
        self.pending_recheck = False   # repair failed: re-check after first reconnect
        self.escalate = False          # next plan should include the deep stack resets
        self._log("info", "برنامه دکتر اینترنت نسخه %s اجرا شد" % VERSION,
                  "Internet Doctor v%s started" % VERSION)

    # ---------- helpers
    def emit(self, ev):
        self.events.put(ev)

    def _log(self, level, fa, en):
        store.log_call(self.log, level, fa, en)

    # ---------- monitoring
    def start_monitoring(self):
        if self.monitoring:
            return
        self.monitoring = True
        self.cancel.clear()
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        self.emit({"type": "monitor_state", "running": True})
        self._log("ok", "مانیتورینگ اینترنت شروع شد", "Internet monitoring started")

    def pause_monitoring(self):
        self.monitoring = False
        self.emit({"type": "monitor_state", "running": False})
        self._log("info", "مانیتورینگ متوقف شد", "Monitoring paused")

    def toggle_monitoring(self):
        if self.monitoring:
            self.pause_monitoring()
        else:
            self.start_monitoring()

    def emergency_stop(self):
        self.cancel.set()
        self._log("warn", "توقف اضطراری: هر عملیات در جریان متوقف می‌شود",
                  "Emergency stop: any running operation will be cancelled")

    def shutdown(self):
        self.monitoring = False
        self.cancel.set()

    def _monitor_loop(self):
        while self.monitoring:
            interval = max(5, int(self.settings.get("interval_seconds", 12)))
            threshold = max(1, int(self.settings.get("fail_threshold", 3)))
            try:
                probe = monitor.check_now()
            except Exception as exc:
                self._log("fail", "خطا در بررسی اتصال: %s" % exc,
                          "Probe error: %s" % exc)
                probe = None
            if probe is not None:
                self.last_probe = probe
                self.emit({"type": "status", "probe": probe})
                if probe.state == "online":
                    if self.fail_count:
                        self._log("ok", "اتصال اینترنت برگشت", "Internet is back")
                    self.fail_count = 0
                    if self.pending_recheck:
                        # first reconnect after a failed repair -> re-verify
                        if self._spawn_worker("recheck"):
                            self.pending_recheck = False
                            self.emit({"type": "recheck_pending", "on": False})
                else:
                    self.fail_count += 1
                    self._log("warn", "مشکل اتصال: %s (%d از %d)" % (
                        probe.summary_fa, self.fail_count, threshold),
                        "Connection problem: %s (%d/%d)" % (
                        probe.summary_en, self.fail_count, threshold))
                    if self.fail_count >= threshold:
                        self._spawn_worker("auto")
                        self.fail_count = 0
            end = time.time() + interval
            while time.time() < end and self.monitoring:
                time.sleep(0.2)

    # ---------- repair pipeline
    def diagnose_now(self):
        self.cancel.clear()
        self._spawn_worker("manual")

    def _spawn_worker(self, trigger):
        with self.worker_lock:
            if self.worker_thread and self.worker_thread.is_alive():
                self._log("warn", "یک عملیات بررسی/تعمیر هم‌اکنون در جریان است",
                          "A diagnose/repair run is already in progress")
                return False
            self.worker_thread = threading.Thread(
                target=self._fix_pipeline, args=(trigger,), daemon=True)
            self.worker_thread.start()
            return True

    def _fix_pipeline(self, trigger):
        if trigger == "recheck":
            self.emit({"type": "activity", "running": True,
                       "fa": "بررسی مجدد پس از وصل شدن اینترنت...",
                       "en": "Post-reconnect re-check..."})
            self._log("ok", "اینترنت وصل شد؛ طبق قول قبلی دوباره بررسی می‌کنم",
                      "Internet is back; running the promised re-check")
        else:
            self.emit({"type": "activity", "running": True,
                       "fa": "در حال بررسی دقیق مشکل...",
                       "en": "Running detailed diagnosis..."})
        probe = self.last_probe or monitor.check_now()
        diag = diagnostics.run_diagnosis(probe, self._log, self.cancel)
        self.last_search_query = diag.search_query
        self.emit({"type": "diagnosis", "findings": diag.findings,
                   "modem_hint": diag.modem_hint})

        plan = list(diag.plan)
        # Escalation: a previous attempt failed -> also include the heavy
        # stack resets (netsh winsock reset / netsh int ip reset).
        if self.escalate or trigger == "recheck":
            for extra in ("winsock_reset", "tcp_reset"):
                if extra not in plan:
                    plan.append(extra)
        # Skip the DNS change when the preferred DNS is already configured.
        if "set_dns" in plan:
            cur = (probe.dns_servers or "").lower()
            pref = str(self.settings.get("preferred_dns", "8.8.8.8")).lower()
            if pref in cur and "1.1.1.1" in cur:
                plan.remove("set_dns")

        summary = {"success": False, "steps": [], "needs_reboot": False}
        if plan and (trigger == "manual" or bool(self.settings.get("autofix", True))):
            if "set_dns" in plan and probe.iface:
                self.settings.set("last_dns_iface", probe.iface)
            ctx = {"iface": probe.iface,
                   "dns": self.settings.get("preferred_dns", "8.8.8.8")}

            def emit_step(ev):
                self.emit(ev)
                self.emit({"type": "activity", "running": True,
                           "fa": "در حال اجرای راه‌حل %d از %d: %s" % (
                               ev.get("i", 0), ev.get("n", 0), ev.get("fa", "")),
                           "en": "Applying fix %d of %d: %s" % (
                               ev.get("i", 0), ev.get("n", 0), ev.get("en", ""))})

            summary = fixes.run_fix_plan(plan, ctx, monitor.quick_check,
                                         self._log, self.cancel, emit_step)
        else:
            if trigger == "recheck":
                self._log("ok", "بررسی مجدد انجام شد؛ مشکل فعالی پیدا نشد",
                          "Re-check finished; no active problem found")
            else:
                self._log("info", "تعمیر خودکار غیرفعال است؛ فقط تشخیص انجام شد",
                          "Auto-fix disabled; diagnosis only")

        self.emit({"type": "activity", "running": True,
                   "fa": "بررسی نهایی اتصال...", "en": "Final connection check..."})
        final_probe = monitor.check_now()
        self.last_probe = final_probe
        self.emit({"type": "status", "probe": final_probe})

        if final_probe.state == "online":
            if summary["steps"]:
                result = "fixed"
            elif trigger == "recheck":
                result = "verified"      # healthy again, promised check done
            else:
                result = "no_fix_needed"
        elif summary["needs_reboot"]:
            result = "needs_reboot"
        else:
            result = "unresolved"

        web_results = []
        if result == "unresolved" and bool(self.settings.get("online_help", True)):
            if final_probe.dns_ok or final_probe.http_status == 204 or final_probe.ext_ping_ok:
                self._log("info", "جستجوی راه‌حل در وب...", "Searching the web for solutions...")
                web_results = online_help.search_web(diag.search_query)
            if not web_results:
                web_results = online_help.fallback_links(diag.search_query)
            if web_results:
                self.emit({"type": "web", "results": web_results,
                           "query": diag.search_query})

        record = self.history.add({
            "trigger": trigger,
            "state_before": probe.state,
            "state_after": final_probe.state,
            "findings": [{"id": f["id"], "fa": f["fa"], "en": f["en"]}
                         for f in diag.findings],
            "fixes": summary["steps"],
            "result": result,
            "web_count": len(web_results),
            "modem_hint": diag.modem_hint,
        })
        self.emit({"type": "final", "record": record})
        self.emit({"type": "activity", "running": False, "fa": "آماده", "en": "Idle"})

        if result == "fixed":
            self._log("ok", "مشکل با موفقیت رفع شد", "Problem fixed successfully")
        elif result == "verified":
            self._log("ok", "بررسی پس از وصل شدن: اتصال کاملاً سالم است",
                      "Post-reconnect check: connection is healthy")
        elif result == "needs_reboot":
            self._log("warn", "برای تکمیل تعمیر، ویندوز را ری‌استارت کنید",
                      "Please restart Windows to finish the repair")
        elif result == "unresolved":
            self._log("fail", "مشکل حل نشد؛ راه‌حل‌های وب و ری‌استارت مودم را امتحان کنید",
                      "Problem not fixed; try the web suggestions and reboot the modem")

        # Failed or needs a reboot?  Arm the post-reconnect re-check and
        # escalate the next repair plan (winsock / TCP-IP resets included).
        if result in ("unresolved", "needs_reboot"):
            self.pending_recheck = True
            self.escalate = True
            self.emit({"type": "recheck_pending", "on": True})
            self._log("info",
                      "به‌محض اولین وصل شدن اینترنت، دوباره بررسی و در صورت نیاز تعمیر می‌شود",
                      "Will re-check and repair again right after the first reconnect")
        else:
            self.escalate = False

    # ---------- misc
    def run_web_search(self):
        q = self.last_search_query

        def worker():
            self.emit({"type": "activity", "running": True,
                       "fa": "جستجوی راه‌حل در وب...", "en": "Searching the web..."})
            res = online_help.search_web(q)
            if not res:
                res = online_help.fallback_links(q)
            self.emit({"type": "web", "results": res, "query": q})
            self.emit({"type": "activity", "running": False,
                       "fa": "آماده", "en": "Idle"})

        threading.Thread(target=worker, daemon=True).start()

    def restore_dns(self):
        iface = self.settings.get("last_dns_iface", "")
        if not iface:
            self._log("info", "تغییری در DNS ثبت نشده بود که برگردانده شود",
                      "No DNS change was recorded to restore")
            return
        ok = fixes.restore_dhcp_dns(iface, self._log)
        if ok:
            self.settings.set("last_dns_iface", "")

    def relaunch_as_admin(self):
        ok = fixes.relaunch_as_admin()
        if ok:
            self._log("info", "برنامه با دسترسی مدیر دوباره اجرا می‌شود",
                      "Relaunching with administrator rights")
        return ok


def selftest():
    """Headless engine test (no GUI). Useful to verify the install."""
    print("== Internet Doctor self-test ==")
    c = Controller()
    c.settings.set("interval_seconds", 15)
    assert c.settings.get("interval_seconds") == 15
    print("[PASS] settings round-trip")

    kb = knowledge.load_kb()
    assert len(kb) >= 10
    print("[PASS] knowledge base: %d entries" % len(kb))

    print("[*] probing connectivity (may take a few seconds)...")
    probe = monitor.check_now()
    print("[PASS] probe: state=%s gw=%s ip=%s dns_ok=%s http=%s" % (
        probe.state, probe.gateway or "-", probe.local_ip or "-",
        probe.dns_ok, probe.http_status))

    diag = diagnostics.run_diagnosis(probe, lambda *a, **k: None, None)
    print("[PASS] diagnosis: findings=%s plan=%s" % (
        [f["id"] for f in diag.findings], diag.plan))

    reg = fixes.build_registry({"iface": probe.iface, "dns": "8.8.8.8"})
    assert "flush_dns" in reg and "winsock_reset" in reg
    print("[PASS] fix registry: %d steps available" % len(reg))

    deep = diagnostics.build_plan([], deep=True)
    assert "winsock_reset" in deep and "tcp_reset" in deep
    print("[PASS] escalated (deep) plan includes winsock + TCP/IP resets")

    try:
        res = online_help.search_web("windows 11 no internet fix")
        print("[PASS] online search: %d results (0 is OK when offline)" % len(res))
    except Exception as exc:
        print("[WARN] online search unavailable: %s" % exc)

    c.history.add({"trigger": "selftest", "state_before": probe.state,
                   "state_after": probe.state, "findings": [], "fixes": [],
                   "result": "no_fix_needed", "web_count": 0,
                   "modem_hint": False})
    print("[PASS] history record saved: %d record(s)" % len(c.history.all()))

    try:
        import pystray  # noqa: F401
        from PIL import Image  # noqa: F401
        from tray_icon import make_status_image, TrayIcon  # noqa: F401
        make_status_image("#34D399")
        print("[PASS] system tray module (pystray + Pillow) OK")
    except Exception as exc:
        print("[WARN] system tray unavailable: %s" % exc)

    print("== self-test finished ==")
    return True


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    try:
        import ctypes
        if os.name == "nt":
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    from ui import InternetDoctorApp
    ctrl = Controller()
    app = InternetDoctorApp(ctrl)

    # ---- system tray (optional; silently skipped when unavailable)
    tray = None
    if "--no-tray" not in sys.argv and bool(ctrl.settings.get("enable_tray", True)):
        try:
            from tray_icon import TrayIcon
            tray = TrayIcon(ctrl)
            if tray.start():
                ctrl.tray = tray
                ctrl._log("ok", "آیکون برنامه کنار ساعت ویندوز فعال شد",
                          "System tray icon enabled")
        except Exception as exc:
            ctrl._log("info", "System Tray در دسترس نیست: %s" % exc,
                      "Tray unavailable: %s" % exc)

    ctrl.start_monitoring()
    try:
        app.mainloop()
    finally:
        if tray is not None:
            tray.stop()


if __name__ == "__main__":
    main()
