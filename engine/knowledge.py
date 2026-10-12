# -*- coding: utf-8 -*-
"""
Internet Doctor - offline bilingual knowledge base.
دکتر اینترنت - پایگاه دانش دوزبانه (آفلاین)

Compiled from common fixes documented by Microsoft support, network vendor
guides and tech community forums. The repair engine maps diagnosis findings
to these entries and applies the matching commands automatically.
"""

_KB = [
    {
        "id": "dns_cache",
        "category": "DNS",
        "fa": {
            "title": "خرابی کش DNS",
            "cause": "ویندوز آدرس‌های قدیمی و خراب را در کش DNS نگه می‌دارد؛ نتیجه‌اش این است که اینترنت وصل است ولی بعضی یا همه سایت‌ها باز نمی‌شوند.",
            "steps": [
                "پاک‌کردن کش DNS با دستور ipconfig /flushdns",
                "تست مجدد بازکردن سایت‌ها",
            ],
        },
        "en": {
            "title": "Corrupted DNS cache",
            "cause": "Windows keeps stale or corrupted entries in its DNS cache, so the connection works but some or all websites fail to open.",
            "steps": [
                "Flush the DNS cache with ipconfig /flushdns",
                "Re-test opening websites",
            ],
        },
        "commands": ["ipconfig /flushdns"],
        "admin": False,
        "reboot": False,
        "search_query": "Windows 11 flush DNS cache fix websites not loading",
    },
    {
        "id": "dns_server",
        "category": "DNS",
        "fa": {
            "title": "سرور DNS پاسخ نمی‌دهد",
            "cause": "DNS پیش‌فرض شرکت ارائه‌دهنده اینترنت خراب، کند یا مسدود شده است؛ پینگ آی‌پی کار می‌کند ولی بازکردن سایت ناموفق است.",
            "steps": [
                "تغییر DNS به سرور عمومی گوگل (8.8.8.8) یا کلادفلر (1.1.1.1)",
                "پاک‌کردن کش DNS بعد از تغییر",
            ],
        },
        "en": {
            "title": "DNS server not responding",
            "cause": "The ISP's default DNS server is broken, slow or blocked; pinging IPs works but opening sites fails.",
            "steps": [
                "Switch DNS to Google (8.8.8.8) or Cloudflare (1.1.1.1)",
                "Flush the DNS cache after switching",
            ],
        },
        "commands": [
            'netsh interface ip set dns name="Wi-Fi" source=static addr=8.8.8.8 register=primary',
            'netsh interface ip add dns name="Wi-Fi" addr=1.1.1.1 index=2',
        ],
        "admin": True,
        "reboot": False,
        "search_query": "Windows 11 change DNS to 8.8.8.8 fix DNS server not responding",
    },
    {
        "id": "dns_service",
        "category": "DNS",
        "fa": {
            "title": "سرویس DNS Client خاموش است",
            "cause": "اگر سرویس Dnscache ویندوز متوقف شده باشد، هیچ سایتی باز نمی‌شود حتی اگر اتصال سالم باشد.",
            "steps": [
                "روشن‌کردن سرویس با دستور net start dnscache",
                "بررسی مجدد بازکردن سایت‌ها",
            ],
        },
        "en": {
            "title": "DNS Client service stopped",
            "cause": "If the Windows Dnscache service is stopped, no website resolves even though the link itself is healthy.",
            "steps": [
                "Start the service with net start dnscache",
                "Re-test opening websites",
            ],
        },
        "commands": ["net start dnscache"],
        "admin": True,
        "reboot": False,
        "search_query": "Windows 11 DNS client service stopped start dnscache fix",
    },
    {
        "id": "dhcp_apipa",
        "category": "IP",
        "fa": {
            "title": "گرفتن IP ناموفق (آدرس 169.254.x.x)",
            "cause": "وقتی ویندوز نتواند از مودم آی‌پی بگیرد، خودش آدرس موقت 169.254.x.x می‌گذارد که به اینترنت وصل نمی‌شود؛ یعنی DHCP مودم یا کابل مشکل دارد.",
            "steps": [
                "آزادکردن و تمدید IP با ipconfig /release و ipconfig /renew",
                "اگر نشد، کارت شبکه را خاموش و روشن کنید",
                "مودم را ری‌استارت کنید",
            ],
        },
        "en": {
            "title": "No valid IP from DHCP (169.254.x.x APIPA)",
            "cause": "When Windows cannot lease an address from the router it falls back to a temporary 169.254.x.x APIPA address that cannot reach the internet.",
            "steps": [
                "Release and renew the IP with ipconfig /release and /renew",
                "If that fails, toggle the network adapter",
                "Reboot the modem/router",
            ],
        },
        "commands": ["ipconfig /release", "ipconfig /renew"],
        "admin": True,
        "reboot": False,
        "search_query": "Windows 11 IP address 169.254 APIPA DHCP failure fix",
    },
    {
        "id": "winsock",
        "category": "IP",
        "fa": {
            "title": "خرابی Winsock",
            "cause": "خرابی رجیستری شبکه (بعد از حذف بدافزار، آنتی‌ویروس یا برنامه‌های VPN) باعث می‌شود هیچ برنامه‌ای به نت وصل نشود.",
            "steps": [
                "ریست Winsock با netsh winsock reset",
                "ری‌استارت ویندوز (الزامی)",
            ],
        },
        "en": {
            "title": "Corrupted Winsock catalog",
            "cause": "Network registry corruption (after malware, antivirus or VPN removal) stops every application from reaching the internet.",
            "steps": [
                "Reset Winsock with netsh winsock reset",
                "Restart Windows (required)",
            ],
        },
        "commands": ["netsh winsock reset"],
        "admin": True,
        "reboot": True,
        "search_query": "Windows 11 netsh winsock reset fix no internet after malware removed",
    },
    {
        "id": "tcp_stack",
        "category": "IP",
        "fa": {
            "title": "خرابی پشته TCP/IP",
            "cause": "اگر پیکربندی TCP/IP خراب شده باشد، حتی پینگ هم جواب نمی‌دهد؛ ریست پشته معمولاً مشکل را حل می‌کند.",
            "steps": [
                "ریست TCP/IP با netsh int ip reset",
                "ری‌استارت ویندوز (الزامی)",
            ],
        },
        "en": {
            "title": "Corrupted TCP/IP stack",
            "cause": "A broken TCP/IP configuration can kill all connectivity including ping; resetting the stack usually restores it.",
            "steps": [
                "Reset TCP/IP with netsh int ip reset",
                "Restart Windows (required)",
            ],
        },
        "commands": ["netsh int ip reset", "ipconfig /flushdns"],
        "admin": True,
        "reboot": True,
        "search_query": "Windows 11 netsh int ip reset fix no connectivity",
    },
    {
        "id": "gateway",
        "category": "Modem",
        "fa": {
            "title": "مودم/روتر پاسخ نمی‌دهد",
            "cause": "اگر پینگ گیت‌وی (مثلاً 192.168.1.1) جواب ندهد، مشکل بین کامپیوتر و مودم است: کابل، سیگنال وای‌فای یا خود مودم هنگ کرده.",
            "steps": [
                "کابل شبکه یا فاصله و کیفیت سیگنال وای‌فای را بررسی کنید",
                "مودم را خاموش کنید، 30 ثانیه صبر کنید و روشن کنید",
                "برنامه وای‌فای را قطع و دوباره وصل می‌کند",
            ],
        },
        "en": {
            "title": "Modem/router unreachable",
            "cause": "If the default gateway (e.g. 192.168.1.1) does not answer ping, the fault is between the PC and the modem: cable, Wi-Fi signal, or a frozen router.",
            "steps": [
                "Check the Ethernet cable or Wi-Fi signal strength",
                "Power-cycle the modem: off, wait 30 seconds, on",
                "The app reconnects Wi-Fi automatically",
            ],
        },
        "commands": ["netsh wlan disconnect", 'netsh wlan connect name="SSID"'],
        "admin": False,
        "reboot": False,
        "search_query": "Windows 11 cannot ping default gateway no internet fix",
    },
    {
        "id": "isp",
        "category": "Modem",
        "fa": {
            "title": "قطعی سمت اپراتور (ISP)",
            "cause": "مودم در دسترس است ولی هیچ آی‌پی عمومی جواب نمی‌دهد؛ یعنی قطعی از سمت شرکت اینترنت است نه سیستم شما.",
            "steps": [
                "چراغ INTERNET یا ONU مودم را بررسی کنید (خاموش یا قرمز یعنی قطعی)",
                "مودم را یک بار ری‌استارت کنید",
                "با پشتیبانی اپراتور تماس بگیرید",
            ],
        },
        "en": {
            "title": "ISP-side outage",
            "cause": "The router is reachable but no public IP answers; the outage is on the provider side, not your computer.",
            "steps": [
                "Check the modem's INTERNET/ONU light (off or red means outage)",
                "Reboot the modem once",
                "Contact your ISP support line",
            ],
        },
        "commands": [],
        "admin": False,
        "reboot": False,
        "search_query": "modem connected but no internet ISP outage troubleshoot",
    },
    {
        "id": "wifi",
        "category": "Wi-Fi",
        "fa": {
            "title": "قطع‌شدن اتصال وای‌فای",
            "cause": "درایور وای‌فای یا ذخیره‌شدن خراب شبکه باعث قطع‌ووصلی مکرر می‌شود؛ وصل‌کردن مجدد معمولاً حلش می‌کند.",
            "steps": [
                "قطع و وصل مجدد با netsh wlan disconnect/connect",
                "اگر تکرار شد، شبکه را Forget و دوباره با رمز وصل کنید",
            ],
        },
        "en": {
            "title": "Wi-Fi disconnected",
            "cause": "Flaky Wi-Fi drivers or a corrupted saved profile cause repeated drops; reconnecting usually restores the link.",
            "steps": [
                "Reconnect with netsh wlan disconnect / connect",
                "If it repeats, forget the network and rejoin with the password",
            ],
        },
        "commands": ["netsh wlan disconnect", 'netsh wlan connect name="SSID"'],
        "admin": False,
        "reboot": False,
        "search_query": "Windows 11 Wi-Fi keeps disconnecting reconnect fix",
    },
    {
        "id": "wlan_service",
        "category": "Wi-Fi",
        "fa": {
            "title": "سرویس WLAN AutoConfig خاموش است",
            "cause": "اگر سرویس WlanSvc متوقف باشد، لیست وای‌فای‌ها خالی است و وصل نمی‌شوید.",
            "steps": [
                "روشن‌کردن سرویس با net start wlansvc",
                "اسکن مجدد شبکه‌های وای‌فای",
            ],
        },
        "en": {
            "title": "WLAN AutoConfig service stopped",
            "cause": "When WlanSvc is stopped the Wi-Fi list is empty and no network can be joined.",
            "steps": [
                "Start the service with net start wlansvc",
                "Re-scan Wi-Fi networks",
            ],
        },
        "commands": ["net start wlansvc"],
        "admin": True,
        "reboot": False,
        "search_query": "Windows 11 WLAN AutoConfig service stopped fix wifi missing",
    },
    {
        "id": "proxy",
        "category": "Proxy",
        "fa": {
            "title": "پروکسی سیستم روشن است",
            "cause": "برنامه‌های VPN، فیلترشکن‌ها یا بدافزارها پروکسی ویندوز را روشن می‌گذارند؛ بعد از بستن برنامه، نت قطع می‌شود.",
            "steps": [
                "خاموش‌کردن ProxyEnable در رجیستری ویندوز",
                "ریست پروکسی WinHTTP با netsh winhttp reset proxy",
            ],
        },
        "en": {
            "title": "System proxy left enabled",
            "cause": "VPN tools, tunneling apps or malware leave a Windows proxy configured; once the app closes, the internet dies.",
            "steps": [
                "Turn off the ProxyEnable registry flag",
                "Reset WinHTTP proxy with netsh winhttp reset proxy",
            ],
        },
        "commands": [
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 0 /f',
            "netsh winhttp reset proxy",
        ],
        "admin": False,
        "reboot": False,
        "search_query": "Windows 11 cannot disable proxy server keeps enabled fix",
    },
    {
        "id": "captive",
        "category": "Proxy",
        "fa": {
            "title": "صفحه ورود شبکه (کپتیو پورتال)",
            "cause": "در هتل، مترو یا شبکه‌های شرکتی باید اول صفحه لاگین را تأیید کنید تا اینترنت باز شود؛ برنامه این حالت را تشخیص می‌دهد.",
            "steps": [
                "مرورگر را باز کنید و صفحه ورود را تأیید کنید",
                "آدرس گیت‌وی مثل http://192.168.1.1 را هم امتحان کنید",
            ],
        },
        "en": {
            "title": "Captive portal sign-in required",
            "cause": "Hotel, metro or corporate networks require accepting a login page before internet is released; the app detects this state.",
            "steps": [
                "Open a browser and complete the sign-in page",
                "Try the gateway address such as http://192.168.1.1",
            ],
        },
        "commands": [],
        "admin": False,
        "reboot": False,
        "search_query": "Windows 11 wifi captive portal login page not opening fix",
    },
    {
        "id": "firewall",
        "category": "Security",
        "fa": {
            "title": "بلاک‌شدن ترافیک توسط فایروال/آنتی‌ویروس",
            "cause": "فایروال سوم‌شخص یا قوانین خراب آنتی‌ویروس می‌تواند ترافیک وب را ببندد در حالی که پینگ و DNS سالم‌اند.",
            "steps": [
                "برنامه برنامه‌های تازه نصب‌شده را بررسی کنید",
                "برای تست، فایروال را موقتاً خاموش کنید (با احتیاط)",
                "قوانین outbound مشکوک را حذف کنید",
            ],
        },
        "en": {
            "title": "Traffic blocked by firewall/antivirus",
            "cause": "A third-party firewall or broken antivirus rules can block web traffic while ping and DNS still work.",
            "steps": [
                "Review recently installed security software",
                "Temporarily disable the firewall to test (carefully)",
                "Remove suspicious outbound rules",
            ],
        },
        "commands": [],
        "admin": False,
        "reboot": False,
        "search_query": "Windows 11 internet connected but browsers cannot open websites firewall fix",
    },
    {
        "id": "adapter",
        "category": "Adapter",
        "fa": {
            "title": "کارت شبکه خاموش یا کابل جدا",
            "cause": "آداپتور شبکه غیرفعال شده یا کابل/آنتن جدا است؛ در Device Manager هم آداپتور با علامت هشدار دیده می‌شود.",
            "steps": [
                "فعال‌کردن آداپتور با netsh interface set interface",
                "بررسی Device Manager و تعویض کابل/پورت",
            ],
        },
        "en": {
            "title": "Adapter disabled or cable unplugged",
            "cause": "The network adapter is administratively disabled or the cable/antenna is detached; Device Manager shows a warning icon.",
            "steps": [
                "Enable the adapter via netsh interface set interface",
                "Check Device Manager and swap cable/port",
            ],
        },
        "commands": ['netsh interface set interface name="Ethernet" admin=enabled'],
        "admin": True,
        "reboot": False,
        "search_query": "Windows 11 network adapter media disconnected fix",
    },
    {
        "id": "driver",
        "category": "Adapter",
        "fa": {
            "title": "خرابی درایور کارت شبکه",
            "cause": "درایور قدیمی یا خراب کارت شبکه باعث خطاهای عجیب و قطعی مکرر می‌شود؛ به‌روزرسانی یا نصب مجدد درایور لازم است.",
            "steps": [
                "بازکردن devmgmt.msc و به‌روزرسانی درایور کارت شبکه",
                "اگر خراب است، Uninstall و اسکن مجدد برای نصب خودکار",
                "دانلود درایور از سایت سازنده لپ‌تاپ/مادربرد",
            ],
        },
        "en": {
            "title": "Network adapter driver issue",
            "cause": "Outdated or corrupted network drivers cause weird errors and repeated drops; updating or reinstalling the driver is required.",
            "steps": [
                "Open devmgmt.msc and update the network driver",
                "If corrupted, uninstall then scan for hardware changes",
                "Download the driver from the laptop/motherboard vendor",
            ],
        },
        "commands": ["devmgmt.msc"],
        "admin": True,
        "reboot": False,
        "search_query": "Windows 11 network adapter driver reinstall fix disconnects",
    },
]


def load_kb():
    """Return the offline knowledge base entries (list of dicts)."""
    return _KB


def find_entry(kb, entry_id):
    for e in kb:
        if e["id"] == entry_id:
            return e
    return None
