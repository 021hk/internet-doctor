# -*- coding: utf-8 -*-
"""
Internet Doctor - system tray integration (pystray + Pillow).
دکتر اینترنت - آیکون کنار ساعت ویندوز (System Tray)

- Dynamic icon: color follows connection status (green/amber/red),
  blue while diagnosing/repairing, gray when monitoring is paused.
- Bilingual tray menu: Show window / Start-Pause monitoring /
  Diagnose & Fix / Exit.
- All UI actions are marshalled through the controller event queue,
  so tray callbacks never touch Tkinter directly (thread-safe).
"""
import threading
import time

# status -> (color, tooltip fa/en handled by caller)
GREEN = "#34D399"; AMBER = "#FBBF24"; RED = "#F87171"
BLUE = "#60A5FA"; GRAY = "#8CA0BF"; BG = "#0B0F1A"; BORDER = "#26324D"


def make_status_image(color, badge=None):
    """Draw the tray icon: dark rounded square + wifi arcs + medical-cross dot."""
    from PIL import Image, ImageDraw
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, size - 2, size - 2], radius=14,
                        fill=BG, outline=BORDER, width=2)
    cx, cy = size // 2, 45
    # wifi arcs (open upward)
    for r in (10, 20, 29):
        bbox = [cx - r, cy - r - 8, cx + r, cy + r - 8]
        d.arc(bbox, start=225, end=315, fill=color, width=6)
    # medical cross as the signal dot
    if badge is None:
        badge = color
    x0, y0, x1, y1 = cx - 7, cy - 7, cx + 7, cy + 7
    d.rounded_rectangle([x0, y0, x1, y1], radius=4, fill=badge)
    d.rectangle([cx - 2, y0 + 1, cx + 2, y1 - 1], fill=BG)
    d.rectangle([x0 + 1, cy - 2, x1 - 1, cy + 2], fill=BG)
    return img


class TrayIcon(object):
    """System tray icon wired to the Controller; optional (graceful fallback)."""

    def __init__(self, ctrl):
        self.ctrl = ctrl
        self.icon = None
        self._poll_stop = threading.Event()
        self._thread = None

    # ---------- lifecycle
    def start(self):
        try:
            import pystray
        except Exception as exc:
            self.ctrl._log("info",
                           "کتابخانه System Tray نصب نیست (%s)" % exc,
                           "Tray library unavailable (%s)" % exc)
            return False
        try:
            menu = pystray.Menu(
                pystray.Item("نمایش پنجره | Show window",
                             self._cb_show, default=True),
                pystray.Item("شروع/توقف پایش | Start/Pause monitoring",
                             self._cb_toggle),
                pystray.Item("بررسی و رفع مشکل | Diagnose && Fix",
                             self._cb_fix),
                pystray.Menu.SEPARATOR,
                pystray.Item("خروج کامل | Exit", self._cb_exit),
            )
            first = make_status_image(GRAY)
            self.icon = pystray.Icon("InternetDoctor", first,
                                     "دکتر اینترنت | Internet Doctor", menu)
            self.icon.run_detached()
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
            return True
        except Exception as exc:
            self.ctrl._log("warn",
                           "System Tray فعال نشد: %s" % exc,
                           "Tray unavailable: %s" % exc)
            self.icon = None
            return False

    def stop(self):
        self._poll_stop.set()
        icon = self.icon
        self.icon = None
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                pass

    # ---------- notifications
    def notify(self, message, title="دکتر اینترنت | Internet Doctor"):
        icon = self.icon
        if icon is None:
            return
        try:
            icon.notify(message, title)
        except Exception:
            pass

    # ---------- background state sync
    def _current_state(self):
        """Return (color, tooltip) from the controller's live state."""
        c = self.ctrl
        try:
            if c.worker_thread and c.worker_thread.is_alive():
                return BLUE, "در حال بررسی/تعمیر | Diagnosing/repairing..."
            if not c.monitoring:
                return GRAY, "مانیتورینگ متوقف | Monitoring paused"
            p = c.last_probe
            if p is None:
                return GRAY, "در حال شروع | Starting..."
            m = {"online": (GREEN, "آنلاین | Online"),
                 "dns": (AMBER, "مشکل DNS | DNS problem"),
                 "captive": (AMBER, "نیاز به لاگین | Captive portal"),
                 "offline": (RED, "قطع | Offline"),
                 "adapter_down": (RED, "کارت شبکه خاموش | Adapter down")}
            color, label = m.get(p.state, (GRAY, "نامشخص | Unknown"))
            if p.state == "online" and p.ext_latency:
                label += " (%dms)" % int(p.ext_latency)
            return color, "دکتر اینترنت: %s" % label
        except Exception:
            return GRAY, "دکتر اینترنت | Internet Doctor"

    def _poll_loop(self):
        last_key = None
        while not self._poll_stop.wait(2.0):
            if self.icon is None:
                return
            try:
                color, tip = self._current_state()
                if (color, tip) != last_key:
                    last_key = (color, tip)
                    self.icon.icon = make_status_image(color)
                    self.icon.title = tip
            except Exception:
                pass

    # ---------- menu callbacks (run in the tray thread; queue-marshalled)
    def _cb_show(self, icon=None, item=None):
        self.ctrl.emit({"type": "tray_show"})

    def _cb_toggle(self, icon=None, item=None):
        self.ctrl.toggle_monitoring()

    def _cb_fix(self, icon=None, item=None):
        self.ctrl.diagnose_now()
        self.ctrl.emit({"type": "tray_show"})

    def _cb_exit(self, icon=None, item=None):
        self.stop()
        self.ctrl.shutdown()
        self.ctrl.emit({"type": "app_exit"})
