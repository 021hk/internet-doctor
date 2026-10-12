# -*- coding: utf-8 -*-
"""
Internet Doctor - diagnosis engine: turn probe results into findings + fix plan.
دکتر اینترنت - موتور تشخیص: تبدیل نتیجه بررسی به یافته‌ها و برنامه تعمیر
"""
import re
from dataclasses import dataclass, field

from .monitor import IS_WINDOWS, run_cmd

FINDING_DEFS = {
    "adapter_down": {
        "fa": "کارت شبکه فعال نیست یا کابل/وای‌فای وصل نیست",
        "en": "Network adapter inactive or cable/Wi-Fi disconnected",
        "kb": ["adapter", "driver"],
        "fixes": ["adapter_toggle"],
    },
    "dhcp_apipa": {
        "fa": "IP معتبر از مودم گرفته نشده (DHCP خراب)",
        "en": "No valid IP from DHCP (APIPA address)",
        "kb": ["dhcp_apipa"],
        "fixes": ["release_renew", "adapter_toggle"],
    },
    "gateway_down": {
        "fa": "مودم/روتر (گیت‌وی) پاسخ نمی‌دهد",
        "en": "Default gateway (modem/router) unreachable",
        "kb": ["gateway", "wifi"],
        "fixes": ["wifi_reconnect", "adapter_toggle"],
    },
    "isp_outage": {
        "fa": "اینترنت سمت اپراتور قطع به نظر می‌رسد",
        "en": "Internet appears to be down on the ISP side",
        "kb": ["isp"],
        "fixes": [],
    },
    "dns_problem": {
        "fa": "DNS کار نمی‌کند؛ نام سایت‌ها باز نمی‌شود",
        "en": "DNS resolution is broken",
        "kb": ["dns_cache", "dns_server", "dns_service"],
        "fixes": ["flush_dns", "start_dnscache", "set_dns"],
    },
    "captive_portal": {
        "fa": "شبکه نیازمند ورود به حساب است (صفحه لاگین)",
        "en": "Captive portal sign-in required",
        "kb": ["captive"],
        "fixes": [],
    },
    "proxy_active": {
        "fa": "پروکسی سیستم روشن است و ممکن است جلوی اتصال را بگیرد",
        "en": "A system proxy is active and may block traffic",
        "kb": ["proxy"],
        "fixes": ["reset_proxy"],
    },
    "dns_service_down": {
        "fa": "سرویس DNS Client ویندوز خاموش است",
        "en": "Windows DNS Client service is stopped",
        "kb": ["dns_service"],
        "fixes": ["start_dnscache"],
    },
    "wlan_service_down": {
        "fa": "سرویس WLAN AutoConfig خاموش است",
        "en": "WLAN AutoConfig service is stopped",
        "kb": ["wlan_service"],
        "fixes": ["start_wlan"],
    },
    "http_blocked": {
        "fa": "پینگ و DNS سالم‌اند ولی وب باز نمی‌شود (احتمال فایروال)",
        "en": "Ping and DNS fine but HTTP blocked (possible firewall)",
        "kb": ["firewall", "proxy"],
        "fixes": ["flush_dns", "reset_proxy"],
    },
    "degraded": {
        "fa": "کیفیت اتصال پایین است (تاخیر زیاد)",
        "en": "Connection quality is poor (high latency)",
        "kb": [],
        "fixes": [],
    },
}

FIX_PRIORITY = [
    "flush_dns", "reset_proxy", "start_dnscache", "set_dns", "start_wlan",
    "wifi_reconnect", "release_renew", "adapter_toggle", "winsock_reset", "tcp_reset",
]

SEARCH_QUERIES = [
    ("dns_problem", "Windows 11 DNS server not responding but internet ping works fix"),
    ("dhcp_apipa", "Windows 11 IP address 169.254 APIPA DHCP failure fix"),
    ("proxy_active", "Windows 11 cannot disable proxy proxy keeps turning on fix"),
    ("captive_portal", "Windows 11 Wi-Fi captive portal login page not opening"),
    ("http_blocked", "Windows 11 internet connected but browsers cannot open websites firewall"),
    ("adapter_down", "Windows 11 network adapter media disconnected fix"),
    ("gateway_down", "Windows 11 cannot ping default gateway no internet fix"),
    ("isp_outage", "Modem connected but no internet ISP outage troubleshoot"),
]

GENERIC_QUERY = "Windows 10 11 no internet connection fix troubleshoot"


@dataclass
class Diagnosis:
    probe: object = None
    findings: list = field(default_factory=list)
    plan: list = field(default_factory=list)
    modem_hint: bool = False
    search_query: str = GENERIC_QUERY


def check_proxy():
    """Read the Windows user proxy state from the registry."""
    out = {"enabled": False, "server": ""}
    if not IS_WINDOWS:
        return out
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    rc, o = run_cmd('reg query "%s" /v ProxyEnable' % key, shell=True, timeout=10)
    if rc == 0 and re.search(r"ProxyEnable\s+REG_DWORD\s+0x1", o):
        out["enabled"] = True
        rc2, o2 = run_cmd('reg query "%s" /v ProxyServer' % key, shell=True, timeout=10)
        if rc2 == 0:
            m = re.search(r"ProxyServer\s+REG_SZ\s+(\S+)", o2)
            if m:
                out["server"] = m.group(1)
    return out


def check_services():
    """Check critical Windows services. Returns {name: status_text}."""
    res = {}
    if not IS_WINDOWS:
        return res
    for name in ("Dnscache", "WlanSvc"):
        rc, o = run_cmd(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Service -Name %s -ErrorAction SilentlyContinue).Status" % name],
            timeout=20)
        lines = [l.strip() for l in (o or "").splitlines() if l.strip()]
        res[name] = lines[-1] if lines else ""
    return res


def _dns_via_public():
    """Test whether an external DNS server answers directly (bypasses config)."""
    rc, out = run_cmd(["nslookup", "-timeout=2", "www.google.com", "8.8.8.8"],
                      timeout=8)
    return rc == 0 and ("Address" in out or "answer" in out.lower())


def build_plan(findings):
    """Order fix ids by invasiveness, deduplicated."""
    wanted = []
    for f in findings:
        wanted.extend(FINDING_DEFS.get(f["id"], {}).get("fixes", []))
    plan = []
    for fid in FIX_PRIORITY:
        if fid in wanted and fid not in plan:
            plan.append(fid)
    return plan


def run_diagnosis(probe, log=None, cancel=None):
    """Run all local diagnosis stages on a probe result."""
    _log = log or (lambda *a, **k: None)
    diag = Diagnosis(probe=probe)
    findings = diag.findings

    def add(fid, dfa="", den=""):
        d = FINDING_DEFS[fid]
        findings.append({"id": fid, "fa": d["fa"], "en": d["en"],
                         "detail_fa": dfa, "detail_en": den, "kb": d["kb"]})

    _log("info", "شروع تشخیص دقیق مشکل...", "Running detailed diagnosis...")

    # 1) adapter / link layer
    if probe.state == "adapter_down":
        add("adapter_down", probe.summary_fa, probe.summary_en)

    # 2) DHCP / IP validity
    if (probe.local_ip or "").startswith("169.254."):
        add("dhcp_apipa",
            "آی‌پی فعلی %s است (آدرس موفقیت‌آمیز نیست)" % probe.local_ip,
            "Current IP is %s (auto-configuration address)" % probe.local_ip)

    # 3) gateway reachability
    if probe.gateway and not probe.gw_ping_ok:
        add("gateway_down",
            "پینگ گیت‌وی %s ناموفق بود" % probe.gateway,
            "Ping to gateway %s failed" % probe.gateway)

    # 4) ISP-side outage: gateway fine, everything outside dead
    if (probe.gateway and probe.gw_ping_ok and not probe.ext_ping_ok
            and not probe.dns_ok and probe.http_status is None):
        add("isp_outage",
            "مودم جواب می‌دهد ولی هیچ سرور بیرونی در دسترس نیست",
            "Router answers but no external server is reachable")

    # 5) DNS problems
    if not probe.dns_ok and (probe.ext_ping_ok or probe.http_status == 204):
        if IS_WINDOWS:
            public_ok = _dns_via_public()
            if public_ok:
                add("dns_problem",
                    "DNS عمومی 8.8.8.8 جواب می‌دهد؛ DNS فعلی سیستم خراب است",
                    "Public DNS 8.8.8.8 answers; the current system DNS is broken")
            else:
                add("dns_problem",
                    "حتی DNS عمومی 8.8.8.8 هم جواب نمی‌دهد (مسدودسازی یا فیلترینگ)",
                    "Even public DNS 8.8.8.8 fails (blocking or filtering)")
        else:
            add("dns_problem")

    # 6) captive portal
    if probe.captive:
        add("captive_portal",
            "صفحه تست به جای کد 204، کد %s برگرداند" % probe.http_status,
            "Test page returned HTTP %s instead of 204" % probe.http_status)

    # 7) system proxy
    proxy = check_proxy()
    if proxy["enabled"]:
        add("proxy_active",
            "پروکسی روی %s تنظیم شده است" % (proxy["server"] or "روشن"),
            "Proxy configured at %s" % (proxy["server"] or "enabled"))

    # 8) critical services
    services = check_services()
    if services.get("Dnscache") == "Stopped":
        add("dns_service_down")
    if services.get("WlanSvc") == "Stopped":
        add("wlan_service_down")

    # 9) HTTP blocked while everything else works
    if probe.dns_ok and probe.ext_ping_ok and probe.http_status is None:
        add("http_blocked")

    # 10) degraded quality (informational)
    if probe.ext_latency and probe.ext_latency >= 200:
        add("degraded",
            "تاخیر پینگ %d میلی‌ثانیه است" % int(probe.ext_latency),
            "Ping latency is %d ms" % int(probe.ext_latency))

    diag.plan = build_plan(findings)
    diag.modem_hint = any(f["id"] in ("gateway_down", "isp_outage") for f in findings)

    for fid in SEARCH_QUERIES:
        if any(f["id"] == fid[0] for f in findings):
            diag.search_query = fid[1]
            break

    if findings:
        _log("warn", "تعداد %d مشکل شناسایی شد" % len(findings),
             "%d problem(s) identified" % len(findings))
    else:
        _log("info", "مشکل مشخصی پیدا نشد؛ تعمیرهای عمومی اجرا می‌شود",
             "No specific problem found; generic repairs will run")
    return diag
