# دکتر اینترنت | Internet Doctor

برنامه دسکتاپ برای ویندوز 10/11 که اینترنت را دائم زیر نظر دارد؛ وقتی اتصال قطع شود، خودش علت را تشخیص می‌دهد، تعمیرهای استاندارد را پله‌پله اجرا می‌کند و اگر حل نشد، راه‌حل‌ها را از وب پیدا می‌کند.

A Windows 10/11 desktop app that constantly watches your connection. When it drops, the app diagnoses the cause, applies standard repairs step by step, and searches the web for solutions if nothing works.

---

## امکانات | Features

- **مانیتورینگ دائمی** — هر چند ثانیه پینگ، DNS و HTTP بررسی می‌شود | Continuous monitoring: ping, DNS and HTTP probes every few seconds
- **تشخیص هوشمند علت** — آداپتور، DHCP/IP، گیت‌وی/مودم، DNS، پروکسی، سرویس‌ها و کپتیو پورتال | Smart cause detection: adapter, DHCP/IP, gateway/modem, DNS, proxy, services, captive portal
- **تعمیر خودکار پله‌پله** — از کم‌خطرترین (فلاش DNS) تا کامل‌ترین (ریست Winsock)؛ بعد از هر گام اتصال تست می‌شود و با برگشتن نت، بقیه گام‌ها اجرا نمی‌شوند | Progressive auto-repair from safest (DNS flush) to deepest (Winsock reset); connectivity is re-checked after every step
- **پایگاه دانش دوزبانه** — ۱۵ مشکل رایج با علت، راه‌حل و دستور دقیق | Bilingual knowledge base: 15 common problems with causes, fixes and exact commands
- **جستجوی وب وقتی حل نشد** — نتایج DuckDuckGo/Bing داخل برنامه با دکمه بازکردن | Web search fallback (DuckDuckGo/Bing) with in-app clickable results
- **دوزبانه کامل** — همه پیام‌ها فارسی + انگلیسی | Fully bilingual: every message in Persian + English
- **آیکون کنار ساعت (System Tray)** — برنامه حتی وقتی پنجره بسته می‌شود در کنار ساعت می‌ماند؛ رنگ آیکون وضعیت اینترنت را نشان می‌دهد و از منوی راست‌کلیک می‌توانید پایش/تعمیر را اجرا کنید | System tray icon that survives closing the window, colored by connection status, with a right-click menu for monitoring and repairs
- **لاگ و تاریخچه** — فایل لاگ روزانه در پوشه `logs` و تاریخچه ساختاریافته در `data/history.json` + تب تاریخچه در برنامه | Daily log file in `logs`, structured history in `data/history.json`, plus an in-app History tab

---

## نصب سریع با فایل نصبی | Quick install (recommended)

1. به صفحه [Releases](https://github.com/021hk/internet-doctor/releases) بروید.
   Go to the Releases page.
2. فایل `InternetDoctor-Setup-1.1.0.exe` را دانلود و اجرا کنید (یا فقط `InternetDoctor.exe` را بدون نصب اجرا کنید — Portable).
   Download and run `InternetDoctor-Setup-1.1.0.exe`, or grab the standalone `InternetDoctor.exe` (portable, no install needed).
3. در صفحه تنظیمات نصب می‌توانید انتخاب کنید که برنامه با شروع ویندوز بالا بیاید.
   The installer can optionally add the app to Windows startup.

در نسخه EXE، تنظیمات و تاریخچه در `%APPDATA%\InternetDoctor` ذخیره می‌شود.
In the EXE build, settings and history live in `%APPDATA%\InternetDoctor`.

## نصب از سورس | Setup from source

1. **پایتون را نصب کنید** — از [python.org/downloads](https://www.python.org/downloads/) نسخه 3.9 یا جدیدتر را بگیرید و در صفحه اول نصب، تیک **Add python.exe to PATH** را حتماً بزنید.
   Install Python 3.9+ from python.org and tick **Add python.exe to PATH** in the installer.
2. **RUN-Windows.bat را اجرا کنید** — بار اول، کتابخانه رابط گرافیکی (customtkinter) را خودش نصب می‌کند و برنامه باز می‌شود.
   Double-click `RUN-Windows.bat` — the first run auto-installs the UI library (customtkinter) and starts the app.
3. **دسترسی مدیر (پیشنهادی)** — برای اینکه همه تعمیرها کار کنند (تغییر DNS، ریست Winsock، تمدید IP، روشن‌کردن سرویس‌ها) روی فایل bat راست‌کلیک و **Run as administrator** بزنید؛ یا داخل برنامه از دکمه «اجرای مجدد به‌صورت مدیر» استفاده کنید.
   For full repair power (DNS change, Winsock reset, IP renew, starting services) right-click the bat file and choose **Run as administrator**, or use the in-app "Run as Admin" button.

---

## نحوه کار | How it works

1. برنامه هر ۱۲ ثانیه (قابل تغییر در تنظیمات) یک بررسی سبک انجام می‌دهد: پینگ 8.8.8.8 و 1.1.1.1،resolve کردن نام و تست HTTP.
   Every 12 s (configurable) the app runs a light probe: ping to 8.8.8.8/1.1.1.1, DNS resolution and an HTTP check.
2. اگر ۳ بررسی پشت‌سرهم ناموفق باشد، موتور تشخیص وارد عمل می‌شود: وضعیت آداپتور، آدرس IP (169.254 = خرابی DHCP)، پینگ گیت‌وی، DNS عمومی، سرویس‌ها و پروکسی بررسی می‌شوند.
   After 3 consecutive failures the diagnosis engine runs: adapter state, IP address (169.254 = DHCP failure), gateway ping, public DNS, services and proxy.
3. بر اساس یافته‌ها، برنامه تعمیرها را به ترتیب از کم‌خطر به پرخطر اجرا می‌کند و بعد از هر گام اتصال را دوباره تست می‌کند:
   Based on the findings, fixes run from least to most invasive, re-checking the link after each step:
   - پاک‌کردن کش DNS | Flush DNS cache
   - خاموش‌کردن پروکسی معیوب | Reset a broken system proxy
   - روشن‌کردن سرویس DNS / WLAN | Start DNS Client / WLAN services
   - تغییر DNS به گوگل یا کلادفلر | Switch DNS to Google/Cloudflare
   - قطع و وصل وای‌فای | Reconnect Wi-Fi
   - تمدید IP (release/renew) | Release and renew the IP
   - خاموش/روشن‌کردن کارت شبکه | Toggle the network adapter
   - ریست Winsock و TCP/IP (نیاز به ری‌استارت ویندوز) | Winsock / TCP-IP reset (Windows restart required)
4. اگر مشکل مودم یا اپراتور باشد، برنامه به‌جای دستور بی‌فایده، راهنمای ری‌استارت مودم و بررسی چراغ‌ها را نشان می‌دهد.
   For modem/ISP faults the app shows modem power-cycle guidance instead of useless commands.
5. اگر هیچ راه‌حلی جواب نداد و مقداری اتصال وجود داشت، برنامه از وب جستجو می‌کند و نتایج را با لینک قابل کلیک نشان می‌دهد.
   If nothing works and some connectivity exists, the app searches the web and shows clickable results.

---

## چه چیزهایی تغییر می‌کند؟ | What the app may change

- کش DNS پاک می‌شود (بی‌خطر) | DNS cache flushed (harmless)
- پرچم پروکسی کاربر در رجیستری خاموش می‌شود (فقط HKCU) | User proxy flag turned off (HKCU only)
- DNS کارت شبکه فعال به 8.8.8.8 / 1.1.1.1 تغییر می‌کند — برگرداندن: تنظیمات ← «بازگرداندن DNS خودکار» | Active adapter DNS set to 8.8.8.8 / 1.1.1.1 — restore from Settings, "Restore auto DNS"
- IP آزاد و دوباره گرفته می‌شود | IP released and renewed
- کارت شبکه یک بار خاموش و روشن می‌شود | Adapter toggled once
- Winsock / TCP-IP ریست می‌شود (فقط به‌عنوان آخرین راه و با ری‌استارت ویندوز) | Winsock / TCP-IP reset (last resort, needs reboot)

همه این‌ها با ساعت و نتیجه در فایل لاگ ثبت می‌شوند. | Every action is logged with a timestamp and result.

---

## ساختار فایل‌ها | Files

```
Internet-Doctor/
├── main.py              نقطه شروع + موتور کنترل | entry point + controller
├── ui.py                پوسته گرافیکی و داشبورد | GUI shell & dashboard
├── ui_pages.py          تب‌های دانش/تاریخچه/تنظیمات | KB/History/Settings tabs
├── tray_icon.py         آیکون کنار ساعت | system tray integration
├── engine/
│   ├── monitor.py       بررسی اتصال | connectivity probes
│   ├── diagnostics.py   موتور تشخیص | diagnosis engine
│   ├── fixes.py         تعمیرهای خودکار | automatic repairs
│   ├── knowledge.py     پایگاه دانش | knowledge base
│   ├── online_help.py   جستجوی وب | web search
│   └── store.py         تنظیمات/تاریخچه/لاگ | settings/history/logging
├── assets/icon.ico      آیکون برنامه | app icon
├── data/                (خودکار ساخته می‌شود | auto-created) settings + history
├── logs/                (خودکار ساخته می‌شود | auto-created) daily log files
├── RUN-Windows.bat      اجرا از سورس | run from source
├── build-exe.bat        ساخت EXE با PyInstaller | build the EXE
├── installer.iss        اسکریپت نصب‌ساز Inno Setup | Inno Setup installer script
├── .github/workflows/   ساخت خودکار EXE در گیت‌هاب | CI that builds the EXE
└── requirements.txt     کتابخانه‌ها | dependencies
```

---

## ساخت EXE و فایل نصبی | Building the EXE yourself

**روش ۱ — خودکار (پیشنهادی):** هر push به این مخزن، روی سرورهای GitHub فایل `InternetDoctor.exe` و `InternetDoctor-Setup.exe` را می‌سازد؛ از تب [Actions](https://github.com/021hk/internet-doctor/actions) یا صفحه Releases دانلود کنید.

**Method 1 — automatic:** every push to this repo builds the EXE and the Setup.exe on GitHub's servers; download them from the Actions artifacts or the Releases page.

**روش ۲ — روی ویندوز خودتان:** `build-exe.bat` را اجرا کنید تا `dist\InternetDoctor.exe` ساخته شود. برای فایل نصبی، [Inno Setup 6](https://jrsoftware.org/isinfo.php) را نصب و روی `installer.iss` راست‌کلیک و Compile کنید.

**Method 2 — on your own PC:** run `build-exe.bat` to produce `dist\InternetDoctor.exe`. For the installer, install [Inno Setup 6](https://jrsoftware.org/isinfo.php) and compile `installer.iss`.

## سوالات متداول | FAQ

**چرا دکمه اجرا را زدم و خطای Python not found داد؟**
پایتون نصب نیست یا هنگام نصب تیک Add to PATH را نزده‌اید؛ پایتون را دوباره نصب کنید و تیک را بزنید.

**Why "Python not found"?** Python is missing or was installed without "Add python.exe to PATH". Reinstall with the option ticked.

**آنتی‌ویروس به netsh گیر می‌دهد؟**
دستورات netsh دستورات رسمی و استاندارد مایکروسافت هستند؛ اگر اسکریپت بلاک شد، پوشه برنامه را در استثناهای آنتی‌ویروس بگذارید.

**Antivirus flags netsh?** These are standard Microsoft commands; whitelist the app folder if blocked.

**چطور DNS قبلی را برگردانم؟**
تنظیمات ← «بازگرداندن DNS خودکار (DHCP)». این دکمه فقط بعد از اولین تغییر DNS فعال می‌شود.

**How to restore my old DNS?** Settings, "Restore auto DNS" — enabled after the first DNS change.

**برنامه را ببندم مانیتورینگ هم قطع می‌شود؟**
خیر — از نسخه 1.1.0 بستن پنجره یعنی کمینه‌سازی به کنار ساعت (System Tray) و پایش ادامه پیدا می‌کند. برای خروج کامل از منوی آیکون کنار ساعت «خروج کامل | Exit» را بزنید، یا در تنظیمات گزینه «بستن پنجره = کمینه‌سازی» را خاموش کنید.

**Does closing the window stop monitoring?** No — since v1.1.0 closing the window hides the app to the system tray and monitoring continues. Use the tray menu "Exit" for a full quit, or disable "Close button hides to tray" in Settings.

---

## تست سلامت | Self-test

برای اطمینان از نصب درست، در CMD در پوشه برنامه:
To verify the install, inside the app folder in CMD:

```
python main.py --selftest
```

---

## سلب مسئولیت | Disclaimer

این برنامه دستورات تعمیری استاندارد و مستندشده ویندوز را اجرا می‌کند؛ با این حال مسئولیت استفاده بر عهده کاربر است. اگر در شبکه شرکتی هستید، قبل از اجرای تعمیرهای خودکار با مدیر شبکه هماهنگ کنید.

The app runs standard, documented Windows repair commands; use at your own discretion. On corporate networks, coordinate with your network administrator before enabling automatic repairs.
