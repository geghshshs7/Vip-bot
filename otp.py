# ── OTP Messages ──────────────────────────────────────────────────────────────


def _ensure_code_tag(text, value):
    """Wrap `value` in <code> if not already wrapped.
    Only replaces occurrences outside of HTML tags so that tg-emoji emoji-id
    attributes (which contain long digit strings) are never corrupted."""
    v = str(value)
    if f"<code>{v}</code>" in text:
        return text
    # Split on HTML tags; odd-indexed parts are tags, even-indexed are plain text
    parts = re.split(r'(<[^>]*>)', text)
    replaced = False
    result = []
    for part in parts:
        if not replaced and not re.match(r'^<[^>]*>$', part) and v in part:
            part = part.replace(v, f'<code>{v}</code>', 1)
            replaced = True
        result.append(part)
    return ''.join(result)


def _send_with_retry(fn, max_retries=5, **kwargs):
    """Call fn(**kwargs) with up to max_retries on 429 rate-limit errors.
    Returns (result, rate_limit_seconds) tuple:
      - result: the API result or None on failure
      - rate_limit_seconds: >0 if all retries exhausted due to rate limit, else 0
    """
    last_wait = 0
    for attempt in range(max_retries):
        try:
            return fn(**kwargs), 0
        except Exception as e:
            err = str(e)
            if "429" in err or "Too Many Requests" in err:
                try:
                    last_wait = int(re.search(r"retry after (\d+)", err).group(1))
                except Exception:
                    last_wait = min(2 ** (attempt + 1), 30)
                capped = min(last_wait, 90)
                print(f"[RETRY] 429 for chat={kwargs.get('chat_id','?')} retry_after={last_wait}s — waiting {capped}s (attempt {attempt+1}/{max_retries})")
                time.sleep(capped)
            else:
                raise
    print(f"[RETRY] All {max_retries} attempts failed for chat={kwargs.get('chat_id','?')} — rate limited {last_wait}s")
    return None, last_wait


# ── Service name auto-detection from SMS text ────────────────────────────────
_SMS_SERVICE_PATTERNS = [
    ("INSTAGRAM",  ["instagram"]),
    ("FACEBOOK",   ["facebook", "fb.com"]),
    ("WHATSAPP",   ["whatsapp"]),
    ("DISCORD",    ["discord"]),
    ("TELEGRAM",   ["telegram"]),
    ("STRIPE",     ["stripe"]),
    ("TIKTOK",     ["tiktok", "tik tok"]),
    ("SNAPCHAT",   ["snapchat"]),
    ("TWITTER",    ["twitter", "x.com"]),
    ("GOOGLE",     ["google"]),
    ("YOUTUBE",    ["youtube"]),
    ("OPENAI",     ["openai", "chatgpt"]),
    ("MICROSOFT",  ["microsoft", "outlook", "hotmail"]),
    ("AMAZON",     ["amazon"]),
    ("NETFLIX",    ["netflix"]),
    ("PAYPAL",     ["paypal"]),
    ("BINANCE",    ["binance"]),
    ("COINBASE",   ["coinbase"]),
    ("LINKEDIN",   ["linkedin"]),
    ("REDDIT",     ["reddit"]),
    ("TWITCH",     ["twitch"]),
    ("UBER",       ["uber"]),
    ("YAHOO",      ["yahoo"]),
    ("APPLE",      ["apple id", "icloud"]),
    ("PINTEREST",  ["pinterest"]),
    ("SIGNAL",     ["signal"]),
    ("LINE",       ["line app", "line verification"]),
    ("VIBER",      ["viber"]),
]


def _detect_service_from_sms(text):
    """Guess the service/app name from OTP SMS content. Returns '' if unknown."""
    if not text:
        return ""
    low = text.lower()
    for svc_name, keywords in _SMS_SERVICE_PATTERNS:
        if any(kw in low for kw in keywords):
            return svc_name
    return ""


def _build_otp_copy_button(otp_str):
    """Build the OTP copy button without displaying a redundant label."""
    _oc_text, _oc_icon = _btn_text_and_icon("otp_copy", "🔒 ")
    button_text = f"{_oc_text}{otp_str}" if _oc_text else str(otp_str)
    try:
        return types.InlineKeyboardButton(
            button_text,
            copy_text=types.CopyTextButton(text=str(otp_str)),
            style="success",
            **_oc_icon,
        )
    except Exception:
        return types.InlineKeyboardButton(
            str(otp_str),
            callback_data="noop",
            style="success",
            **_oc_icon,
        )


def send_otp_message(
    chat_id,
    otp,
    number,
    seconds,
    service="",
    sms_body="",
    force_group_fmt=False,
    _skip_reward=False,
):
    import html as _html
    # Detect service from SMS body first (more accurate), fall back to panel value
    _svc_raw = _detect_service_from_sms(sms_body) or service
    svc = _svc_raw.upper() if _svc_raw else "—"
    c_name, flag = get_country_details(number)
    otp_str = str(otp)
    _tag = get_group_tag()
    _tagged = tag_number(number, _tag)
    # HTML-escape SMS body so special chars (&, <, >) don't break Telegram HTML
    # parsing and force a plain-text fallback (which strips blockquotes)
    _sms_val = _html.escape(sms_body) if sms_body else "—"
    _rflag = _resolve_flag(flag)
    _emoji_extra = _msg_emoji_vars()   # {emoji_NAME: <tg-emoji>...} for custom emoji slots
    _svc_emoji_html = _v2_svc_emoji(svc)
    _emoji_number_pre  = _get_dm_emoji("number_pre")
    _emoji_country_pre = _get_dm_emoji("country_pre")
    _emoji_country_post= _get_dm_emoji("country_post")
    _country_short = get_country_short(number)
    _group_country_short = get_group_country_short(number, svc)
    _country_lang = get_country_language(_country_short)
    _sms_lang = detect_sms_language(sms_body)
    _grp_vars = {**_emoji_extra,
                 **dict(svc=svc, number=mask_number(number), tagged_number=_tagged,
                     taged_number=_tagged,
                     tagged_number_b=tag_number_bold(number, _tag),
                     country=c_name, flag=_rflag, otp=otp_str,
                     country_short=_country_short, country_lang=_country_lang,
                     country_short_b=to_math_bold(_group_country_short),
                     sms_lang=_sms_lang, sms_lang_b=to_math_bold(_sms_lang),
                     sms_body=_sms_val, sms=_sms_val,
                     vname=svc, text=_sms_val,
                     svc_emoji=_svc_emoji_html,
                     emoji_number_pre=_emoji_number_pre,
                     emoji_country_pre=_emoji_country_pre,
                     emoji_country_post=_emoji_country_post)}
    _dm_vars  = {**_emoji_extra,
                 **dict(svc=svc, number=(number if str(number).startswith("+") else "+" + str(number)),
                     tagged_number=_tagged, taged_number=_tagged,
                     country=c_name, flag=_rflag, otp=otp_str,
                     sms_body=_sms_val, sms=_sms_val,
                     vname=svc, text=_sms_val,
                     svc_emoji=_svc_emoji_html,
                     emoji_number_pre=_emoji_number_pre,
                     emoji_country_pre=_emoji_country_pre,
                     emoji_country_post=_emoji_country_post)}

    class _SafeDict(dict):
        """Return the original placeholder for any missing key so the template
        still renders instead of throwing KeyError and falling back to default."""
        def __missing__(self, k):
            return "{" + k + "}"

    def _make_bold_italic(text):
        """Wrap in bold+italic unless text has <blockquote> or <tg-emoji> (these break inside <b><i>)."""
        if "<blockquote>" in text or "<tg-emoji" in text:
            return text
        return f"<b><i>{text}</i></b>"

    def _build_message(key, vars_dict):
        """Return (text, used_default). Only falls back to default on truly
        unrecoverable errors (e.g. broken brace syntax like a lone '{')."""
        try:
            txt = get_template(key).format_map(_SafeDict(vars_dict))
            return _make_bold_italic(_ensure_code_tag(txt, otp_str)), False
        except Exception as e:
            print(f"[TEMPLATE] ⚠️ Custom template '{key}' format error ({e}), using default")
        try:
            txt = _DEFAULT_TEMPLATES[key].format_map(_SafeDict(vars_dict))
        except Exception:
            txt = otp_str
        return _make_bold_italic(_ensure_code_tag(txt, otp_str)), True

    def _try_send(label, chat_id, text, markup, parse_mode="HTML"):
        """Send message; if Telegram rejects it return (None, err_str)."""
        try:
            if label.startswith("DM"):
                _throttle_dm_send()
            result, rl = _send_with_retry(bot.send_message,
                                          chat_id=chat_id, text=text,
                                          parse_mode=parse_mode, reply_markup=markup)
            return result, rl, None
        except Exception as e:
            return None, 0, str(e)

    def _strip_html(txt):
        """Remove all HTML tags for plain text fallback."""
        import re as _re
        return _re.sub(r"<[^>]+>", "", txt)

    if chat_id == get_otp_group_id() or force_group_fmt:
        markup = types.InlineKeyboardMarkup()
        markup.add(_build_otp_copy_button(otp_str))
        _btns = []
        if get_bot_link():
            _nb_text, _nb_icon = _btn_text_and_icon("number_bot", "🤖 𝗡𝘂𝗺𝗯𝗲𝗿 𝗕𝗼𝘁")
            _btns.append(types.InlineKeyboardButton(_nb_text, url=get_bot_link(), style="primary", **_nb_icon))
        if get_channel2():
            _mc_text, _mc_icon = _btn_text_and_icon("main_channel", "📢 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹")
            _btns.append(types.InlineKeyboardButton(_mc_text, url=get_channel2(), style="danger", **_mc_icon))
        if _btns:
            markup.row(*_btns)

        message, used_default = _build_message("otp_group", _grp_vars)
        sent, rl, err = _try_send("GROUP", chat_id, message, markup)

        # If custom template caused a send error, retry with default HTML
        if err and not used_default:
            print(f"[OTP-GROUP] ⚠️ Send failed (custom template HTML error?): {err} — retrying with default")
            message = _ensure_code_tag(_DEFAULT_TEMPLATES["otp_group"].format_map(_SafeDict(_grp_vars)), otp_str)
            sent, rl, err = _try_send("GROUP-DEFAULT", chat_id, message, markup)

        # Last resort: strip HTML and send as plain text
        if err:
            print(f"[OTP-GROUP] ⚠️ HTML send failed: {err} — retrying as plain text")
            plain_msg = _strip_html(message)
            sent, rl, err = _try_send("GROUP-PLAIN", chat_id, plain_msg, markup, parse_mode=None)

        if err:
            print(f"[OTP-GROUP] ❌ Exception sending to group {chat_id}: {err}")
        elif sent:
            print(f"[OTP-GROUP] ✅ Sent OTP={otp_str} num={mask_number(number)} svc={svc} to group {chat_id}")
            if is_auto_delete():
                _schedule_delete(chat_id, sent.message_id)
        else:
            print(f"[OTP-GROUP] ❌ FAILED to send OTP={otp_str} num={mask_number(number)} — rate limited {rl}s")
        return bool(sent and not err)
    else:
        uid = chat_id  # DM: chat_id == user_id
        last_svc_info = _user_last_svc.get(uid)
        dm_markup = types.InlineKeyboardMarkup(row_width=2)
        dm_markup.add(_build_otp_copy_button(otp_str))
        _is_v2 = uid in _v2_users

        # NOTE: "Number Assigned" message is intentionally NOT deleted when OTP arrives.
        # The number stays visible in the user's chat until they explicitly request a new one.
        # _user_last_num_msg tracking is still maintained so "Change Number" works correctly.

        # Add reward — ONLY for Instagram and Facebook OTPs (not WhatsApp/Telegram)
        _REWARD_SVCS = {"INSTAGRAM", "FACEBOOK"}
        _reward_eligible = svc.upper() in _REWARD_SVCS
        _reward_amt = (
            get_reward_per_otp()
            if _reward_eligible and not _skip_reward
            else 0.0
        )
        _cur = get_currency()
        if _reward_eligible and _reward_amt > 0:
            _new_bal = add_reward(uid, _reward_amt)
        else:
            _new_bal = get_balance(uid)
        _reward_emoji = '<tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji>'
        _dm_vars["reward"]  = f"{_reward_emoji} {_cur}{_reward_amt:.2f}" if _reward_amt > 0 else ""
        _dm_vars["balance"] = f"{_cur}{_new_bal:.2f}"

        _dm_tpl_key = "otp_dm_v2" if _is_v2 else "otp_dm"
        message, used_default = _build_message(_dm_tpl_key, _dm_vars)

        # Always append reward line (even if template lacks {reward})
        if _reward_eligible and _reward_amt > 0:
            _reward_emoji  = '<tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji>'
            _balance_emoji = '<tg-emoji emoji-id="5197434882321567830">💰</tg-emoji>'
            message = message + f"\n\n{_reward_emoji} <b>+{_cur}{_reward_amt:.2f}</b>  |  {_balance_emoji} {_cur}{_new_bal:.2f}"

        result, rl, err = _try_send("DM", chat_id, message, dm_markup)

        # If send failed, retry with default template
        if err and not used_default:
            print(f"[OTP-DM] ⚠️ Send failed: {err} — retrying with default template")
            message = _ensure_code_tag(_DEFAULT_TEMPLATES[_dm_tpl_key].format_map(_SafeDict(_dm_vars)), otp_str)
            result, rl, err = _try_send("DM-DEFAULT", chat_id, message, dm_markup)

        # Last resort: strip all HTML and send as plain text
        if err:
            print(f"[OTP-DM] ⚠️ HTML send failed: {err} — retrying as plain text")
            plain_dm = _strip_html(message)
            result, rl, err = _try_send("DM-PLAIN", chat_id, plain_dm, dm_markup, parse_mode=None)

        if err:
            print(f"[OTP-DM] ❌ Exception sending to user {chat_id}: {err}")
        elif result:
            print(f"[OTP-DM] ✅ Sent OTP={otp_str} to user {chat_id}")
            # Do NOT store OTP message in _user_last_num_msg —
            # that tracker is only for "Number Assigned" messages
        else:
            print(f"[OTP-DM] ❌ FAILED to send OTP={otp_str} to user {chat_id} — rate limited {rl}s")
        return bool(result and not err)


_dm_retry_lock = threading.Lock()
_dm_retry_queue = []
_DM_RETRY_MAX_ATTEMPTS = 5
_DM_RETRY_DELAY_SECONDS = 5


def _queue_otp_dm_retry(uid, otp, number, seconds, service="", sms_body=""):
    """Retry a failed DM without sending the already-delivered group message again."""
    with _dm_retry_lock:
        _dm_retry_queue.append({
            "uid": int(uid),
            "otp": str(otp),
            "number": str(number),
            "seconds": seconds,
            "service": service,
            "sms_body": sms_body,
            "attempts": 0,
            "retry_at": time.monotonic() + _DM_RETRY_DELAY_SECONDS,
        })


def _otp_dm_retry_worker():
    """Deliver transiently failed OTP DMs while the number is still assigned."""
    while True:
        item = None
        with _dm_retry_lock:
            now = time.monotonic()
            for index, candidate in enumerate(_dm_retry_queue):
                if candidate.get("retry_at", 0) <= now:
                    item = _dm_retry_queue.pop(index)
                    break
        if item is None:
            time.sleep(0.5)
            continue

        uid = item["uid"]
        number = item["number"]
        current_uid, _match_kind = _resolve_user_for_number(number)
        if current_uid != uid:
            print(
                f"[OTP-DM-RETRY] Skipped stale assignment "
                f"uid={uid} num={mask_number(number)}"
            )
            continue

        delivered = send_otp_message(
            uid,
            item["otp"],
            number,
            item["seconds"],
            item["service"],
            item["sms_body"],
            _skip_reward=True,
        )
        if delivered:
            with otp_stats_lock:
                otp_stats[str(uid)] = otp_stats.get(str(uid), 0) + 1
            _save_otp_stats()
            print(
                f"[OTP-DM-RETRY] ✅ Delivered OTP={item['otp']} "
                f"to uid={uid}"
            )
            continue

        item["attempts"] += 1
        if item["attempts"] < _DM_RETRY_MAX_ATTEMPTS:
            item["retry_at"] = time.monotonic() + _DM_RETRY_DELAY_SECONDS
            with _dm_retry_lock:
                _dm_retry_queue.append(item)
            print(
                f"[OTP-DM-RETRY] ⚠️ Retry {item['attempts']}/"
                f"{_DM_RETRY_MAX_ATTEMPTS - 1} queued for uid={uid}"
            )
        else:
            print(
                f"[OTP-DM-RETRY] ❌ Giving up after "
                f"{_DM_RETRY_MAX_ATTEMPTS - 1} retries for uid={uid}"
            )


threading.Thread(
    target=_otp_dm_retry_worker,
    daemon=True,
    name="otp-dm-retry",
).start()


def is_group_otp_send_enabled():
    return _group_settings.get("group_otp_send", True)


_otp_group_retry_lock = threading.Lock()
_otp_group_retry_queue = []
_OTP_GROUP_RETRY_MAX_ATTEMPTS = 8
_OTP_GROUP_RETRY_DELAY_SECONDS = 3


def _queue_otp_group_retry(group_id, otp, number, seconds, service="", sms_body=""):
    """Retry a transient group delivery without repeating the user DM."""
    with _otp_group_retry_lock:
        for item in _otp_group_retry_queue:
            if (
                item["group_id"] == int(group_id)
                and item["otp"] == str(otp)
                and item["number"] == str(number)
            ):
                return True
        _otp_group_retry_queue.append(
            {
                "group_id": int(group_id),
                "otp": str(otp),
                "number": str(number),
                "seconds": seconds,
                "service": service,
                "sms_body": sms_body,
                "attempts": 0,
                "retry_at": time.monotonic() + _OTP_GROUP_RETRY_DELAY_SECONDS,
            }
        )
    return True


def _dispatch_otp(otp, number, seconds, service="", sms_body=""):
    grp = get_otp_group_id()
    clean = re.sub(r"\D", "", str(number))
    uid, match_kind = _resolve_user_for_number(number)
    group_sent = False
    group_retry_queued = False
    dm_sent = False
    print(f"[DISPATCH] OTP={otp} num={number} svc={service} group={grp} user_dm={uid} map={match_kind} grp_send={is_group_otp_send_enabled()}")
    if grp and is_group_otp_send_enabled():
        group_sent = bool(send_otp_message(grp, otp, number, seconds, service, sms_body))
        if not group_sent:
            group_retry_queued = _queue_otp_group_retry(
                grp, otp, number, seconds, service, sms_body
            )
            print(
                f"[DISPATCH] ⚠️ Group delivery failed; retry queued for "
                f"number={mask_number(number)}"
            )
    elif grp and not is_group_otp_send_enabled():
        print(f"[DISPATCH] ℹ️ Group OTP send is DISABLED — skipping group send (DM only mode)")
    else:
        print(f"[DISPATCH] ⚠️ No OTP group configured — skipping group send!")
    # Forward to all extra groups
    extra_grps = _group_settings.get("extra_groups", [])
    for eg in extra_grps:
        eg_id = eg.get("id")
        if eg_id:
            try:
                group_sent = bool(_send_to_extra_group(
                    eg_id, otp, number, seconds, service, sms_body, eg
                )) or group_sent
            except Exception as _eg_err:
                print(f"[DISPATCH] ❌ Extra group {eg_id} error: {_eg_err}")
    if uid:
        dm_sent = bool(
            send_otp_message(uid, otp, number, seconds, service, sms_body)
        )
        if dm_sent:
            # Track OTP receive count per user only after a successful DM.
            with otp_stats_lock:
                otp_stats[str(uid)] = otp_stats.get(str(uid), 0) + 1
            _save_otp_stats()
        else:
            _queue_otp_dm_retry(
                uid, otp, number, seconds, service, sms_body
            )
            print(
                f"[DISPATCH] ⚠️ DM failed for uid={uid}; "
                "queued a number-checked retry"
            )
        # NOTE: number is NOT auto-released — repeat OTPs on the same number
        # will keep going to the same user's DM until they clear or reassign.
        if dm_sent:
            print(f"[DISPATCH] ✅ DM sent to uid={uid} for number={number} (mapping kept for repeat OTPs)")
    else:
        print(f"[DISPATCH] ℹ️ No unique user DM mapping for {number} ({match_kind}) — DM skipped")
    # A successful DM is still a successful dispatch.  If the group was
    # temporarily unavailable, the group-only retry above will complete it
    # without duplicating the DM.
    return bool(group_sent or group_retry_queued or dm_sent)


def _otp_group_retry_worker():
    """Deliver failed group OTPs independently from the panel pollers."""
    while True:
        item = None
        with _otp_group_retry_lock:
            now = time.monotonic()
            for index, candidate in enumerate(_otp_group_retry_queue):
                if candidate.get("retry_at", 0) <= now:
                    item = _otp_group_retry_queue.pop(index)
                    break
        if item is None:
            time.sleep(0.5)
            continue
        if not is_group_otp_send_enabled():
            continue
        delivered = bool(
            send_otp_message(
                item["group_id"],
                item["otp"],
                item["number"],
                item["seconds"],
                item["service"],
                item["sms_body"],
            )
        )
        if delivered:
            print(
                f"[OTP-GROUP-RETRY] ✅ Delivered OTP={item['otp']} "
                f"to group={item['group_id']}"
            )
            continue
        item["attempts"] += 1
        if item["attempts"] < _OTP_GROUP_RETRY_MAX_ATTEMPTS:
            item["retry_at"] = (
                time.monotonic() + _OTP_GROUP_RETRY_DELAY_SECONDS
            )
            with _otp_group_retry_lock:
                _otp_group_retry_queue.append(item)
        else:
            print(
                f"[OTP-GROUP-RETRY] ❌ Giving up after "
                f"{_OTP_GROUP_RETRY_MAX_ATTEMPTS - 1} retries"
            )


threading.Thread(
    target=_otp_group_retry_worker,
    daemon=True,
    name="otp-group-retry",
).start()


# ── Augestel SMS panel monitor ───────────────────────────────────────────────
# Augestel is handled inside this bot so its SMS uses the same inbox/group
# dispatch path and the same message template/buttons as every other panel.
AUGESTEL_API_BASE = "https://augestel.com/api/v1/iprn"
# Augestel permits one messages request per minute.  Keep this fixed at one
# minute so an old/deployed environment value can never silently change it
# back to the previous five-minute cadence.
AUGESTEL_POLL_SECONDS = 60
AUGESTEL_START_DATE = os.environ.get("AUGESTEL_START_DATE", "2000-01-01")
AUGESTEL_STATE_FILE = os.environ.get(
    "AUGESTEL_STATE_FILE", "augestel_bot_state.json"
)
AUGESTEL_KEY_FILE = os.environ.get(
    "AUGESTEL_KEY_FILE", "augestel_api_key.json"
)
AUGESTEL_MAX_PAGES = max(
    1, int(os.environ.get("AUGESTEL_MAX_PAGES", "100"))
)
AUGESTEL_MAX_STORED = 10000
AUGESTEL_KEY_HISTORY_LIMIT = 10
_augestel_history_sync = threading.Event()


def _augestel_get_api_key():
    """Use the admin-updated key first, then fall back to the environment secret."""
    saved = load_json(AUGESTEL_KEY_FILE, {})
    if isinstance(saved, dict):
        saved_key = str(saved.get("api_key") or "").strip()
        if saved_key:
            return saved_key
    return os.environ.get("AUGESTEL_API_KEY", "").strip()


def _augestel_key_marker(api_key):
    """Identify a configured key without persisting or logging the key itself."""
    return hashlib.sha256((api_key or "").encode("utf-8")).hexdigest()


def _augestel_save_api_key(api_key):
    """Persist the key without printing or echoing its value."""
    save_json(
        AUGESTEL_KEY_FILE,
        {
            "api_key": api_key,
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        },
    )
    # A new credential may point at a different panel/history.  Clear the
    # delivery ledger so the next background cycle performs a full sync.
    _save_augestel_state(
        {
            "bootstrapped": False,
            "fingerprints": [],
            "key_marker": _augestel_key_marker(api_key),
            "key_sync_limit": AUGESTEL_KEY_HISTORY_LIMIT,
        }
    )
    _augestel_history_sync.set()


def _augestel_reset_to_environment_key():
    """Remove the bot override and resync the environment-backed panel."""
    try:
        if os.path.exists(AUGESTEL_KEY_FILE):
            os.remove(AUGESTEL_KEY_FILE)
    except Exception as error:
        print(f"[AUGESTEL] key reset error: {error}")
        raise
    _save_augestel_state(
        {
            "bootstrapped": False,
            "fingerprints": [],
            "key_marker": _augestel_key_marker(
                os.environ.get("AUGESTEL_API_KEY", "").strip()
            ),
            "key_sync_limit": AUGESTEL_KEY_HISTORY_LIMIT,
        }
    )
    _augestel_history_sync.set()


def _augestel_state():
    state = load_json(AUGESTEL_STATE_FILE, {})
    if not isinstance(state, dict):
        state = {}
    bootstrapped = state.get("bootstrapped") is True
    fingerprints = state.get("fingerprints", [])
    if not isinstance(fingerprints, list):
        fingerprints = []
    try:
        key_sync_limit = max(0, int(state.get("key_sync_limit", 0)))
    except (TypeError, ValueError):
        key_sync_limit = 0
    # State files written by older versions may still be waiting for their
    # first sync. Treat that pending sync as a bounded key-history sync rather
    # than replaying the entire panel history.
    if not bootstrapped and "key_sync_limit" not in state:
        key_sync_limit = AUGESTEL_KEY_HISTORY_LIMIT
    return {
        "bootstrapped": bootstrapped,
        "fingerprints": [str(v) for v in fingerprints][-AUGESTEL_MAX_STORED:],
        "key_marker": str(state.get("key_marker") or ""),
        "key_sync_limit": key_sync_limit,
    }


def _save_augestel_state(state):
    try:
        key_sync_limit = max(0, int(state.get("key_sync_limit", 0)))
    except (TypeError, ValueError):
        key_sync_limit = 0
    save_json(
        AUGESTEL_STATE_FILE,
        {
            "bootstrapped": bool(state.get("bootstrapped")),
            "fingerprints": list(state.get("fingerprints", []))[-AUGESTEL_MAX_STORED:],
            "key_marker": str(state.get("key_marker") or ""),
            "key_sync_limit": key_sync_limit,
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        },
    )


def _augestel_fingerprint(row):
    parts = (
        row.get("source"),
        row.get("number"),
        row.get("message"),
        row.get("rate"),
        row.get("status"),
        row.get("type"),
        row.get("received_at"),
    )
    raw = "\x1f".join("" if value is None else str(value) for value in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _augestel_fetch_page(api_key, page):
    today = datetime.datetime.utcnow().date().isoformat()
    response = requests.get(
        f"{AUGESTEL_API_BASE}/messages",
        params={
            "start_date": os.environ.get("AUGESTEL_START_DATE", AUGESTEL_START_DATE),
            "end_date": os.environ.get("AUGESTEL_END_DATE", today),
            "per_page": 50,
            "page": page,
            "_ts": int(time.time()),
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Cache-Control": "no-cache, no-store",
            "Pragma": "no-cache",
            "User-Agent": "AugestelTelegramBot/1.0",
        },
        timeout=20,
    )
    try:
        payload = response.json()
    except Exception:
        payload = {}
    if response.status_code == 429:
        retry_after = 60
        try:
            retry_after = int(payload.get("error", {}).get("retry_after", 60))
        except Exception:
            pass
        raise RuntimeError(f"rate limited; retry after {retry_after}s")
    if response.status_code != 200:
        detail = payload.get("error", {}).get("message") if isinstance(payload, dict) else ""
        raise RuntimeError(
            detail or f"Augestel returned HTTP {response.status_code}"
        )
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError("Augestel returned an unexpected response")
    rows = payload.get("data")
    if not isinstance(rows, list):
        rows = []
    pagination = payload.get("pagination") or {}
    try:
        last_page = max(1, int(pagination.get("last_page", 1)))
    except Exception:
        last_page = 1
    return rows, last_page


def _augestel_row_to_otp(row):
    if not isinstance(row, dict):
        return None
    number = str(
        row.get("number")
        or row.get("phone")
        or row.get("msisdn")
        or row.get("from")
        or row.get("to")
        or ""
    ).strip()
    sms_body = str(
        row.get("message")
        or row.get("sms")
        or row.get("text")
        or row.get("body")
        or row.get("content")
        or ""
    ).strip()
    service = str(
        row.get("service")
        or row.get("app")
        or row.get("source")
        or row.get("sender")
        or ""
    ).strip()
    if not service:
        service = _detect_service_from_sms(sms_body)
    otp = extract_otp_from_sms(sms_body)
    if not number or not otp:
        return None
    return number, otp, sms_body, service


def _augestel_recent_valid_rows(rows, limit):
    """Return up to ``limit`` valid rows, oldest-to-newest.

    Augestel page 1 contains the newest history. Sorting by the panel's
    timestamp makes this work even when the API response order changes.
    """
    candidates = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not _augestel_row_to_otp(row):
            continue
        timestamp = str(
            row.get("received_at")
            or row.get("created_at")
            or row.get("createdAt")
            or ""
        )
        candidates.append((timestamp, index, row))
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = [item[2] for item in candidates[:max(0, int(limit))]]
    selected.reverse()
    return selected


def _augestel_send_group_only(otp, number, service, sms_body):
    """Replay history through the normal group + assigned-user delivery path.

    This function kept its old name for compatibility with the bounded
    key-change sync, but history must not be group-only: an assigned user also
    needs the code in their inbox.
    """
    return bool(_dispatch_otp(otp, number, 0, service, sms_body))


def _augestel_forward_rows(rows, state, known, group_only=False):
    """Forward a fetched page immediately and keep failed rows retryable."""
    sent = 0
    ordered_rows = sorted(
        [row for row in rows if isinstance(row, dict)],
        key=lambda row: str(row.get("received_at", "")),
    )
    for row in ordered_rows:
        fingerprint = _augestel_fingerprint(row)
        if fingerprint in known:
            continue
        parsed = _augestel_row_to_otp(row)
        if not parsed:
            continue
        number, otp, sms_body, service = parsed
        delivered = (
            _augestel_send_group_only(otp, number, service, sms_body)
            if group_only
            else _dispatch_otp(otp, number, 0, service, sms_body)
        )
        if not delivered:
            print(
                f"[AUGESTEL] ⚠️ Telegram delivery failed; will retry "
                f"num={mask_number(number)}"
            )
            continue
        known.add(fingerprint)
        state["fingerprints"] = list(known)[-AUGESTEL_MAX_STORED:]
        _save_augestel_state(state)
        sent += 1
        print(
            f"[AUGESTEL] ✅ forwarded num={mask_number(number)} "
            f"svc={service or '—'}"
        )
        time.sleep(0.2)
    return sent


def _augestel_monitor():
    state = _augestel_state()
    missing_key_logged = False
    print(
        f"[AUGESTEL] Monitor started; polling every {AUGESTEL_POLL_SECONDS}s "
        f"(mode={'new only' if state['bootstrapped'] else 'initial history sync'})"
    )
    while True:
        cycle_started = time.monotonic()
        try:
            # Reload on every cycle so /setaugestelkey takes effect without restart.
            api_key = _augestel_get_api_key()
            current_key_marker = _augestel_key_marker(api_key)
            if (
                _augestel_history_sync.is_set()
                or state.get("key_marker") != current_key_marker
            ):
                state = {
                    "bootstrapped": False,
                    "fingerprints": [],
                    "key_marker": current_key_marker,
                    "key_sync_limit": AUGESTEL_KEY_HISTORY_LIMIT,
                }
                _augestel_history_sync.clear()
                print(
                    "[AUGESTEL] API key changed; "
                    f"starting latest {AUGESTEL_KEY_HISTORY_LIMIT}-code group sync"
                )
            if not api_key:
                if not missing_key_logged:
                    print("[AUGESTEL] Waiting: no API key configured")
                    missing_key_logged = True
                time.sleep(AUGESTEL_POLL_SECONDS)
                continue
            missing_key_logged = False
            first_rows, last_page = _augestel_fetch_page(api_key, 1)
            known = set(state["fingerprints"])

            if not state["bootstrapped"] and state.get("key_sync_limit", 0) > 0:
                # A newly supplied key should replay only the latest ten valid
                # codes. Mark all other rows from page 1 as seen so they do not
                # leak into a later polling cycle.
                history_rows = _augestel_recent_valid_rows(
                    first_rows, state["key_sync_limit"]
                )
                history_fingerprints = {
                    _augestel_fingerprint(row) for row in history_rows
                }
                sent = _augestel_forward_rows(
                    history_rows, state, known, group_only=True
                )
                for row in first_rows:
                    if isinstance(row, dict):
                        fingerprint = _augestel_fingerprint(row)
                        if fingerprint not in history_fingerprints:
                            known.add(fingerprint)
                state["fingerprints"] = list(known)[-AUGESTEL_MAX_STORED:]
                if all(fingerprint in known for fingerprint in history_fingerprints):
                    state["key_sync_limit"] = 0
                    state["bootstrapped"] = True
                _save_augestel_state(state)
                if state["bootstrapped"]:
                    print(
                        "[AUGESTEL] Latest "
                        f"{len(history_rows)}-code group sync complete"
                    )
                else:
                    print("[AUGESTEL] Latest-code group sync pending retries")
            else:
                # Normal operation: page 1 is delivered immediately. No
                # historical pages are replayed after the bounded key sync.
                sent = _augestel_forward_rows(first_rows, state, known)
                if not state["bootstrapped"]:
                    state["bootstrapped"] = True
                    state["fingerprints"] = list(known)[-AUGESTEL_MAX_STORED:]
                    _save_augestel_state(state)
                    print("[AUGESTEL] Initial sync complete")
            if sent == 0:
                print("[AUGESTEL] No new SMS")
        except Exception as error:
            print(f"[AUGESTEL] poll error: {error}")
        # Keep the poll cadence at one minute from cycle start rather than
        # adding a full minute after every request/send operation.  This
        # prevents a slow API response or a burst of Telegram sends from
        # stretching the effective interval to several minutes.
        elapsed = time.monotonic() - cycle_started
        time.sleep(max(0.5, AUGESTEL_POLL_SECONDS - elapsed))


threading.Thread(target=_augestel_monitor, daemon=True, name="augestel-monitor").start()


def _augestel_delete_secret_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass


def _augestel_store_key_from_message(message, api_key):
    api_key = (api_key or "").strip()
    _augestel_delete_secret_message(message)
    if not api_key:
        bot.send_message(
            message.chat.id,
            "❌ API key খালি রাখা যাবে না। আবার /setaugestelkey দিন।",
            parse_mode="HTML",
        )
        return
    if api_key.casefold() in {"clear", "reset", "env"}:
        try:
            _augestel_reset_to_environment_key()
        except Exception as error:
            print(f"[AUGESTEL] key reset error: {error}")
            bot.send_message(message.chat.id, "❌ API key reset করা যায়নি।")
            return
        bot.send_message(
            message.chat.id,
            "✅ Bot-এর saved Augestel key মুছে দেওয়া হয়েছে। এখন environment-এর "
            "AUGESTEL_API_KEY ব্যবহার হবে।",
        )
        return
    _augestel_save_api_key(api_key)
    bot.send_message(
        message.chat.id,
        "✅ Augestel API key securely save হয়েছে। Monitor restart ছাড়াই পরের "
        f"{AUGESTEL_POLL_SECONDS} সেকেন্ডের cycle-এ নতুন key ব্যবহার করবে।",
    )


@bot.message_handler(commands=["setaugestelkey", "augestelkey"])
def _augestel_key_command(message):
    uid = message.from_user.id
    if not is_super_admin(uid):
        return
    command_parts = (message.text or "").split(None, 1)
    if len(command_parts) == 2:
        _augestel_store_key_from_message(message, command_parts[1])
        return
    prompt = bot.send_message(
        message.chat.id,
        "🔐 <b>Augestel API key update</b>\n\n"
        "নতুন key-টি এই chat-এ পাঠান। Save হওয়ার পর incoming key message "
        "delete করার চেষ্টা করা হবে।\n\n"
        "Environment key-তে ফিরে যেতে লিখুন: <code>clear</code>",
        parse_mode="HTML",
    )
    bot.register_next_step_handler(prompt, _augestel_key_step)


def _augestel_key_step(message):
    if not is_super_admin(message.from_user.id):
        return
    if _is_back(message.text):
        bot.send_message(message.chat.id, "❌ API key update বাতিল করা হয়েছে।")
        return
    _augestel_store_key_from_message(message, message.text or "")


@bot.message_handler(commands=["augestelstatus"])
def _augestel_status_command(message):
    if not is_super_admin(message.from_user.id):
        return

    def _check():
        saved = load_json(AUGESTEL_KEY_FILE, {})
        source = "bot override" if isinstance(saved, dict) and saved.get("api_key") else "environment"
        api_key = _augestel_get_api_key()
        if not api_key:
            bot.send_message(
                message.chat.id,
                "❌ Augestel API key configured নেই। /setaugestelkey ব্যবহার করুন।",
            )
            return
        try:
            rows, last_page = _augestel_fetch_page(api_key, 1)
            bot.send_message(
                message.chat.id,
                f"✅ Augestel API reachable\n"
                f"🔐 Key source: <code>{source}</code>\n"
                f"📥 Page 1 rows: <code>{len(rows)}</code>\n"
                f"📄 Pages available: <code>{last_page}</code>\n"
                f"⏱ Poll interval: <code>{AUGESTEL_POLL_SECONDS}s</code>",
                parse_mode="HTML",
            )
        except Exception as error:
            bot.send_message(
                message.chat.id,
                f"❌ Augestel API check failed: <code>{error}</code>",
                parse_mode="HTML",
            )

    threading.Thread(target=_check, daemon=True).start()


def send_status_message(chat_id, status_text):
    message = (
        "⚙️ <b>𝗦𝗧𝗔𝗧𝗨𝗦 𝗔𝗟𝗘𝗥𝗧</b> ⚙️\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"📛 {status_text} 📛\n\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "🤖⚡ <b>𝗔𝗥 𝗢𝗧𝗣 𝗕𝗢𝗧 — 𝗔𝗖𝗧𝗜𝗩𝗘</b> ⚡🤖"
    )
    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
    except Exception as e:
        print(f"[MONITOR] Status send error: {e}")


# ── Country helpers ───────────────────────────────────────────────────────────


_ISO_TO_COUNTRY = {
    "AF":"Afghanistan","AL":"Albania","DZ":"Algeria","AD":"Andorra","AO":"Angola",
    "AG":"Antigua and Barbuda","AR":"Argentina","AM":"Armenia","AU":"Australia",
    "AT":"Austria","AZ":"Azerbaijan","BS":"Bahamas","BH":"Bahrain","BD":"Bangladesh",
    "BB":"Barbados","BY":"Belarus","BE":"Belgium","BZ":"Belize","BJ":"Benin",
    "BT":"Bhutan","BO":"Bolivia","BA":"Bosnia and Herzegovina","BW":"Botswana",
    "BR":"Brazil","BN":"Brunei","BG":"Bulgaria","BF":"Burkina Faso","BI":"Burundi",
    "CV":"Cape Verde","KH":"Cambodia","CM":"Cameroon","CA":"Canada",
    "CF":"Central African Republic","TD":"Chad","CL":"Chile","CN":"China",
    "CO":"Colombia","KM":"Comoros","CG":"Congo","CD":"DR Congo","CR":"Costa Rica",
    "CI":"Ivory Coast","HR":"Croatia","CU":"Cuba","CY":"Cyprus","CZ":"Czech Republic",
    "DK":"Denmark","DJ":"Djibouti","DM":"Dominica","DO":"Dominican Republic",
    "EC":"Ecuador","EG":"Egypt","SV":"El Salvador","GQ":"Equatorial Guinea",
    "ER":"Eritrea","EE":"Estonia","SZ":"Eswatini","ET":"Ethiopia","FJ":"Fiji",
    "FI":"Finland","FR":"France","GA":"Gabon","GM":"Gambia","GE":"Georgia",
    "DE":"Germany","GH":"Ghana","GR":"Greece","GD":"Grenada","GT":"Guatemala",
    "GN":"Guinea","GW":"Guinea-Bissau","GY":"Guyana","HT":"Haiti","HN":"Honduras",
    "HU":"Hungary","IS":"Iceland","IN":"India","ID":"Indonesia","IR":"Iran",
    "IQ":"Iraq","IE":"Ireland","IL":"Israel","IT":"Italy","JM":"Jamaica",
    "JP":"Japan","JO":"Jordan","KZ":"Kazakhstan","KE":"Kenya","KI":"Kiribati",
    "KW":"Kuwait","KG":"Kyrgyzstan","LA":"Laos","LV":"Latvia","LB":"Lebanon",
    "LS":"Lesotho","LR":"Liberia","LY":"Libya","LI":"Liechtenstein","LT":"Lithuania",
    "LU":"Luxembourg","MG":"Madagascar","MW":"Malawi","MY":"Malaysia","MV":"Maldives",
    "ML":"Mali","MT":"Malta","MH":"Marshall Islands","MR":"Mauritania","MU":"Mauritius",
    "MX":"Mexico","FM":"Micronesia","MD":"Moldova","MC":"Monaco","MN":"Mongolia",
    "ME":"Montenegro","MA":"Morocco","MZ":"Mozambique","MM":"Myanmar","NA":"Namibia",
    "NR":"Nauru","NP":"Nepal","NL":"Netherlands","NZ":"New Zealand","NI":"Nicaragua",
    "NE":"Niger","NG":"Nigeria","NO":"Norway","OM":"Oman","PK":"Pakistan",
    "PW":"Palau","PA":"Panama","PG":"Papua New Guinea","PY":"Paraguay","PE":"Peru",
    "PH":"Philippines","PL":"Poland","PT":"Portugal","QA":"Qatar","RO":"Romania",
    "RU":"Russia","RW":"Rwanda","KN":"Saint Kitts and Nevis","LC":"Saint Lucia",
    "VC":"Saint Vincent","WS":"Samoa","SM":"San Marino","ST":"Sao Tome and Principe",
    "SA":"Saudi Arabia","SN":"Senegal","RS":"Serbia","SC":"Seychelles",
    "SL":"Sierra Leone","SG":"Singapore","SK":"Slovakia","SI":"Slovenia",
    "SB":"Solomon Islands","SO":"Somalia","ZA":"South Africa","SS":"South Sudan",
    "ES":"Spain","LK":"Sri Lanka","SD":"Sudan","SR":"Suriname","SE":"Sweden",
    "CH":"Switzerland","SY":"Syria","TW":"Taiwan","TJ":"Tajikistan","TZ":"Tanzania",
    "TH":"Thailand","TL":"Timor-Leste","TG":"Togo","TO":"Tonga","TT":"Trinidad and Tobago",
    "TN":"Tunisia","TR":"Turkey","TM":"Turkmenistan","TV":"Tuvalu","UG":"Uganda",
    "UA":"Ukraine","AE":"UAE","GB":"United Kingdom","US":"United States","UY":"Uruguay",
    "UZ":"Uzbekistan","VU":"Vanuatu","VE":"Venezuela","VN":"Vietnam","YE":"Yemen",
    "ZM":"Zambia","ZW":"Zimbabwe",
}

def get_country_details(num_str):
    try:
        num_str = str(num_str).strip()
        if not num_str.startswith("+"):
            num_str = "+" + num_str
        parsed = phonenumbers.parse(num_str)
        country_code = region_code_for_number(parsed)
        country_name = geocoder.description_for_number(parsed, "en")
        if not country_name and country_code:
            country_name = _ISO_TO_COUNTRY.get(country_code, country_code)
        flag = "".join(chr(ord(c.upper()) + 127397) for c in (country_code or ""))
        return (country_name or country_code or "Unknown"), (flag or "🌐")
    except Exception:
        return "Unknown", "🌐"


def get_country_short(num_str) -> str:
    """Return the ISO 2-letter country code (e.g. 'NG', 'BD') for a phone number."""
    try:
        s = str(num_str).strip()
        if not s.startswith("+"):
            s = "+" + s
        parsed = phonenumbers.parse(s)
        return region_code_for_number(parsed) or "??"
    except Exception:
        return "??"


def get_group_country_short(num_str, service="") -> str:
    """Return the group label code, preserving the bot's country occurrence number.

    Country selectors distinguish duplicate ranges as e.g. ``Laos 1`` and
    ``Laos 2``.  The OTP group should use the matching compact form
    (``LA 1`` / ``LA 2``) instead of losing that distinction.
    """
    iso_code = get_country_short(num_str)
    clean_number = re.sub(r"\D", "", str(num_str))
    if not clean_number:
        return iso_code

    country_name, _ = get_country_details(num_str)
    country_name_key = re.sub(r"\s+", " ", str(country_name or "")).strip().casefold()

    def _suffix_from_label(label):
        match = re.match(r"^(.*?)\s+(\d+)$", str(label or "").strip())
        if not match:
            return ""
        base_name = re.sub(r"\s+", " ", match.group(1)).strip().casefold()
        return match.group(2) if base_name == country_name_key else ""

    # Manual stock keeps the exact country label as its dictionary key.
    # Prefer the service that delivered the number, then inspect other services
    # as a fallback for OTPs received after a panel/service name changes.
    service_keys = []
    preferred_service = str(service or "").strip().lower()
    if preferred_service:
        service_keys.append(preferred_service)
    for stock_service in stock:
        if stock_service not in service_keys:
            service_keys.append(stock_service)
    for stock_service in service_keys:
        for label, numbers in (stock.get(stock_service) or {}).items():
            if any(re.sub(r"\D", "", str(item)) == clean_number for item in (numbers or [])):
                suffix = _suffix_from_label(label)
                return f"{iso_code} {suffix}" if suffix else iso_code

    # Live-console ranges use the same ordering as the country selector.  A
    # longest-prefix match avoids confusing overlapping ranges.
    config_services = []
    preferred_config_service = str(service or "").strip().upper()
    if preferred_config_service:
        config_services.append(preferred_config_service)
    for config_service in _console_config:
        if config_service not in config_services:
            config_services.append(config_service)
    for config_service in config_services:
        ranges = list((_console_config.get(config_service) or {}).get("ranges") or [])
        matches = []
        for position, configured_range in enumerate(ranges):
            prefix = re.sub(r"\D", "", str(configured_range))
            if prefix and clean_number.startswith(prefix):
                range_country, _ = get_country_details(prefix)
                matches.append((len(prefix), position, str(range_country or ""), configured_range))
        if not matches:
            continue
        _, matched_position, matched_country, _ = max(matches, key=lambda item: item[0])
        same_country_ranges = [
            position
            for position, configured_range in enumerate(ranges)
            if (get_country_details(re.sub(r"\D", "", str(configured_range)))[0] or "").casefold()
            == matched_country.casefold()
        ]
        if len(same_country_ranges) > 1:
            occurrence = same_country_ranges.index(matched_position) + 1
            return f"{iso_code} {occurrence}"
        return iso_code

    return iso_code


_COUNTRY_LANG_MAP = {
    "NG": "EN", "GH": "EN", "KE": "EN", "UG": "EN", "ZA": "EN", "US": "EN",
    "GB": "EN", "PH": "EN", "IN": "EN", "PK": "EN", "TZ": "EN", "ZM": "EN",
    "SL": "EN", "LR": "EN", "GM": "EN", "MW": "EN", "BD": "BN", "ID": "ID",
    "BR": "PT", "PT": "PT", "CN": "ZH", "TW": "ZH", "HK": "ZH", "SA": "AR",
    "EG": "AR", "AE": "AR", "IQ": "AR", "DZ": "AR", "MA": "AR", "TN": "AR",
    "TR": "TR", "SW": "SW", "IR": "FA", "RU": "RU", "UA": "UA", "DE": "DE",
    "AT": "DE", "FR": "FR", "SN": "FR", "CI": "FR", "CM": "FR", "CD": "FR",
    "ES": "ES", "MX": "ES", "AR": "ES", "CO": "ES", "IT": "IT", "JP": "JA",
    "KR": "KO", "VN": "VI", "TH": "TH", "MY": "MS", "MM": "MY", "KH": "KM",
    "NP": "NE", "LK": "SI", "ET": "AM", "SO": "SO", "NL": "NL", "PL": "PL",
    "GR": "EL", "IL": "HE",
}


def get_country_language(country_code: str) -> str:
    """Return a short primary-language code for the given ISO country code."""
    return _COUNTRY_LANG_MAP.get((country_code or "").upper(), "EN")


def detect_sms_language(text: str) -> str:
    """Detect the language code from the complete SMS body.

    Script detection handles non-Latin languages.  For Latin-script messages,
    common OTP wording is scored so Spanish/French/etc. are not all reported
    as English just because they use the same alphabet.
    """
    if not text or text in ("—", "-"):
        return "EN"
    text = str(text)
    # Arabic / Urdu script
    if any('\u0600' <= c <= '\u06FF' for c in text):
        return "AR"
    # Bengali script
    if any('\u0980' <= c <= '\u09FF' for c in text):
        return "BN"
    # Cyrillic (Russian / Ukrainian)
    if any('\u0400' <= c <= '\u04FF' for c in text):
        return "RU"
    # Thai
    if any('\u0E00' <= c <= '\u0E7F' for c in text):
        return "TH"
    # Japanese Hiragana / Katakana — check BEFORE CJK because Japanese SMS
    # contains both Hiragana/Katakana AND CJK characters together.
    # Pure Chinese has no Hiragana/Katakana, so this correctly distinguishes JA vs ZH.
    if any('\u3040' <= c <= '\u30FF' for c in text):
        return "JA"
    # Korean Hangul
    if any('\uAC00' <= c <= '\uD7AF' for c in text):
        return "KO"
    # CJK Unified Ideographs (Chinese) — only reached if no Hiragana/Katakana found
    if any('\u4E00' <= c <= '\u9FFF' for c in text):
        return "ZH"
    # Hindi / Devanagari
    if any('\u0900' <= c <= '\u097F' for c in text):
        return "HI"
    # Greek
    if any('\u0370' <= c <= '\u03FF' for c in text):
        return "EL"
    # Hebrew
    if any('\u0590' <= c <= '\u05FF' for c in text):
        return "HE"
    # Armenian
    if any('\u0530' <= c <= '\u058F' for c in text):
        return "HY"
    # Georgian
    if any('\u10A0' <= c <= '\u10FF' for c in text):
        return "KA"

    lower = text.casefold()
    words = set(re.findall(r"[a-zÀ-ÿ]+", lower))
    language_markers = {
        "ES": (
            ("código", "codigo", "verificación", "verificacion", "contraseña",
             "inicia sesión", "inicia sesion", "tu código", "tu codigo"),
            2,
        ),
        "FR": (
            ("votre", "votre code", "code de", "vérification", "verification",
             "connexion", "utilisez", "confirmez"),
            2,
        ),
        "PT": (
            ("código", "codigo", "verificação", "verificacao", "senha",
             "seu código", "seu codigo", "utilize"),
            2,
        ),
        "ID": (
            ("kode", "verifikasi", "anda", "gunakan", "untuk", "masuk",
             "jangan bagikan"),
            2,
        ),
        "MS": (
            ("kod", "pengesahan", "sahkan", "anda", "gunakan", "untuk",
             "jangan kongsi"),
            2,
        ),
        "TR": (
            ("doğrulama", "dogrulama", "kodunuz", "giriş", "giris",
             "kullanın", "kullanin", "şifreniz", "sifreniz"),
            2,
        ),
        "IT": (
            ("codice", "verifica", "verificazione", "accesso", "tuo codice",
             "utilizza", "condividere"),
            2,
        ),
        "DE": (
            ("bestätigung", "bestatigung", "verifizierung", "dein code",
             "ihr code", "verwenden", "teilen"),
            2,
        ),
        "NL": (
            ("verificatie", "jouw code", "gebruik", "inloggen", "deel deze",
             "bevestig"),
            2,
        ),
        "VI": (
            ("mã xác minh", "ma xac minh", "xác minh", "xac minh",
             "của bạn", "cua ban", "đăng nhập", "dang nhap"),
            2,
        ),
        "RO": (
            ("codul", "verificare", "confirmare", "parola", "folosește",
             "foloseste", "nu distribui"),
            2,
        ),
        "PL": (
            ("kod weryfikacyjny", "weryfikacyjny", "potwierdź", "potwierdz",
             "zaloguj", "twój kod", "twoj kod"),
            2,
        ),
        "SW": (
            ("msimbo", "uthibitisho", "ingia", "yako", "tumia",
             "usishiriki"),
            2,
        ),
        "TL": (
            ("ang iyong", "iyong code", "pagpapatunay", "gamitin",
             "mag log in", "huwag ibahagi"),
            2,
        ),
    }

    scores = {}
    for language, (markers, minimum_score) in language_markers.items():
        score = 0
        for marker in markers:
            if " " in marker:
                if marker in lower:
                    score += 2
            elif marker in words:
                score += 1
        if score >= minimum_score:
            scores[language] = score
    if scores:
        return max(scores, key=scores.get)

    # langid carries a broad 97-language model for full Latin-script SMS
    # messages that are not covered by the common OTP phrase hints above.
    # Keep it after script and phrase detection because short OTP messages can
    # otherwise be confused by brand names, numbers, or mixed-language text.
    try:
        detected_language, _ = _langid_classify(text)
        if detected_language:
            return str(detected_language).upper()
    except Exception:
        pass
    return "EN"


def to_math_bold(text: str) -> str:
    """Convert ASCII letters/digits to Unicode Mathematical Sans-Serif Bold."""
    result = []
    for ch in str(text):
        if 'A' <= ch <= 'Z':
            result.append(chr(0x1D5D4 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            result.append(chr(0x1D5EE + ord(ch) - ord('a')))
        elif '0' <= ch <= '9':
            result.append(chr(0x1D7EC + ord(ch) - ord('0')))
        else:
            result.append(ch)
    return ''.join(result)


# ── Stock helpers ─────────────────────────────────────────────────────────────


