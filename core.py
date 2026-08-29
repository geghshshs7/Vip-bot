# ── Single-file deployment bootstrap ──────────────────────────────────────────
# Railway-তে শুধু bot.py upload করলেও প্রয়োজনীয় runtime packages install করার
# fallback রাখি। requirements.txt থাকলে Railway build-time-এ install করবে;
# এই অংশটি শুধু সেই ক্ষেত্রে কাজ করবে যখন bot.py একাই deploy করা হয়।
import importlib.util as _importlib_util
import subprocess as _subprocess
import sys as _sys

_RUNTIME_PACKAGES = (
    ("telebot", "pytelegrambotapi>=4.36.0"),
    ("emoji", "emoji>=2.15.0"),
    ("openpyxl", "openpyxl>=3.1.5"),
    ("phonenumbers", "phonenumbers>=9.0.34"),
    ("requests", "requests>=2.34.2"),
    ("bs4", "beautifulsoup4>=4.15.0"),
    ("xlrd", "xlrd>=2.0.2"),
    ("langid", "langid>=1.1.6"),
)


def _ensure_single_file_dependencies():
    for module_name, package_name in _RUNTIME_PACKAGES:
        if _importlib_util.find_spec(module_name) is not None:
            continue
        print(f"[BOOTSTRAP] Installing missing package: {package_name}", flush=True)
        _subprocess.check_call(
            [
                _sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-cache-dir",
                package_name,
            ]
        )


_ensure_single_file_dependencies()

import telebot
from telebot import types
import json
import os
import re
import emoji as _emoji_lib
import time
import threading
_LINE_SEP = '<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>'
import datetime
import requests
import hashlib
import phonenumbers
import random
import csv
import io
import tempfile
import openpyxl
import xlrd
from bs4 import BeautifulSoup
from phonenumbers import region_code_for_number, geocoder
from langid import classify as _langid_classify

_PID_FILE = "/tmp/ar_otp_bot.pid"
_my_pid = os.getpid()
if os.path.exists(_PID_FILE):
    try:
        _old_pid = int(open(_PID_FILE).read().strip())
        if _old_pid != _my_pid:
            try:
                os.kill(_old_pid, 9)
                time.sleep(5)
                print(f"[START] Killed old instance PID {_old_pid}")
            except ProcessLookupError:
                pass
    except Exception:
        pass
open(_PID_FILE, "w").write(str(_my_pid))

API_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
# <<SYNC:SUPER_ADMIN_IDS:START>>
SUPER_ADMIN_IDS = [
    6664150885,
    8523774444,
]
# <<SYNC:SUPER_ADMIN_IDS:END>>
ADMIN_IDS = list(SUPER_ADMIN_IDS)
CHANNEL_2 = ""

# ── Panel 1 (Mahofuza) ───────────────────────────────────────────────────────
P1_BASE_URL = "http://91.232.105.47/ints"
P1_LOGIN_PAGE = P1_BASE_URL + "/login"
P1_SIGNIN_URL = P1_BASE_URL + "/signin"
P1_CDR_PAGE = P1_BASE_URL + "/agent/SMSCDRStats"
P1_CDR_DATA_URL = P1_BASE_URL + "/agent/res/data_smscdr.php"
P1_USER_NAME = "Mahofuza"
P1_PASSWORD = "Mahofuza"

# ── Panel 2 (Sagardas50 / XISORA) ────────────────────────────────────────────
P2_BASE_URL = "http://94.23.31.29/sms"
P2_SIGNIN_URL = P2_BASE_URL + "/signmein"
P2_REPORTS_PAGE = P2_BASE_URL + "/client/Reports"
P2_DATA_URL = P2_BASE_URL + "/client/ajax/dt_reports.php"
P2_USER_NAME = "Sagardas50"
P2_PASSWORD = "Sagardas50"

# ── Panel 3 (Rabbi1_FD) ───────────────────────────────────────────────────────
P3_BASE_URL = "http://168.119.13.175/ints"
P3_LOGIN_PAGE = P3_BASE_URL + "/login"
P3_SIGNIN_URL = P3_BASE_URL + "/signin"
P3_CDR_PAGE = P3_BASE_URL + "/agent/SMSCDRStats"
P3_CDR_DATA_URL = P3_BASE_URL + "/agent/res/data_smscdr.php"
P3_USER_NAME = "Rabbi1_FD"
P3_PASSWORD = "Rabbi12"

# ── Panel 4 (Rabbi12) ─────────────────────────────────────────────────────────
P4_BASE_URL = "http://144.217.71.192/ints"
P4_LOGIN_PAGE = P4_BASE_URL + "/login"
P4_SIGNIN_URL = P4_BASE_URL + "/signin"
P4_CDR_PAGE = P4_BASE_URL + "/agent/SMSCDRStats"
P4_CDR_DATA_URL = P4_BASE_URL + "/agent/res/data_smscdr.php"
P4_USER_NAME = "Rabbi12"
P4_PASSWORD = "Rabbi12"

# ── Panel 5 (Rabbi12_v2 / 51.75.144.178) ─────────────────────────────────────
P5_BASE_URL = "http://51.75.144.178/ints"
P5_LOGIN_PAGE = P5_BASE_URL + "/login"
P5_SIGNIN_URL = P5_BASE_URL + "/signin"
P5_CDR_PAGE = P5_BASE_URL + "/agent/SMSCDRStats"
P5_CDR_DATA_URL = P5_BASE_URL + "/agent/res/data_smscdr.php"
P5_USER_NAME = "Rabbi12"
P5_PASSWORD = "Rabbi12@"

# ── Panel 6 (Sagardas50 / TrueSMS.net — SMSRanges) ───────────────────────────
P6_BASE_URL = "https://truesms.net"
P6_LOGIN_PAGE = P6_BASE_URL + "/login"
P6_SIGNIN_URL = P6_BASE_URL + "/signin"
P6_CDR_PAGE = P6_BASE_URL + "/agent/SMSRanges"
P6_CDR_DATA_URL = P6_BASE_URL + "/agent/res/data_smsranges.php"
P6_USER_NAME = "Sagardas50"
P6_PASSWORD = "Sagardas50"

# ── Builtin extra panels (hardcoded, always started automatically) ─────────────
# <<SYNC:_BUILTIN_PANELS:START>>
_BUILTIN_PANELS = [
    {'id': 'd39020', 'host': '139.99.69.196', 'base_url': 'http://139.99.69.196/ints', 'url_hint': 'http://139.99.69.196/ints/agent/SMSCDRStats', 'username': 'Mahofuza12', 'password': 'Mahofuza12', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': 6664150885},
    {'id': 'bp2', 'host': '139.99.9.4', 'base_url': 'http://139.99.9.4/ints', 'url_hint': 'http://139.99.9.4/ints/agent/SMSCDRStats', 'username': 'Rabbi12', 'password': 'Rabbi12', 'engine': 'ints_smsranges', 'data_path': '/agent/res/data_smsranges.php', 'admin_id': None},
    {'id': 'bp3', 'host': '54.36.173.235', 'base_url': 'http://54.36.173.235/ints', 'url_hint': 'http://54.36.173.235/ints/agent/SMSCDRStats', 'username': 'Rabbi12', 'password': 'Rabbi@', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': None},
    {'id': 'd42653', 'host': '54.39.104.241', 'base_url': 'http://54.39.104.241/ints', 'url_hint': 'http://54.39.104.241/ints/agent/SMSCDRStats', 'username': 'Rabbi5', 'password': 'Rabbi5', 'engine': 'ints_smsranges', 'data_path': '/agent/res/data_smsranges.php', 'admin_id': 6664150885},
    {'id': 'bp5', 'host': '213.32.24.208', 'base_url': 'http://213.32.24.208/ints', 'url_hint': 'http://213.32.24.208/ints/agent/SMSCDRStats', 'username': 'mahofuza', 'password': 'mahofuza@', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': None},
    {'id': 'bp6', 'host': '15.235.182.3', 'base_url': 'http://15.235.182.3/konekta', 'url_hint': 'http://15.235.182.3/konekta/agent/SMSCDRReports', 'username': 'Rabbi200', 'password': 'Rabbi200', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': None},
    {'id': 'bp7', 'host': 'nexor-iprn.com', 'base_url': 'https://nexor-iprn.com', 'url_hint': 'https://nexor-iprn.com/agent/SMSCDRStats', 'username': 'Rabbi12', 'password': 'Rabbi12@', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': None},
    {'id': 'bp8', 'host': '51.77.52.79', 'base_url': 'http://51.77.52.79/ints', 'url_hint': 'http://51.77.52.79/ints/agent/SMSCDRStats', 'username': 'Rabbi12', 'password': 'Rabbi12', 'engine': 'ints_smsranges', 'data_path': '/agent/res/data_smsranges.php', 'admin_id': None},
    {'id': 'bp9', 'host': '51.210.208.26', 'base_url': 'http://51.210.208.26/ints', 'url_hint': 'http://51.210.208.26/ints/agent/SMSCDRStats', 'username': 'Dasbabu50_FD', 'password': 'Dasbabu50_FD', 'engine': 'ints_smsranges', 'data_path': '/agent/res/data_smsranges.php', 'admin_id': None},
    {'id': 'bp11', 'host': '139.99.68.231', 'base_url': 'http://139.99.68.231/ints', 'url_hint': 'http://139.99.68.231/ints/agent/SMSCDRStats', 'username': 'Rabbi12', 'password': 'Rabbi12', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': None},
    {'id': 'bp12', 'host': '51.75.144.178', 'base_url': 'http://51.75.144.178/ints', 'url_hint': 'http://51.75.144.178/ints/agent/SMSCDRStats', 'username': 'Rabbi12', 'password': 'Rabbi12@', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': None},
    {'id': 'd20591', 'host': '54.39.104.241', 'base_url': 'http://54.39.104.241/ints', 'url_hint': 'http://54.39.104.241/ints/client/SMSCDRStats', 'username': 'Atik9898', 'password': 'Atik9898', 'engine': 'html_scrape', 'data_path': 'http://54.39.104.241/ints/client/SMSCDRStats', 'admin_id': 6664150885},
    {'id': 'pscall1', 'host': 'pscall.net', 'base_url': 'http://pscall.net/restapi', 'url_hint': 'http://pscall.net/restapi/smsreport', 'username': 'api:pscall.net', 'password': '', 'api_key': 'SFNSQz1SS2NygIF6QlBR', 'api_key_param': 'key', 'engine': 'api_key', 'data_path': '/smsreport', 'admin_id': None},
    {'id': 'd34527', 'host': '151.80.19.204', 'base_url': 'http://151.80.19.204/ints', 'url_hint': 'http://151.80.19.204/ints/agent/SMSCDRStats', 'username': 'Atik9898', 'password': 'Atik9898', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': 6664150885},
    {'id': 'd6180', 'host': '91.232.105.47', 'base_url': 'http://91.232.105.47/ints', 'url_hint': 'http://91.232.105.47/ints/agent/SMSCDRStats', 'username': 'Mahofuza', 'password': 'Mahofuza12@', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': 6664150885},
    {'id': 'd76011', 'host': '139.99.69.196', 'base_url': 'http://139.99.69.196/ints', 'url_hint': 'http://139.99.69.196/ints/agent/SMSCDRStats', 'username': 'Mahofuza12', 'password': 'Mahofuza1', 'engine': 'ints_smsranges', 'data_path': '/agent/res/data_smsranges.php', 'admin_id': 6664150885},
    {'id': 'fastx1', 'host': '2eee7.com', 'base_url': 'https://2eee7.com/@Access/@Bot/2eee7/@public', 'url_hint': 'https://2eee7.com/@Access/@Bot/2eee7/@public/api/liveaccess', 'username': 'MURAD', 'password': '', 'api_key': 'MURAD_979BB07726A593010D1BA4A2', 'api_key_param': 'api_key', 'engine': 'api_key', 'data_path': '/api/success-otp-info', 'admin_id': None},
    {'id': 'bp13', 'host': '168.119.13.175', 'base_url': 'http://168.119.13.175/ints', 'url_hint': 'http://168.119.13.175/ints/agent/SMSCDRStats', 'username': 'Rabbi1_FD', 'password': 'Rabbi12', 'engine': 'ints_smsranges', 'data_path': '/agent/res/data_smsranges.php', 'admin_id': None},
    {'id': 'mbcs1', 'host': 'mbcs-ms.com', 'base_url': 'https://mbcs-ms.com', 'url_hint': 'https://mbcs-ms.com/agent/SMSCDRReports', 'username': 'Rabbi', 'password': 'Rabbi12', 'engine': 'html_scrape', 'data_path': 'https://mbcs-ms.com/agent/SMSCDRReports', 'admin_id': None},
    {'id': 'bp10', 'host': 'ivasms.com', 'base_url': 'https://ivasms.com', 'url_hint': 'https://ivasms.com/portal/sms/received', 'username': 'mdrashub2@gmail.com', 'password': 'Rabbi+nnn', 'engine': 'iva_sms', 'data_path': '/portal/sms/received', 'admin_id': None},
    {'id': 'd82649', 'host': '93.190.143.35', 'base_url': 'http://93.190.143.35/ints', 'url_hint': 'http://93.190.143.35/ints/agent/SMSCDRReports', 'username': 'Rabbi12', 'password': 'Rabbi12@', 'engine': 'ints_smscdr', 'data_path': '/agent/res/data_smscdr.php', 'admin_id': 8523774444},
]
# <<SYNC:_BUILTIN_PANELS:END>>

# ── Extra panels outside sync block (never overwritten by _sync_settings_to_botpy) ──
_EXTRA_PANELS = [
    {'id': 'fastx1', 'host': '2eee7.com', 'base_url': 'https://2eee7.com/@Access/@Bot/2eee7/@public',
     'url_hint': 'https://2eee7.com/@Access/@Bot/2eee7/@public/api/liveaccess', 'username': 'MURAD', 'password': '',
     'api_key': 'MURAD_979BB07726A593010D1BA4A2', 'api_key_param': 'api_key',
     'engine': 'api_key', 'data_path': '/api/success-otp-info', 'admin_id': None},
    {'id': 'mbcs1', 'host': 'mbcs-ms.com', 'base_url': 'https://mbcs-ms.com',
     'url_hint': 'https://mbcs-ms.com/agent/SMSCDRReports', 'username': 'Rabbi', 'password': 'Rabbi12',
     'engine': 'html_scrape', 'data_path': 'https://mbcs-ms.com/agent/SMSCDRReports', 'admin_id': None},
]
# Merge into _BUILTIN_PANELS in memory (deduplicated) so startup loop picks them up
_bp_ids_set = {p["id"] for p in _BUILTIN_PANELS}
for _ep in _EXTRA_PANELS:
    if _ep["id"] not in _bp_ids_set:
        _BUILTIN_PANELS.append(_ep)
del _bp_ids_set

POLL_INTERVAL = 1
DATA_FILE = "stock_data.json"
USERS_FILE = "users.json"
SEEN_FILE = "seen_otps.json"
V2_USERS_FILE = "v2_users.json"

bot = telebot.TeleBot(API_TOKEN, threaded=True, num_threads=150)

# ── Persistent helpers ────────────────────────────────────────────────────────


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


stock = load_json(
    DATA_FILE,
    {
        "whatsapp": {},
        "facebook": {},
        "telegram": {},
        "instagram": {},
        "pc clone": {},
        "binance": {},
    },
)
users = load_json(USERS_FILE, [])
seen_otps = load_json(SEEN_FILE, {})

USER_NAMES_FILE = "user_names.json"
user_names = load_json(USER_NAMES_FILE, {})

ADMINS_FILE = "admins.json"
ADMIN_EXPIRY_FILE = "admin_expiry.json"
ADMIN_SETTINGS_FILE = "admin_settings.json"

CONSOLE_CONFIG_FILE = "console_config.json"
_CONSOLE_SVC_NAMES = [
    "FACEBOOK", "WHATSAPP", "INSTAGRAM", "TELEGRAM",
    "TWITTER", "TIKTOK", "SNAPCHAT", "GOOGLE",
    "BINANCE", "YOUTUBE", "LINKEDIN", "AMAZON",
]
_console_config = load_json(CONSOLE_CONFIG_FILE, {
    svc: {"enabled": False, "ranges": []} for svc in _CONSOLE_SVC_NAMES
})
# Ensure all default services exist
for _csvc in _CONSOLE_SVC_NAMES:
    if _csvc not in _console_config:
        _console_config[_csvc] = {"enabled": False, "ranges": []}

def save_console_config():
    save_json(CONSOLE_CONFIG_FILE, _console_config)

_cc_addrange_state: dict = {}  # uid -> sid

_extra_admins = load_json(ADMINS_FILE, [])
for _aid in _extra_admins:
    if _aid not in ADMIN_IDS:
        ADMIN_IDS.append(_aid)

# {str(uid): expiry_unix_timestamp}  — None means permanent
_admin_expiry = load_json(ADMIN_EXPIRY_FILE, {})

# per-admin settings: {str(uid): {otp_group_link, otp_group_id, channel2, bot_link}}
_admin_settings = load_json(ADMIN_SETTINGS_FILE, {})


def is_super_admin(uid):
    return uid in SUPER_ADMIN_IDS


def save_admins():
    save_json(ADMINS_FILE, [a for a in ADMIN_IDS if a not in SUPER_ADMIN_IDS])
    _sync_settings_to_botpy()


def save_admin_expiry():
    save_json(ADMIN_EXPIRY_FILE, _admin_expiry)


def save_admin_settings():
    save_json(ADMIN_SETTINGS_FILE, _admin_settings)


def get_admin_setting(uid, key, default=""):
    """Return per-admin setting, fall back to global group_settings."""
    return _admin_settings.get(str(uid), {}).get(key, _group_settings.get(key, default))


def add_admin(uid, months=None):
    """Add uid as admin. months=None means permanent (super admin only can set)."""
    if uid in SUPER_ADMIN_IDS:
        return False  # already super admin
    if uid not in ADMIN_IDS:
        ADMIN_IDS.append(uid)
    if months:
        expiry = time.time() + months * 30 * 24 * 3600
        _admin_expiry[str(uid)] = expiry
    else:
        _admin_expiry.pop(str(uid), None)
    save_admins()
    save_admin_expiry()
    return True


def remove_admin(uid):
    if uid in SUPER_ADMIN_IDS:
        return False
    if uid in ADMIN_IDS:
        ADMIN_IDS.remove(uid)
        _admin_expiry.pop(str(uid), None)
        _admin_settings.pop(str(uid), None)
        save_admins()
        save_admin_expiry()
        save_admin_settings()
        return True
    return False


def _admin_expiry_checker():
    """Background thread: remove expired admins every 10 minutes."""
    while True:
        time.sleep(600)
        now = time.time()
        to_remove = [
            int(uid) for uid, exp in list(_admin_expiry.items())
            if exp and now >= exp
        ]
        for uid in to_remove:
            remove_admin(uid)
            try:
                bot.send_message(
                    uid,
                    "⚠️ <b>Admin Access Expired!</b>\n\n"
                    "Your admin access has expired.\n"
                    "Contact the admin for new access.",
                    parse_mode="HTML",
                )
            except Exception:
                pass


threading.Thread(target=_admin_expiry_checker, daemon=True).start()

GROUP_SETTINGS_FILE = "group_settings.json"
# <<SYNC:_group_settings_defaults:START>>
_group_settings = load_json(GROUP_SETTINGS_FILE, {
    'otp_group_id': -1003850531522,
    'otp_group_link': 'https://t.me/+BC0-N3KJkiYyOTE1',
    'auto_delete': False,
    'auto_delete_seconds': 3600,
    'channel2': 'https://t.me/+hEL3d0gv6zk4ZmI1',
    'bot_link': 'https://t.me/hot_otp_bot',
    'support_id': '',
    'group_otp_send': True,
    'group_tag': 'PB',
    'numbers_per_batch': 5,
    'v2_active_panel': 'stex',
    'v3_enabled': False,
    'extra_groups': [{'id': -1003738666960, 'bot_link': 'https://t.me/pbpremium_otp_bot', 'channel_link': 'https://t.me/+JsT0epbhAY8zNDY1'}],
    'v2_user_mode': True,
    'fastx_api_key': 'MURAD_88F18AB46B13F781BD52C4E1',
})
# <<SYNC:_group_settings_defaults:END>>

CHANNEL_1 = _group_settings["otp_group_link"]
OTP_GROUP_ID = _group_settings["otp_group_id"]


def save_group_settings():
    save_json(GROUP_SETTINGS_FILE, _group_settings)
    _sync_settings_to_botpy()


def _apply_saved_api_keys():
    """Override global API keys from saved group_settings (if admin changed them)."""
    global FASTX_API_KEY, STEX_API_KEY, V3_API_KEY, MK_API_KEY
    if _group_settings.get("fastx_api_key"):
        FASTX_API_KEY = _group_settings["fastx_api_key"]
    if _group_settings.get("stex_api_key"):
        STEX_API_KEY = _group_settings["stex_api_key"]
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "stex":
                p["api_key"] = STEX_API_KEY
    if _group_settings.get("voltex_api_key"):
        V3_API_KEY = _group_settings["voltex_api_key"]
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "voltex":
                p["api_key"] = V3_API_KEY
    if _group_settings.get("mk_api_key"):
        MK_API_KEY = _group_settings["mk_api_key"]
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "mk":
                p["api_key"] = MK_API_KEY


def get_otp_group_id():
    return _group_settings.get("otp_group_id")


def get_otp_group_link():
    return _group_settings.get("otp_group_link", "")


def get_numbers_per_batch():
    return int(_group_settings.get("numbers_per_batch", 1))


def _svc_display_emoji(svc):
    m = {"facebook": "🔵", "instagram": "📸", "whatsapp": "💚", "telegram": "✈️",
         "binance": "🟡", "pc clone": "💻", "twitter": "🐦", "tiktok": "🎵",
         "snapchat": "👻", "google": "🔴", "youtube": "📺"}
    return m.get((svc or "").lower(), "📱")


def _build_numbers_display_kb(
    svc, scnt, display_nums, flag, c_name,
    is_v2=False, v2_prefix=None, v2_sid=None, cc_removed=False
):
    """Build inline keyboard: service header + copy-able number buttons + action buttons."""
    svc_label = v2_sid if is_v2 else svc
    emoji = _svc_display_emoji(svc_label)
    keyboard = []
    # Row: service name header
    _hdr_icon_id = _svc_icon_emoji_id(svc_label)
    _hdr_kwargs = {"icon_custom_emoji_id": _hdr_icon_id} if _hdr_icon_id else {}
    keyboard.append([types.InlineKeyboardButton(
        f"{svc_label.upper()}",
        callback_data="noop", style="success", **_hdr_kwargs
    )])
    # One row per number
    for dnum in display_nums:
        keyboard.append([types.InlineKeyboardButton(
            f"{dnum}",
            copy_text=types.CopyTextButton(text=dnum), style="primary",
            **_flag_btn_kwargs(flag, "5447508713181034519")
        )])
    # Row 1: Change Number + OTP Group on same row
    change_cb = f"v2rng:{v2_prefix}:{v2_sid}" if is_v2 else f"n:{svc}:{scnt}"
    _cn_text, _cn_icon = _btn_text_and_icon("change_number", "🔄 Change Number")
    action_row = [types.InlineKeyboardButton(_cn_text, callback_data=change_cb, style="danger", **_cn_icon)]
    if get_otp_group_link():
        _og_text, _og_icon = _btn_text_and_icon("otp_group_btn", "📢 OTP Group")
        action_row.append(types.InlineKeyboardButton(_og_text, url=get_otp_group_link(), style="success", **_og_icon))
    keyboard.append(action_row)
    # Row 2: Toggle country code
    if cc_removed:
        _cc_text, _cc_icon = "Add CC", {"icon_custom_emoji_id": _ADD_CC_ICON_ID}
    else:
        _cc_text, _cc_icon = "Remove CC", {"icon_custom_emoji_id": _REMOVE_CC_ICON_ID}
    keyboard.append([
        types.InlineKeyboardButton(
            _cc_text, callback_data="rmcc", style="danger", **_cc_icon
        )
    ])
    # Row 3: Back alone
    back_cb = "v2back" if is_v2 else "back_to_services"
    _bk_text, _bk_icon = _btn_text_and_icon("back", "⬅️ Back")
    keyboard.append([types.InlineKeyboardButton(_bk_text, callback_data=back_cb, style="primary", **_bk_icon)])
    return types.InlineKeyboardMarkup(keyboard)


def _extract_username(link):
    """Extract @username from a t.me link for use with get_chat_member."""
    if not link:
        return None
    link = link.strip().rstrip("/")
    if "joinchat" in link or "/+" in link:
        return None
    if "t.me/" in link:
        uname = link.split("t.me/")[-1].split("/")[0]
        if uname:
            return "@" + uname
    return None


def _check_member(chat_ref, user_id):
    """Returns True if member, False if not, None if cannot check."""
    if not chat_ref:
        return None
    try:
        m = bot.get_chat_member(chat_ref, user_id)
        return m.status not in ("left", "kicked")
    except Exception:
        return None


def get_channel2():
    return _group_settings.get("channel2", "")


def get_bot_link():
    return _group_settings.get("bot_link", "")


def get_group_tag():
    return _group_settings.get("group_tag", "BOT")


def is_auto_delete():
    return _group_settings.get("auto_delete", True)


def _schedule_delete(chat_id, msg_id):
    delay = _group_settings.get("auto_delete_seconds", 3600)
    def _do_delete():
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    threading.Timer(delay, _do_delete).start()

# ── Message templates ──────────────────────────────────────────────────────────

TEMPLATES_FILE = "message_templates.json"
# <<SYNC:_DEFAULT_TEMPLATES:START>>
_DEFAULT_TEMPLATES = {
    'start': '<tg-emoji emoji-id="5461117441612462242">🌟</tg-emoji> <b>WELCOME TO NUMBER BOT x PB TECH</b> <tg-emoji emoji-id="5461117441612462242">🌟</tg-emoji>\n\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>USER DASHBOARD</b>\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n<tg-emoji emoji-id="5202216593966244027">👤</tg-emoji> <b>User:</b> {uname}\n<tg-emoji emoji-id="5282843764451195532">🆔</tg-emoji> <b>User ID:</b> <code>{uid}</code>\n<tg-emoji emoji-id="5451882707875276247">📊</tg-emoji> <b>Account Status:</b> <tg-emoji emoji-id="5316919747214854314">💎</tg-emoji> Premium\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n<tg-emoji emoji-id="5458603043203327669">⚠️</tg-emoji> <b>IMPORTANT NOTICE</b>\n\nPlease JOIN our channel below,\nthen click VERIFY to continue <tg-emoji emoji-id="5420323339723881652">✅</tg-emoji>\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n\n<tg-emoji emoji-id="5391112412445288650">⚡</tg-emoji> <b>Fast • Secure • Premium Service</b> <tg-emoji emoji-id="5391112412445288650">⚡</tg-emoji>\n\n<tg-emoji emoji-id="5461117441612462242">🌟</tg-emoji> <i>Powered by</i>\n<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>NUMBER BOT x PB TECH</b> <tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>',
    'verify_success': '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>VERIFICATION COMPLETE!</b> <tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>\n\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n   <tg-emoji emoji-id="5206607081334906820">✅</tg-emoji> <b>ACCESS GRANTED</b>\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n  <tg-emoji emoji-id="5352899869369446268">👋</tg-emoji> <b>Welcome, {vname}!</b>\n  <tg-emoji emoji-id="5282843764451195532">🆔</tg-emoji> <b>ID:</b> <code>{uid}</code>\n  <tg-emoji emoji-id="5451882707875276247">📊</tg-emoji> <b>Status:</b> <tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> Premium\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n\n<tg-emoji emoji-id="5420323339723881652">✅</tg-emoji> <b>YOU CAN GET NUMBER NOW!</b> <tg-emoji emoji-id="5420323339723881652">✅</tg-emoji>',
    'otp_group': '{flag} #{country_short_b} {svc_emoji} <b>{tagged_number_b}</b> #{sms_lang_b}',
    'otp_dm': '{flag} {number} {svc_emoji} {svc}\n{emoji_country_pre} COUNTRY:{country}{flag}',
    'otp_dm_v2': '{emoji_number_pre}{number} {svc_emoji}{svc}\n{emoji_country_pre}{country}{emoji_country_post}',
    'number_assigned': '✅ <b>Number Assigned Successfully !</b>\n\n🔧 <b>Platform :</b> {svc}\n🌍 <b>Country :</b> {flag} {country}\n\n📞 <b>Number :</b> <code>{number}</code>\n\n⏱ <b>Auto code fetch :</b> 10:00s',
    'broadcast': '🔥 <b>𝗔𝗥 𝗢𝗧𝗣 𝗕𝗢𝗧 — 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧!</b> 🔥\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n\n📢 {text} 📢\n\n<tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji><tg-emoji emoji-id="5870818207383686839">〰️</tg-emoji>\n🤖🔥 <i>𝙿𝚘𝚠𝚎𝚛𝚎𝚍 𝚋𝚢</i>  <b>𝗔𝗥 𝗢𝗧𝗣 𝗕𝗢𝗧</b>  🔥🤖',
}
# <<SYNC:_DEFAULT_TEMPLATES:END>>
_templates = load_json(TEMPLATES_FILE, dict(_DEFAULT_TEMPLATES))
for _k, _v in _DEFAULT_TEMPLATES.items():
    if _k not in _templates:
        _templates[_k] = _v
_edit_template_state = {}


def _fmt_pyval(val, indent=0):
    """Format a Python value as readable source code."""
    pad = "    " * indent
    inner = "    " * (indent + 1)
    if isinstance(val, dict):
        if not val:
            return "{}"
        lines = ["{"]
        for k, v in val.items():
            lines.append(f"{inner}{repr(k)}: {repr(v)},")
        lines.append(f"{pad}}}")
        return "\n".join(lines)
    elif isinstance(val, list):
        if not val:
            return "[]"
        lines = ["["]
        for item in val:
            lines.append(f"{inner}{repr(item)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)
    return repr(val)


def _sync_block(source, marker_name, new_content):
    """Replace content between <<SYNC:X:START>> and <<SYNC:X:END>> markers."""
    start_marker = f"# <<SYNC:{marker_name}:START>>"
    end_marker   = f"# <<SYNC:{marker_name}:END>>"
    s = source.find(start_marker)
    e = source.find(end_marker)
    if s == -1 or e == -1:
        return source
    return (
        source[:s + len(start_marker)] + "\n" +
        new_content + "\n" +
        source[e:]
    )


def _sync_settings_to_botpy():
    """Auto-patch bot.py so its hardcoded defaults always match live settings.
    This ensures that when bot.py is pushed to Railway/any server, all panels,
    admin IDs, and other settings are already baked in — no data loss on redeploy.
    """
    try:
        bot_file = os.path.abspath(__file__)
        with open(bot_file, "r", encoding="utf-8") as f:
            source = f.read()

        # Sync message templates
        source = _sync_block(
            source, "_DEFAULT_TEMPLATES",
            f"_DEFAULT_TEMPLATES = {_fmt_pyval(_templates)}"
        )
        # Sync services list
        source = _sync_block(
            source, "_DEFAULT_SERVICES",
            f"_DEFAULT_SERVICES = {_fmt_pyval(_services)}"
        )
        # Sync group settings defaults
        source = _sync_block(
            source, "_group_settings_defaults",
            f"_group_settings = load_json(GROUP_SETTINGS_FILE, {_fmt_pyval(_group_settings)})"
        )

        # ── Sync SUPER_ADMIN_IDS ──────────────────────────────────────────────
        source = _sync_block(
            source, "SUPER_ADMIN_IDS",
            f"SUPER_ADMIN_IDS = {_fmt_pyval(SUPER_ADMIN_IDS)}"
        )

        # ── Sync _BUILTIN_PANELS (merge with dynamic panels) ─────────────────
        # Build merged panel list: start with all dynamic panels, then add any
        # BUILTIN panels not already present (by id OR by host+username+password).
        # Dynamic panels added via /addpanel are promoted to hardcoded — so
        # Railway always has them. Dedup by identity, not just id, so a stale
        # hardcoded duplicate can never resurrect a panel that was removed.
        _seen_ids = set()
        _seen_keys = set()
        _merged_panels = []
        for _p in (_dynamic_panels + _BUILTIN_PANELS):
            _pid = _p.get("id")
            _pkey = (_p.get("host", ""), _p.get("username", ""), _p.get("password", ""))
            if _pid and _pid not in _seen_ids and _pkey not in _seen_keys:
                _seen_ids.add(_pid)
                _seen_keys.add(_pkey)
                # Strip runtime-only keys that shouldn't be hardcoded
                _clean = {k: v for k, v in _p.items() if k not in ("cookie_str",)}
                _merged_panels.append(_clean)
        source = _sync_block(
            source, "_BUILTIN_PANELS",
            f"_BUILTIN_PANELS = {_fmt_pyval(_merged_panels)}"
        )

        # Atomic write: write to temp file first, then rename — prevents corruption
        tmp_file = bot_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(source)
        os.replace(tmp_file, bot_file)
        print("[SYNC] ✅ bot.py auto-patched with latest settings (panels, admins, templates)")
    except Exception as e:
        print(f"[SYNC] ❌ Failed to patch bot.py: {e}")


def save_templates():
    save_json(TEMPLATES_FILE, _templates)
    _sync_settings_to_botpy()


def get_template(key):
    return _templates.get(key, _DEFAULT_TEMPLATES.get(key, ""))


_TEMPLATE_LABELS = {
    "start": "🚀 Start / Welcome Message",
    "otp_group": "📲 OTP Message (Group)",
    "otp_dm": "📲 OTP Message (DM/User — V1)",
    "otp_dm_v2": "📡 OTP Message (DM/User — V2)",
    "verify_success": "✅ Verify Success Message",
    "number_assigned": "☎️ Number Assigned Message",
    "broadcast": "📢 Broadcast Message",
}

_TEMPLATE_VARS = {
    "start": "{uname} = username, {uid} = user ID | Icons: {emoji_start_header}, {emoji_start_crown}, {emoji_start_user}, {emoji_start_id}, {emoji_start_status}, {emoji_start_workers}, {emoji_start_powered}",
    "otp_group": "{svc} = service, {number} = number, {tagged_number} = number with TAG, {tagged_number_b} = bold number with TAG, {country} = country, {flag} = flag, {otp} = OTP code, {sms_body} or {sms} = full SMS, {country_short} = ISO code (NG/BD), {country_short_b} = bold ISO code, {country_lang} = country default lang, {sms_lang} = language detected from the full panel SMS, {sms_lang_b} = bold full-SMS language, {svc_emoji} = service icon emoji",
    "otp_dm": "{svc} = service, {number} = number, {country} = country, {flag} = flag, {otp} = OTP code, {sms_body} or {sms} = full SMS, {reward} = reward, {balance} = balance",
    "otp_dm_v2": "{svc} = service, {number} = number, {country} = country, {flag} = flag, {otp} = OTP code, {sms_body} or {sms} = full SMS, {reward} = reward, {balance} = balance",
    "verify_success": "{vname} = username, {uid} = user ID",
    "number_assigned": "{svc} = service, {country} = country, {flag} = flag, {number} = number",
    "broadcast": "{text} = broadcast content",
}

# ── End Message templates ──────────────────────────────────────────────────────

SERVICES_FILE = "services.json"
# <<SYNC:_DEFAULT_SERVICES:START>>
_DEFAULT_SERVICES = [
    {'label': 'Instagram →', 'key': 'instagram'},
    {'label': 'Facebook 💎', 'key': 'facebook'},
    {'label': 'WhatsApp', 'key': 'whatsapp'},
    {'label': 'Telegram', 'key': 'telegram'},
    {'label': 'Binance', 'key': 'binance'},
    {'label': 'Pc Clone', 'key': 'pcclone'},
    {'label': 'Fib', 'key': 'fib'},
]
# <<SYNC:_DEFAULT_SERVICES:END>>
_services = load_json(SERVICES_FILE, list(_DEFAULT_SERVICES))
_addservice_state = {}
_countdowns = {}

# ── Buy Service ───────────────────────────────────────────────────────────────
BUY_SERVICE_FILE = "buy_service_settings.json"
_buy_service_settings = load_json(BUY_SERVICE_FILE, {
    "premium_prices": {"3M": 0, "6M": 0, "1Y": 0},
    "vpn_services": [
        {"id": "nord_7d",       "emoji_id": "5334944492300573096", "name": "NORD",       "duration": "7D",    "price": 20},
        {"id": "express_7d",    "emoji_id": "5346335574498251610", "name": "EXPRESS",    "duration": "7D",    "price": 20},
        {"id": "ipvanish_7d",   "emoji_id": "5352597830089347330", "name": "IP VANISH",  "duration": "7D",    "price": 20},
        {"id": "surfshark_7d",  "emoji_id": "5190447043545438788", "name": "SURFSHARK",  "duration": "7D",    "price": 20},
        {"id": "hma_7d",        "emoji_id": "5346134750417403743", "name": "HMA",        "duration": "7D",    "price": 20},
        {"id": "pia_7d",        "emoji_id": "5328064671951896068", "name": "PIA",        "duration": "7D",    "price": 20},
        {"id": "proton_14d",    "emoji_id": "5348390922507817684", "name": "PROTON",     "duration": "14D",   "price": 30},
        {"id": "express_30d",   "emoji_id": "5346335574498251610", "name": "EXPRESS 30D","duration": "30D",   "price": 45},
        {"id": "hma_30d",       "emoji_id": "5346134750417403743", "name": "HMA 30D",    "duration": "30D",   "price": 45},
        {"id": "9proxy_1gb",    "emoji_id": "5336983442125001376", "name": "9 PROXY",    "duration": "1GB",   "price": 100},
        {"id": "owlproxy_200mb","emoji_id": "5334530732331143967", "name": "OWL PROXY",  "duration": "200MB", "price": 10},
    ],
    "binance_id": "1138284235",
    "bkash_number": "01340670062",
    "bkash_emoji_id": "5348469219761626211",
    "binance_emoji_id": "5431815433011736909",
    "nagad_number": "01320750520",
    "nagad_emoji_id": "6190392842544748430",
    "dollar_rate": 128,
})

def save_buy_service_settings():
    save_json(BUY_SERVICE_FILE, _buy_service_settings)

# ── Migrate: ensure every VPN entry has a unique id ──────────────────────────
def _migrate_vpn_ids():
    vpns = _buy_service_settings.get("vpn_services", [])
    changed = False
    seen_ids = set()
    for i, v in enumerate(vpns):
        vid = v.get("id", "")
        if not vid or vid in seen_ids:
            v["id"] = f"vpn_{int(time.time() * 1000)}_{i}"
            changed = True
        seen_ids.add(v["id"])
    if changed:
        save_buy_service_settings()

_migrate_vpn_ids()

# {uid: {"type": "premium|vpn", "label": "...", "price": N}}
_buy_pending: dict = {}
# {uid: {"file_id": ..., "pending": {...}}} — screenshot saved, waiting for TG username
_buy_screenshot_pending: dict = {}
# {admin_uid: target_uid}
_admin_dmu_state: dict = {}
# Admin buy service step state
_buy_admin_state: dict = {}


def _update_buy_order_status(order_id, status, completed_by=None):
    """Update a payment order's status without failing the Telegram callback."""
    if not order_id:
        return False
    try:
        import json as _json_order, os as _os_order
        order_file = "buy_orders_log.json"
        if not _os_order.path.exists(order_file):
            return False
        with open(order_file, "r") as _order_f:
            orders = _json_order.load(_order_f)
        if not isinstance(orders, list):
            return False
        updated = False
        for order in orders:
            if isinstance(order, dict) and order.get("order_id") == order_id:
                order["status"] = status
                order["status_updated_at"] = time.time()
                if completed_by is not None:
                    order["completed_by"] = int(completed_by)
                updated = True
                break
        if updated:
            with open(order_file, "w") as _order_f:
                _json_order.dump(orders, _order_f, ensure_ascii=False)
        return updated
    except Exception as _order_status_error:
        print(f"[BUY-ORDER] Could not update order status: {_order_status_error}")
        return False

USER_MAP_FILE = "user_map.json"
_raw_user_map = load_json(USER_MAP_FILE, {})
user_map: dict[str, int] = {k: int(v) for k, v in _raw_user_map.items()}
user_map_lock = threading.Lock()
assigned_time: dict[str, float] = {}
# Telegram applies a bot-wide send limit.  OTP monitors run in many threads, so
# pace DM sends centrally instead of letting a burst of panels trigger 429s.
_dm_rate_lock = threading.Lock()
_dm_next_send_at = 0.0
_DM_MIN_INTERVAL = 0.05

OTP_STATS_FILE = "otp_stats.json"
otp_stats: dict[str, int] = load_json(OTP_STATS_FILE, {})
otp_stats_lock = threading.Lock()


def _save_otp_stats():
    with otp_stats_lock:
        save_json(OTP_STATS_FILE, otp_stats)


CUSTOM_EMOJI_FILE = "custom_emojis.json"
_custom_emojis: dict = load_json(CUSTOM_EMOJI_FILE, {"flags": {}, "services": {}})
_custom_emoji_lock = threading.Lock()

# ── Payment / Reward System ────────────────────────────────────────────────────
BALANCES_FILE        = "balances.json"
WITHDRAW_FILE        = "withdraw_requests.json"
REWARD_SETTINGS_FILE = "reward_settings.json"
REFERRALS_FILE       = "referrals.json"

_balances_lock         = threading.Lock()
_withdraw_lock         = threading.Lock()
_reward_settings_lock  = threading.Lock()
_referrals_lock        = threading.Lock()

_balances:          dict = load_json(BALANCES_FILE, {})
_withdraw_requests: list = load_json(WITHDRAW_FILE, [])
_reward_settings:   dict = load_json(REWARD_SETTINGS_FILE, {
    "reward_per_otp": 0.50,
    "currency":       "৳",
    "min_withdraw":   50.0,
})

def _save_balances():
    with _balances_lock:
        save_json(BALANCES_FILE, _balances)

def _save_withdraws():
    with _withdraw_lock:
        save_json(WITHDRAW_FILE, _withdraw_requests)

def _save_reward_settings():
    with _reward_settings_lock:
        save_json(REWARD_SETTINGS_FILE, _reward_settings)

# ── Referral system ────────────────────────────────────────────────────────────
_referrals: dict = load_json(REFERRALS_FILE, {})  # str(new_uid) → referrer_uid (int)

def _save_referrals():
    with _referrals_lock:
        save_json(REFERRALS_FILE, _referrals)

def get_refer_commission() -> float:
    with _reward_settings_lock:
        return float(_reward_settings.get("refer_commission", 10.0))

def _get_refer_link(uid: int) -> str:
    try:
        me = bot.get_me()
        return f"https://t.me/{me.username}?start=ref{uid}"
    except Exception:
        bl = get_bot_link()
        return f"{bl}?start=ref{uid}" if bl else ""

def _get_refer_count(uid: int) -> int:
    with _referrals_lock:
        return sum(1 for v in _referrals.values() if v == uid)

def get_balance(uid: int) -> float:
    with _balances_lock:
        return float(_balances.get(str(uid), 0.0))

def add_reward(uid: int, amount: float) -> float:
    """Add OTP reward to user balance. Returns new balance."""
    with _balances_lock:
        key = str(uid)
        _balances[key] = float(_balances.get(key, 0.0)) + float(amount)
        bal = _balances[key]
    _save_balances()
    return bal

def deduct_balance(uid: int, amount: float):
    """Deduct from balance. Returns (success, new_balance)."""
    with _balances_lock:
        key = str(uid)
        cur = float(_balances.get(key, 0.0))
        if cur < float(amount) - 0.001:
            return False, cur
        _balances[key] = max(0.0, cur - float(amount))
        new_bal = _balances[key]
    _save_balances()
    return True, new_bal

def get_reward_per_otp() -> float:
    with _reward_settings_lock:
        return float(_reward_settings.get("reward_per_otp", 0.50))

def get_currency() -> str:
    with _reward_settings_lock:
        return _reward_settings.get("currency", "৳")

def get_min_withdraw() -> float:
    with _reward_settings_lock:
        return float(_reward_settings.get("min_withdraw", 50.0))

_HARDCODED_FLAGS = {
    "🇮🇶": "5976458232313420307",
    "🇪🇬": "5976310790381115423",
    "🇾🇪": "5976685311529327157",
    "🇸🇦": "5976726495970729818",
    "🇧🇭": "5976668522502166844",
    "🇰🇼": "5976679732366809576",
    "🇶🇦": "5976723966234991338",
    "🇦🇪": "5976594713489185156",
    "🇴🇲": "5976284621145381432",
    "🇸🇩": "5976733342148598412",
    "🇹🇳": "5976645965333929511",
    "🇵🇸": "5976410742860027765",
    "🇯🇴": "5976421677846764717",
    "🇱🇧": "5976529279662430823",
    "🇩🇿": "5976325273010837563",
    "🇲🇦": "5976435580655901165",
    "🇸🇴": "5976732113787966649",
    "🇩🇯": "5976613946352736850",
    "🇰🇲": "5976698870741083962",
    "🇱🇾": "5976334146413272193",
    "🇺🇸": "5976518134222298962",
    "🇺🇦": "5976654508023880370",
    "🇵🇱": "5976482692152170488",
    "🇰🇿": "5976819202839812519",
    "🇨🇳": "5976702693261975275",
    "🇦🇿": "5976582940983827573",
    "🇪🇺": "5976278161514568573",
    "🇦🇲": "5976638015349463422",
    "🇷🇺": "5976725997754521724",
    "🇺🇿": "5976637328154696110",
    "🇩🇪": "5976493356555968244",
    "🇯🇵": "5976688764683033429",
    "🇹🇷": "5976491638569048813",
    "🇧🇾": "5976363304946245889",
    "🇬🇧": "5976531856642807659",
    "🇮🇳": "5976491823252642237",
    "🇧🇷": "5976287034917001256",
    "🇿🇲": "5976750457593272380",
    "🏴󐁧󐁢󐁷󐁬󐁳󐁿": "5976752617961822505",
    "🇻🇮": "5976644294591650501",
    "🇻🇳": "5976537109387810524",
    "🇻🇦": "5976413624783083695",
    "🇻🇺": "5978614254356404774",
    "🇺🇾": "5976387133424803250",
    "🇺🇬": "5976539578994006362",
    "🇹🇲": "5978875276698851977",
    "🇹🇹": "5976426599879285465",
    "🇹🇬": "5976576434108372678",
    "🇹🇭": "5976342573139106020",
    "🇹🇿": "5976297192514656545",
    "🇹🇯": "5976597573937404746",
    "🇨🇭": "5976561599291333244",
    "🇸🇪": "5976775179425028923",
    "🇸🇿": "5976741725924759442",
    "🇸🇷": "5976300113092417676",
    "🇪🇸": "5976424031488843687",
    "🇱🇰": "5976302702957697673",
    "🇸🇸": "5976604952691218010",
    "🇰🇷": "5976617773168597444",
    "🇿🇦": "5976697079739718234",
    "🇸🇧": "5976631860661329134",
    "🇸🇮": "5978926704637253502",
    "🇸🇰": "5976365662883290025",
    "🇸🇬": "5976545437329399582",
    "🇸🇱": "5976596925397342449",
    "🇸🇨": "5978929268732729465",
    "🇷🇸": "5976463012612020480",
    "🏴󐁧󐁢󐁳󐁣󐁿": "5976465473628282873",
    "🇸🇹": "5976699343187482779",
    "🇸🇳": "5976483722944320690",
    "🇸🇲": "5976790357839452073",
    "🇼🇸": "5976637886500444833",
    "🇰🇳": "5976520505044244501",
    "🇻🇨": "5976353941917538351",
    "🇱🇨": "5976475772959857175",
    "🇷🇼": "5976558287871547862",
    "🇷🇴": "5976646540859546652",
    "🇵🇷": "5976449608019090815",
    "🇵🇭": "5976772181537858123",
    "🇵🇹": "5976327106961873123",
    "🇵🇪": "5976420350701869282",
    "🇵🇾": "5976609745874721028",
    "🇵🇬": "5976504321607475018",
    "🇵🇦": "5976690366705834196",
    "🇵🇼": "5976497857681693092",
    "🇵🇰": "5976723210320748190",
    "🇳🇴": "5976327557933439693",
    "🇳🇬": "5976523777809323703",
    "🇳🇪": "5976647932428950438",
    "🇳🇿": "5976512722563503846",
    "🇳🇱": "5976438003017456076",
    "🇳🇵": "5976563609336026965",
    "🇳🇦": "5976603874654426417",
    "🇲🇿": "5976389130584594356",
    "🇲🇪": "5976333948844776590",
    "🇲🇽": "5976658300480002579",
    "🇲🇳": "5976560392405522726",
    "🇲🇨": "5976425521842494767",
    "🇲🇩": "5976792247625064355",
    "🏴󐁧󐁢󐁳󐁣󐁴󐁿": "5976465473628282873",
}
# Merge hardcoded flags — hardcoded always win; user-saved only override if non-empty
_hf_merged = dict(_HARDCODED_FLAGS)
for _k, _v in _custom_emojis.get("flags", {}).items():
    if _v and _k not in _HARDCODED_FLAGS:
        _hf_merged[_k] = _v
_custom_emojis["flags"] = _hf_merged
del _hf_merged
# Persist merged flags immediately so restarts don't lose hardcoded entries
save_json(CUSTOM_EMOJI_FILE, _custom_emojis)

def _save_custom_emojis():
    with _custom_emoji_lock:
        save_json(CUSTOM_EMOJI_FILE, _custom_emojis)

# Tracks last service+country per user so OTP message buttons know what to request
_user_last_svc: dict[int, tuple] = {}   # uid -> (svc, scnt)
# Tracks last "active number/OTP" message_id per user so buttons can be stripped
_user_last_num_msg: dict[int, int] = {} # uid -> message_id
# Stores the current number message view. The displayed number can be changed
# without changing the full number kept in user_map for OTP matching.
_user_number_views: dict[int, dict] = {}
# Tracks users currently in V2 mode — DM OTP messages skip Get New Number / Change Country
# Persisted to V2_USERS_FILE so bot restarts don't reset V2 mode
_v2_users: set = set(load_json(V2_USERS_FILE, []))

def _save_v2_users():
    save_json(V2_USERS_FILE, list(_v2_users))


def _save_user_map():
    with user_map_lock:
        save_json(USER_MAP_FILE, user_map)


def register_number(user_id, number):
    clean = re.sub(r"\D", "", str(number))
    with user_map_lock:
        user_map[clean] = user_id
        assigned_time[clean] = time.time()
    _save_user_map()


def _resolve_user_for_number(number):
    """Resolve a user's assignment even when a panel changes number formatting.

    Exact matches remain authoritative.  As a safe fallback, compare the last
    ten digits only when exactly one active mapping has that suffix.  This
    handles local/international prefixes without guessing between users.
    """
    clean = re.sub(r"\D", "", str(number))
    if not clean:
        return None, "empty"
    with user_map_lock:
        exact = user_map.get(clean)
        if exact:
            return exact, "exact"
        if len(clean) < 10:
            return None, "missing"
        suffix = clean[-10:]
        matches = [
            (mapped, uid)
            for mapped, uid in user_map.items()
            if re.sub(r"\D", "", str(mapped)).endswith(suffix)
        ]
    matched_uids = {uid for _, uid in matches}
    if len(matched_uids) == 1:
        return next(iter(matched_uids)), "suffix"
    return None, "ambiguous" if matches else "missing"


def _throttle_dm_send():
    """Reserve the next DM send slot so concurrent monitors stay below limits."""
    global _dm_next_send_at
    with _dm_rate_lock:
        now = time.monotonic()
        send_at = max(now, _dm_next_send_at)
        _dm_next_send_at = send_at + _DM_MIN_INTERVAL
    delay = send_at - now
    if delay > 0:
        time.sleep(delay)


def mask_number(number):
    s = str(number)
    if len(s) <= 9:
        return s[:3] + "***" + s[-3:]
    return s[:6] + "***" + s[-3:]


def _remove_country_code(number):
    """Return only the national digits while preserving the OTP mapping."""
    clean = re.sub(r"\D", "", str(number))
    if not clean:
        return ""
    try:
        parsed = phonenumbers.parse(f"+{clean}", None)
        country_code = str(parsed.country_code or "")
    except Exception:
        country_code = ""
    if country_code and clean.startswith(country_code):
        national = clean[len(country_code):]
        if national:
            return national
    return clean


def _remember_number_view(
    uid, svc, scnt, display_nums, flag, c_name,
    is_v2=False, v2_prefix=None, v2_sid=None
):
    _user_number_views[uid] = {
        "svc": svc,
        "scnt": scnt,
        "display_nums": display_nums,
        "original_display_nums": list(display_nums),
        "flag": flag,
        "c_name": c_name,
        "is_v2": is_v2,
        "v2_prefix": v2_prefix,
        "v2_sid": v2_sid,
        "cc_removed": False,
    }


def _handle_remove_cc_callback(call):
    """Toggle country codes on the visible copy buttons only."""
    uid = call.from_user.id
    view = _user_number_views.get(uid)
    if not view or _user_last_num_msg.get(uid) != call.message.message_id:
        bot.answer_callback_query(
            call.id, "❌ This number message is no longer active.", show_alert=True
        )
        return
    display_nums = view.get("display_nums") or []
    if view.get("cc_removed"):
        original_nums = view.get("original_display_nums") or display_nums
        display_nums[:] = original_nums
        view["cc_removed"] = False
        answer_text = "✅ Country code added back."
    else:
        stripped_nums = [_remove_country_code(num) for num in display_nums]
        # Mutate the shared list so an active countdown keeps the stripped values.
        display_nums[:] = stripped_nums
        view["cc_removed"] = True
        answer_text = "✅ Country code removed."

    markup = _build_numbers_display_kb(
        view["svc"],
        view["scnt"],
        display_nums,
        view["flag"],
        view["c_name"],
        is_v2=view.get("is_v2", False),
        v2_prefix=view.get("v2_prefix"),
        v2_sid=view.get("v2_sid"),
        cc_removed=view.get("cc_removed", False),
    )
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )
        bot.answer_callback_query(call.id, answer_text)
    except Exception as exc:
        print(f"[REMOVE CC] Failed to update number buttons: {exc}")
        bot.answer_callback_query(call.id, "❌ Could not update the number.", show_alert=True)


def tag_number(number, tag):
    """Format number as: first3[custom emoji]<b>TAG</b>[custom emoji]last4"""
    clean = re.sub(r"\D", "", str(number))
    if len(clean) >= 7:
        return f'{clean[:3]}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji><b>{tag}</b><tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{clean[-4:]}'
    return clean


def tag_number_bold(number, tag):
    """Like tag_number but with math-bold digits and tag text — safe HTML."""
    clean = re.sub(r"\D", "", str(number))
    if len(clean) >= 7:
        return (f'{to_math_bold(clean[:3])}'
                f'<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>'
                f'<b>{to_math_bold(str(tag))}</b>'
                f'<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>'
                f'{to_math_bold(clean[-4:])}')
    return to_math_bold(clean)


