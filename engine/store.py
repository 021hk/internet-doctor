# -*- coding: utf-8 -*-
"""
Internet Doctor - data storage: settings, history and logging.
دکتر اینترنت - ذخیره‌سازی داده‌ها: تنظیمات، تاریخچه و لاگ
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime

IS_WINDOWS = (os.name == "nt")


def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def app_data_dir():
    """Writable folder for settings/history/logs.
    Running from source: project folder.  Frozen EXE (PyInstaller):
    %APPDATA%\\InternetDoctor so data survives temp-extraction."""
    if getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        d = os.path.join(base, "InternetDoctor")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            d = os.path.expanduser("~")
        return d
    return project_root()


DATA_DIR = os.path.join(app_data_dir(), "data")
LOG_DIR = os.path.join(app_data_dir(), "logs")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")

DEFAULT_SETTINGS = {
    "interval_seconds": 12,     # how often to check connectivity
    "fail_threshold": 3,        # consecutive failures before auto-repair
    "autofix": True,            # run repairs automatically
    "online_help": True,        # search the web when repairs fail
    "preferred_dns": "8.8.8.8", # fallback DNS server
    "language": "bilingual",    # fa | en | bilingual (UI is bilingual)
    "last_dns_iface": "",       # interface whose DNS was changed (for restore)
    "enable_tray": True,        # system-tray icon next to the clock
    "close_to_tray": True,      # closing the window hides to tray instead of exit
}

_LEVEL_MAP = {"info": logging.INFO, "ok": logging.INFO,
              "warn": logging.WARNING, "fail": logging.ERROR}


def ensure_dirs():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        pass


class Settings:
    """Thread-safe settings store persisted to data/settings.json."""

    def __init__(self):
        self._lock = threading.Lock()
        self._data = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
            for k in DEFAULT_SETTINGS:
                if k in stored:
                    self._data[k] = stored[k]
        except Exception:
            pass

    def get(self, key, fallback=None):
        with self._lock:
            return self._data.get(key, fallback)

    def set(self, key, value, save=True):
        with self._lock:
            self._data[key] = value
            if save:
                self._save()

    def _save(self):
        ensure_dirs()
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


class History:
    """Structured repair history persisted to data/history.json."""

    LIMIT = 400

    def __init__(self):
        self._lock = threading.Lock()
        self._records = []
        self._load()

    def _load(self):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                self._records = json.load(f)
        except Exception:
            self._records = []

    def all(self):
        with self._lock:
            return list(self._records)

    def add(self, record):
        record = dict(record)
        record.setdefault("time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with self._lock:
            self._records.insert(0, record)
            if len(self._records) > self.LIMIT:
                self._records = self._records[: self.LIMIT]
            self._save()
        return record

    def _save(self):
        ensure_dirs()
        try:
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self._records, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def clear(self):
        with self._lock:
            self._records = []
            self._save()


class QueueLogHandler(logging.Handler):
    """Pushes bilingual log records into a queue consumed by the UI."""

    def __init__(self, q):
        super().__init__()
        self.q = q

    def emit(self, record):
        try:
            level = record.levelname.lower()
            level = {"warning": "warn", "error": "fail"}.get(level, level)
            self.q.put_nowait({
                "type": "log",
                "level": level,
                "fa": getattr(record, "fa", record.getMessage()),
                "en": getattr(record, "en", record.getMessage()),
            })
        except Exception:
            pass


def setup_logger(ui_queue=None):
    """Create the app logger: daily UTF-8 file + console + optional UI queue."""
    ensure_dirs()
    log_path = os.path.join(
        LOG_DIR, "internet_doctor_%s.log" % datetime.now().strftime("%Y-%m-%d"))
    logger = logging.getLogger("internet_doctor")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s",
                            "%Y-%m-%d %H:%M:%S")
    try:
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if ui_queue is not None:
        qh = QueueLogHandler(ui_queue)
        qh.setFormatter(fmt)
        logger.addHandler(qh)
    return logger


def log_call(logger, level, fa, en):
    """Log one bilingual entry: file gets both, UI queue gets structured event."""
    text = "%s | %s" % (fa, en)
    logger.log(_LEVEL_MAP.get(level, logging.INFO), text,
               extra={"fa": fa, "en": en})
