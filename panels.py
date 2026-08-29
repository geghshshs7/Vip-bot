def save_stock():
    save_json(DATA_FILE, stock)


def register_user(chat_id, first_name="", last_name="", username=""):
    if chat_id not in users:
        users.append(chat_id)
        save_json(USERS_FILE, users)
    full = f"{first_name} {last_name}".strip()
    if full and username:
        display = f"{full} (@{username})"
    elif full:
        display = full
    elif username:
        display = f"@{username}"
    else:
        display = None
    if display:
        user_names[str(chat_id)] = display
        save_json(USER_NAMES_FILE, user_names)


# ── Panel sessions ────────────────────────────────────────────────────────────

_p1_session = None
_p1_sesskey = None
_p1_lock = threading.Lock()

_p2_session = None
_p2_lock = threading.Lock()

_p3_session = None
_p3_csstr = None
_p3_lock = threading.Lock()

_p4_session = None
_p4_sesskey = None
_p4_lock = threading.Lock()

_p5_session = None
_p5_sesskey = None
_p5_lock = threading.Lock()

_p6_session = None
_p6_sesskey = None
_p6_lock = threading.Lock()


# ── Panel stats (for /panels command) ─────────────────────────────────────────
_panel_stats = {
    "p1": {
        "name": "Mahofuza",
        "host": "91.232.105.47",
        "status": "⏳",
        "count": 0,
        "last": None,
        "errors": 0,
    },
    "p2": {
        "name": "Sagardas50",
        "host": "94.23.31.29",
        "status": "⏳",
        "count": 0,
        "last": None,
        "errors": 0,
    },
    "p3": {
        "name": "Rabbi1_FD",
        "host": "168.119.13.175",
        "status": "⏳",
        "count": 0,
        "last": None,
        "errors": 0,
    },
    "p4": {
        "name": "Rabbi12",
        "host": "144.217.71.192",
        "status": "⏳",
        "count": 0,
        "last": None,
        "errors": 0,
    },
    "p5": {
        "name": "Rabbi12_v2",
        "host": "51.75.144.178",
        "status": "⏳",
        "count": 0,
        "last": None,
        "errors": 0,
    },
    "p6": {
        "name": "TrueSMS/Ranges",
        "host": "truesms.net",
        "status": "⏳",
        "count": 0,
        "last": None,
        "errors": 0,
    },
}
_stats_lock = threading.Lock()


def _record_fetch(pid, count):
    with _stats_lock:
        _panel_stats[pid]["status"] = "🟢"
        _panel_stats[pid]["count"] = count
        _panel_stats[pid]["last"] = time.time()
        _panel_stats[pid]["errors"] = 0


def _record_error(pid):
    with _stats_lock:
        _panel_stats[pid]["status"] = "🔴"
        _panel_stats[pid]["errors"] += 1


# ── Demo OTP state ─────────────────────────────────────────────────────────────
_demo_active = False
_demo_lock = threading.Lock()
_demo_cfg_id_counter = 1
_demo_configs: list = [
    {"id": 1, "name": "Config 1", "active": False, "numbers": ["8801700000000"], "digits": 6, "services": ["Facebook"], "interval": 30}
]
_demo_next_fire: dict = {}
_demo_svc_state: dict = {}
_demo_cfg_temp: dict = {}

seen_lock = threading.Lock()

# ── Dynamic panel system ───────────────────────────────────────────────────────
DYNAMIC_PANELS_FILE = "dynamic_panels.json"
_dynamic_panels = load_json(DYNAMIC_PANELS_FILE, [])
_dynamic_sessions = {}
_dynamic_locks = {}
_addpanel_state = {}
_testpanel_state = {}
_pending_force_add = {}   # panel_id → panel dict (login failed, user wants force-add)
_pending_excel = {}  # uid → {'numbers': [...], 'filename': str}
_awaiting_slot_excel = set()  # UIDs currently in finalize_auto_add Excel-wait state

# Migrate old panels that use panel_type → new engine/data_path format
def _migrate_dynamic_panels():
    changed = False
    for p in _dynamic_panels:
        if "panel_type" in p and "engine" not in p:
            pt = p.pop("panel_type", "smscdr")
            p["engine"] = "ints_smsranges" if pt == "smsranges" else "ints_smscdr"
            p["data_path"] = (
                "/agent/res/data_smsranges.php" if pt == "smsranges"
                else "/agent/res/data_smscdr.php"
            )
            changed = True
        if "engine" not in p:
            p["engine"] = "ints_smscdr"
            p["data_path"] = "/agent/res/data_smscdr.php"
            changed = True
    if changed:
        save_json(DYNAMIC_PANELS_FILE, _dynamic_panels)
        print(f"[MIGRATE] Migrated {len(_dynamic_panels)} dynamic panels to universal format")

_migrate_dynamic_panels()


def _dedupe_dynamic_panels():
    """Remove duplicate panels (same host+username+password), keeping only the
    most-recently-added copy. Runs on every save so re-adding a panel that
    already exists automatically replaces the old entry instead of stacking
    duplicates — self-heals even if duplicates got introduced by a race."""
    global _dynamic_panels
    seen = {}
    ordered_keys = []
    for p in _dynamic_panels:
        key = (p.get("host", ""), p.get("username", ""), p.get("password", ""))
        if key not in seen:
            ordered_keys.append(key)
        seen[key] = p  # last one wins (freshest)
    deduped = [seen[k] for k in ordered_keys]
    if len(deduped) != len(_dynamic_panels):
        removed = len(_dynamic_panels) - len(deduped)
        print(f"[DEDUPE] Removed {removed} duplicate panel(s)")
        _dynamic_panels = deduped


def save_dynamic_panels():
    _dedupe_dynamic_panels()
    save_json(DYNAMIC_PANELS_FILE, _dynamic_panels)
    _sync_settings_to_botpy()


def _get_dp_lock(pid):
    if pid not in _dynamic_locks:
        _dynamic_locks[pid] = threading.Lock()
    return _dynamic_locks[pid]


# ── Universal Panel Engine ─────────────────────────────────────────────────────
# Supports any SMS panel: INTS (math captcha), Xisora, or custom panels.
# Auto-detects login page, captcha, signin path, token, and data endpoint.

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# All known login page paths to try (in order)
_LOGIN_PAGE_PATHS = [
    "/login", "/signin", "/signmein",
    "/ints/login", "/sms/login", "/konekta/login",
    "/admin/login", "/user/login", "/agent/login", "/panel/login",
    "/index.php", "/",
]

# All known signin (POST) paths to try
_SIGNIN_PATHS = [
    "/signin", "/signmein", "/login",
    "/ints/signin", "/sms/signin", "/konekta/signin",
    "/admin/signin", "/user/signin", "/panel/signin",
    "/ints/login", "/sms/login", "/konekta/login",
    "/index.php", "/signIn", "/auth/login", "/auth/signin",
]

# All known data endpoints: (path, param_style, engine_name)
# param_style: "ints" or "xisora"
_DATA_ENDPOINTS = [
    ("/agent/res/data_smscdr.php",              "ints",   "ints_smscdr"),
    ("/agent/res/data_smsranges.php",            "ints",   "ints_smsranges"),
    ("/agent/res/data_smscdrreports.php",        "ints",   "ints_smscdr"),
    ("/ints/agent/res/data_smscdr.php",          "ints",   "ints_smscdr"),
    ("/ints/agent/res/data_smsranges.php",       "ints",   "ints_smsranges"),
    ("/sms/agent/res/data_smscdr.php",           "ints",   "ints_smscdr"),
    ("/sms/agent/res/data_smsranges.php",        "ints",   "ints_smsranges"),
    ("/konekta/agent/res/data_smscdr.php",       "ints",   "ints_smscdr"),
    ("/konekta/agent/res/data_smsranges.php",    "ints",   "ints_smsranges"),
    ("/client/ajax/dt_reports.php",              "xisora", "xisora"),
    ("/client/ajax/dt_smscdr.php",               "xisora", "xisora"),
    ("/api/sms/cdr",                             "ints",   "ints_smscdr"),
]

# Dashboard pages to probe for sesskey/csstr token
_DASHBOARD_PATHS = [
    "/agent/SMSCDRStats", "/agent/SMSRanges", "/agent/SMSCDRReports",
    "/ints/agent/SMSCDRStats", "/ints/agent/SMSRanges", "/ints/agent/SMSCDRReports",
    "/sms/agent/SMSCDRStats", "/sms/agent/SMSRanges",
    "/konekta/agent/SMSCDRStats", "/konekta/agent/SMSRanges", "/konekta/agent/SMSCDRReports",
    "/agent/", "/dashboard", "/admin/", "/home",
]


def _extract_panel_base_url(raw_url: str) -> str | None:
    """
    Extract the panel base URL (scheme+host+any-path-prefix) from ANY panel URL.
    Handles paths like /konekta/agent/SMSCDRReports, /ints/login, etc.
    """
    url = raw_url.strip().split("?")[0].split("#")[0].rstrip("/")
    if not re.match(r"https?://", url, re.IGNORECASE):
        return None
    # Strip from first occurrence of known endpoint/action segment onwards
    cleaned = re.sub(
        r"/(?:agent|login|signin|signmein|client|api|dashboard|auth)(?:/.*)?$",
        "", url, flags=re.IGNORECASE,
    )
    return cleaned.rstrip("/") or url


def _univ_build_url(base_endpoint: str, token: str, date_str: str, style: str) -> str:
    if style == "xisora":
        return (
            f"{base_endpoint}"
            f"?fdate1={date_str}%2000:00:00&fdate2={date_str}%2023:59:59"
            f"&ftermination=&fclient=&fnum=&fcli="
            f"&fgdate=0&fgtermination=0&fgclient=0&fgnumber=0&fgcli=0&fg=0"
        )
    base_q = (
        f"{base_endpoint}"
        f"?fdate1={date_str}%2000:00:00&fdate2={date_str}%2023:59:59"
        f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth="
        f"&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0"
    )
    # Only append sesskey when token is actually present (cookie-based panels don't need it)
    if token:
        base_q += f"&sesskey={token}"
    return base_q


def _univ_extract_token(html: str) -> str:
    sk = re.search(r"sesskey=([A-Za-z0-9+/=]+)", html)
    if sk:
        return sk.group(1)
    cs = re.search(r"csstr=([a-f0-9]{16,})", html)
    if cs:
        return cs.group(1)
    return ""


def _univ_is_login_page(url: str, text: str) -> bool:
    """Return True if response looks like still-on-login-page."""
    u = (url or "").lower()
    t = (text or "").lower()[:800]
    if any(w in t for w in ("invalid password", "incorrect password", "wrong password",
                             "login failed", "invalid username", "invalid credentials",
                             "authentication failed", "wrong credentials",
                             "username or password")):
        return True
    # Login form still visible = still on login page (only if very short response)
    if "type=\"password\"" in (text or "").lower() and len(text) < 300:
        return True
    # URL still looks like a login/sign-in page (catches /sign-in with hyphen too)
    if any(w in u for w in ("/login", "/signin", "/signmein", "/sign-in", "/sign_in")):
        if len(text) < 10000:
            return True
    return False


def _univ_detect_form_fields(html: str):
    """Auto-detect login form field names from HTML. Returns (user_field, pass_field).
    Only matches visible text/email inputs — skips hidden, radio, checkbox, submit."""
    _SKIP_NAMES = {"password", "_token", "csrf_token", "token", "capt", "captcha",
                   "theme-style", "theme_style", "remember", "remember_me", "submit"}

    # Detect password field name
    pf_m = re.search(
        r'<input[^>]+type=["\']password["\'][^>]*name=["\']([^"\']+)["\']'
        r'|<input[^>]+name=["\']([^"\']+)["\'][^>]*type=["\']password["\']',
        html, re.IGNORECASE,
    )
    pass_field = (pf_m.group(1) or pf_m.group(2)).strip() if pf_m else "password"
    _SKIP_NAMES.add(pass_field)

    # 1st priority: exact well-known names
    for name in ("username", "user", "login", "email", "uname", "usr", "user_name"):
        if re.search(rf'name=["\']({re.escape(name)})["\']', html, re.IGNORECASE):
            return name, pass_field

    # 2nd priority: any text/email input whose name doesn't look like a non-user field
    for m in re.finditer(
        r'<input[^>]+type=["\'](?:text|email)["\'][^>]*name=["\']([^"\']+)["\']'
        r'|<input[^>]+name=["\']([^"\']+)["\'][^>]*type=["\'](?:text|email)["\']',
        html, re.IGNORECASE,
    ):
        candidate = (m.group(1) or m.group(2) or "").strip()
        if candidate.lower() not in _SKIP_NAMES and candidate:
            return candidate, pass_field

    # fallback
    return "username", pass_field


def _universal_login(panel):
    """Login to any SMS panel. Returns (session, token, engine, data_path) or (None,)*4."""
    pid = panel["id"]
    base = panel["base_url"].rstrip("/")
    username = panel["username"]
    password = panel["password"]
    # url_hint: original full URL the user provided (may contain path like /konekta/agent/...)
    url_hint = panel.get("url_hint", "")

    sess = requests.Session()
    sess.headers.update({"User-Agent": _UA})
    sess.verify = False

    # ── Step 1: Find login page ──────────────────────────────────────────────
    # Build a prioritized list: try the hint URL first, then known paths
    login_page_candidates = []
    if url_hint:
        # Try sibling paths of the hint URL (same prefix, different suffix)
        hint_base = _extract_panel_base_url(url_hint) or base
        for lp in ["/login", "/signin", "/signmein", "/"]:
            login_page_candidates.append(hint_base + lp)
    for lp in _LOGIN_PAGE_PATHS:
        login_page_candidates.append(base + lp)
    # Deduplicate while preserving order
    seen_lp = set()
    login_page_candidates = [x for x in login_page_candidates if not (x in seen_lp or seen_lp.add(x))]

    login_html = ""
    login_url_used = ""
    for candidate in login_page_candidates:
        try:
            r = sess.get(candidate, timeout=12, verify=False)
            txt_lo = r.text.lower()
            if r.status_code == 200 and (
                "password" in txt_lo or "username" in txt_lo or "login" in txt_lo
            ):
                login_html = r.text
                login_url_used = candidate
                print(f"[{pid}] Login page found: {candidate}")
                break
        except Exception:
            continue

    if not login_html:
        print(f"[{pid}] ❌ Login page not found at {base}")
        return None, None, None, None

    # ── Step 2: Build post data ──────────────────────────────────────────────
    user_field, pass_field = _univ_detect_form_fields(login_html)
    post_data: dict = {user_field: username, pass_field: password}
    print(f"[{pid}] Form fields: {user_field}={username}, {pass_field}=***")

    # Math captcha — try "What is X + Y" first, then plain "X + Y" near a capt field
    m_cap = re.search(r"[Ww]hat is (\d+) \+ (\d+)", login_html)
    if not m_cap and re.search(r'name=["\']capt["\']', login_html, re.IGNORECASE):
        m_cap = re.search(r'(\d+)\s*\+\s*(\d+)', login_html)
    if m_cap:
        ans = int(m_cap.group(1)) + int(m_cap.group(2))
        post_data["capt"] = ans
        print(f"[{pid}] Math captcha: {m_cap.group(1)}+{m_cap.group(2)}={ans}")

    # Collect ALL hidden fields from the login form (CSRF tokens, session seeds, etc.)
    for hf in re.finditer(
        r'<input[^>]+type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']'
        r'|<input[^>]+name=["\']([^"\']+)["\'][^>]*type=["\']hidden["\'][^>]*value=["\']([^"\']*)["\']',
        login_html, re.IGNORECASE,
    ):
        n = (hf.group(1) or hf.group(3) or "").strip()
        v = (hf.group(2) or hf.group(4) or "").strip()
        if n and n.lower() not in (user_field.lower(), pass_field.lower()):
            post_data[n] = v

    # ── Step 3: Try signin paths ─────────────────────────────────────────────
    # Build candidate signin URLs: derive from login page URL first, then fallbacks
    login_dir = re.sub(r"/[^/]+$", "", login_url_used)  # directory of login page
    signin_candidates = []
    for sp in ["/signin", "/signmein", "/login"]:
        signin_candidates.append(login_dir + sp)   # same directory
    for sp in _SIGNIN_PATHS:
        signin_candidates.append(base + sp)
    # Deduplicate
    seen_sp = set()
    signin_candidates = [x for x in signin_candidates if not (x in seen_sp or seen_sp.add(x))]

    logged_sess = None
    login_resp_text = ""
    for sp_url in signin_candidates:
        try:
            r2 = sess.post(
                sp_url, data=post_data, timeout=12, allow_redirects=True, verify=False,
                headers={"Referer": login_url_used},
            )
            if r2.status_code in (200, 201, 302) and not _univ_is_login_page(r2.url, r2.text):
                logged_sess = sess
                login_resp_text = r2.text
                print(f"[{pid}] ✅ Signed in via {sp_url} → {r2.url}")
                break
        except Exception:
            continue

    if not logged_sess:
        print(f"[{pid}] ❌ Login failed — all signin paths exhausted")
        return None, None, None, None

    # ── Step 3b: Validate session by probing the original URL (soft check) ──────
    # Only used as a hint — never hard-fails a successful login POST
    if url_hint:
        try:
            chk = logged_sess.get(url_hint, timeout=10, verify=False, allow_redirects=True)
            if _univ_is_login_page(chk.url, chk.text):
                print(f"[{pid}] ⚠️ Hint URL looks like login page after signin — proceeding anyway")
            elif len(chk.text) < 50:
                print(f"[{pid}] ⚠️ Hint page very short ({len(chk.text)}b) — proceeding anyway")
            else:
                print(f"[{pid}] ✅ Session validated via {url_hint} ({len(chk.text)}b)")
                login_resp_text = login_resp_text or chk.text
        except Exception as e:
            print(f"[{pid}] ⚠️ Session validation skipped: {e}")

    # ── Step 4: Extract session token ────────────────────────────────────────
    token = _univ_extract_token(login_resp_text)
    if not token:
        # Probe dashboard pages — include hint URL itself
        dash_candidates = []
        if url_hint:
            dash_candidates.append(url_hint)
        hint_base2 = _extract_panel_base_url(url_hint) if url_hint else base
        for dp in _DASHBOARD_PATHS:
            if hint_base2 and hint_base2 != base:
                dash_candidates.append(hint_base2 + dp)
            dash_candidates.append(base + dp)
        for dash_url in dash_candidates:
            try:
                rd = logged_sess.get(dash_url, timeout=10, verify=False)
                token = _univ_extract_token(rd.text)
                if token:
                    print(f"[{pid}] Token found via {dash_url}")
                    break
            except Exception:
                continue
    print(f"[{pid}] Token: {'found (' + token[:8] + '...)' if token else 'empty (cookie-based)'}")

    # ── Step 5: Probe data endpoints ─────────────────────────────────────────
    # For html_scrape panels, skip all probing — data_path IS the page URL
    if panel.get("engine") == "html_scrape":
        dp = panel.get("data_path", url_hint or base)
        print(f"[{pid}] html_scrape panel — skipping probe, using page: {dp}")
        return logged_sess, token, "html_scrape", dp

    today = time.strftime("%Y-%m-%d")
    hint_base3 = _extract_panel_base_url(url_hint) if url_hint else None

    # Step 5a: Scrape the dashboard/hint page HTML to extract AJAX data URLs
    # Many panels embed the data URL directly in their JS (ajax: "/path/to/data.php")
    scraped_ep_candidates = []
    pages_to_scrape = []
    if url_hint:
        pages_to_scrape.append(url_hint)
    for dp in _DASHBOARD_PATHS:
        if hint_base3 and hint_base3 != base:
            pages_to_scrape.append(hint_base3 + dp)
        pages_to_scrape.append(base + dp)
    for scrape_url in pages_to_scrape[:8]:  # limit to avoid slow startup
        try:
            rp = logged_sess.get(scrape_url, timeout=10, verify=False)
            if rp.status_code != 200:
                continue
            pg = rp.text
            # Look for ajax/url patterns pointing to data PHP files
            for m in re.finditer(
                r'''["']([^"']*(?:data_sms|dt_reports|dt_sms|cdr|reports)[^"']*\.php)['"''',
                pg, re.IGNORECASE
            ):
                raw = m.group(1)
                # Convert to absolute URL
                if raw.startswith("http"):
                    abs_ep = raw
                elif raw.startswith("/"):
                    parsed_host = re.match(r"(https?://[^/]+)", scrape_url)
                    abs_ep = (parsed_host.group(1) if parsed_host else base) + raw
                else:
                    abs_ep = base + "/" + raw.lstrip("/")
                style = "xisora" if "dt_reports" in raw or "dt_sms" in raw else "ints"
                eng = "xisora" if style == "xisora" else "ints_smscdr"
                scraped_ep_candidates.append((abs_ep, raw, style, eng))
                print(f"[{pid}] 🔎 Scraped data URL from {scrape_url}: {raw}")
        except Exception:
            continue

    # Step 5b: Build known-path candidates (hint_base first, then base)
    known_ep_candidates = []
    for ep_path, style, eng_name in _DATA_ENDPOINTS:
        if hint_base3 and hint_base3 != base:
            known_ep_candidates.append((hint_base3 + ep_path, ep_path, style, eng_name))
        known_ep_candidates.append((base + ep_path, ep_path, style, eng_name))

    # Combine: scraped first (highest confidence), then known paths
    all_ep_candidates = scraped_ep_candidates + known_ep_candidates

    for full_ep, ep_path, style, eng_name in all_ep_candidates:
        try:
            test_url = _univ_build_url(full_ep, token, today, style)
            rr = logged_sess.get(
                test_url, timeout=10, verify=False,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            body = rr.text.strip()
            print(f"[{pid}] Probe {full_ep} → HTTP {rr.status_code}, body={len(body)}b, starts={body[:30]!r}")
            if rr.status_code == 200 and body and not body.startswith("<"):
                try:
                    data = json.loads(body)
                    if "aaData" in data:
                        resolved_path = ep_path if full_ep.startswith(base) else ("/" + ep_path.lstrip("/"))
                        print(f"[{pid}] ✅ Data endpoint: {full_ep} (engine={eng_name})")
                        if hint_base3 and hint_base3 != base and full_ep.startswith(hint_base3):
                            panel["base_url"] = hint_base3
                        return logged_sess, token, eng_name, resolved_path
                except Exception:
                    pass
        except Exception as probe_err:
            print(f"[{pid}] Probe error {full_ep}: {probe_err}")
            continue

    # ── Step 5c: HTML table scraping fallback ────────────────────────────────
    # For panels that render data directly in HTML (no AJAX JSON endpoint)
    html_scrape_url = None
    html_pages_to_try = []
    if url_hint:
        html_pages_to_try.append(url_hint)
    for dp in _DASHBOARD_PATHS:
        if hint_base3 and hint_base3 != base:
            html_pages_to_try.append(hint_base3 + dp)
        html_pages_to_try.append(base + dp)
    for pg_url in html_pages_to_try[:6]:
        try:
            rp = logged_sess.get(pg_url, timeout=10, verify=False)
            if rp.status_code != 200 or _univ_is_login_page(rp.url, rp.text):
                continue
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(rp.text, "lxml")
            tables = soup.find_all("table")
            for tbl in tables:
                rows = tbl.find_all("tr")
                if len(rows) >= 3:  # at least header + 2 data rows
                    print(f"[{pid}] 🔎 HTML scraping fallback: found table with {len(rows)} rows at {pg_url}")
                    html_scrape_url = pg_url
                    break
            if html_scrape_url:
                break
        except Exception:
            continue
    if html_scrape_url:
        return logged_sess, token, "html_scrape", html_scrape_url

    # Login succeeded but no endpoint matched → return with INTS default
    print(f"[{pid}] ⚠️ Login OK but no data endpoint found — using default")
    return logged_sess, token, "ints_smscdr", "/agent/res/data_smscdr.php"


def _universal_fetch(panel):
    """Fetch OTPs from any panel using the universal engine."""
    pid = panel["id"]
    base = panel["base_url"].rstrip("/")
    engine = panel.get("engine", "ints_smscdr")
    # IVA SMS has its own fetcher
    if engine == "iva_sms":
        return _iva_fetch(panel)
    # API Key panels have their own fetcher
    if engine == "api_key":
        return _api_key_fetch(panel)
    data_path = panel.get("data_path", "/agent/res/data_smscdr.php")
    style = "xisora" if engine == "xisora" else "ints"
    found = {}

    with _get_dp_lock(pid):
        sd = _dynamic_sessions.get(pid, {})
        if not sd.get("session"):
            sess, tok, det_eng, det_path = _universal_login(panel)
            if not sess:
                _record_error(pid)
                return found
            if det_eng and engine != "html_scrape" and (det_eng != engine or det_path != data_path):
                panel["engine"] = det_eng
                panel["data_path"] = det_path
                engine = det_eng
                data_path = det_path
                style = "xisora" if engine == "xisora" else "ints"
                save_dynamic_panels()
            _dynamic_sessions[pid] = {"session": sess, "token": tok}
            sd = _dynamic_sessions[pid]

        sess = sd["session"]
        token = sd.get("token", "")
        today = time.strftime("%Y-%m-%d")
        full_ep = base + data_path
        hdrs = {"X-Requested-With": "XMLHttpRequest"}

        def _do_get():
            return sess.get(
                _univ_build_url(full_ep, token, today, style),
                headers=hdrs, timeout=15, verify=False,
            )

        # ── HTML scraping engine ──────────────────────────────────────────────
        if engine == "html_scrape":
            page_url = data_path  # data_path is the full page URL for this engine
            try:
                rp = sess.get(page_url, timeout=15, verify=False)
                if rp.status_code != 200 or _univ_is_login_page(rp.url, rp.text):
                    print(f"[{pid}] Session expired (html_scrape) — re-login")
                    _dynamic_sessions[pid] = {}
                    sess2, tok2, det_eng, det_path = _universal_login(panel)
                    if not sess2:
                        _record_error(pid)
                        return found
                    if det_eng and det_eng != "html_scrape":
                        panel["engine"] = det_eng
                        panel["data_path"] = det_path
                        engine = det_eng
                        data_path = det_path
                        save_dynamic_panels()
                    _dynamic_sessions[pid] = {"session": sess2, "token": tok2}
                    rp = sess2.get(page_url, timeout=15, verify=False)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(rp.text, "lxml")
                # Find header row to map column positions
                tbl = None
                for t in soup.find_all("table"):
                    if len(t.find_all("tr")) >= 3:
                        tbl = t
                        break
                if not tbl:
                    _record_fetch(pid, 0)
                    return found
                headers = [th.get_text(strip=True).lower()
                           for th in (tbl.find("tr").find_all(["th", "td"]))]
                # Heuristic column detection
                num_col = next((i for i, h in enumerate(headers)
                                if any(w in h for w in ("number", "msisdn", "phone", "mobile", "num"))), None)
                txt_col = next((i for i, h in enumerate(headers)
                                if any(w in h for w in ("message", "sms", "text", "body", "msg"))), None)
                svc_col = next((i for i, h in enumerate(headers)
                                if any(w in h for w in ("service", "route", "dest", "sender"))), None)
                row_count = 0
                for tr in tbl.find_all("tr")[1:]:  # skip header
                    cells = tr.find_all(["td", "th"])
                    if not cells:
                        continue
                    row_count += 1
                    number = cells[num_col].get_text(strip=True) if num_col is not None and num_col < len(cells) else ""
                    sms_txt = cells[txt_col].get_text(strip=True) if txt_col is not None and txt_col < len(cells) else ""
                    service = cells[svc_col].get_text(strip=True) if svc_col is not None and svc_col < len(cells) else ""
                    # Fallback: scan all cells for phone-like pattern and OTP
                    if not number:
                        for c in cells:
                            ct = c.get_text(strip=True)
                            if re.match(r"^\+?\d{7,15}$", ct):
                                number = ct
                                break
                    if not sms_txt:
                        for c in cells:
                            ct = c.get_text(strip=True)
                            if len(ct) > 10 and re.search(r"\d{4,8}", ct):
                                sms_txt = ct
                                break
                    otp = extract_otp_from_sms(sms_txt)
                    if number and otp:
                        key = f"{number}:{sms_txt}"
                        found[key] = (number, otp, sms_txt, service)
                _record_fetch(pid, row_count)
                if found:
                    print(f"[{pid}] ✅ HTML-scraped {row_count} rows, {len(found)} OTPs")
            except Exception as e:
                print(f"[{pid}] HTML scrape error: {e}")
                _record_error(pid)
                _dynamic_sessions[pid] = {}
            return found

        # ── JSON / AJAX engine (default) ──────────────────────────────────────
        try:
            r = _do_get()
            body = r.text.strip()
            if r.status_code != 200 or not body or body.startswith("<") or "Direct Script" in body:
                print(f"[{pid}] Session expired — re-login")
                _dynamic_sessions[pid] = {}
                sess2, tok2, det_eng, det_path = _universal_login(panel)
                if not sess2:
                    _record_error(pid)
                    return found
                if det_eng:
                    panel["engine"] = det_eng
                    panel["data_path"] = det_path
                    engine = det_eng
                    data_path = det_path
                    style = "xisora" if engine == "xisora" else "ints"
                    full_ep = base + data_path
                    save_dynamic_panels()
                _dynamic_sessions[pid] = {"session": sess2, "token": tok2}
                sd = _dynamic_sessions[pid]
                sess = sess2
                token = tok2
                r = _do_get()
                body = r.text.strip()

            rows = json.loads(body).get("aaData", [])
            for row in rows:
                parsed = _univ_parse_row(row, engine)
                if not parsed:
                    continue
                number, service, sms_txt = parsed
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch(pid, len(rows))
            if found:
                print(f"[{pid}] ✅ Fetched {len(rows)} rows, {len(found)} OTPs")
        except Exception as e:
            print(f"[{pid}] Fetch error: {e}")
            _record_error(pid)
            _dynamic_sessions[pid] = {}
    return found


def _univ_parse_row(row, engine):
    """Parse one aaData row. Returns (number, service, sms_text) or None."""
    try:
        if not row:
            return None
        cells = [str(c).strip() for c in row]
        # Standard INTS layout: [date, range, number, cli/service, client, sms, ...]
        # extract_otp_from_sms already enforces real-SMS validation (≥4 alpha chars)
        if len(cells) > 5:
            number  = cells[2]
            service = cells[3]
            sms_txt = cells[5]
            if number and extract_otp_from_sms(sms_txt):
                return number, service, sms_txt
        # Shorter rows (some panels only have 5 cols)
        if len(cells) > 4:
            number  = cells[2]
            service = cells[3]
            sms_txt = cells[4]
            if number and extract_otp_from_sms(sms_txt):
                return number, service, sms_txt
    except Exception:
        pass
    return None


# ── API Key Panel Engine ───────────────────────────────────────────────────────

_API_KEY_ENDPOINTS = [
    "/api/sms",
    "/api/messages",
    "/api/received",
    "/api/sms/received",
    "/api/v1/sms",
    "/api/v1/messages",
    "/api/inbox",
    "/api/sms/list",
    "/api/data",
    "/sms",
    "/api/otp",
]

_API_KEY_PARAMS = ["api_key", "token", "key", "apikey", "access_token"]


def _api_key_test(base_url, api_key):
    """Try common API endpoints with key. Returns (path, param_style) or (None, None).
    param_style: 'bearer', 'api_key=xxx', 'token=xxx', etc.
    """
    base = base_url.rstrip("/")
    hdrs = {"Accept": "application/json", "User-Agent": _UA}
    for path in _API_KEY_ENDPOINTS:
        # Try query param variants
        for param in _API_KEY_PARAMS:
            try:
                r = requests.get(
                    f"{base}{path}?{param}={api_key}",
                    timeout=8, verify=False, headers=hdrs,
                )
                if r.status_code == 200:
                    try:
                        data = r.json()
                        if isinstance(data, list):
                            print(f"[APIKEY-TEST] ✅ {path}?{param}= → array")
                            return path, param
                        if isinstance(data, dict):
                            for dk in ("data", "sms", "messages", "records", "result", "items", "list"):
                                if dk in data and isinstance(data[dk], list):
                                    print(f"[APIKEY-TEST] ✅ {path}?{param}= → dict.{dk}")
                                    return path, f"{param}|resp={dk}"
                            if any(k in data for k in ("status", "success", "ok", "error")):
                                print(f"[APIKEY-TEST] ✅ {path}?{param}= → status obj")
                                return path, param
                    except Exception:
                        pass
            except Exception:
                continue
        # Try Authorization: Bearer header
        try:
            r = requests.get(
                f"{base}{path}", timeout=8, verify=False,
                headers={**hdrs, "Authorization": f"Bearer {api_key}"},
            )
            if r.status_code == 200:
                try:
                    data = r.json()
                    if isinstance(data, (list, dict)):
                        print(f"[APIKEY-TEST] ✅ {path} → Bearer header")
                        return path, "bearer"
                except Exception:
                    pass
        except Exception:
            continue
    return None, None


def _api_key_fetch(panel):
    """Fetch OTPs from an API-key authenticated panel."""
    pid      = panel["id"]
    base     = panel["base_url"].rstrip("/")
    api_key  = panel.get("api_key", "")
    data_path = panel.get("data_path", "/api/sms")
    param_style = panel.get("api_key_param", "api_key")
    found = {}
    try:
        hdrs = {"Accept": "application/json", "User-Agent": _UA}
        if param_style == "bearer":
            url = f"{base}{data_path}"
            hdrs["Authorization"] = f"Bearer {api_key}"
        elif "|resp=" in param_style:
            pname = param_style.split("|resp=")[0]
            url = f"{base}{data_path}?{pname}={api_key}"
        else:
            url = f"{base}{data_path}?{param_style}={api_key}"

        r = requests.get(url, timeout=15, verify=False, headers=hdrs)
        if r.status_code != 200:
            print(f"[{pid}] API key fetch HTTP {r.status_code}")
            _record_error(pid)
            return found

        raw = r.json()
        rows = []
        if isinstance(raw, list):
            rows = raw
        elif isinstance(raw, dict):
            resp_key = param_style.split("|resp=")[1] if "|resp=" in param_style else None
            if resp_key and resp_key in raw:
                rows = raw[resp_key]
            else:
                for dk in ("data", "otps", "sms", "messages", "records", "result", "items", "list"):
                    val = raw.get(dk)
                    if isinstance(val, list):
                        rows = val
                        break
                    elif isinstance(val, dict):
                        # Handle nested format e.g. fastxotps: {data: {otps: [...]}}
                        for inner in ("otps", "data", "sms", "messages", "records", "result", "items", "list"):
                            inner_val = val.get(inner)
                            if isinstance(inner_val, list):
                                rows = inner_val
                                break
                        if rows:
                            break

        for row in rows:
            number = sms_txt = service = ""
            if isinstance(row, dict):
                number  = str(row.get("number") or row.get("phone") or row.get("msisdn") or
                              row.get("from") or row.get("sender") or row.get("to") or "").strip()
                sms_txt = str(row.get("message") or row.get("sms") or row.get("text") or
                              row.get("body") or row.get("content") or "").strip()
                service = str(row.get("service") or row.get("sender") or row.get("source") or "").strip()
            elif isinstance(row, list):
                if len(row) > 2: number  = str(row[2]).strip()
                if len(row) > 5: sms_txt = str(row[5]).strip()
                elif len(row) > 3: sms_txt = str(row[3]).strip()
                if len(row) > 3: service = str(row[3]).strip()
            # Auto-detect service from SMS content when panel doesn't provide it
            if not service and sms_txt:
                service = _detect_service_from_sms(sms_txt)
            otp = extract_otp_from_sms(sms_txt)
            if number and otp:
                key = f"{number}:{sms_txt}"
                found[key] = (number, otp, sms_txt, service)

        _record_fetch(pid, len(rows))
        if found:
            print(f"[{pid}] ✅ API key: {len(rows)} rows, {len(found)} OTPs")
    except Exception as e:
        print(f"[{pid}] API key fetch error: {e}")
        _record_error(pid)
    return found


# ─────────────────────────────────────────────────────────────────────────────

# ── FastXOTPs (fastxotps.com) helpers ─────────────────────────────────────────
FASTX_BASE = "https://2eee7.com/@Access/@Bot/2eee7/@public"
FASTX_API_KEY = "MURAD_979BB07726A593010D1BA4A2"

# ── V3 Panel — Voltex SMS (api.2oo9.cloud) ────────────────────────────────────
V3_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
V3_API_KEY = "M1412DHZM68"

# ── Stex SMS Panel (api.2oo9.cloud) ───────────────────────────────────────────
STEX_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
STEX_API_KEY = "M5RJL9BUG2M"

# ── MK Panel (mkonlinesms.com) ────────────────────────────────────────────────
MK_BASE_URL = "https://mkonlinesms.com/@Telegram/@Bot/3oo10/@public/api"
MK_API_KEY = "MK-MAHADE_E73D4700555C5B02F77F5C4B"

# ── V2 Panel Registry (for toggle system) ─────────────────────────────────────
_V2_PANELS_REGISTRY = [
    {"id": "fastx",  "name": "FastX SMS",  "base_url": None,          "api_key": None},
    {"id": "stex",   "name": "Stex SMS",   "base_url": STEX_BASE_URL, "api_key": STEX_API_KEY},
    {"id": "voltex", "name": "Voltex SMS", "base_url": V3_BASE_URL,   "api_key": V3_API_KEY},
    {"id": "mk",     "name": "MK Panel",   "base_url": MK_BASE_URL,   "api_key": MK_API_KEY},
]

# Apply any admin-overridden API keys saved in group_settings
_apply_saved_api_keys()

# Keywords to detect synthetic services from OTP message content
_FASTX_MSG_SERVICE_KEYWORDS = {
    "INSTAGRAM": ["instagram"],
    "TIKTOK":    ["tiktok", "tik tok"],
    "SNAPCHAT":  ["snapchat"],
    "TWITTER":   ["twitter", "x.com"],
    "GOOGLE":    ["google"],
    "YOUTUBE":   ["youtube"],
    "LINKEDIN":  ["linkedin"],
    "AMAZON":    ["amazon"],
}


def _fastx_detect_extra_services(base_services):
    """
    Inject synthetic services (INSTAGRAM, etc.) derived from parent carrier ranges.
    INSTAGRAM inherits all FACEBOOK ranges since they share the same carrier routes.
    Also scans recent OTPs for any extra ranges not already covered.
    Returns the enriched services list.
    """
    # Map synthetic service -> which liveaccess services share its carrier routes
    _carrier_parents = {
        "INSTAGRAM": {"FACEBOOK", "FB"},
        "TIKTOK":    {"FACEBOOK", "TWILIO"},
        "SNAPCHAT":  {"TWILIO"},
    }
    # Preferred insertion position (insert after parent)
    _insert_after = {
        "INSTAGRAM": {"FACEBOOK", "FB"},
        "TIKTOK":    {"FACEBOOK", "TWILIO"},
        "SNAPCHAT":  {"TWILIO"},
    }

    existing_sids = {s.get("sid", "").upper() for s in base_services}
    now_ms = int(time.time() * 1000)

    # Build a flat list of (prefix, range_str) from all base service ranges
    all_prefixes = []
    for svc in base_services:
        for rng in svc.get("ranges", []):
            prefix = rng.rstrip("X")
            all_prefixes.append((prefix, rng))
    all_prefixes.sort(key=lambda x: -len(x[0]))

    # Step 1: seed synthetic ranges from parent carrier's liveaccess ranges
    synthetic: dict = {}  # sid -> {ranges: set, last_at: int}
    for sid, parents in _carrier_parents.items():
        if sid.upper() in existing_sids:
            continue  # already in liveaccess, handle via merge below
        for svc in base_services:
            if svc.get("sid", "").upper() in parents:
                parent_ranges = set(svc.get("ranges", []))
                if parent_ranges:
                    entry = synthetic.setdefault(sid, {"ranges": set(), "last_at": 0})
                    entry["ranges"] |= parent_ranges
                    ts = svc.get("last_at", now_ms)
                    if ts > entry["last_at"]:
                        entry["last_at"] = ts

    # Step 2: also scan recent OTPs for any extra ranges not covered by parent
    try:
        r = requests.get(f"{FASTX_BASE}/api/success-otp-info",
                         params={"api_key": FASTX_API_KEY},
                         timeout=10, verify=False)
        if r.status_code == 200:
            d = r.json()
            otps = d.get("data", {}).get("otps", d.get("otps", []))
            if isinstance(otps, list):
                for otp in otps:
                    msg = (otp.get("message") or "").lower()
                    num = str(otp.get("number") or "").strip().lstrip("+")
                    if not num:
                        continue
                    ts = otp.get("time", now_ms)
                    for sid, keywords in _FASTX_MSG_SERVICE_KEYWORDS.items():
                        if not any(kw in msg for kw in keywords):
                            continue
                        matched_rng = None
                        for prefix, rng in all_prefixes:
                            if num.startswith(prefix):
                                matched_rng = rng
                                break
                        if not matched_rng and len(num) >= 7:
                            plen = max(4, min(9, len(num) - 6))
                            matched_rng = num[:plen] + "XXX"
                        if matched_rng:
                            entry = synthetic.setdefault(sid, {"ranges": set(), "last_at": 0})
                            entry["ranges"].add(matched_rng)
                            if ts > entry["last_at"]:
                                entry["last_at"] = ts
    except Exception as e:
        print(f"[FASTX] detect_extra_services OTP scan error: {e}")

    if not synthetic:
        return base_services

    enriched = list(base_services)
    for sid, info in synthetic.items():
        sid_upper = sid.upper()
        merged = False
        for svc in enriched:
            if svc.get("sid", "").upper() == sid_upper:
                existing_ranges = set(svc.get("ranges", []))
                new_ranges = info["ranges"] - existing_ranges
                if new_ranges:
                    svc["ranges"] = sorted(existing_ranges | info["ranges"])
                    print(f"[FASTX] Merged {len(new_ranges)} range(s) into existing {sid!r}: {sorted(new_ranges)}")
                merged = True
                break
        if not merged:
            new_svc = {
                "sid": sid,
                "ranges": sorted(info["ranges"]),
                "last_at": info["last_at"],
            }
            parents = _insert_after.get(sid, set())
            insert_idx = len(enriched)
            for i, svc in enumerate(enriched):
                if svc.get("sid", "").upper() in parents:
                    insert_idx = i + 1
                    break
            enriched.insert(insert_idx, new_svc)
            print(f"[FASTX] Injected synthetic {sid!r} with {len(new_svc['ranges'])} ranges: {new_svc['ranges']}")

    return enriched


def _fastx_liveaccess():
    """Return list of live services [{sid, ranges, last_at}] from fastxotps,
    enriched with synthetic services (INSTAGRAM, etc.) detected from recent OTPs."""
    try:
        r = requests.get(f"{FASTX_BASE}/api/liveaccess",
                         params={"api_key": FASTX_API_KEY},
                         timeout=15, verify=False)
        if r.status_code == 200:
            d = r.json()
            status_val = d.get("status", "ok")
            status_ok = (status_val in ("ok", "success", "200", True, 1)) or bool(status_val)
            base = d.get("services") or d.get("data") or d.get("result") or []
            if isinstance(base, dict):
                base = base.get("services") or base.get("data") or []
            if isinstance(base, list) and (base or status_ok):
                return _fastx_detect_extra_services(base)
        print(f"[FASTX] liveaccess HTTP {r.status_code}")
    except Exception as e:
        print(f"[FASTX] liveaccess error: {e}")
    return []


def _fastx_getnum(prefix):
    """Allocate a number for the given range prefix. Returns full_number str or None."""
    try:
        r = requests.post(f"{FASTX_BASE}/api/getnum",
                          params={"api_key": FASTX_API_KEY},
                          data={"prefix": prefix},
                          timeout=15, verify=False)
        if r.status_code == 200:
            resp = r.json()
            d = resp.get("data") or {}
            num = d.get("full_number") or d.get("no_plus_number")
            if num:
                return num if num.startswith("+") else "+" + num
            print(f"[FASTX] getnum no number in response: {resp}")
        else:
            print(f"[FASTX] getnum HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[FASTX] getnum error: {e}")
    return None


# ── Cloud Panel Generic Helpers (Stex SMS / Voltex SMS) ───────────────────────

def _cloud_liveaccess(base_url, api_key):
    """Get live services from a 2oo9.cloud-style panel. Returns [{sid, ranges, last_at}]."""
    try:
        headers = {"mauthapi": api_key}
        r = requests.get(f"{base_url}/liveaccess",
                         headers=headers, timeout=15, verify=False)
        if r.status_code == 200:
            d = r.json()
            meta = d.get("meta") or {}
            if meta.get("status") == "ok" or meta.get("code") == 200:
                data = d.get("data") or {}
                svcs = data.get("services") or data.get("data") or []
                if isinstance(svcs, list) and svcs:
                    return svcs
    except Exception as e:
        print(f"[CLOUD] liveaccess error {base_url}: {e}")
    return []


def _cloud_getnum(base_url, api_key, prefix, sid=None):
    """Allocate a number from a 2oo9.cloud-style panel. Returns number string or None.
    API requires: mauthapi header + JSON body {"rid": "<digits>", "sid": "<service>"}.
    """
    try:
        headers = {"mauthapi": api_key, "Content-Type": "application/json"}
        import re as _re
        rid = _re.sub(r'X+$', '', str(prefix).strip())
        # Use known sid first; fall back to common service names
        sid_candidates = []
        if sid:
            sid_candidates.append(sid)
        sid_candidates += ["Facebook", "WhatsApp", "Google", "Telegram", "Instagram"]
        for sid_try in sid_candidates:
            try:
                import json as _json
                r = requests.post(f"{base_url}/getnum",
                                  headers=headers,
                                  data=_json.dumps({"rid": rid, "sid": sid_try}),
                                  timeout=15, verify=False)
                if r.status_code == 200:
                    d = r.json()
                    meta = d.get("meta") or {}
                    if meta.get("code") == 200 or meta.get("status") == "ok":
                        data = d.get("data") or {}
                        num = (data.get("full_number") or data.get("no_plus_number") or
                               data.get("number") or data.get("phone"))
                        if num:
                            s = str(num).strip()
                            return s if s.startswith("+") else "+" + s
            except Exception:
                continue
    except Exception as e:
        print(f"[CLOUD] getnum error {base_url}: {e}")
    return None


def _cloud_fetch_otps_sse(base_url, api_key, seen_keys, panel_name="CLOUD"):
    """Read a short burst from the SSE /sms stream and return new OTP events.
    Returns dict key->(number,otp,sms_txt,service) for events not in seen_keys.
    """
    found = {}
    try:
        import json as _json
        headers = {
            "mauthapi": api_key,
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }
        r = requests.get(f"{base_url}/sms", headers=headers,
                         stream=True, timeout=8, verify=False)
        if r.status_code != 200:
            return found
        buf = ""
        for raw in r.iter_lines(chunk_size=256, decode_unicode=True):
            if raw is None:
                continue
            line = raw.strip()
            if line.startswith("data:"):
                payload = line[5:].strip()
                try:
                    obj = _json.loads(payload)
                    # Nested under data key or direct
                    inner = obj.get("data") if isinstance(obj, dict) else None
                    if isinstance(inner, dict):
                        obj = inner
                    number = str(obj.get("number") or obj.get("phone") or
                                 obj.get("no") or "").strip()
                    sms_txt = str(obj.get("message") or obj.get("sms") or
                                  obj.get("text") or obj.get("body") or "").strip()
                    service = str(obj.get("service") or obj.get("app") or
                                  obj.get("sid") or "").strip()
                    if number and sms_txt:
                        otp = extract_otp_from_sms(sms_txt)
                        if otp:
                            key = f"{number}:{sms_txt}"
                            if key not in seen_keys:
                                found[key] = (number, otp, sms_txt, service)
                except Exception:
                    pass
            # Stop after collecting some events or hitting a retry line
            if len(found) >= 20:
                break
        r.close()
    except Exception as e:
        pass
    return found


def _cloud_fetch_otps(base_url, api_key, panel_name="CLOUD"):
    """Wrapper kept for backward compat — returns dict without seen-key dedup."""
    return _cloud_fetch_otps_sse(base_url, api_key, set(), panel_name)


# ── MK Panel helpers (uses Authorization: Bearer instead of mauthapi) ─────────

def _mk_headers():
    return {"Authorization": f"Bearer {MK_API_KEY}", "Accept": "application/json"}


def _mk_liveaccess():
    """Get live services from MK Panel. Returns [{sid, ranges, last_at}]."""
    try:
        r = requests.get(f"{MK_BASE_URL}/liveaccess",
                         headers=_mk_headers(), timeout=15, verify=False)
        if r.status_code == 200:
            d = r.json()
            # Format 1: {"status":"ok","services":[...]}
            svcs = d.get("services")
            if isinstance(svcs, list) and svcs:
                return svcs
            # Format 2: {"meta":{...},"data":{"services":[...]}}
            data = d.get("data") or {}
            svcs = data.get("services") or data.get("data") or []
            if isinstance(svcs, list) and svcs:
                return svcs
        else:
            print(f"[MK] liveaccess HTTP {r.status_code}")
    except Exception as e:
        print(f"[MK] liveaccess error: {e}")
    return []


def _mk_getnum(prefix, sid=None):
    """Allocate a number from MK Panel using Bearer auth."""
    import re as _re, json as _json
    try:
        rid = _re.sub(r'X+$', '', str(prefix).strip())
        candidates = ([sid] if sid else []) + ["WhatsApp", "Facebook", "Google", "Telegram", "Instagram"]
        for sid_try in candidates:
            try:
                r = requests.post(f"{MK_BASE_URL}/getnum",
                                  headers={**_mk_headers(), "Content-Type": "application/json"},
                                  data=_json.dumps({"rid": rid, "sid": sid_try}),
                                  timeout=15, verify=False)
                if r.status_code == 200:
                    d = r.json()
                    meta = d.get("meta") or {}
                    if meta.get("code") == 200 or meta.get("status") == "ok" or d.get("status") == "ok":
                        data = d.get("data") or {}
                        num = (data.get("full_number") or data.get("no_plus_number") or
                               data.get("number") or data.get("phone"))
                        if num:
                            s = str(num).strip()
                            return s if s.startswith("+") else "+" + s
            except Exception:
                continue
    except Exception as e:
        print(f"[MK] getnum error: {e}")
    return None


def _mk_fetch_otps():
    """Poll MK Panel /success-otp-info with Bearer auth. Returns {key:(num,otp,sms,svc)}."""
    found = {}
    try:
        r = requests.get(f"{MK_BASE_URL}/success-otp-info",
                         headers=_mk_headers(), timeout=15, verify=False)
        if r.status_code == 200:
            raw = r.json()
            data = raw.get("data") or {}
            rows = []
            for k in ("otps", "sms", "messages", "records", "result", "items"):
                v = data.get(k) if isinstance(data, dict) else None
                if isinstance(v, list) and v:
                    rows = v
                    break
            if not rows and isinstance(data, list):
                rows = data
            if not rows:
                rows = _cloud_extract_rows(raw)
            found = _cloud_parse_otp_rows(rows)
            if found:
                print(f"[MK] /success-otp-info -> {len(found)} OTP(s)")
        else:
            print(f"[MK] /success-otp-info HTTP {r.status_code}")
    except Exception as e:
        print(f"[MK] fetch_otps error: {e}")
    return found


# ── V2 Active Panel Router ─────────────────────────────────────────────────────

def _get_v2_active_panel_id():
    return _group_settings.get("v2_active_panel", "fastx")


def _v2_active_liveaccess():
    """Get live services from the currently active V2 panel."""
    pid = _get_v2_active_panel_id()
    if pid == "fastx":
        return _fastx_liveaccess()
    elif pid == "stex":
        return _cloud_liveaccess(STEX_BASE_URL, STEX_API_KEY)
    elif pid == "voltex":
        return _cloud_liveaccess(V3_BASE_URL, V3_API_KEY)
    elif pid == "mk":
        return _mk_liveaccess()
    return _fastx_liveaccess()


def _v2_active_getnum(prefix, sid=None):
    """Allocate a number from the currently active V2 panel."""
    pid = _get_v2_active_panel_id()
    if pid == "fastx":
        return _fastx_getnum(prefix)
    elif pid == "stex":
        return _cloud_getnum(STEX_BASE_URL, STEX_API_KEY, prefix, sid=sid)
    elif pid == "voltex":
        return _cloud_getnum(V3_BASE_URL, V3_API_KEY, prefix, sid=sid)
    elif pid == "mk":
        return _mk_getnum(prefix, sid=sid)
    return _fastx_getnum(prefix)


def _fastx_fetch_otps_rest():
    """Fetch OTPs from FastX via REST API /api/otps endpoint."""
    found = {}
    try:
        r = requests.get(
            f"{FASTX_BASE}/api/success-otp-info",
            params={"api_key": FASTX_API_KEY},
            timeout=15, verify=False,
            headers={"Accept": "application/json", "User-Agent": _UA},
        )
        if r.status_code != 200:
            print(f"[FASTX-REST] HTTP {r.status_code}")
            return found
        raw = r.json()
        rows = []
        if isinstance(raw, list):
            rows = raw
        elif isinstance(raw, dict):
            for dk in ("data", "otps", "sms", "messages", "records", "result", "items", "list"):
                val = raw.get(dk)
                if isinstance(val, list):
                    rows = val
                    break
                elif isinstance(val, dict):
                    for inner in ("otps", "data", "sms", "messages", "records", "result"):
                        inner_val = val.get(inner)
                        if isinstance(inner_val, list):
                            rows = inner_val
                            break
                    if rows:
                        break
        for row in rows:
            if not isinstance(row, dict):
                continue
            number = str(row.get("number") or row.get("phone") or row.get("msisdn") or
                         row.get("from") or row.get("to") or "").strip()
            sms_txt = str(row.get("message") or row.get("sms") or row.get("text") or
                          row.get("body") or row.get("content") or "").strip()
            service = str(row.get("service") or row.get("app") or row.get("sender") or
                          row.get("source") or "").strip()
            if not service and sms_txt:
                service = _detect_service_from_sms(sms_txt)
            otp = extract_otp_from_sms(sms_txt)
            if number and otp:
                key = f"{number}:{sms_txt}"
                found[key] = (number, otp, sms_txt, service)
        if found:
            print(f"[FASTX-REST] ✅ {len(rows)} rows, {len(found)} OTPs found")
    except Exception as e:
        print(f"[FASTX-REST] error: {e}")
    return found


def _v2_active_fetch_otps():
    """Fetch OTPs from the currently active V2 panel."""
    pid = _get_v2_active_panel_id()
    if pid == "fastx":
        return _fastx_fetch_otps_rest()
    elif pid == "stex":
        return _cloud_fetch_otps(STEX_BASE_URL, STEX_API_KEY, "STEX")
    elif pid == "voltex":
        return _cloud_fetch_otps(V3_BASE_URL, V3_API_KEY, "VOLTEX")
    elif pid == "mk":
        return _mk_fetch_otps()
    return {}


def _v2_active_panel_name():
    pid = _get_v2_active_panel_id()
    for p in _V2_PANELS_REGISTRY:
        if p["id"] == pid:
            return p["name"]
    return "FastX SMS"


def _live_traffic_text():
    """Fetch and format live OTP traffic for WhatsApp, Facebook, Instagram, Telegram."""
    from collections import defaultdict

    now = time.time()
    panel_name = _v2_active_panel_name()
    pid = _get_v2_active_panel_id()

    TARGET_SVCS = {"WHATSAPP", "FACEBOOK", "INSTAGRAM", "TELEGRAM"}
    SVC_EMOJI = {
        "WHATSAPP":  "💬 WhatsApp",
        "FACEBOOK":  "📘 Facebook",
        "INSTAGRAM": "📸 Instagram",
        "TELEGRAM":  "✈️ Telegram",
    }
    SVC_ORDER = ["WHATSAPP", "FACEBOOK", "INSTAGRAM", "TELEGRAM"]

    # Fetch raw rows from active panel
    rows = []
    try:
        if pid == "fastx":
            r = requests.get(
                f"{FASTX_BASE}/api/success-otp-info",
                params={"api_key": FASTX_API_KEY},
                timeout=10, verify=False,
                headers={"Accept": "application/json"},
            )
            if r.status_code == 200:
                raw = r.json()
                if isinstance(raw, list):
                    rows = raw
                elif isinstance(raw, dict):
                    for dk in ("data", "otps", "sms", "messages", "records", "result", "items", "list"):
                        val = raw.get(dk)
                        if isinstance(val, list):
                            rows = val
                            break
                        elif isinstance(val, dict):
                            for inner_k in ("otps", "data", "sms", "messages"):
                                inner_val = val.get(inner_k)
                                if isinstance(inner_val, list):
                                    rows = inner_val
                                    break
                            if rows:
                                break
        else:
            if pid == "mk":
                r = requests.get(
                    f"{MK_BASE_URL}/success-otp-info",
                    headers=_mk_headers(),
                    timeout=10, verify=False,
                )
            else:
                base_url = STEX_BASE_URL if pid == "stex" else V3_BASE_URL
                api_key  = STEX_API_KEY  if pid == "stex" else V3_API_KEY
                r = requests.get(
                    f"{base_url}/success-otp",
                    headers={"mauthapi": api_key, "Accept": "application/json"},
                    timeout=10, verify=False,
                )
            if r.status_code == 200:
                rows = _cloud_extract_rows(r.json())
    except Exception as e:
        return f"❌ Error fetching traffic: {e}"

    if not rows:
        return (
            f"🔴 <b>LIVE TRAFFIC</b>  🔵 {panel_name}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ No recent traffic data from panel."
        )

    # Parse rows → group by service
    num_otp_map = {}  # (num_masked, otp_fmt, service) → {count, ago}

    for row in rows:
        if not isinstance(row, dict):
            continue
        number = str(
            row.get("number") or row.get("phone") or row.get("msisdn") or
            row.get("from") or row.get("to") or ""
        ).strip().lstrip("+")
        sms_txt = str(
            row.get("message") or row.get("sms") or row.get("text") or
            row.get("body") or row.get("content") or ""
        ).strip()
        service = str(
            row.get("service") or row.get("app") or row.get("sender") or
            row.get("source") or row.get("sid") or ""
        ).strip().upper()
        if not service and sms_txt:
            service = _detect_service_from_sms(sms_txt).upper()

        if service not in TARGET_SVCS:
            continue
        otp = extract_otp_from_sms(sms_txt)
        if not number or not otp:
            continue

        # Mask number: keep prefix + XXX
        num_clean = re.sub(r"\D", "", number)
        if len(num_clean) >= 8:
            plen = max(4, min(7, len(num_clean) - 6))
            num_masked = num_clean[:plen] + "XXX"
        else:
            num_masked = (number[:4] + "XXX") if len(number) > 4 else number

        # Format OTP with dash
        if len(otp) == 6:
            otp_fmt = f"{otp[:3]}-{otp[3:]}"
        elif len(otp) == 4:
            otp_fmt = f"{otp[:2]}-{otp[2:]}"
        else:
            otp_fmt = otp

        # Time ago
        ts_raw = (
            row.get("time") or row.get("timestamp") or
            row.get("created_at") or row.get("ts") or 0
        )
        try:
            ts_val = float(ts_raw)
            if ts_val > 1e12:
                ts_val /= 1000
            ago = int(now - ts_val)
        except Exception:
            ago = 0

        if ago < 60:
            time_str = f"{ago}s ago"
        elif ago < 3600:
            time_str = f"{ago // 60}m ago"
        else:
            time_str = f"{ago // 3600}h ago"

        key = (num_masked, otp_fmt, service)
        if key not in num_otp_map:
            num_otp_map[key] = {"count": 0, "time_str": time_str}
        num_otp_map[key]["count"] += 1
        num_otp_map[key]["time_str"] = time_str

    # Build per-service entry lists
    svc_entries = defaultdict(list)
    for (num_masked, otp_fmt, service), info in num_otp_map.items():
        cnt = info["count"]
        cnt_str = f" ({cnt}×)" if cnt > 1 else ""
        svc_entries[service].append(f"{num_masked}  {otp_fmt}{cnt_str}  {info['time_str']}")

    # ── Fetch live console ranges from liveaccess ────────────────────────────
    _live_ranges = {}   # sid_upper -> [range1, range2, ...]
    try:
        _la_svcs = _v2_active_liveaccess()
        for _la in _la_svcs:
            _sid = str(_la.get("sid") or _la.get("service") or _la.get("name") or "").upper()
            _rngs = _la.get("ranges") or []
            if _sid and _rngs:
                _live_ranges[_sid] = list(_rngs)
        # Instagram shares Facebook ranges
        if "INSTAGRAM" not in _live_ranges and "FACEBOOK" in _live_ranges:
            _live_ranges["INSTAGRAM"] = _live_ranges["FACEBOOK"]
    except Exception as _le:
        print(f"[LIVE-TRAFFIC] liveaccess error: {_le}")

    # ── Compose message ───────────────────────────────────────────────────────
    ts_now = time.strftime("%H:%M:%S")
    lines = [f"🔴 <b>LIVE TRAFFIC</b>  🔵 {panel_name}"]
    has_any = False
    for svc in SVC_ORDER:
        entries = svc_entries.get(svc)
        ranges = _live_ranges.get(svc) or _live_ranges.get(svc.replace("WHATSAPP", "WA")) or []
        if not entries and not ranges:
            continue
        has_any = True
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"<b>{SVC_EMOJI[svc]}</b>")
        # Show live ranges first
        if ranges:
            _rng_codes = "  ".join(f"<code>{r}</code>" for r in ranges[:12])
            lines.append(f"📡 <i>Ranges:</i> {_rng_codes}")
        # Then show recent OTPs
        if entries:
            for entry in entries[:8]:
                lines.append(entry)
        elif ranges:
            lines.append("  ⏳ No recent OTPs yet")

    if not has_any:
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚠️ No WA / FB / IG / TG traffic or ranges from panel.")

    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🔄 {ts_now}")
    return "\n".join(lines)


def _v2_panel_toggle_markup():
    """Build inline keyboard for V2 panel toggle in admin panel."""
    active = _get_v2_active_panel_id()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in _V2_PANELS_REGISTRY:
        check = "✅" if p["id"] == active else "⭕"
        markup.add(types.InlineKeyboardButton(
            f"{check} {p['name']}",
            callback_data=f"v2panel_set:{p['id']}", style="success"
        ))
    return markup


def _v2_dispatch_found(found):
    """Dedup + dispatch a dict of {key: (number,otp,sms_txt,service)} OTPs."""
    global seen_otps
    for key, (number, otp, sms_txt, service) in found.items():
        with seen_lock:
            if key in seen_otps:
                continue
            seen_otps[key] = True
            save_json(SEEN_FILE, seen_otps)
        try:
            clean = re.sub(r"\D", "", str(number))
            with user_map_lock:
                t_start = assigned_time.get(clean)
            seconds = int(time.time() - t_start) if t_start else 0
            _dispatch_otp(otp, number, seconds, service, sms_txt)
            print(f"[V2-MONITOR] ✅ OTP={otp} num={number} svc={service} secs={seconds}")
        except Exception as e:
            print(f"[V2-MONITOR] dispatch error: {e}")


def _cloud_parse_otp_rows(rows):
    """Parse a list of SMS row dicts into {key: (number,otp,sms_txt,service)}."""
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        number = str(row.get("number") or row.get("phone") or row.get("no") or
                     row.get("msisdn") or row.get("from") or "").strip()
        sms_txt = str(row.get("message") or row.get("sms") or row.get("text") or
                      row.get("body") or row.get("content") or "").strip()
        service = str(row.get("service") or row.get("app") or row.get("sid") or
                      row.get("sender") or "").strip()
        if not service and sms_txt:
            service = _detect_service_from_sms(sms_txt)
        otp = extract_otp_from_sms(sms_txt)
        if number and otp:
            key = f"{number}:{sms_txt}"
            found[key] = (number, otp, sms_txt, service)
    return found


def _cloud_extract_rows(raw):
    """Extract list of SMS rows from a parsed JSON response."""
    rows = []
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, dict):
        return rows
    # format: {"meta":{...}, "data": {"sms":[...]} } or {"data":[...]}
    data_blob = raw.get("data") or {}
    for dk in ("sms", "messages", "otps", "records", "result", "items", "list"):
        v = data_blob.get(dk) if isinstance(data_blob, dict) else None
        if isinstance(v, list) and v:
            return v
    if isinstance(data_blob, list) and data_blob:
        return data_blob
    for dk in ("sms", "messages", "otps", "records", "result", "items"):
        v = raw.get(dk)
        if isinstance(v, list) and v:
            return v
    return rows


def _cloud_fetch_otps_rest(base_url, api_key, panel_name="CLOUD"):
    """REST-style poll: tries multiple URL patterns + endpoints for recent OTPs."""
    import json as _json

    # Build candidate base URLs (with and without @public prefix)
    alt_base = base_url.replace("/@public/api", "/api").replace("@public/api", "api")
    if alt_base == base_url:
        alt_base = None

    url_bases = [base_url]
    if alt_base:
        url_bases.append(alt_base)

    # Endpoints to try on each base
    endpoints = ["/success-otp", "/sms", "/messages", "/inbox", "/otps",
                 "/sms/list", "/sms/recent", "/receive", "/cdr"]

    for ub in url_bases:
        for ep in endpoints:
            full_url = f"{ub}{ep}"
            for hdrs in [
                {"mauthapi": api_key},                           # bare auth
                {"mauthapi": api_key, "Accept": "application/json"},
            ]:
                try:
                    r = requests.get(full_url, headers=hdrs, timeout=10, verify=False)
                    ct = r.headers.get("content-type", "")
                    print(f"[{panel_name}-REST] {ep} → HTTP {r.status_code} ct={ct[:40]}")
                    if r.status_code != 200:
                        continue
                    if "text/event-stream" in ct:
                        # It's SSE — parse the first few lines as SSE events
                        found = {}
                        for line in r.text.splitlines():
                            line = line.strip()
                            if not line.startswith("data:"):
                                continue
                            payload = line[5:].strip()
                            if not payload or payload in ("{}", "null"):
                                continue
                            try:
                                obj = _json.loads(payload)
                                inner = obj.get("data") if isinstance(obj, dict) else None
                                if isinstance(inner, dict):
                                    obj = inner
                                tmp = _cloud_parse_otp_rows([obj])
                                found.update(tmp)
                            except Exception:
                                pass
                        if found:
                            print(f"[{panel_name}-REST] ✅ {len(found)} OTPs via SSE-as-REST {ep}")
                            return found
                        continue
                    raw = r.json()
                    rows = _cloud_extract_rows(raw)
                    found = _cloud_parse_otp_rows(rows)
                    if found:
                        print(f"[{panel_name}-REST] ✅ {len(found)} OTPs via {ep}")
                        return found
                    elif rows:
                        print(f"[{panel_name}-REST] {ep} returned {len(rows)} rows but no OTPs")
                        return {}
                except Exception as e:
                    print(f"[{panel_name}-REST] {ep} error: {e}")
                    continue
    return {}


def _v2_panel_monitor():
    """Background thread: persistent SSE for STEX/VOLTEX, REST poll for FastX."""
    global seen_otps
    import json as _json
    print("[V2-MONITOR] Started — persistent connection mode")
    _last_pid = [None]
    _fail_count = 0

    while True:
        try:
            pid = _get_v2_active_panel_id()

            # ── FastX: REST polling ───────────────────────────────────────────
            if pid == "fastx":
                found = _fastx_fetch_otps_rest()
                if found:
                    _v2_dispatch_found(found)
                time.sleep(POLL_INTERVAL)
                continue

            # ── STEX / VOLTEX / MK: REST polling via /success-otp ───────────
            if pid == "stex":
                base_url, api_key, pname = STEX_BASE_URL, STEX_API_KEY, "STEX"
            elif pid == "voltex":
                base_url, api_key, pname = V3_BASE_URL, V3_API_KEY, "VOLTEX"
            elif pid == "mk":
                base_url, api_key, pname = MK_BASE_URL, MK_API_KEY, "MK"
            else:
                time.sleep(POLL_INTERVAL)
                continue

            if pid != _last_pid[0]:
                print(f"[V2-MONITOR] Starting REST poll for {pname} /success-otp ✅")
                _last_pid[0] = pid
                _fail_count = 0

            # Poll success-otp endpoint — MK uses /success-otp-info + Bearer, others use /success-otp + mauthapi
            _otp_path = "/success-otp-info" if pid == "mk" else "/success-otp"
            success_url = f"{base_url}{_otp_path}"
            _poll_headers = _mk_headers() if pid == "mk" else {"mauthapi": api_key, "Accept": "application/json"}
            try:
                r = requests.get(
                    success_url,
                    headers=_poll_headers,
                    timeout=10, verify=False
                )
                if r.status_code == 200:
                    _fail_count = 0
                    raw = r.json()
                    rows = _cloud_extract_rows(raw)
                    if rows:
                        found = _cloud_parse_otp_rows(rows)
                        if found:
                            print(f"[V2-MONITOR] {pname} /success-otp → {len(found)} OTP(s)")
                            _v2_dispatch_found(found)
                else:
                    _fail_count += 1
                    print(f"[V2-MONITOR] {pname} /success-otp HTTP {r.status_code} (fail #{_fail_count})")
                    if _fail_count == 12:
                        _alert_txt = (
                            f"⚠️ <b>V2 PANEL ALERT</b>\n\n"
                            f"📡 Panel: <b>{pname}</b>\n"
                            f"❌ /success-otp returning HTTP {r.status_code} for 60s+\n\n"
                            f"OTPs <b>cannot be forwarded</b> until this is fixed.\n"
                            f"👉 Please check/renew the API key in bot settings."
                        )
                        for _sad in SUPER_ADMIN_IDS:
                            try:
                                bot.send_message(_sad, _alert_txt, parse_mode="HTML")
                            except Exception:
                                pass
            except Exception as _poll_err:
                _fail_count += 1
                print(f"[V2-MONITOR] {pname} poll error: {_poll_err}")

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"[V2-MONITOR] loop error: {e}")
            time.sleep(5)


threading.Thread(target=_v2_panel_monitor, daemon=True).start()


def _v2_svc_emoji(sid):
    _defaults = {
        "INSTAGRAM": ("5319160079465857105", "📸"),
        "FACEBOOK":  ("5323261730283863478", "🔵"),
        "TELEGRAM":  ("5330237710655306682", "✈️"),
        "WHATSAPP":  ("5334998226636390258", "💚"),
        "TIKTOK":    ("5327982530702359565", "🎵"),
        "TWITTER":   (None, "🐦"),
        "BINANCE":   (None, "🟡"),
        "SNAPCHAT":  (None, "👻"),
        "GOOGLE":    (None, "🔴"),
        "YOUTUBE":   (None, "📺"),
        "LINKEDIN":  (None, "💼"),
        "AMAZON":    (None, "🛒"),
    }
    key = (sid or "").upper()
    # Check custom override first
    with _custom_emoji_lock:
        custom_id = _custom_emojis.get("services", {}).get(key)
    if custom_id:
        fb = _defaults.get(key, (None, "📱"))[1]
        return f'<tg-emoji emoji-id="{custom_id}">{fb}</tg-emoji>'
    # Fall back to hardcoded defaults
    default_id, fb = _defaults.get(key, (None, "📱"))
    if default_id:
        return f'<tg-emoji emoji-id="{default_id}">{fb}</tg-emoji>'
    return fb


_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "\u200d"
    "\ufe0f"
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    """Remove all Unicode emojis from a string using the emoji library + regex fallback."""
    cleaned = _emoji_lib.replace_emoji(text, replace="")
    cleaned = _EMOJI_RE.sub("", cleaned)
    return " ".join(cleaned.split())


def _svc_icon_emoji_id(sid):
    """Return icon_custom_emoji_id for known services (for inline buttons)."""
    m = {
        "INSTAGRAM": "5319160079465857105",
        "FACEBOOK":  "5323261730283863478",
        "TELEGRAM":  "5330237710655306682",
        "WHATSAPP":  "5334998226636390258",
        "TIKTOK":    "5327982530702359565",
    }
    key = (sid or "").upper()
    with _custom_emoji_lock:
        override = _custom_emojis.get("services", {}).get(key)
    return override or m.get(key)


def _resolve_flag(flag):
    """Convert a flag emoji to <tg-emoji> tag if a custom ID is set (HTML messages only).
    Checks specific flag map first, then falls back to the 'flag_default' msg_slot."""
    if not flag:
        return flag
    with _custom_emoji_lock:
        eid = _custom_emojis.get("flags", {}).get(flag)
        if not eid:
            slot = _custom_emojis.get("msg_slots", {}).get("flag_default", {})
            eid  = slot.get("id") if isinstance(slot, dict) else None
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{flag}</tg-emoji>'
    return flag


def _flag_icon_emoji_id(flag, fallback=None):
    """Return icon_custom_emoji_id for a flag emoji (for inline buttons).
    Checks specific flag map first, then falls back to the 'flag_default' msg_slot."""
    if not flag:
        return fallback
    with _custom_emoji_lock:
        eid = _custom_emojis.get("flags", {}).get(flag)
        if not eid:
            slot = _custom_emojis.get("msg_slots", {}).get("flag_default", {})
            eid  = slot.get("id") if isinstance(slot, dict) else None
    return eid or fallback


def _flag_btn_kwargs(flag, fallback=None):
    """Return dict with icon_custom_emoji_id if a custom ID exists for this flag."""
    eid = _flag_icon_emoji_id(flag, fallback)
    return {"icon_custom_emoji_id": eid} if eid else {}


# ── DM message fixed-position emoji ───────────────────────────────────────────
_DM_EMOJI_DEFAULTS = {
    "number_pre":  {"id": "5422858869372104873", "fb": "📞"},
    "country_pre": {"id": "5287292843763713628", "fb": "🌍"},
    "country_post":{"id": "5210956306952758910", "fb": "✨"},
}
_DM_EMOJI_LABELS = {
    "number_pre":  "Before Number",
    "country_pre": "Before Country",
    "country_post":"After Country",
}

def _get_dm_emoji(key):
    """Return <tg-emoji> HTML for a DM fixed emoji slot.
    Priority: msg_slots[dm_<key>]  →  dm_emoji[key]  →  hardcoded default."""
    slot_map = {"number_pre": "dm_number_pre", "country_pre": "dm_country_pre", "country_post": "dm_country_post"}
    defaults = _DM_EMOJI_DEFAULTS.get(key, {})
    slot_name = slot_map.get(key, "")
    with _custom_emoji_lock:
        cfg = (_custom_emojis.get("msg_slots", {}).get(slot_name)
               or _custom_emojis.get("dm_emoji", {}).get(key, {}))
    eid = (cfg.get("id") if isinstance(cfg, dict) else None) or defaults.get("id", "")
    fb  = (cfg.get("fb") if isinstance(cfg, dict) else None) or defaults.get("fb", "")
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>' if eid else fb


# ── Button emoji config ────────────────────────────────────────────────────────
_BTN_EMOJI_PREFIX = {
    "otp_copy":         "🔒 ",
    "number_bot":       "🤖 ",
    "main_channel":     "📢 ",
    "change_number":    "🔄 ",
    "otp_group_btn":    "📢 ",
    "remove_cc":        "📵 ",
    "add_cc":           "➕ ",
    "back":             "⬅️ ",
    "refresh":          "🔄 ",
    "start_otp_group":  "🔥 ",
    "start_channel":    "📢 ",
    "start_verify":     "✅ ",
    "get_number":       "📲 ",
    "saport":           "📞 ",
    "balance":          "💰 ",
    "developer":        "👨‍💻 ",
    "withdraw":         "💸 ",
    "refer":            "🔗 ",
    "admin_panel":      "⚙️ ",
}
_BTN_EMOJI_SUFFIX = {
    "start_otp_group":  " 🔥",
    "start_channel":    " 📢",
    "start_verify":     " ✅",
    "admin_panel":      " ⚙️",
}
# CC toggle icons are kept in bot.py so this feature is self-contained.
_REMOVE_CC_ICON_ID = "5377747517897187291"
_ADD_CC_ICON_ID = "5420323438508155202"
_BTN_DEFAULT_ICONS = {
    "otp_copy":         "5296369303661067030",
    "number_bot":       "5323523560080158541",
    "main_channel":     "5217822164362739968",
    "change_number":    "5348125953090403204",
    "otp_group_btn":    "5458603043203327669",
    "back":             "5210952531676504517",
    "refresh":          "5386367538735104399",
    "start_otp_group":  "5420323339723881652",
    "start_channel":    "5451882707875276247",
    "start_verify":     "5206607081334906820",
    "get_number":       "5296424506875722458",
    "saport":           "5267294466716244344",
    "balance":          "5296591052822585948",
    "developer":        "5267456597436699660",
    "withdraw":         "5298716928490120985",
    "refer":            "5267041999948653482",
    "admin_panel":      "5420155432272438703",
}
_BTN_DISPLAY_NAMES = {
    "otp_copy":         "🔒 OTP Copy (copy button in OTP message)",
    "number_bot":       "🤖 Number Bot (bot link in OTP message)",
    "main_channel":     "📢 Main Channel (channel in OTP message)",
    "change_number":    "🔄 Change Number (change number)",
    "otp_group_btn":    "📢 OTP Group (group button after showing number)",
    "back":             "⬅️ Back (go back)",
    "refresh":          "🔄 Refresh",
    "start_otp_group":  "🔥 Start — OTP Group JOIN button",
    "start_channel":    "📢 Start — Main Channel JOIN button",
    "start_verify":     "✅ Start — VERIFY button",
    "get_number":       "📲 Get Number (main menu button)",
    "saport":           "📞 Support (main menu button)",
    "balance":          "💰 Balance (main menu button)",
    "developer":        "👨‍💻 Developer Info (main menu button)",
    "withdraw":         "💸 Withdraw (main menu button)",
    "refer":            "🔗 Reffer (main menu button)",
    "admin_panel":      "⚙️ Admin Panel (main menu button)",
}

# ── Admin panel & settings button icon IDs (overridable from bot) ─────────────
_ADMIN_BTN_DEFAULT_ICONS = {
    # Admin panel main menu buttons
    "num_add":          "5420323438508155202",
    "sob_clear":        "5422557736330106570",
    "broadcast":        "5352980533150259581",
    "user_count":       "5267294466716244344",
    "user_list":        "5420145051336485498",
    "otp_stats":        "5355208818017999139",
    "demo_otp":         "5267041999948653482",
    "add_panel":        "5420323438508155202",
    "remove_panel":     "5422557736330106570",
    "add_service":      "5420323438508155202",
    "remove_service":   "5422557736330106570",
    "panels":           "5463352748751753567",
    "test_panel":       "5337255927735163754",
    "purano_send":      "5193100774988617665",
    "purano_off":       "5352974971167611327",
    "settings":         "5190447043545438788",
    "remove_admin":     "5422557736330106570",
    "support_id":       "5352694861990501856",
    "edit_msgs":        "5193071182663947673",
    "v2_panel":         "5334530732331143967",
    "live_console":     "5337267511261960341",
    "extra_groups":     "5420323438508155202",
    "custom_emoji":     "5352552689983067014",
    "api_key":          "5190781475468915802",
    "payment_settings": "5190576863226933563",
    "user_menu":        "5267456597436699660",
    "live_traffic":     "5337267511261960341",
    # Settings inline buttons
    "grp_link":         "5420517437885943844",
    "grp_chat_id":      "5355208818017999139",
    "auto_delete":      "5422557736330106570",
    "remove_group":     "5422557736330106570",
    "grp_send":         "5193100774988617665",
    "num_tag":          "5267295703666824255",
    "nums_per_user":    "5267294466716244344",
    "join_channel":     "5267041999948653482",
    "bot_link":         "5352892752608663501",
}
_ADMIN_BTN_DISPLAY_NAMES = {
    "num_add":          "𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱 (admin panel)",
    "sob_clear":        "𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿 (admin panel)",
    "broadcast":        "𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 (admin panel)",
    "user_count":       "𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁 (admin panel)",
    "user_list":        "𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁 (admin panel)",
    "otp_stats":        "𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀 (admin panel)",
    "demo_otp":         "𝗗𝗘𝗠𝗢 𝗢𝗧𝗣 (admin panel)",
    "add_panel":        "𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹 (admin panel)",
    "remove_panel":     "𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹 (admin panel)",
    "add_service":      "𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 (admin panel)",
    "remove_service":   "𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 (admin panel)",
    "panels":           "𝗣𝗮𝗻𝗲𝗹𝘀 (admin panel)",
    "test_panel":       "𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹 (admin panel)",
    "purano_send":      "𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽𝗲 𝗦𝗲𝗻𝗱 (admin panel)",
    "purano_off":       "𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗕𝗼𝗻𝗱𝗵𝗼 (admin panel)",
    "settings":         "𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 (admin panel)",
    "remove_admin":     "𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻 (admin panel)",
    "support_id":       "𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗 (admin panel)",
    "edit_msgs":        "𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀 (admin panel)",
    "v2_panel":         "𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁 (admin panel)",
    "live_console":     "𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴 (admin panel)",
    "extra_groups":     "𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀 (admin panel)",
    "custom_emoji":     "𝗖𝘂𝘀𝘁𝗼𝗺 𝗘𝗺𝗼𝗷𝗶 (admin panel)",
    "api_key":          "𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲 (admin panel)",
    "payment_settings": "𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 (admin panel)",
    "user_menu":        "𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂 (admin panel)",
    "live_traffic":     "🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰 (admin panel)",
    "grp_link":         "Group Link (settings inline)",
    "grp_chat_id":      "Group Chat ID (settings inline)",
    "auto_delete":      "Auto Delete (settings inline)",
    "remove_group":     "Remove Group (settings inline)",
    "grp_send":         "Group Send (settings inline)",
    "num_tag":          "Number Tag (settings inline)",
    "nums_per_user":    "Numbers Per User (settings inline)",
    "join_channel":     "Join Channel (settings inline)",
    "bot_link":         "Bot Link (settings inline)",
}


def _get_admin_btn_icon(key):
    """Return icon_custom_emoji_id for an admin/settings button.
    Checks custom overrides first, then falls back to defaults."""
    with _custom_emoji_lock:
        override = _custom_emojis.get("admin_btns", {}).get(key)
    return override or _ADMIN_BTN_DEFAULT_ICONS.get(key, "")


def _btn_text_and_icon(key, default_text, default_icon_id=None):
    """Return (text, icon_kwargs). When a custom emoji is set, strip the old plain
    emoji prefix and suffix from the button text so only the custom icon remains."""
    with _custom_emoji_lock:
        custom_id = _custom_emojis.get("buttons", {}).get(key)
    icon_id = custom_id or default_icon_id or _BTN_DEFAULT_ICONS.get(key)
    text = default_text
    if icon_id:
        # Strip leading plain-emoji prefix
        prefix = _BTN_EMOJI_PREFIX.get(key, "")
        if prefix and text.startswith(prefix):
            text = text[len(prefix):]
        # Strip trailing plain-emoji suffix
        suffix = _BTN_EMOJI_SUFFIX.get(key, "")
        if suffix and text.endswith(suffix):
            text = text[: -len(suffix)]
    return text, ({"icon_custom_emoji_id": icon_id} if icon_id else {})


# ── Message emoji slots ────────────────────────────────────────────────────────
# Predefined named icon slots  (slot_key → (default_fallback_char, display_label))
_MSG_ICON_SLOTS = {
    "start_header":  ("🔥", "Start — Title Header Icon"),
    "start_crown":   ("👑", "Start — Dashboard Crown"),
    "start_user":    ("👨‍💻", "Start — User Icon"),
    "start_id":      ("🗣️", "Start — ID Icon"),
    "start_status":  ("📊", "Start — Status Icon"),
    "start_workers": ("👀", "Start — Workers Icon"),
    "start_powered": ("😊", "Start — Powered By Icon"),
    "otp_phone":     ("📱", "OTP Group — Phone Icon"),
    "otp_key":       ("🔑", "OTP — Key/OTP Icon"),
    "otp_world":     ("🌍", "OTP — Country Icon"),
    "otp_sms":       ("📩", "OTP — SMS Icon"),
    "verify_title":  ("🔥", "Verify — Success Icon"),
    # ── DM emoji positional ───────────────────────────────────────────────────
    "dm_number_pre":   ("📞", "DM — Before Number"),
    "dm_country_pre":  ("🌍", "DM — Before Country Name"),
    "dm_country_post": ("✨", "DM — After Country Name"),
    # ── Flag default ──────────────────────────────────────────────────────────
    "flag_default":  ("🏳️", "Flag — Default Custom Emoji for all flags"),
}
_msg_icon_set_state: dict = {}  # uid → {"key": slot_key}

# Hardcoded default custom emoji IDs for group OTP message slots.
# These apply when the admin has NOT set a custom emoji via the panel.
# Admin-set values always take priority over these.
_MSG_ICON_DEFAULT_IDS = {
    "otp_key":   {"id": "5296369303661067030", "fb": "🔑"},
    "otp_world": {"id": "5447410659077661506", "fb": "🌍"},
    "otp_sms":   {"id": "5443038326535759644", "fb": "📩"},
}


def _msg_emoji_vars():
    """Build {emoji_NAME: tg-emoji-html or default-char} vars for template substitution.
    Predefined slots always have a fallback so {emoji_NAME} never raises KeyError."""
    result = {}
    for name, (default_char, _) in _MSG_ICON_SLOTS.items():
        result[f"emoji_{name}"] = default_char
    with _custom_emoji_lock:
        slots = dict(_custom_emojis.get("msg_slots", {}))
    # Apply hardcoded default IDs first (only when not overridden by admin)
    for name, cfg in _MSG_ICON_DEFAULT_IDS.items():
        if name not in slots:
            eid, fb = cfg["id"], cfg["fb"]
            result[f"emoji_{name}"] = f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'
    # Admin-set custom slots take priority
    for name, cfg in slots.items():
        eid = cfg.get("id", "")
        fb  = cfg.get("fb", "")
        result[f"emoji_{name}"] = f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>' if eid else fb
    # DM positional aliases — template uses {emoji_number_pre} etc. directly
    for alias, slot_name, default_id, default_fb in [
        ("emoji_number_pre",   "dm_number_pre",   "5422858869372104873", "📞"),
        ("emoji_country_pre",  "dm_country_pre",  "5287292843763713628", "🌍"),
        ("emoji_country_post", "dm_country_post", "5210956306952758910", "✨"),
    ]:
        cfg = slots.get(slot_name, {})
        eid = cfg.get("id") or default_id
        fb  = cfg.get("fb") or default_fb
        result[alias] = f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'
    return result


def _v2_build_console_markup():
    """Build Live Console keyboard — Step 1: show enabled services as buttons."""
    _STYLES = ["success", "primary", "danger"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    btns = []
    idx = 0
    for sid in _CONSOLE_SVC_NAMES:
        cfg = _console_config.get(sid, {})
        if not cfg.get("enabled"):
            continue
        if not cfg.get("ranges"):
            continue
        _icon_id = _svc_icon_emoji_id(sid)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            f"{sid}", callback_data=f"v2svc_cc:{sid}",
            style=_STYLES[idx % len(_STYLES)], **_btn_kwargs
        ))
        idx += 1
    if btns:
        markup.add(*btns)
    return markup, bool(btns)


def _v2_build_country_markup(sid):
    """Build country buttons for a specific service — Step 2.
    Shows both V2 live ranges AND V1 stock countries for the same service."""
    cfg = _console_config.get(sid, {})
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = []

    # V2 live range buttons
    v2_rows = []
    country_totals = {}
    for prefix in cfg.get("ranges", []):
        c_name, flag = get_country_details(prefix)
        if c_name and c_name not in ("Unknown", ""):
            country_totals[c_name] = country_totals.get(c_name, 0) + 1
        else:
            c_name = "Unknown Country"
            country_totals[c_name] = country_totals.get(c_name, 0) + 1
        v2_rows.append((prefix, c_name, flag))

    country_seen = {}
    for prefix, c_name, flag in v2_rows:
        country_seen[c_name] = country_seen.get(c_name, 0) + 1
        label = (
            f"{c_name} {country_seen[c_name]}"
            if country_totals[c_name] > 1
            else c_name
        )
        btns.append(types.InlineKeyboardButton(
            label, callback_data=f"v2csvc:{sid}:{prefix}", style="primary",
            **_flag_btn_kwargs(flag)
        ))

    # V1 stock country buttons for the same service (manual/stock numbers)
    svc_key = sid.lower()
    svc_stock = dict(stock.get(svc_key, {}))
    for cnt, nums in svc_stock.items():
        if not nums:
            continue
        _, flag = get_country_details(nums[0])
        btns.append(types.InlineKeyboardButton(
            f"{cnt}",
            callback_data=f"n:{svc_key}:{cnt}",
            style="success",
            **_flag_btn_kwargs(flag)
        ))

    if btns:
        markup.add(*btns)
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="v2back", style="danger"))
    return markup, bool(btns)


def _cc_services_markup():
    """Admin: inline keyboard listing all console services."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for sid in _CONSOLE_SVC_NAMES:
        cfg = _console_config.get(sid, {"enabled": False, "ranges": []})
        check = "✅" if cfg.get("enabled") else "⭕"
        rng_cnt = len(cfg.get("ranges", []))
        btns.append(types.InlineKeyboardButton(
            f"{check} {sid} ({rng_cnt})",
            callback_data=f"cc_svc:{sid}", style="success"
        ))
    for i in range(0, len(btns), 2):
        markup.add(*btns[i:i + 2])
    return markup


def _cc_service_detail_markup(sid):
    """Admin: inline keyboard for a single console service — toggle + ranges."""
    cfg = _console_config.get(sid, {"enabled": False, "ranges": []})
    markup = types.InlineKeyboardMarkup(row_width=1)
    enabled = cfg.get("enabled", False)
    toggle_label = "🔴 Disable" if enabled else "🟢 Enable"
    markup.add(types.InlineKeyboardButton(toggle_label, callback_data=f"cc_toggle:{sid}", style="primary"))
    for prefix in cfg.get("ranges", []):
        c_name, flag = get_country_details(prefix)
        if c_name and c_name not in ("Unknown", ""):
            rlabel = f"🗑️ {c_name} ({prefix})"
        else:
            rlabel = f"🗑️ ({prefix})"
        markup.add(types.InlineKeyboardButton(rlabel, callback_data=f"cc_delrange:{sid}:{prefix}", style="danger",
                                              **_flag_btn_kwargs(flag)))
    markup.add(types.InlineKeyboardButton("➕ Add Range", callback_data=f"cc_addrange:{sid}", style="success"))
    markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="cc_back", style="primary"))
    return markup


def _v2_custom_range_step(message):
    """Handle user input for CUSTOM RANGE — find matching range and allocate number."""
    uid = message.from_user.id
    txt = (message.text or "").strip()

    if _intercept_menu_btn(message):
        return
    if txt in ("❌ Cancel", "❌ cancel"):
        bot.send_message(
            message.chat.id,
            "❌ Cancelled.",
            reply_markup=v2_switch_menu(),
            parse_mode="HTML",
        )
        return

    prefix = re.sub(r"[^\d]", "", txt)
    if not prefix:
        msg = bot.send_message(
            message.chat.id,
            "❌ <b>Invalid input!</b> Numbers only (e.g. <code>8801</code>)\n\nTry again:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _v2_custom_range_step)
        return

    bot.send_message(message.chat.id, f"⏳ Searching for a number with <b>{prefix}</b>...", parse_mode="HTML")

    services = _v2_active_liveaccess()
    matched_prefix = None
    matched_sid = None
    for svc in services:
        sid = svc.get("sid", "?")
        for rng in svc.get("ranges", []):
            clean = rng.rstrip("X")
            if clean.startswith(prefix) or prefix.startswith(clean):
                matched_prefix = clean
                matched_sid = sid
                break
        if matched_prefix:
            break

    if not matched_prefix:
        msg2 = bot.send_message(
            message.chat.id,
            f"❌ <b>Range not found!</b>\n\n"
            f"No live range with <code>{prefix}</code> right now.\n\n"
            f"Try another prefix or check <b>LIVE RANGE</b>:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg2, _v2_custom_range_step)
        return

    num = _v2_active_getnum(matched_prefix)
    if not num:
        bot.send_message(
            message.chat.id,
            f"❌ <b>Number allocation failed!</b>\n"
            f"Range <code>{matched_prefix}</code> has no numbers right now. Try again later.",
            reply_markup=v2_switch_menu(),
            parse_mode="HTML",
        )
        return

    with user_map_lock:
        old_nums = [k for k, v in user_map.items() if v == uid]
        for old_clean in old_nums:
            user_map.pop(old_clean, None)
            assigned_time.pop(old_clean, None)
    if old_nums:
        _save_user_map()
    register_number(uid, num)
    c_name, flag = get_country_details(num)
    display_num = num if num.startswith("+") else "+" + num
    _user_last_svc[uid] = (matched_sid.lower(), c_name)

    n_batch_cr = get_numbers_per_batch()
    cr_nums = [num]
    for _ in range(n_batch_cr - 1):
        extra = _v2_active_getnum(matched_prefix)
        if extra:
            cr_nums.append(extra)
    for crn in cr_nums:
        register_number(uid, crn)
    display_nums_cr = [n if n.startswith("+") else "+" + n for n in cr_nums]
    _remember_number_view(
        uid, matched_sid.lower(), c_name, display_nums_cr, flag, c_name,
        is_v2=True, v2_prefix=matched_prefix, v2_sid=matched_sid
    )
    refresh_kb = _build_numbers_display_kb(
        matched_sid.lower(), c_name, display_nums_cr, flag, c_name,
        is_v2=True, v2_prefix=matched_prefix, v2_sid=matched_sid
    )
    sent_number = bot.send_message(
        message.chat.id,
        ".",
        reply_markup=refresh_kb,
    )
    _user_last_num_msg[uid] = sent_number.message_id
    bot.send_message(message.chat.id, "🔄 V2 SWITCH menu:", reply_markup=v2_switch_menu(), parse_mode="HTML")


def _v2_show_console(chat_id):
    """Send V2 Console service list to chat_id (admin-configured)."""
    markup, has_btns = _v2_build_console_markup()
    if not has_btns:
        bot.send_message(chat_id,
                         "❌ Admin has not configured any service yet.",
                         parse_mode="HTML")
        return
    bot.send_message(
        chat_id,
        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>SELECT PLATFORM</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )


# ── V3 Panel API helpers ───────────────────────────────────────────────────────

def _v3_get_services():
    """Return list of service dicts from V3 panel API."""
    try:
        for endpoint in ["/services", "/numbers", "/"]:
            r = requests.get(f"{V3_BASE_URL}{endpoint}",
                             params={"apikey": V3_API_KEY},
                             timeout=15, verify=False)
            if r.status_code == 200:
                try:
                    d = r.json()
                except Exception:
                    continue
                services = (d.get("services") or d.get("data") or
                            d.get("numbers") or d.get("list") or [])
                if isinstance(services, list) and services:
                    return services
                if isinstance(services, dict):
                    return [{"sid": k, "count": v} for k, v in services.items()]
    except Exception as e:
        print(f"[V3] get_services error: {e}")
    return []


def _v3_getnum(service_id):
    """Allocate a number for a service from V3 panel. Returns number string or None."""
    try:
        for method, endpoint in [("POST", "/getnum"), ("GET", "/getnum"), ("POST", "/allocate")]:
            try:
                if method == "POST":
                    r = requests.post(f"{V3_BASE_URL}{endpoint}",
                                      params={"apikey": V3_API_KEY},
                                      data={"service": service_id},
                                      timeout=15, verify=False)
                else:
                    r = requests.get(f"{V3_BASE_URL}{endpoint}",
                                     params={"apikey": V3_API_KEY, "service": service_id},
                                     timeout=15, verify=False)
                if r.status_code == 200:
                    d = r.json()
                    num = (d.get("number") or d.get("full_number") or d.get("phone") or
                           (d.get("data") or {}).get("number") or
                           (d.get("data") or {}).get("full_number"))
                    if num:
                        s = str(num).strip()
                        return s if s.startswith("+") else "+" + s
            except Exception:
                continue
    except Exception as e:
        print(f"[V3] getnum error: {e}")
    return None


def fetch_v3_panel():
    """Fetch recent OTPs from V3 panel. Returns dict key->(number,otp,sms_txt,service)."""
    found = {}
    try:
        for endpoint in ["/sms", "/messages", "/otps", "/otp"]:
            try:
                r = requests.get(f"{V3_BASE_URL}{endpoint}",
                                 params={"apikey": V3_API_KEY},
                                 timeout=15, verify=False)
                if r.status_code != 200:
                    continue
                d = r.json()
                rows = (d.get("data") or d.get("messages") or d.get("sms") or
                        d.get("otps") or d.get("list") or [])
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    number = str(row.get("number") or row.get("phone") or "").strip()
                    sms_txt = str(row.get("message") or row.get("sms") or
                                  row.get("text") or row.get("body") or "").strip()
                    service = str(row.get("service") or row.get("app") or "").strip()
                    if not number or not sms_txt:
                        continue
                    otp = extract_otp_from_sms(sms_txt)
                    if otp:
                        key = f"{number}:{sms_txt}"
                        found[key] = (number, otp, sms_txt, service)
                if found or rows:
                    break
            except Exception:
                continue
        _record_fetch("v3", len(found))
        if found:
            print(f"[V3] ✅ {len(found)} OTP(s) fetched")
    except Exception as e:
        print(f"[V3] fetch error: {e}")
    return found


def _v3_build_console_markup(services):
    """Build inline keyboard for V3 service list."""
    _STYLES = ["success", "primary", "danger"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    btns = []
    for idx, svc in enumerate(services):
        sid = str(svc.get("sid") or svc.get("service") or svc.get("name") or svc.get("id") or "?")
        cnt = svc.get("count") or svc.get("available") or svc.get("total") or 0
        _icon_id = _svc_icon_emoji_id(sid)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            f"{sid} ({cnt})", callback_data=f"v3svc:{sid}",
            style=_STYLES[idx % len(_STYLES)], **_btn_kwargs
        ))
    if btns:
        markup.add(*btns)
    _rf_text, _rf_icon = _btn_text_and_icon("refresh", "🔄 Refresh")
    markup.add(types.InlineKeyboardButton(_rf_text, callback_data="v3back", style="danger", **_rf_icon))
    return markup, bool(btns)


def _v3_show_console(chat_id):
    """Send V3 service list to user."""
    if not _group_settings.get("v3_enabled", True):
        bot.send_message(chat_id, "❌ <b>V3 Panel is currently disabled.</b>", parse_mode="HTML")
        return
    services = _v3_get_services()
    markup, has = _v3_build_console_markup(services)
    text = (
        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>SELECT PLATFORM</b>"
        if has else
        "⚠️ No service available right now.\n"
        "🔄 Please try again later."
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")


def _send_to_extra_group(chat_id, otp, number, seconds, service, sms_body, grp_config):
    """Send OTP message to an extra group with its own custom button links.
    Uses exactly the same variable set and formatting logic as send_otp_message."""
    import html as _html
    # Detect service from SMS body first (more accurate), fall back to panel value
    _svc_raw = _detect_service_from_sms(sms_body) or service
    svc = _svc_raw.upper() if _svc_raw else "—"
    c_name, flag = get_country_details(number)
    otp_str = str(otp)
    _tag = get_group_tag()
    _tagged = tag_number(number, _tag)
    _sms_val = _html.escape(sms_body) if sms_body else "—"
    _rflag = _resolve_flag(flag)
    _emoji_extra = _msg_emoji_vars()
    _svc_emoji_html = _v2_svc_emoji(svc)
    _emoji_number_pre  = _get_dm_emoji("number_pre")
    _emoji_country_pre = _get_dm_emoji("country_pre")
    _emoji_country_post= _get_dm_emoji("country_post")

    _country_short_eg = get_country_short(number)
    _group_country_short_eg = get_group_country_short(number, svc)
    _country_lang_eg = get_country_language(_country_short_eg)
    _sms_lang_eg = detect_sms_language(sms_body)
    _grp_vars = {**_emoji_extra,
                 **dict(svc=svc, number=mask_number(number), tagged_number=_tagged,
                        taged_number=_tagged, tagged_number_b=tag_number_bold(number, _tag),
                        country=c_name, flag=_rflag, otp=otp_str,
                        country_short=_country_short_eg, country_lang=_country_lang_eg,
                        country_short_b=to_math_bold(_group_country_short_eg),
                        sms_lang=_sms_lang_eg, sms_lang_b=to_math_bold(_sms_lang_eg),
                        sms_body=_sms_val, sms=_sms_val, vname=svc, text=_sms_val,
                        svc_emoji=_svc_emoji_html,
                        emoji_number_pre=_emoji_number_pre,
                        emoji_country_pre=_emoji_country_pre,
                        emoji_country_post=_emoji_country_post)}

    class _SafeDict(dict):
        def __missing__(self, k):
            return "{" + k + "}"

    def _make_bold_italic(text):
        if "<blockquote>" in text or "<tg-emoji" in text:
            return text
        return f"<b><i>{text}</i></b>"

    try:
        txt = get_template("otp_group").format_map(_SafeDict(_grp_vars))
        message = _make_bold_italic(_ensure_code_tag(txt, otp_str))
    except Exception as _tmpl_err:
        print(f"[EXTRA-GRP] ⚠️ Template error: {_tmpl_err} — using default")
        try:
            txt = _DEFAULT_TEMPLATES["otp_group"].format_map(_SafeDict(_grp_vars))
            message = _make_bold_italic(_ensure_code_tag(txt, otp_str))
        except Exception:
            message = f"<b><i>OTP: <code>{otp_str}</code></i></b>"

    markup = types.InlineKeyboardMarkup()
    markup.add(_build_otp_copy_button(otp_str))

    _btns = []
    _bl = grp_config.get("bot_link") or get_bot_link()
    _cl = grp_config.get("channel_link") or grp_config.get("channel2") or get_channel2()
    if _bl:
        _nb_text, _nb_icon = _btn_text_and_icon("number_bot", "🤖 𝗡𝘂𝗺𝗯𝗲𝗿 𝗕𝗼𝘁")
        _btns.append(types.InlineKeyboardButton(_nb_text, url=_bl, style="primary", **_nb_icon))
    if _cl:
        _mc_text, _mc_icon = _btn_text_and_icon("main_channel", "📢 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹")
        _btns.append(types.InlineKeyboardButton(_mc_text, url=_cl, style="danger", **_mc_icon))
    if _btns:
        markup.row(*_btns)

    try:
        sent, rl = _send_with_retry(bot.send_message,
                                     chat_id=chat_id, text=message,
                                     parse_mode="HTML", reply_markup=markup)
        if sent:
            print(f"[EXTRA-GRP] ✅ Sent OTP={otp_str} to extra group {chat_id}")
            if is_auto_delete():
                _schedule_delete(chat_id, sent.message_id)
        else:
            print(f"[EXTRA-GRP] ❌ Failed to send to {chat_id} — rate limited {rl}s")
    except Exception as e:
        # Try stripping HTML as last resort
        try:
            import re as _re2
            plain = _re2.sub(r"<[^>]+>", "", message)
            sent2, _ = _send_with_retry(bot.send_message,
                                        chat_id=chat_id, text=plain,
                                        parse_mode=None, reply_markup=markup)
            if sent2:
                print(f"[EXTRA-GRP] ✅ Sent OTP={otp_str} to extra group {chat_id} (plain text fallback)")
                if is_auto_delete():
                    _schedule_delete(chat_id, sent2.message_id)
            else:
                print(f"[EXTRA-GRP] ❌ Failed to send to {chat_id} (plain fallback) — rate limited")
        except Exception as _plain_err:
            print(f"[EXTRA-GRP] ❌ Error sending to {chat_id}: {e} | plain fallback: {_plain_err}")


def _show_extra_groups(message):
    """Show admin panel for managing extra groups."""
    groups = _group_settings.get("extra_groups", [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ Add Extra Group", callback_data="eg_add", style="primary"))
    for i, g in enumerate(groups):
        gid = g.get("id", "?")
        link = g.get("link", "")
        label = link or str(gid)
        markup.add(
            types.InlineKeyboardButton(f"📢 Group #{i+1} — {str(gid)}", callback_data=f"eg_info:{i}", style="danger"),
        )
        markup.add(
            types.InlineKeyboardButton(f"🔗 Bot Link ({i+1})", callback_data=f"eg_setbot:{i}", style="success"),
            types.InlineKeyboardButton(f"📢 Ch Link ({i+1})", callback_data=f"eg_setch:{i}", style="primary"),
        )
        markup.add(
            types.InlineKeyboardButton(f"🧪 Test Send #{i+1}", callback_data=f"eg_test:{i}", style="success"),
            types.InlineKeyboardButton(f"🗑️ Remove #{i+1}", callback_data=f"eg_del:{i}", style="danger"),
        )
    bot.send_message(
        message.chat.id,
        "📡 <b>EXTRA GROUPS</b>\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"🔢 Total extra groups: <b>{len(groups)}</b>\n\n"
        "Add groups here to send OTP to all groups.\n"
        "Each group can have its own bot link and channel link.\n\n"
        "💡 <i>The bot must be added as <b>Admin</b> in that group.</i>\n"
        "🧪 <i>Use the Test Send button to check if the bot can send messages to that group.</i>\n\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
        reply_markup=markup,
        parse_mode="HTML",
    )


_eg_state = {}


def _eg_add_step1(message):
    """Step 1: get group chat ID."""
    uid = message.from_user.id
    if _is_back(message.text) or _intercept_menu_btn(message):
        _go_admin_panel(message)
        return
    raw = (message.text or "").strip().lstrip("@")
    gid = None
    if raw.lstrip("-").isdigit():
        gid = int(raw)
    elif raw.startswith("https://t.me/"):
        pass
    if gid is None:
        try:
            gid = int(raw)
        except Exception:
            pass
    if gid is None:
        msg = bot.send_message(message.chat.id,
            "❌ Enter a valid Chat ID (e.g. <code>-1001234567890</code>)\n\nTry again:",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _eg_add_step1)
        return
    _eg_state[uid] = {"id": gid}
    msg = bot.send_message(message.chat.id,
        f"✅ Group ID: <code>{gid}</code>\n\n"
        "Enter the <b>Bot Link</b> for OTP messages in this group\n"
        "(type <code>skip</code> to skip):",
        reply_markup=_back_admin_kb(), parse_mode="HTML")
    bot.register_next_step_handler(msg, _eg_add_step2)


def _eg_add_step2(message):
    """Step 2: get bot link."""
    uid = message.from_user.id
    if _is_back(message.text) or _intercept_menu_btn(message):
        _go_admin_panel(message)
        return
    txt = (message.text or "").strip()
    _eg_state[uid]["bot_link"] = "" if txt.lower() == "skip" else txt
    msg = bot.send_message(message.chat.id,
        "Enter the <b>Channel Link</b> for OTP messages in this group\n"
        "(type <code>skip</code> to skip):",
        reply_markup=_back_admin_kb(), parse_mode="HTML")
    bot.register_next_step_handler(msg, _eg_add_step3)


def _eg_add_step3(message):
    """Step 3: get channel link and save."""
    uid = message.from_user.id
    if _is_back(message.text) or _intercept_menu_btn(message):
        _go_admin_panel(message)
        return
    txt = (message.text or "").strip()
    state = _eg_state.pop(uid, {})
    state["channel_link"] = "" if txt.lower() == "skip" else txt
    extra = _group_settings.setdefault("extra_groups", [])
    extra.append(state)
    save_group_settings()
    bot.send_message(message.chat.id,
        f"✅ <b>Extra Group Added!</b>\n\n"
        f"🆔 ID: <code>{state.get('id')}</code>\n"
        f"🤖 Bot Link: {state.get('bot_link') or '—'}\n"
        f"📢 Channel Link: {state.get('channel_link') or '—'}",
        parse_mode="HTML")
    _show_extra_groups(message)


def _eg_edit_link_step(message):
    """Handle link edit input for an existing extra group."""
    uid = message.from_user.id
    if _is_back(message.text) or _intercept_menu_btn(message):
        _go_admin_panel(message)
        return
    state = _eg_state.pop(uid, {})
    idx = state.get("_edit_idx")
    field = state.get("_field")
    extra = _group_settings.get("extra_groups", [])
    if idx is None or field is None or idx >= len(extra):
        bot.send_message(message.chat.id, "❌ State error — please try again.")
        _show_extra_groups(message)
        return
    txt = (message.text or "").strip()
    extra[idx][field] = "" if txt.lower() == "skip" else txt
    save_group_settings()
    gid = extra[idx].get("id", "?")
    bot.send_message(
        message.chat.id,
        f"✅ <b>Group #{idx+1} Updated!</b>\n\n"
        f"🆔 ID: <code>{gid}</code>\n"
        f"🤖 Bot Link: {extra[idx].get('bot_link') or '—'}\n"
        f"📢 Channel Link: {extra[idx].get('channel_link') or '—'}",
        parse_mode="HTML"
    )
    _show_extra_groups(message)


def v3_panel_monitor():
    global seen_otps
    print("[V3-MONITOR] Started. Pre-loading existing records...")
    existing = fetch_v3_panel()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[V3-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            if _group_settings.get("v3_enabled", True):
                process_new_otps(fetch_v3_panel())
        except Exception as e:
            print(f"[V3-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


# ──────────────────────────────────────────────────────────────────────────────

def _start_dynamic_panel(panel):
    pid = panel["id"]
    with _stats_lock:
        _panel_stats[pid] = {
            "name": panel.get("username", pid),
            "host": panel.get("host", ""),
            "status": "⏳",
            "count": 0,
            "last": None,
            "errors": 0,
        }

    def monitor():
        global seen_otps
        print(f"[{pid}-MONITOR] Started. Pre-loading existing records...")
        existing = _universal_fetch(panel)
        with seen_lock:
            for key in existing:
                seen_otps[key] = True
            save_json(SEEN_FILE, seen_otps)
        print(f"[{pid}-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
        while True:
            try:
                process_new_otps(_universal_fetch(panel))
            except Exception as e:
                print(f"[{pid}-MONITOR] Loop error: {e}")
            time.sleep(POLL_INTERVAL)

    threading.Thread(target=monitor, daemon=True).start()


# ─── IVA SMS (ivasms.com) engine ─────────────────────────────────────────────

_iva_scrapers: dict = {}
_iva_lock_map: dict = {}


def _iva_get_lock(pid):
    if pid not in _iva_lock_map:
        _iva_lock_map[pid] = threading.Lock()
    return _iva_lock_map[pid]


_IVA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _iva_make_session(cookie_str=""):
    """Create a plain requests.Session with browser headers + optional cookies."""
    sess = requests.Session()
    sess.headers.update(_IVA_HEADERS)
    if cookie_str:
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                sess.cookies.set(k.strip(), v.strip(), domain="ivasms.com")
    return sess


# Keep old name for compatibility
def _iva_make_scraper():
    return _iva_make_session()


def _iva_set_cookies(sess, cookie_str):
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            sess.cookies.set(k.strip(), v.strip(), domain="ivasms.com")


def _iva_login(panel):
    """Login to ivasms.com using browser cookies (plain requests — no cloudscraper).
    Railway/cloud server IPs are blocked by Cloudflare for email/password login,
    so we ONLY support cookie-based login here.
    """
    pid     = panel["id"]
    cookies = panel.get("cookie_str", "")
    base    = "https://ivasms.com"

    if not cookies:
        return False

    sess = _iva_make_session(cookies)
    try:
        r = sess.get(
            f"{base}/portal/sms/received",
            timeout=20,
            allow_redirects=True,
        )
        if r.status_code == 200 and "login" not in r.url.lower():
            _iva_scrapers[pid] = sess
            print(f"[{pid}] ✅ IVA SMS: Cookie login OK ({r.url})")
            return True
        print(f"[{pid}] ❌ IVA SMS: Cookie login failed — status={r.status_code} url={r.url}")
        return False
    except Exception as e:
        print(f"[{pid}] ❌ IVA SMS cookie login error: {e}")
        return False


def _iva_parse_page(html):
    """Parse ivasms.com SMS received page → {key: (number, otp, sms_txt, service)}."""
    found = {}

    # 1) Embedded JS array (e.g. var data = [...])
    for pat in [
        r'(?:data|rows|messages|smsList|records|smsData)\s*[:=]\s*(\[.*?\])\s*[,;]',
        r'\.DataTable\([^)]*data\s*:\s*(\[.*?\])',
    ]:
        m = re.search(pat, html, re.DOTALL | re.I)
        if m:
            try:
                records = json.loads(m.group(1))
                for rec in records:
                    if not isinstance(rec, dict):
                        continue
                    num = str(rec.get("number", rec.get("phone", rec.get("msisdn", ""))))
                    txt = str(rec.get("message", rec.get("sms", rec.get("text", rec.get("body", "")))))
                    svc = str(rec.get("service", rec.get("cli", rec.get("sender", "IVA"))))
                    otp = extract_otp_from_sms(txt)
                    if num and otp:
                        found[f"{num}:{txt}"] = (num, otp, txt, svc)
                if found:
                    return found
            except Exception:
                pass

    # 2) HTML table: look for rows with phone number + SMS content
    from html.parser import HTMLParser
    class _TblParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.rows, self._cur_row, self._cur_cell, self._in_td = [], [], [], False
        def handle_starttag(self, tag, attrs):
            if tag == "tr":   self._cur_row = []
            elif tag == "td": self._in_td = True; self._cur_cell = []
        def handle_endtag(self, tag):
            if tag == "td":
                self._cur_row.append("".join(self._cur_cell).strip())
                self._in_td = False
            elif tag == "tr" and self._cur_row:
                self.rows.append(self._cur_row)
        def handle_data(self, data):
            if self._in_td: self._cur_cell.append(data)

    parser = _TblParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    phone_re = re.compile(r"^\+?\d{7,15}$")
    for row in parser.rows:
        clean = [re.sub(r"\s+", " ", c).strip() for c in row]
        nums = [c for c in clean if phone_re.match(c)]
        smses = [c for c in clean if extract_otp_from_sms(c)]
        if nums and smses:
            n, t = nums[0], smses[0]
            found[f"{n}:{t}"] = (n, extract_otp_from_sms(t), t, "IVA")

    return found


def _iva_parse_rows(rows, default_svc="IVA"):
    """Convert a list of dicts (DataTables / JSON) to found-dict entries."""
    found = {}
    for rec in rows:
        if not isinstance(rec, dict):
            # DataTables may return list-of-lists
            continue
        num = str(rec.get("number", rec.get("phone", rec.get("msisdn",
              rec.get("sender", rec.get("from", ""))))))
        txt = str(rec.get("message", rec.get("sms", rec.get("text",
              rec.get("body", rec.get("content", ""))))))
        svc = str(rec.get("service", rec.get("cli", rec.get("application",
              rec.get("app", rec.get("shortcode", default_svc))))))
        otp = extract_otp_from_sms(txt)
        if num and otp:
            found[f"{num}:{txt}"] = (num, otp, txt, svc)
    return found


def _iva_dt_post(scraper, url, csrf_token, page_html="", start=0, length=100):
    """Send a DataTables server-side POST and return parsed rows."""
    today = time.strftime("%Y-%m-%d")
    payload = {
        "draw": "1",
        "start": str(start),
        "length": str(length),
        "search[value]": "",
        "search[regex]": "false",
        "_token": csrf_token,
        "start_date": today,
        "end_date": today,
        # Common DataTables column ordering params (harmless if unused)
        "order[0][column]": "0",
        "order[0][dir]": "desc",
    }
    hdrs = {
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*",
        "Referer": "https://ivasms.com/portal/sms/received",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    r = scraper.post(url, data=payload, headers=hdrs, timeout=25)
    if r.status_code != 200:
        return None, r.status_code
    ct = r.headers.get("Content-Type", "")
    if "json" not in ct:
        return None, 0
    try:
        return r.json(), 200
    except Exception:
        return None, 0


def _iva_fetch(panel):
    """Fetch latest OTPs from ivasms.com.

    Strategy (in order):
      1. Load /portal/sms/received, grab CSRF token + discover AJAX URL
      2. Try DataTables POST to the discovered/candidate AJAX endpoints
      3. Fall back to plain HTML table parse of the page
    """
    pid  = panel["id"]
    base = "https://ivasms.com"
    found = {}

    with _iva_get_lock(pid):
        scraper = _iva_scrapers.get(pid)
        if not scraper:
            if not _iva_login(panel):
                _record_error(pid)
                return found
            scraper = _iva_scrapers[pid]

        today = time.strftime("%Y-%m-%d")

        # ── Step 1: load the page ─────────────────────────────────────────────
        try:
            r = scraper.get(f"{base}/portal/sms/received",
                            params={"start_date": today, "end_date": today},
                            timeout=30)
        except Exception as e:
            print(f"[{pid}] IVA page load error: {e}")
            _iva_scrapers.pop(pid, None)
            _record_error(pid)
            return found

        # Session expired?
        if r.status_code != 200 or "login" in r.url.lower():
            print(f"[{pid}] IVA session expired → re-login")
            _iva_scrapers.pop(pid, None)
            if not _iva_login(panel):
                _record_error(pid)
                return found
            scraper = _iva_scrapers[pid]
            try:
                r = scraper.get(f"{base}/portal/sms/received",
                                params={"start_date": today, "end_date": today},
                                timeout=30)
            except Exception as e:
                print(f"[{pid}] IVA page reload error: {e}")
                _record_error(pid)
                return found

        html = r.text

        # ── Step 2: extract CSRF token from page ──────────────────────────────
        csrf = ""
        for pat in [
            r'<meta[^>]+name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']',
            r'"_token"\s*:\s*"([^"]+)"',
            r"_token[\"']\s*:\s*[\"']([^\"']+)[\"']",
            r'<input[^>]+name=["\']_token["\'][^>]*value=["\']([^"\']+)["\']',
        ]:
            m = re.search(pat, html, re.I)
            if m:
                csrf = m.group(1)
                break

        # ── Step 3: discover DataTables AJAX URL from page JS ─────────────────
        # Looks for patterns like: ajax: '/portal/sms/received/data'  or  url: '...'
        ajax_url_candidates = []
        for pat in [
            r"""ajax\s*:\s*['"](\/portal\/sms\/[^'"]+)['"]""",
            r"""url\s*:\s*['"](\/portal\/sms\/[^'"]+)['"]""",
            r"""action\s*=\s*['"](\/portal\/sms\/[^'"]+)['"]""",
            r"""fetch\(['"](\/portal\/sms\/[^'"?]+)""",
        ]:
            for m in re.finditer(pat, html, re.I):
                ep = m.group(1)
                if ep not in ajax_url_candidates:
                    ajax_url_candidates.append(ep)

        # Add hardcoded fallback candidates (most common Laravel SMS panel patterns)
        for fallback in [
            "/portal/sms/received/data",
            "/portal/sms/received-data",
            "/portal/received/sms/data",
            "/portal/sms/datatable",
            "/portal/sms/ajax",
            "/portal/sms/list",
            "/portal/api/sms/received",
            "/portal/sms/received",          # POST to same URL (common)
        ]:
            if fallback not in ajax_url_candidates:
                ajax_url_candidates.append(fallback)

        # ── Step 4: try DataTables POST on each candidate ─────────────────────
        for ep in ajax_url_candidates:
            ep_url = base + ep if ep.startswith("/") else ep
            try:
                js, code = _iva_dt_post(scraper, ep_url, csrf, html)
                if js is None:
                    continue
                # DataTables standard: {"draw":N, "data":[...], "recordsTotal":N}
                rows = (js if isinstance(js, list)
                        else js.get("data", js.get("records",
                             js.get("rows", js.get("sms", [])))))
                if isinstance(rows, list) and rows:
                    # Rows may be list-of-dicts or list-of-lists
                    if isinstance(rows[0], dict):
                        found = _iva_parse_rows(rows)
                    else:
                        # list-of-lists: try to figure out columns from header
                        # Best-effort: assume [id, number, message, service, ...]
                        for row in rows:
                            if len(row) >= 3:
                                num = str(row[1]) if len(row) > 1 else ""
                                txt = str(row[2]) if len(row) > 2 else ""
                                svc = str(row[3]) if len(row) > 3 else "IVA"
                                otp = extract_otp_from_sms(txt)
                                if num and otp:
                                    found[f"{num}:{txt}"] = (num, otp, txt, svc)
                    if found:
                        print(f"[{pid}] ✅ IVA DataTables hit: {ep_url} → {len(found)} OTPs")
                        # Remember this working endpoint for next time
                        if panel.get("iva_ajax_url") != ep_url:
                            panel["iva_ajax_url"] = ep_url
                            save_dynamic_panels()
                        break
            except Exception as ex:
                print(f"[{pid}] IVA AJAX probe {ep}: {ex}")
                continue

        # ── Step 5: fall back to static HTML table parse ─────────────────────
        if not found:
            found = _iva_parse_page(html)
            if found:
                print(f"[{pid}] ✅ IVA HTML-table parse → {len(found)} OTPs")

        _record_fetch(pid, len(found))
        if found:
            print(f"[{pid}] ✅ IVA SMS total: {len(found)} OTPs found")
        else:
            # Debug: log first 300 chars of page so we know what we're getting
            preview = html[:300].replace("\n", " ").strip()
            print(f"[{pid}] IVA SMS: 0 OTPs. Page preview: {preview}")

    return found


# ─────────────────────────────────────────────────────────────────────────────


def extract_otp_from_sms(sms_text):
    if not sms_text:
        return None
    sms_text = str(sms_text).strip()
    if len(sms_text) < 4:
        return None
    # Pure short numeric codes (4-8 digits only) — treat directly as OTP
    # WhatsApp/Telegram panels sometimes store just the raw code
    if re.match(r"^\d{4,8}$", sms_text):
        return sms_text
    # WhatsApp format: "123-456" or "123 456" (digits separated by dash/space)
    wa_m = re.match(r"^(\d{3})[- ](\d{3})$", sms_text)
    if wa_m:
        return wa_m.group(1) + wa_m.group(2)
    # Must have at least 1 letter for longer strings — pure long digit strings
    # (e.g. phone numbers "88017XXXXXXX") are not OTPs.
    # Non-Latin script (Japanese, Chinese, Arabic etc.) counts as a letter too —
    # those SMS always contain non-ASCII characters alongside the OTP digits.
    has_latin = bool(re.search(r"[a-zA-Z]", sms_text))
    has_non_ascii = bool(re.search(r"[^\x00-\x7F]", sms_text))
    if not has_latin and not has_non_ascii:
        return None
    cleaned = re.sub(r"(?<=\d) (?=\d)", "", sms_text)
    cleaned = re.sub(r"(\d)-(\d)", r"\1\2", cleaned)
    cleaned = re.sub(r"(\d)\.(\d)", r"\1\2", cleaned)
    m = re.search(r"\b(\d{4,8})\b", cleaned, re.ASCII)
    return m.group(1) if m else None


# ── Panel 1 login & fetch (Mahofuza) ─────────────────────────────────────────


def p1_login():
    global _p1_session, _p1_sesskey
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = sess.get(P1_LOGIN_PAGE, timeout=15)
        m = re.search(r"What is (\d+) \+ (\d+)", r.text)
        if not m:
            print("[P1] Could not find captcha")
            return False
        answer = int(m.group(1)) + int(m.group(2))
        r2 = sess.post(
            P1_SIGNIN_URL,
            data={"username": P1_USER_NAME, "password": P1_PASSWORD, "capt": answer},
            timeout=15,
            allow_redirects=True,
        )
        if "login" in r2.url.lower() or "login" in r2.text.lower()[:500]:
            print("[P1] Login failed — still on login page")
            return False
        r3 = sess.get(
            P1_CDR_PAGE, timeout=15, headers={"Referer": P1_BASE_URL + "/agent/"}
        )
        sk = re.search(r"sesskey=([A-Za-z0-9+/=]+)", r3.text)
        _p1_sesskey = sk.group(1) if sk else ""
        _p1_session = sess
        print(f"[P1] Logged in. sesskey={_p1_sesskey}")
        return True
    except Exception as e:
        print(f"[P1] Login error: {e}")
        return False


def fetch_panel1():
    global _p1_session, _p1_sesskey
    found = {}
    with _p1_lock:
        try:
            today = time.strftime("%Y-%m-%d")

            def build_url():
                return (
                    f"{P1_CDR_DATA_URL}"
                    f"?fdate1={today}%2000:00:00"
                    f"&fdate2={today}%2023:59:59"
                    f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth="
                    f"&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0"
                    f"&sesskey={_p1_sesskey or ''}"
                )

            headers = {"Referer": P1_CDR_PAGE, "X-Requested-With": "XMLHttpRequest"}
            if _p1_session is None:
                if not p1_login():
                    return found
            r = _p1_session.get(build_url(), headers=headers, timeout=15)
            body = r.text.strip()
            if (
                r.status_code != 200
                or not body
                or body.startswith("<")
                or "Direct Script" in body
            ):
                print(f"[P1] Bad response ({r.status_code}), re-logging in.")
                _p1_session = None
                if not p1_login():
                    return found
                r = _p1_session.get(build_url(), headers=headers, timeout=15)
                body = r.text.strip()
            rows = json.loads(body).get("aaData", [])
            for row in rows:
                number = str(row[2]).strip()
                service = str(row[3]).strip()
                sms_txt = str(row[5]).strip()
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch("p1", len(rows))
            if found:
                print(f"[P1] ✅ Fetched {len(found)} records.")
        except Exception as e:
            print(f"[P1] Fetch error: {e}")
            _record_error("p1")
            _p1_session = None
    return found


# ── Panel 2 login & fetch (Sagardas50 / XISORA) ──────────────────────────────


def p2_login():
    global _p2_session
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = sess.post(
            P2_SIGNIN_URL,
            data={"username": P2_USER_NAME, "password": P2_PASSWORD},
            timeout=15,
            allow_redirects=True,
        )
        if "signin" in r.url.lower() or "login" in r.url.lower():
            print("[P2] Login failed — still on login page")
            return False
        _p2_session = sess
        print(f"[P2] Logged in. URL={r.url}")
        return True
    except Exception as e:
        print(f"[P2] Login error: {e}")
        return False


def fetch_panel2():
    global _p2_session
    found = {}
    with _p2_lock:
        try:
            today = time.strftime("%Y-%m-%d")
            url = (
                f"{P2_DATA_URL}"
                f"?fdate1={today}%2000:00:00"
                f"&fdate2={today}%2023:59:59"
                f"&ftermination=&fclient=&fnum=&fcli="
                f"&fgdate=0&fgtermination=0&fgclient=0&fgnumber=0&fgcli=0&fg=0"
            )
            headers = {"Referer": P2_REPORTS_PAGE, "X-Requested-With": "XMLHttpRequest"}
            if _p2_session is None:
                if not p2_login():
                    return found
            r = _p2_session.get(url, headers=headers, timeout=15)
            body = r.text.strip()
            if r.status_code != 200 or not body or body.startswith("<"):
                print(f"[P2] Bad response ({r.status_code}), re-logging in.")
                _p2_session = None
                if not p2_login():
                    return found
                r = _p2_session.get(url, headers=headers, timeout=15)
                body = r.text.strip()
            rows = json.loads(body).get("aaData", [])
            for row in rows:
                if not isinstance(row[0], str):
                    continue
                number = str(row[2]).strip()
                service = str(row[3]).strip()
                sms_txt = str(row[10]).strip()
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch("p2", len(rows))
            if found:
                print(f"[P2] ✅ Fetched {len(found)} records.")
        except Exception as e:
            print(f"[P2] Fetch error: {e}")
            _record_error("p2")
            _p2_session = None
    return found


# ── Shared OTP processor ──────────────────────────────────────────────────────


def process_new_otps(current):
    global seen_otps
    for key, (number, otp, sms_txt, service) in current.items():
        with seen_lock:
            if key in seen_otps:
                continue
            seen_otps[key] = True
            save_json(SEEN_FILE, seen_otps)
        clean = re.sub(r"\D", "", str(number))
        with user_map_lock:
            t_start = assigned_time.get(clean)
        seconds = int(time.time() - t_start) if t_start else 0
        _dispatch_otp(otp, number, seconds, service, sms_txt or "")
        print(
            f"[MONITOR] ✅ Forwarded OTP={otp} for {number} ({service}) in {seconds}s"
        )


# ── Global OTP monitors ───────────────────────────────────────────────────────


def panel1_monitor():
    global seen_otps
    print("[P1-MONITOR] Started. Pre-loading existing records...")
    existing = fetch_panel1()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[P1-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            process_new_otps(fetch_panel1())
        except Exception as e:
            print(f"[P1-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


def panel2_monitor():
    global seen_otps
    print("[P2-MONITOR] Started. Pre-loading existing records...")
    existing = fetch_panel2()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[P2-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            process_new_otps(fetch_panel2())
        except Exception as e:
            print(f"[P2-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


# ── Panel 3 login & fetch (Rabbi1_FD) ────────────────────────────────────────


def p3_login():
    global _p3_session, _p3_csstr
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = sess.get(P3_LOGIN_PAGE, timeout=15)
        m = re.search(r"What is (\d+) \+ (\d+)", r.text)
        if not m:
            print("[P3] Could not find captcha")
            return False
        answer = int(m.group(1)) + int(m.group(2))
        r2 = sess.post(
            P3_SIGNIN_URL,
            data={"username": P3_USER_NAME, "password": P3_PASSWORD, "capt": answer},
            timeout=15,
            allow_redirects=True,
        )
        if "login" in r2.url.lower() or "signin" in r2.url.lower():
            print("[P3] Login failed — still on login page")
            return False
        r3 = sess.get(
            P3_CDR_PAGE, timeout=15, headers={"Referer": P3_BASE_URL + "/agent/"}
        )
        cs = re.search(r"csstr=([a-f0-9]+)", r3.text)
        _p3_csstr = cs.group(1) if cs else ""
        _p3_session = sess
        print(f"[P3] Logged in. csstr={_p3_csstr}")
        return True
    except Exception as e:
        print(f"[P3] Login error: {e}")
        return False


def fetch_panel3():
    global _p3_session, _p3_csstr
    found = {}
    with _p3_lock:
        try:
            today = time.strftime("%Y-%m-%d")

            def build_url():
                return (
                    f"{P3_CDR_DATA_URL}"
                    f"?fdate1={today}%2000:00:00"
                    f"&fdate2={today}%2023:59:59"
                    f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth="
                    f"&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0"
                    f"&csstr={_p3_csstr or ''}"
                )

            headers = {"Referer": P3_CDR_PAGE, "X-Requested-With": "XMLHttpRequest"}
            if _p3_session is None:
                if not p3_login():
                    return found
            r = _p3_session.get(build_url(), headers=headers, timeout=15)
            body = r.text.strip()
            if (
                r.status_code != 200
                or not body
                or body.startswith("<")
                or "Direct Script" in body
            ):
                print(f"[P3] Bad response ({r.status_code}), re-logging in.")
                _p3_session = None
                if not p3_login():
                    return found
                r = _p3_session.get(build_url(), headers=headers, timeout=15)
                body = r.text.strip()
            rows = json.loads(body).get("aaData", [])
            for row in rows:
                if not isinstance(row[0], str):
                    continue
                number = str(row[2]).strip()
                service = str(row[3]).strip()
                sms_txt = str(row[5]).strip()
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch("p3", len(rows))
            if found:
                print(f"[P3] ✅ Fetched {len(found)} records.")
        except Exception as e:
            print(f"[P3] Fetch error: {e}")
            _record_error("p3")
            _p3_session = None
    return found


def panel3_monitor():
    global seen_otps
    print("[P3-MONITOR] Started. Pre-loading existing records...")
    existing = fetch_panel3()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[P3-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            process_new_otps(fetch_panel3())
        except Exception as e:
            print(f"[P3-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


# ── Panel 4 login & fetch (Rabbi12 / 144.217.71.192) ─────────────────────────


def p4_login():
    global _p4_session, _p4_sesskey
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = sess.get(P4_LOGIN_PAGE, timeout=15)
        m = re.search(r"What is (\d+) \+ (\d+)", r.text)
        if not m:
            print("[P4] Could not find captcha")
            return False
        answer = int(m.group(1)) + int(m.group(2))
        r2 = sess.post(
            P4_SIGNIN_URL,
            data={"username": P4_USER_NAME, "password": P4_PASSWORD, "capt": answer},
            timeout=15,
            allow_redirects=True,
        )
        if "SMSDashboard" not in r2.url and "agent" not in r2.url:
            print(f"[P4] Login failed: {r2.url}")
            return False
        r3 = sess.get(
            P4_CDR_PAGE, timeout=15, headers={"Referer": P4_BASE_URL + "/agent/"}
        )
        sk = re.search(r"sesskey=([A-Za-z0-9+/=]+)", r3.text)
        _p4_sesskey = sk.group(1) if sk else ""
        _p4_session = sess
        print(f"[P4] Logged in. sesskey={_p4_sesskey}")
        return True
    except Exception as e:
        print(f"[P4] Login error: {e}")
        return False


def fetch_panel4():
    global _p4_session, _p4_sesskey
    found = {}
    with _p4_lock:
        if not _p4_session and not p4_login():
            return found
        today = time.strftime("%Y-%m-%d")

        def build_url():
            return (
                f"{P4_CDR_DATA_URL}"
                f"?fdate1={today}%2000:00:00&fdate2={today}%2023:59:59"
                f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth="
                f"&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0"
                f"&sesskey={_p4_sesskey}"
            )

        headers = {"Referer": P4_CDR_PAGE, "X-Requested-With": "XMLHttpRequest"}
        try:
            r = _p4_session.get(build_url(), headers=headers, timeout=15)
            body = r.text.strip()
            if (
                r.status_code != 200
                or not body
                or body.startswith("<")
                or "Direct Script" in body
            ):
                print(f"[P4] Bad response ({r.status_code}), re-logging in.")
                _p4_session = None
                if not p4_login():
                    return found
                r = _p4_session.get(build_url(), headers=headers, timeout=15)
                body = r.text.strip()
            rows = json.loads(body).get("aaData", [])
            for row in rows:
                if not isinstance(row[0], str):
                    continue
                number = str(row[2]).strip()
                service = str(row[3]).strip()
                sms_txt = str(row[5]).strip()
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch("p4", len(rows))
            if found:
                print(f"[P4] ✅ Fetched {len(found)} records.")
        except Exception as e:
            print(f"[P4] Fetch error: {e}")
            _record_error("p4")
            _p4_session = None
    return found


def panel4_monitor():
    global seen_otps
    print("[P4-MONITOR] Started. Pre-loading existing records...")
    existing = fetch_panel4()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[P4-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            process_new_otps(fetch_panel4())
        except Exception as e:
            print(f"[P4-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


# ── Panel 5 login & fetch (Rabbi12_v2 / 51.75.144.178) ───────────────────────


def p5_login():
    global _p5_session, _p5_sesskey
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = sess.get(P5_LOGIN_PAGE, timeout=15)
        m = re.search(r"What is (\d+) \+ (\d+)", r.text)
        if not m:
            print("[P5] Could not find captcha")
            return False
        answer = int(m.group(1)) + int(m.group(2))
        r2 = sess.post(
            P5_SIGNIN_URL,
            data={"username": P5_USER_NAME, "password": P5_PASSWORD, "capt": answer},
            timeout=15,
            allow_redirects=True,
        )
        if "SMSDashboard" not in r2.url and "agent" not in r2.url:
            print(f"[P5] Login failed: {r2.url}")
            return False
        r3 = sess.get(
            P5_CDR_PAGE, timeout=15, headers={"Referer": P5_BASE_URL + "/agent/"}
        )
        sk = re.search(r"sesskey=([A-Za-z0-9+/=]+)", r3.text)
        _p5_sesskey = sk.group(1) if sk else ""
        _p5_session = sess
        print(f"[P5] Logged in. sesskey={_p5_sesskey}")
        return True
    except Exception as e:
        print(f"[P5] Login error: {e}")
        return False


def fetch_panel5():
    global _p5_session, _p5_sesskey
    found = {}
    with _p5_lock:
        if not _p5_session and not p5_login():
            return found
        today = time.strftime("%Y-%m-%d")

        def build_url():
            return (
                f"{P5_CDR_DATA_URL}"
                f"?fdate1={today}%2000:00:00&fdate2={today}%2023:59:59"
                f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth="
                f"&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0"
                f"&sesskey={_p5_sesskey}"
            )

        headers = {"Referer": P5_CDR_PAGE, "X-Requested-With": "XMLHttpRequest"}
        try:
            r = _p5_session.get(build_url(), headers=headers, timeout=15)
            body = r.text.strip()
            if (
                r.status_code != 200
                or not body
                or body.startswith("<")
                or "Direct Script" in body
            ):
                print(f"[P5] Bad response ({r.status_code}), re-logging in.")
                _p5_session = None
                if not p5_login():
                    return found
                r = _p5_session.get(build_url(), headers=headers, timeout=15)
                body = r.text.strip()
            rows = json.loads(body).get("aaData", [])
            for row in rows:
                if not isinstance(row[0], str):
                    continue
                number = str(row[2]).strip()
                service = str(row[3]).strip()
                sms_txt = str(row[5]).strip()
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch("p5", len(rows))
            if found:
                print(f"[P5] ✅ Fetched {len(found)} records.")
        except Exception as e:
            print(f"[P5] Fetch error: {e}")
            _record_error("p5")
            _p5_session = None
    return found


def panel5_monitor():
    global seen_otps
    print("[P5-MONITOR] Started. Pre-loading existing records...")
    existing = fetch_panel5()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[P5-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            process_new_otps(fetch_panel5())
        except Exception as e:
            print(f"[P5-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


# ── Panel 6 login & fetch (TrueSMS.net / SMSRanges) ──────────────────────────


def p6_login():
    global _p6_session, _p6_sesskey
    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = sess.get(P6_LOGIN_PAGE, timeout=20, verify=False)
        m = re.search(r"What is (\d+) \+ (\d+)", r.text)
        if m:
            answer = int(m.group(1)) + int(m.group(2))
            r2 = sess.post(
                P6_SIGNIN_URL,
                data={
                    "username": P6_USER_NAME,
                    "password": P6_PASSWORD,
                    "capt": answer,
                },
                timeout=20,
                allow_redirects=True,
                verify=False,
            )
        else:
            r2 = sess.post(
                P6_SIGNIN_URL,
                data={"username": P6_USER_NAME, "password": P6_PASSWORD},
                timeout=20,
                allow_redirects=True,
                verify=False,
            )
        if "login" in r2.url.lower() and "agent" not in r2.url.lower():
            print(f"[P6] Login failed: {r2.url}")
            return False
        r3 = sess.get(
            P6_CDR_PAGE,
            timeout=20,
            headers={"Referer": P6_BASE_URL + "/agent/"},
            verify=False,
        )
        sk = re.search(r"sesskey=([A-Za-z0-9+/=]+)", r3.text)
        cs = re.search(r"csstr=([a-f0-9]+)", r3.text)
        _p6_sesskey = sk.group(1) if sk else (cs.group(1) if cs else "")
        _p6_session = sess
        print(f"[P6] Logged in. token={_p6_sesskey[:10] if _p6_sesskey else 'none'}")
        return True
    except Exception as e:
        print(f"[P6] Login error: {e}")
        return False


def fetch_panel6():
    global _p6_session, _p6_sesskey
    found = {}
    with _p6_lock:
        try:
            today = time.strftime("%Y-%m-%d")

            def build_url():
                return (
                    f"{P6_CDR_DATA_URL}"
                    f"?fdate1={today}%2000:00:00"
                    f"&fdate2={today}%2023:59:59"
                    f"&frange=&fclient=&fnum=&fcli=&fgdate=&fgmonth="
                    f"&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0"
                    f"&sesskey={_p6_sesskey or ''}"
                )

            headers = {"Referer": P6_CDR_PAGE, "X-Requested-With": "XMLHttpRequest"}
            if _p6_session is None:
                if not p6_login():
                    return found
            r = _p6_session.get(build_url(), headers=headers, timeout=20, verify=False)
            body = r.text.strip()
            if (
                r.status_code != 200
                or not body
                or body.startswith("<")
                or "Direct Script" in body
            ):
                print(f"[P6] Bad response ({r.status_code}), re-logging in.")
                _p6_session = None
                if not p6_login():
                    return found
                r = _p6_session.get(
                    build_url(), headers=headers, timeout=20, verify=False
                )
                body = r.text.strip()
            rows = json.loads(body).get("aaData", [])
            for row in rows:
                if not isinstance(row[0], str):
                    continue
                number = str(row[2]).strip()
                service = str(row[3]).strip() if len(row) > 3 else "TrueSMS"
                sms_txt = str(row[5]).strip() if len(row) > 5 else ""
                if not sms_txt and len(row) > 4:
                    sms_txt = str(row[4]).strip()
                otp = extract_otp_from_sms(sms_txt)
                if otp:
                    key = f"{number}:{sms_txt}"
                    found[key] = (number, otp, sms_txt, service)
            _record_fetch("p6", len(rows))
            if found:
                print(f"[P6] ✅ Fetched {len(found)} records.")
        except Exception as e:
            print(f"[P6] Fetch error: {e}")
            _record_error("p6")
            _p6_session = None
    return found


def panel6_monitor():
    global seen_otps
    print("[P6-MONITOR] Started (TrueSMS/SMSRanges). Pre-loading existing records...")
    existing = fetch_panel6()
    with seen_lock:
        for key in existing:
            seen_otps[key] = True
        save_json(SEEN_FILE, seen_otps)
    print(f"[P6-MONITOR] Pre-loaded {len(existing)} records. Watching for new ones...")
    while True:
        try:
            process_new_otps(fetch_panel6())
        except Exception as e:
            print(f"[P6-MONITOR] Loop error: {e}")
        time.sleep(POLL_INTERVAL)


# ── Demo OTP monitor ──────────────────────────────────────────────────────────


def _demo_fire_service(cfg_name, digits, numbers, svc):
    """Send one demo OTP for a single service to main group + all extra groups."""
    otp = "".join([str(random.randint(0, 9)) for _ in range(digits)])
    number = random.choice(numbers)
    # Main group
    main_grp = get_otp_group_id()
    if main_grp:
        try:
            send_otp_message(main_grp, otp, number, "—", svc, "")
        except Exception as e:
            print(f"[DEMO] {cfg_name} main group error ({svc}): {e}")
    # Extra groups
    extra_grps = _group_settings.get("extra_groups", [])
    for eg in extra_grps:
        eg_id = eg.get("id")
        if eg_id:
            try:
                _send_to_extra_group(eg_id, otp, number, "—", svc, "", eg)
            except Exception as e:
                print(f"[DEMO] {cfg_name} extra group {eg_id} error ({svc}): {e}")


def demo_monitor():
    print("[DEMO] Thread started.")
    while True:
        now = time.time()
        with _demo_lock:
            configs = list(_demo_configs)
        for cfg in configs:
            if not cfg.get("active"):
                continue
            cid = cfg["id"]
            if now >= _demo_next_fire.get(cid, 0):
                _demo_next_fire[cid] = now + cfg["interval"]
                services = cfg.get("services") or ["Facebook"]
                digits = cfg["digits"]
                numbers = cfg["numbers"]
                cfg_name = cfg["name"]
                # Fire all services simultaneously in separate threads
                threads = []
                for svc in services:
                    t = threading.Thread(
                        target=_demo_fire_service,
                        args=(cfg_name, digits, numbers, svc),
                        daemon=True
                    )
                    t.start()
                    threads.append(t)
        time.sleep(1)


def demo_status_text():
    with _demo_lock:
        configs = list(_demo_configs)
    running = [c for c in configs if c.get("active")]
    status = f"🟢 <b>{len(running)} running</b>" if running else "🔴 <b>All stopped</b>"
    lines = (
        f"🎭🔥 <b>DEMO OTP PANEL</b> 🔥🎭\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"📡 <b>Status ▸▸</b>  {status}\n"
        f"📋 <b>Configs:</b>  {len(configs)}\n\n"
    )
    for cfg in configs:
        icon = "🟢" if cfg.get("active") else "🔴"
        svcs = ", ".join(cfg.get("services") or ["?"])
        nums = cfg["numbers"]
        lines += (
            f"{icon} <b>{cfg['name']}</b>\n"
            f"  💬 {svcs}  |  🔢 {cfg['digits']} digits  |  ⏱️ {cfg['interval']}s  |  📱 {len(nums)} num\n\n"
        )
    lines += "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>"
    return lines


def demo_cfg_inline_markup():
    with _demo_lock:
        configs = list(_demo_configs)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for cfg in configs:
        icon = "⏹️ Stop" if cfg.get("active") else "▶️ Start"
        action = "stop" if cfg.get("active") else "start"
        markup.add(
            types.InlineKeyboardButton(
                f"{icon}  {cfg['name']}",
                callback_data=f"cfg_toggle:{cfg['id']}:{action}", style="success"
            )
        )
    return markup


def demo_menu_markup():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    with _demo_lock:
        cfg_count = len(_demo_configs)
    m.add("➕ 𝗖𝗼𝗻𝗳𝗶𝗴 𝗬𝗼𝗴 𝗞𝗼𝗿𝗼")
    if cfg_count > 0:
        m.add("🗑️ 𝗖𝗼𝗻𝗳𝗶𝗴 𝗠𝘂𝗰𝗵𝗼")
    m.add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟")
    return m


