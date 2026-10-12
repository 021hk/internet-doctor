# -*- coding: utf-8 -*-
"""
Internet Doctor - automatic repair engine (Windows commands).
دکتر اینترنت - موتور تعمیر خودکار (دستورات ویندوز)

Fixes are ordered from least to most invasive. After every step the engine
re-checks connectivity and stops as soon as the internet is back. Every
executed command is logged. Destructive steps (Winsock / TCP-IP reset) are
Microsoft-documented procedures and require a Windows restart afterwards.
"""
import ctypes
import os
import sys
import time

from .monitor import run_cmd, get_wifi_ssid

IS_WINDOWS = (os.name == "nt")


def is_admin():
    """True when running with Windows administrator rights."""
    if not IS_WINDOWS:
        return hasattr(os, "geteuid") and os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    """Re-launch the app elevated via UAC. Returns True when triggered."""
    if not IS_WINDOWS:
        return False
    try:
        script = os.path.abspath(sys.argv[0])
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, '"%s"' % script, None, 1)
        return rc > 32
    except Exception:
        return False


def build_registry(ctx):
    """Build the available fix steps for the current context.

    ctx: {"iface": active interface name, "dns": preferred DNS server}
    Returns {fix_id: {id, fa, en, cmds, admin, reboot, settle}}
    """
    iface = ctx.get("iface") or ""
    dns1 = ctx.get("dns") or "8.8.8.8"
    reg = {}

    def add(fid, fa, en, cmds=(), admin=False, reboot=False, settle=2.0):
        reg[fid] = {"id": fid, "fa": fa, "en": en, "cmds": list(cmds),
                    "admin": admin, "reboot": reboot, "settle": settle}

    add("flush_dns",
        "پاک‌کردن کش DNS",
        "Flush the DNS cache",
        ["ipconfig /flushdns"], settle=2)

    add("reset_proxy",
        "خاموش‌کردن پروکسی سیستمی",
        "Turn off the system proxy",
        ['reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f',
         'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /f',
         "netsh winhttp reset proxy"], settle=2)

    add("start_dnscache",
        "روشن‌کردن سرویس DNS Client",
        "Start the DNS Client service",
        ["net start dnscache"], admin=True, settle=3)

    if iface:
        add("set_dns",
            "تنظیم DNS روی %s و 1.1.1.1" % dns1,
            "Set DNS to %s / 1.1.1.1" % dns1,
            ['netsh interface ip set dns name="%s" source=static addr=%s register=primary' % (iface, dns1),
             'netsh interface ip add dns name="%s" addr=1.1.1.1 index=2' % iface],
            admin=True, settle=4)

    add("start_wlan",
        "روشن‌کردن سرویس WLAN AutoConfig",
        "Start the WLAN AutoConfig service",
        ["net start wlansvc"], admin=True, settle=3)

    ssid = get_wifi_ssid()
    if ssid:
        add("wifi_reconnect",
            "قطع و وصل مجدد وای‌فای (%s)" % ssid,
            "Reconnect Wi-Fi (%s)" % ssid,
            ["netsh wlan disconnect",
             'netsh wlan connect name="%s"' % ssid], settle=8)

    add("release_renew",
        "تمدید IP (آزادسازی و تخصیص مجدد)",
        "Release and renew the IP address",
        ["ipconfig /release", "ipconfig /renew"], settle=10)

    if iface:
        add("adapter_toggle",
            "خاموش و روشن‌کردن کارت شبکه (%s)" % iface,
            "Disable & re-enable the adapter (%s)" % iface,
            ['netsh interface set interface name="%s" admin=disabled' % iface,
             "timeout /t 3 /nobreak >nul",
             'netsh interface set interface name="%s" admin=enabled' % iface],
            admin=True, settle=8)

    add("winsock_reset",
        "ریست Winsock (نیاز به ری‌استارت ویندوز)",
        "Reset Winsock catalog (reboot required)",
        ["netsh winsock reset"], admin=True, reboot=True, settle=2)

    add("tcp_reset",
        "ریست پشته TCP/IP (نیاز به ری‌استارت ویندوز)",
        "Reset the TCP/IP stack (reboot required)",
        ["netsh int ip reset", "ipconfig /flushdns"],
        admin=True, reboot=True, settle=2)

    return reg


def restore_dhcp_dns(iface, log):
    """Set the interface DNS back to automatic (DHCP)."""
    if not IS_WINDOWS:
        return False
    cmd = 'netsh interface ip set dns name="%s" source=dhcp' % iface
    rc, _out = run_cmd(cmd, timeout=30, shell=True)
    log("ok" if rc == 0 else "fail",
        "بازگرداندن DNS به حالت خودکار روی «%s» %s" % (iface, "انجام شد" if rc == 0 else "ناموفق بود"),
        "Restoring automatic DNS on '%s' %s" % (iface, "done" if rc == 0 else "failed"))
    return rc == 0


def run_fix_plan(plan_ids, ctx, quick_probe, log, cancel, emit_step=None):
    """Execute the repair plan step by step, stopping when internet returns.

    Returns {"success": bool, "steps": [...], "needs_reboot": bool}
    """
    emit = emit_step or (lambda ev: None)
    if not IS_WINDOWS:
        log("warn", "تعمیر خودکار فقط روی ویندوز کار می‌کند",
            "Automatic repair works on Windows only")
        return {"success": False, "steps": [], "needs_reboot": False}

    reg = build_registry(ctx)
    plan = [p for p in plan_ids if p in reg]
    total = len(plan)
    steps_out = []
    needs_reboot = False
    success = False

    log("info", "برنامه تعمیر با %d گام شروع شد" % total,
        "Repair plan started with %d step(s)" % total)

    for i, fid in enumerate(plan, 1):
        step = reg[fid]
        if cancel.is_set():
            log("warn", "تعمیر توسط کاربر متوقف شد", "Repair stopped by user")
            break
        if needs_reboot:
            steps_out.append({"id": fid, "fa": step["fa"], "en": step["en"],
                              "status": "skip", "reason": "reboot"})
            continue
        if step["admin"] and not is_admin():
            log("warn", "«%s» به دسترسی مدیر نیاز دارد و رد شد" % step["fa"],
                "'%s' needs admin rights - skipped" % step["en"])
            steps_out.append({"id": fid, "fa": step["fa"], "en": step["en"],
                              "status": "skip", "reason": "admin"})
            emit({"type": "fix_step", "i": i, "n": total, "id": fid,
                  "fa": step["fa"], "en": step["en"], "status": "skip"})
            continue

        emit({"type": "fix_step", "i": i, "n": total, "id": fid,
              "fa": step["fa"], "en": step["en"], "status": "start"})
        log("info", "اجرا: %s" % step["fa"], "Running: %s" % step["en"])

        for cmd in step["cmds"]:
            rc, out = run_cmd(cmd, timeout=90, shell=True)
            lines = [l.strip() for l in (out or "").splitlines() if l.strip()]
            tail = lines[-1][:160] if lines else ""
            if rc != 0:
                log("warn", "دستور با کد %s تمام شد: %s | %s" % (rc, cmd.split()[0], tail),
                    "Command rc=%s: %s | %s" % (rc, cmd.split()[0], tail))

        time.sleep(step["settle"])

        if step["reboot"]:
            needs_reboot = True
            steps_out.append({"id": fid, "fa": step["fa"], "en": step["en"],
                              "status": "reboot"})
            emit({"type": "fix_step", "i": i, "n": total, "id": fid,
                  "fa": step["fa"], "en": step["en"], "status": "reboot"})
            log("warn",
                "برای اعمال این تعمیر باید ویندوز ری‌استارت شود؛ ادامه برنامه متوقف شد",
                "Windows must restart for this fix; stopping the repair plan")
            break

        if quick_probe():
            success = True
            steps_out.append({"id": fid, "fa": step["fa"], "en": step["en"],
                              "status": "fixed"})
            emit({"type": "fix_step", "i": i, "n": total, "id": fid,
                  "fa": step["fa"], "en": step["en"], "status": "fixed"})
            log("ok", "اتصال برقرار شد", "Connection restored")
            break

        steps_out.append({"id": fid, "fa": step["fa"], "en": step["en"],
                          "status": "ran"})
        emit({"type": "fix_step", "i": i, "n": total, "id": fid,
              "fa": step["fa"], "en": step["en"], "status": "ran"})
        log("info", "این گام تمام شد ولی اتصال هنوز برقرار نشده",
            "Step finished but connection is still down")

    return {"success": success, "steps": steps_out, "needs_reboot": needs_reboot}
