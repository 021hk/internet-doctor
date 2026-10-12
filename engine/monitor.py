# -*- coding: utf-8 -*-
"""
Internet Doctor - connectivity probing and basic network info.
دکتر اینترنت - بررسی اتصال اینترنت و اطلاعات شبکه
"""
import os
import re
import socket
import subprocess
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime

IS_WINDOWS = (os.name == "nt")

PING_TARGETS = ["8.8.8.8", "1.1.1.1"]
DNS_HOST = "www.google.com"
HTTP_TARGET = "http://www.gstatic.com/generate_204"

PS_INFO = (
    "$c = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and "
    "$_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1; "
    "if ($c) { Write-Output ('IF=' + $c.InterfaceAlias); "
    "Write-Output ('IP=' + $c.IPv4Address.IPAddress); "
    "Write-Output ('GW=' + $c.IPv4DefaultGateway.NextHop); "
    "Write-Output ('DNS=' + ($c.DNSServer.ServerAddresses -join ',')) } "
    "else { Write-Output 'IF=NONE' }"
)


def run_cmd(cmd, timeout=8, shell=False):
    """Run a command with its window hidden. Returns (returncode, output)."""
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if IS_WINDOWS else 0
    try:
        p = subprocess.run(cmd, shell=shell, capture_output=True, text=True,
                           timeout=timeout, creationflags=creationflags,
                           errors="ignore")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return -1, "command not found"
    except subprocess.TimeoutExpired:
        return -2, "timeout"
    except Exception as exc:
        return -3, str(exc)


def ping(host, timeout_ms=2500):
    """Ping one host. Returns (ok: bool, latency_ms: float or None)."""
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(max(1, int(round(timeout_ms / 1000.0)))), host]
    rc, out = run_cmd(cmd, timeout=timeout_ms / 1000.0 + 3.0)
    if rc != 0:
        return False, None
    m = re.search(r"[=<]\s*(\d+)\s*ms", out)
    return True, (float(m.group(1)) if m else None)


def resolve(host=DNS_HOST, timeout=4.0):
    """DNS resolution with a hard timeout. Returns (ip or None, error or None)."""
    box = {}

    def worker():
        try:
            info = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
            box["ip"] = info[0][4][0]
        except Exception as exc:
            box["err"] = str(exc)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    if "ip" in box:
        return box["ip"], None
    return None, box.get("err", "timeout")


def http_probe(url=HTTP_TARGET, timeout=6):
    """HTTP status of the connectivity test URL.
    204 means a normal internet path; 200/301/302 usually means captive portal."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (InternetDoctor/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, url
    except Exception as exc:
        return None, str(exc)


def get_network_info():
    """Return active interface info: iface name, IPv4, gateway, DNS servers."""
    info = {"iface": "", "ip": "", "gateway": "", "dns": ""}
    if IS_WINDOWS:
        rc, out = run_cmd(["powershell", "-NoProfile", "-Command", PS_INFO], timeout=20)
        if rc == 0:
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("IF="):
                    info["iface"] = line[3:].strip()
                elif line.startswith("IP="):
                    info["ip"] = line[3:].strip()
                elif line.startswith("GW="):
                    info["gateway"] = line[3:].strip()
                elif line.startswith("DNS="):
                    info["dns"] = line[4:].strip()
    else:
        rc, out = run_cmd("ip -4 route show default 2>/dev/null", shell=True, timeout=5)
        m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", out)
        if m:
            info["gateway"] = m.group(1)
        rc, out = run_cmd("ip -4 -o addr show scope global 2>/dev/null", shell=True, timeout=5)
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", out)
        if m:
            info["ip"] = m.group(1)
        try:
            with open("/etc/resolv.conf", "r", encoding="utf-8", errors="ignore") as f:
                ns = re.findall(r"nameserver\s+(\d+\.\d+\.\d+\.\d+)", f.read())
            if ns:
                info["dns"] = ",".join(ns[:3])
        except Exception:
            pass
    return info


@dataclass
class ProbeResult:
    when: str = ""
    iface: str = ""
    local_ip: str = ""
    gateway: str = ""
    dns_servers: str = ""
    gw_ping_ok: bool = False
    gw_latency: object = None
    ext_ping_ok: bool = False
    ext_latency: object = None
    dns_ok: bool = False
    http_status: object = None
    captive: bool = False
    state: str = "offline"   # online | dns | captive | offline | adapter_down
    summary_fa: str = ""
    summary_en: str = ""


def _classify(res):
    """Turn raw probe fields into a single state + bilingual summary."""
    no_iface = (not res.iface) if IS_WINDOWS else (not res.local_ip)
    if no_iface and not res.ext_ping_ok and not res.dns_ok:
        res.state = "adapter_down"
        res.summary_fa = "هیچ کارت شبکه فعالی پیدا نشد؛ کابل یا وای‌فای وصل نیست"
        res.summary_en = "No active network adapter; cable or Wi-Fi is disconnected"
        return
    if res.dns_ok and res.http_status == 204:
        res.state = "online"
        res.summary_fa = "اتصال اینترنت برقرار است"
        res.summary_en = "Internet connection is working"
    elif res.http_status in (200, 301, 302) and res.dns_ok:
        res.state = "captive"
        res.summary_fa = "شبکه نیازمند ورود به حساب است (صفحه لاگین هتل/شرکت)"
        res.summary_en = "Network requires sign-in (captive portal detected)"
    elif res.ext_ping_ok and not res.dns_ok:
        res.state = "dns"
        res.summary_fa = "اینترنت وصل است ولی DNS جواب نمی‌دهد (سایت‌ها باز نمی‌شوند)"
        res.summary_en = "IP connectivity works but DNS fails (sites do not open)"
    elif res.gw_ping_ok and not res.ext_ping_ok and not res.dns_ok:
        res.state = "offline"
        res.summary_fa = "مودم در دسترس است ولی اینترنت قطع است (احتمال قطعی سمت اپراتور)"
        res.summary_en = "Router reachable but internet is down (likely ISP outage)"
    else:
        res.state = "offline"
        res.summary_fa = "اتصال اینترنت قطع است"
        res.summary_en = "Internet connection is down"


def check_now():
    """One full connectivity probe. Blocking for a few seconds, thread-safe."""
    res = ProbeResult()
    res.when = datetime.now().strftime("%H:%M:%S")
    info = get_network_info()
    res.iface = info["iface"]
    res.local_ip = info["ip"]
    res.gateway = info["gateway"]
    res.dns_servers = info["dns"]

    box = {}

    def _do_ping(target):
        box.setdefault("pings", []).append(ping(target))

    def _do_dns():
        box["dns"] = resolve(DNS_HOST)

    def _do_http():
        box["http"] = http_probe()

    threads = [threading.Thread(target=_do_ping, args=(t,), daemon=True)
               for t in PING_TARGETS]
    threads.append(threading.Thread(target=_do_dns, daemon=True))
    threads.append(threading.Thread(target=_do_http, daemon=True))
    for t in threads:
        t.start()
    if res.gateway:
        res.gw_ping_ok, res.gw_latency = ping(res.gateway, 1500)
    for t in threads:
        t.join(9.0)

    pings = box.get("pings", [])
    res.ext_ping_ok = any(ok for ok, _ in pings)
    lats = [l for _, l in pings if l]
    res.ext_latency = min(lats) if lats else None
    res.dns_ok = bool(box.get("dns", (None,))[0])
    st, _extra = box.get("http", (None, None))
    res.http_status = st
    res.captive = st in (200, 301, 302)
    _classify(res)
    return res


def quick_check():
    """Light-weight check used between repair steps. True if internet is usable."""
    box = {}

    def _dns():
        box["dns"] = resolve(DNS_HOST, 3.5)[0]

    def _http():
        box["http"] = http_probe(timeout=4.5)[0]

    t1 = threading.Thread(target=_dns, daemon=True)
    t2 = threading.Thread(target=_http, daemon=True)
    t1.start()
    t2.start()
    t1.join(6.0)
    t2.join(6.0)
    if box.get("http") == 204:
        return True
    if box.get("dns"):
        return True
    return False


def get_wifi_ssid():
    """Current Wi-Fi SSID via netsh (Windows). Empty string if not available."""
    if not IS_WINDOWS:
        return ""
    rc, out = run_cmd(["netsh", "wlan", "show", "interfaces"], timeout=10)
    for line in out.splitlines():
        m = re.match(r"\s*SSID\s*:\s*(.+?)\s*$", line)
        if m:
            return m.group(1)
    return ""
