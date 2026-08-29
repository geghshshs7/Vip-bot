# ── Menus ─────────────────────────────────────────────────────────────────────


def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    _gn_text, _gn_icon = _btn_text_and_icon("get_number", "📲 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥")
    markup.add(types.KeyboardButton(_gn_text, style="success", **_gn_icon))
    _sp_text, _sp_icon = _btn_text_and_icon("saport", "📞 𝗦𝗔𝗣𝗢𝗥𝗧")
    _bl_text, _bl_icon = _btn_text_and_icon("balance", "💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲")
    markup.add(types.KeyboardButton(_sp_text, style="danger", **_sp_icon),
               types.KeyboardButton(_bl_text, style="primary", **_bl_icon))
    _dv_text, _dv_icon = _btn_text_and_icon("developer", "👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼")
    _wd_text, _wd_icon = _btn_text_and_icon("withdraw", "💸 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄")
    markup.add(types.KeyboardButton(_dv_text, style="success", **_dv_icon),
               types.KeyboardButton(_wd_text, style="danger", **_wd_icon))
    _rf_text, _rf_icon = _btn_text_and_icon("refer", "🔗 𝗥𝗲𝗳𝗳𝗲𝗿")
    markup.row(
        types.KeyboardButton(_rf_text, style="primary", **_rf_icon),
        types.KeyboardButton("Buy Service", style="success", icon_custom_emoji_id="5251467997561778767"),
    )
    if user_id in ADMIN_IDS:
        _ap_text, _ap_icon = _btn_text_and_icon("admin_panel", "⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 ⚙️")
        markup.add(types.KeyboardButton(_ap_text, style="primary", **_ap_icon))
    return markup


def v2_switch_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🔴 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗚𝗘"))
    markup.add(types.KeyboardButton("⌨️ 𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘"))
    markup.add(types.KeyboardButton("🔙 𝗩𝟭 𝗦𝗪𝗜𝗧𝗖𝗛"))
    return markup


def save_services():
    save_json(SERVICES_FILE, _services)
    _sync_settings_to_botpy()


def _get_svc_map():
    return {s["label"]: s["key"] for s in _services}


SERVICE_BUTTON_MAP = {}


def _v1_build_service_markup():
    """Build V1 service list as inline keyboard — only shows services that have stock.
    Shows all services from _services list that have stock, PLUS any stock key that
    has numbers but is not in _services (e.g. telegram added manually)."""
    _STYLES = ["success", "primary", "danger"]
    btns = []
    idx = 0
    seen_keys = set()

    # First: services defined in _services (preserves ordering/labels)
    for svc_info in _services:
        label = _strip_emoji(svc_info.get("label", ""))
        key   = svc_info.get("key", "")
        total = sum(len(v) for v in stock.get(key, {}).values())
        if not total:
            seen_keys.add(key)
            continue
        seen_keys.add(key)
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    # Second: any stock key with numbers NOT already listed above
    for key, country_map in stock.items():
        if key in seen_keys:
            continue
        total = sum(len(v) for v in country_map.values())
        if not total:
            continue
        label = key.title()  # e.g. "telegram" → "Telegram"
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    markup = types.InlineKeyboardMarkup(row_width=1)
    for btn in btns:
        markup.add(btn)
    return markup, bool(btns)


def _build_combined_service_markup():
    """Build combined V1 (stock) + V2 (live console) service buttons in one markup."""
    _STYLES = ["success", "primary", "danger"]
    btns = []
    idx = 0
    seen_keys = set()

    # Collect enabled V2 service keys (lowercase) to suppress duplicate V1 buttons
    _v2_enabled_keys = {
        sid.lower() for sid in _CONSOLE_SVC_NAMES
        if _console_config.get(sid, {}).get("enabled") and _console_config.get(sid, {}).get("ranges")
    }

    # V1 stock services (skip any that already have a V2 counterpart)
    for svc_info in _services:
        label = _strip_emoji(svc_info.get("label", ""))
        key   = svc_info.get("key", "")
        total = sum(len(v) for v in stock.get(key, {}).values())
        seen_keys.add(key)
        if not total:
            continue
        if key.lower() in _v2_enabled_keys:
            continue  # V2 already covers this service (manual numbers merged there)
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    for key, country_map in stock.items():
        if key in seen_keys:
            continue
        total = sum(len(v) for v in country_map.values())
        if not total:
            continue
        if key.lower() in _v2_enabled_keys:
            continue  # V2 already covers this service
        label = key.title()
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    # V2 live console services
    for sid in _CONSOLE_SVC_NAMES:
        cfg = _console_config.get(sid, {})
        if not cfg.get("enabled"):
            continue
        if not cfg.get("ranges"):
            continue
        _icon_id = _svc_icon_emoji_id(sid)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            f"{sid}",
            callback_data=f"v2svc_cc:{sid}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    markup = types.InlineKeyboardMarkup(row_width=1)
    for btn in btns:
        markup.add(btn)
    return markup, bool(btns)


def show_services(message):
    markup, has_btns = _build_combined_service_markup()
    if not has_btns:
        bot.send_message(
            message.chat.id,
            "❌ <b>No stock available in any service.</b>\nPlease notify the admin.",
            parse_mode="HTML",
        )
        return
    bot.send_message(
        message.chat.id,
        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
        reply_markup=markup,
        parse_mode="HTML",
    )


def show_countries(chat_id, svc):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    if svc in stock:
        for cnt, nums in stock[svc].items():
            if nums:
                _, flag = get_country_details(nums[0])
                btns.append(
                    types.InlineKeyboardButton(
                        f"{cnt}", callback_data=f"n:{svc}:{cnt}", style="primary",
                        **_flag_btn_kwargs(flag)
                    )
                )
    if btns:
        markup.add(*btns)
    markup.add(
        types.InlineKeyboardButton("⬅️ 𝗕𝗮𝗰𝗸", callback_data="back_to_services", style="danger")
    )
    bot.send_message(
        chat_id,
        "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b>",
        reply_markup=markup,
        parse_mode="HTML",
    )


# ── Handlers ──────────────────────────────────────────────────────────────────


@bot.message_handler(commands=["start"])
def start_cmd(message):
    u = message.from_user
    # ── Referral handling — check BEFORE register_user so we know if new ──────
    _is_new_user = message.chat.id not in users
    _payload = (message.text or "").split(None, 1)[1].strip() if len((message.text or "").split(None, 1)) > 1 else ""
    if _is_new_user and _payload.startswith("ref") and _payload[3:].isdigit():
        _referrer_uid = int(_payload[3:])
        if _referrer_uid != message.from_user.id:
            _claimed = False
            with _referrals_lock:
                if str(message.from_user.id) not in _referrals:
                    _referrals[str(message.from_user.id)] = _referrer_uid
                    _claimed = True
            if _claimed:
                _save_referrals()
                _commission = get_refer_commission()
                _cur = get_currency()
                _new_bal = add_reward(_referrer_uid, _commission)
                try:
                    bot.send_message(
                        _referrer_uid,
                        f'<tg-emoji emoji-id="5267041999948653482">🔗</tg-emoji> <b>Referral Commission!</b>\n\n'
                        f'👤 Ekjon new user tomar link diye join korecho!\n'
                        f'💰 Commission: <b>+{_cur}{_commission:.2f}</b>\n'
                        f'💳 New Balance: <code>{_cur}{_new_bal:.2f}</code>',
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
    register_user(
        message.chat.id,
        first_name=u.first_name or "",
        last_name=u.last_name or "",
        username=u.username or "",
    )
    import html as _html
    uname = f"@{u.username}" if u.username else (u.first_name or "User")
    uname = _html.escape(str(uname))
    uid_str = _html.escape(str(u.id))
    markup = types.InlineKeyboardMarkup()
    _grp = get_otp_group_link() or CHANNEL_1
    if _grp:
        _sog_text, _sog_icon = _btn_text_and_icon("start_otp_group", "🔥 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽 𝗝𝗢𝗜𝗡 🔥")
        markup.add(types.InlineKeyboardButton(_sog_text, url=_grp, style="success", **_sog_icon))
    if get_channel2():
        _sch_text, _sch_icon = _btn_text_and_icon("start_channel", "📢 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗝𝗢𝗜𝗡 📢")
        markup.add(types.InlineKeyboardButton(_sch_text, url=get_channel2(), style="primary", **_sch_icon))
    _sv_text, _sv_icon = _btn_text_and_icon("start_verify", "✅ 𝗩𝗘𝗥𝗜𝗙𝗬 𝗞𝗢𝗥𝗢 ✅")
    markup.add(types.InlineKeyboardButton(_sv_text, callback_data="v", style="danger", **_sv_icon))
    class _SS(dict):
        def __missing__(self, k): return f"{{{k}}}"
    bot.send_message(
        message.chat.id,
        get_template("start").format_map(_SS(uname=uname, uid=uid_str, **_msg_emoji_vars())),
        reply_markup=markup,
        parse_mode="HTML",
    )


@bot.message_handler(commands=["test"])
def test_cmd(message):
    fake_otp = str(random.randint(100000, 999999))
    fake_number = "8801712345678"
    fake_svc = "Instagram"
    fake_secs = 12
    fake_sms = f"Your Instagram code is {fake_otp}. Don't share this code."
    # Preview with GROUP format (force_group_fmt=True) so admin sees the exact group message
    bot.send_message(message.chat.id, "👁 <b>Group Format Preview:</b>", parse_mode="HTML")
    send_otp_message(message.chat.id, fake_otp, fake_number, fake_secs, fake_svc, fake_sms, force_group_fmt=True)
    try:
        send_otp_message(get_otp_group_id(), fake_otp, fake_number, fake_secs, fake_svc, fake_sms)
        bot.send_message(
            message.chat.id, "✅ Sent to group as well!", parse_mode="HTML"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Group-e pathate parina: <code>{e}</code>",
            parse_mode="HTML",
        )


@bot.message_handler(commands=["panels"])
def panels_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    with _stats_lock:
        stats = {k: dict(v) for k, v in _panel_stats.items()}
    lines = ""
    for pid in ["p1", "p2", "p3", "p4", "p5", "p6"]:
        s = stats.get(pid, {})
        if s.get("last"):
            ago = int(time.time() - s["last"])
            last_str = f"{ago}s ago"
        else:
            last_str = "never"
        err_str = f"  ⚠️ {s['errors']} err" if s.get("errors") else ""
        lines += (
            f"{s.get('status', '⏳')} <b>{s.get('name', '?')}</b>\n"
            f"   🌐 <code>{s.get('host', '?')}</code>\n"
            f"   📊 {s.get('count', 0)} records  •  🕐 {last_str}{err_str}\n\n"
        )
    with _demo_lock:
        demo_on = _demo_active
    demo_str = "🟢 Running" if demo_on else "🔴 Stopped"
    bot.send_message(
        message.chat.id,
        f"📡 <b>PANEL STATUS</b>\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"{lines}"
        f"🎭 <b>Demo OTP:</b>  {demo_str}\n\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        f"🔄 <i>Updates every {POLL_INTERVAL}s</i>",
        parse_mode="HTML",
    )
    caller_uid = message.from_user.id
    # Super admin sees all, others see only their own panels
    dp_copy = [
        p for p in _dynamic_panels
        if is_super_admin(caller_uid) or p.get("admin_id") == caller_uid
    ]
    if dp_copy:
        dp_lines = ""
        for p in dp_copy:
            pid = p["id"]
            with _stats_lock:
                s = _panel_stats.get(pid, {})
            st = s.get("status", "⏳")
            cnt = s.get("count", 0)
            err = s.get("errors", 0)
            t = s.get("last")
            last_str = f"{int(time.time() - t)}s ago" if t else "never"
            err_str = f"  ⚠️ {err} err" if err else ""
            dp_lines += (
                f"{st} <b>{p.get('username', '?')}</b> <code>[{pid}]</code>\n"
                f"   🌐 <code>{p.get('host', '?')}</code>\n"
                f"   📊 {cnt} records  •  🕐 {last_str}{err_str}\n\n"
            )
        bot.send_message(
            message.chat.id,
            f"📡 <b>DYNAMIC PANELS</b>\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"{dp_lines}"
            f"💡 <i>Use /addpanel to add a new panel</i>",
            parse_mode="HTML",
        )
    else:
        bot.send_message(
            message.chat.id,
            "📋 <b>Tomar kono dynamic panel nei.</b>\n\n"
            "💡 <i>Use /addpanel to add a new panel.</i>",
            parse_mode="HTML",
        )


@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(
        message.chat.id,
        "✍️ <b>Send broadcast content:</b>\n\n"
        "📝 Text, 🖼️ Photo, 🎥 Video, 🎭 Sticker,\n"
        "🎞️ GIF, 🎵 Audio, 🎤 Voice, 📎 Document — all accepted!\n\n"
        "✨ <b>If you want to use a Custom Emoji:</b>\n"
        "Text-er jetukute emoji boshaite chao, sekhane emoji ID lekho:\n"
        "<code>5976350888195791241 Guinea 5319160079465857105 Instagram Method 5325684684544289988</code>\n"
        "<i>Wherever you place the ID, the custom emoji will render there</i>\n\n"
        "🔙 Press the <b>Admin Panel</b> button to go back.",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, do_broadcast)


def _clr_service_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    services = [
        ("facebook", "💬"),
        ("instagram", "📸"),
        ("whatsapp", "📱"),
        ("telegram", "✈️"),
        ("binance", "🪙"),
        ("pc clone", "💻"),
    ]
    for svc, icon in services:
        total = sum(len(v) for v in stock.get(svc, {}).values())
        markup.add(
            types.InlineKeyboardButton(
                f"{icon} {svc.upper()} ({total})", callback_data=f"clr_s:{svc}", style="success"
            )
        )
    markup.add(types.InlineKeyboardButton(" Clear ALL Stock", callback_data="clr_all", style="primary"))
    return markup


@bot.message_handler(commands=["addpanel"])
def addpanel_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    _show_addpanel_type_select(message.chat.id, message.from_user.id)


def _show_addpanel_type_select(chat_id, uid):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔑 Add with Username + Password", callback_data="aptype:pass", style="danger"),
        types.InlineKeyboardButton("🗝️ Add with API Key", callback_data="aptype:apikey", style="success"),
    )
    bot.send_message(
        chat_id,
        "🔧🔥 <b>ADD NEW PANEL</b> 🔥🔧\n\n"
        "How do you want to add the panel?\n\n"
        "🔑 <b>Username + Password</b> — login and add\n"
        "🗝️ <b>API Key</b> — add using panel API key",
        reply_markup=markup,
        parse_mode="HTML",
    )


def _ap_get_url(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addpanel_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    url = (message.text or "").strip()

    # Use the universal base extractor — handles ANY path prefix (/konekta, /ints, etc.)
    base_url = _extract_panel_base_url(url) if re.match(r"https?://", url, re.IGNORECASE) else None

    if not base_url:
        msg = bot.send_message(
            message.chat.id,
            "❌ <b>Enter a valid URL!</b>\n\n"
            "Example:\n"
            "• <code>http://1.2.3.4</code>\n"
            "• <code>http://1.2.3.4/konekta</code>\n"
            "• <code>http://1.2.3.4/konekta/agent/SMSCDRReports</code>\n"
            "• <code>https://mypanel.com</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _ap_get_url)
        return

    host_m = re.search(r"//([^/]+)", base_url)
    uid = message.from_user.id
    _addpanel_state[uid]["data"]["base_url"] = base_url
    _addpanel_state[uid]["data"]["host"] = host_m.group(1) if host_m else base_url
    _addpanel_state[uid]["data"]["url_hint"] = url  # preserve original URL as hint

    # ── IVA SMS special flow (ivasms.com) — cookie only ─────────────────────
    if "ivasms.com" in base_url.lower():
        msg = bot.send_message(
            message.chat.id,
            "🌐 <b>IVA SMS Panel detected!</b>\n\n"
            "⚠️ Cloudflare blocks email/password login from the Railway server IP.\n"
            "<b>You'll need to log in using a browser cookie.</b>\n\n"
        "📋 <b>How to get Cookie:</b>\n"
        "1. Login to <b>ivasms.com</b> in Chrome\n"
        "2. Open this link in browser:\n"
            "   <code>javascript:document.cookie</code>\n"
        "   (paste in address bar)\n"
        "   <b>OR</b> on PC: F12 → Application → Cookies → https://ivasms.com\n"
        "3. Copy <code>laravel_session</code> value\n\n"
        "🍪 Now paste the cookie:\n"
            "<code>laravel_session=eyJ...</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        bot.register_next_step_handler(msg, _iva_ap_get_cookie)
        return
    # ─────────────────────────────────────────────────────────────────────────

    msg = bot.send_message(
        message.chat.id,
        f"✅ <b>URL set:</b> <code>{base_url}</code>\n\n"
        f"👤 <b>Step 2/3:</b> Username pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _ap_get_user)


def _ap_get_user(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addpanel_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    username = (message.text or "").strip()
    if not username:
        msg = bot.send_message(message.chat.id, "❌ Enter Username:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _ap_get_user)
        return
    _addpanel_state[message.from_user.id]["data"]["username"] = username
    msg = bot.send_message(
        message.chat.id,
        f"✅ Username: <code>{username}</code>\n\n🔑 <b>Step 3/3:</b> Password pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _ap_get_pass)


def _ap_get_pass(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    uid = message.from_user.id
    if _is_back(message.text):
        _addpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    password = (message.text or "").strip()
    if not password:
        msg = bot.send_message(message.chat.id, "❌ Enter Password:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _ap_get_pass)
        return
    data = _addpanel_state.get(uid, {}).get("data", {})
    data["password"] = password
    wait_msg = bot.send_message(
        message.chat.id,
        "⏳🔥 <b>Connecting & auto-detecting panel type...</b>\n"
        "<i>Looking for login page, solving captcha, testing data endpoint...</i>",
        parse_mode="HTML",
    )
    panel_id = f"d{int(time.time()) % 100000}"
    panel = {
        "id": panel_id,
        "host": data.get("host", ""),
        "base_url": data.get("base_url", ""),
        "url_hint": data.get("url_hint", ""),
        "username": data.get("username", ""),
        "password": password,
        "engine": "ints_smscdr",
        "data_path": "/agent/res/data_smscdr.php",
        "admin_id": uid,
    }
    chat_id = message.chat.id
    _addpanel_state.pop(uid, None)

    def _do_add():
        sess, token, det_engine, det_path = _universal_login(panel)
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except Exception:
            pass
        if not sess:
            # Save panel data for force-add (Railway IP might be blocked by panel)
            _pending_force_add[panel_id] = panel
            force_markup = types.InlineKeyboardMarkup(row_width=1)
            force_markup.add(
                types.InlineKeyboardButton(
                    "⚠️ Force Add (Skip Login)",
                    callback_data=f"forceadd:{panel_id}", style="primary"
                )
            )
            force_markup.add(
                types.InlineKeyboardButton("❌ Cancel", callback_data=f"forceadd_cancel:{panel_id}", style="danger")
            )
            bot.send_message(
                chat_id,
        "⚠️ <b>Login Verification Failed!</b>\n\n"
        "Many panels block Railway server IPs.\n"
        "If you still want to save the panel credentials,\n"
        "<b>Force Add</b> — the panel will try to login automatically later.\n\n"
                f"🌐 Host: <code>{data.get('host', '')}</code>\n"
                f"👤 User: <code>{data.get('username', '')}</code>",
                reply_markup=force_markup,
                parse_mode="HTML",
            )
            return
        if det_engine:
            panel["engine"] = det_engine
            panel["data_path"] = det_path
        _dynamic_sessions[panel_id] = {"session": sess, "token": token}
        _dynamic_panels.append(panel)
        save_dynamic_panels()
        _start_dynamic_panel(panel)
        engine_label = {
            "ints_smscdr":   "INTS — SMSCDRStats",
            "ints_smsranges":"INTS — SMSRanges",
            "xisora":        "Xisora",
            "html_scrape":   "HTML Scrape",
        }.get(panel.get("engine", ""), panel.get("engine", "Auto"))
        bot.send_message(
            chat_id,
            f"✅🔥 <b>PANEL ADDED & STARTED!</b> 🔥✅\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🆔 <b>ID      ▸▸</b> <code>{panel_id}</code>\n"
            f"🌐 <b>Host    ▸▸</b> <code>{data.get('host','')}</code>\n"
            f"👤 <b>User    ▸▸</b> <code>{data.get('username','')}</code>\n"
            f"🔍 <b>Engine  ▸▸</b> <code>{engine_label}</code>\n"
            f"📂 <b>Endpoint▸▸</b> <code>{panel.get('data_path','')}</code>\n\n"
            f"📡 Monitor thread started! Use /panels to check.",
            parse_mode="HTML",
        )

    threading.Thread(target=_do_add, daemon=True).start()


# ── IVA SMS add-panel flow (cookie only — email/pass blocked by Cloudflare) ───

def _iva_ap_get_email(message):
    """Legacy handler — redirects to cookie flow immediately."""
    _iva_ap_get_cookie(message)


def _iva_ap_get_pass(message):
    """Legacy handler — redirects to cookie flow immediately."""
    _iva_ap_get_cookie(message)


def _iva_ap_get_cookie(message):
    """Collect browser cookie and connect to ivasms.com."""
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    cookie_str = (message.text or "").strip()
    if not cookie_str or "=" not in cookie_str:
        msg = bot.send_message(message.chat.id,
            "❌ <b>Enter Cookie!</b>\n\n"
            "Format: <code>laravel_session=eyJ0...</code>\n\n"
        "📱 <b>How to get on Phone:</b>\n"
        "1. Login to ivasms.com in Chrome\n"
        "2. Type in address bar:\n"
            "   <code>javascript:alert(document.cookie)</code>\n"
        "3. Copy whatever appears in the popup\n\n"
            "💻 <b>On PC:</b> F12 → Application → Cookies → ivasms.com → laravel_session copy",
            reply_markup=_back_admin_kb(), parse_mode="HTML",
            disable_web_page_preview=True)
        bot.register_next_step_handler(msg, _iva_ap_get_cookie)
        return
    _iva_do_connect(message, cookie_str=cookie_str)


def _iva_do_connect(message, cookie_str):
    """Build panel dict and connect using cookie."""
    uid = message.from_user.id
    _addpanel_state.pop(uid, None)
    chat_id = message.chat.id

    panel_id = f"iva{int(time.time()) % 100000}"
    panel = {
        "id": panel_id,
        "host": "ivasms.com",
        "base_url": "https://ivasms.com",
        "url_hint": "https://ivasms.com/portal/sms/received",
        "username": "ivasms",
        "password": "",
        "cookie_str": cookie_str,
        "engine": "iva_sms",
        "data_path": "/portal/sms/received",
        "admin_id": uid,
    }

    wait_msg = bot.send_message(chat_id,
        "⏳ <b>IVA SMS — logging in with cookie...</b>", parse_mode="HTML")

    def _do():
        ok = _iva_login(panel)
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except Exception:
            pass

        if not ok:
            msg2 = bot.send_message(chat_id,
                "❌ <b>Cookie didn't work!</b>\n\n"
                "Possible karon:\n"
                "• Cookie has expired (log in fresh)\n"
                "• Pura cookie copy hoy nai\n\n"
                "Abar fresh cookie pathao:\n"
                "<code>laravel_session=eyJ0...</code>",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            _addpanel_state[uid] = {"step": "iva_cookie", "data": {}}
            bot.register_next_step_handler(msg2, _iva_ap_get_cookie)
            return

        _dynamic_panels.append(panel)
        save_dynamic_panels()
        _start_dynamic_panel(panel)

        bot.send_message(chat_id,
            f"✅🔥 <b>IVA SMS PANEL ADDED!</b> 🔥✅\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🆔 <b>ID     ▸▸</b> <code>{panel_id}</code>\n"
            f"🌐 <b>Host   ▸▸</b> <code>ivasms.com</code>\n"
            f"🔑 <b>Login  ▸▸</b> <code>Cookie ✅</code>\n\n"
            f"📡 Monitor started! New OTP ashle group-e pathabe.\n"
            f"⚠️ Cookie expire hole: <code>/ivacookie</code>",
            parse_mode="HTML")

    threading.Thread(target=_do, daemon=True).start()


# ── API Key Panel Add Flow ─────────────────────────────────────────────────────

_apk_state = {}   # uid → {"url": ..., "api_key": ...}


def _apk_start(message):
    """Ask for panel URL (Step 1 of API key flow)."""
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    _apk_state[uid] = {}
    msg = bot.send_message(
        message.chat.id,
        "🗝️🔥 <b>ADD PANEL WITH API KEY</b> 🔥🗝️\n\n"
        "📡 <b>Step 1/2:</b> Send the Panel URL\n\n"
        "✅ <b>Any format accepted:</b>\n"
        "• <code>http://1.2.3.4</code>\n"
        "• <code>http://1.2.3.4/api</code>\n"
        "• <code>https://mypanel.com</code>\n"
        "• <code>https://mypanel.com/api/sms</code>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _apk_get_url)


def _apk_get_url(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _apk_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    url = (message.text or "").strip()
    if not re.match(r"https?://", url, re.IGNORECASE):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid URL! (must start with http:// or https://)",
            reply_markup=_back_admin_kb(), parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _apk_get_url)
        return
    # Extract base URL
    m = re.match(r"(https?://[^/]+(?:/[^?#]*)?)", url, re.IGNORECASE)
    base_url = m.group(1).rstrip("/") if m else url.rstrip("/")
    # If URL contains known API paths, strip them to get clean base
    for suffix in ["/api/sms", "/api/messages", "/api/received", "/api/v1", "/api"]:
        if base_url.lower().endswith(suffix):
            base_url = base_url[: -len(suffix)]
            break
    _apk_state[uid]["base_url"] = base_url
    host_m = re.search(r"//([^/]+)", base_url)
    _apk_state[uid]["host"] = host_m.group(1) if host_m else base_url

    msg = bot.send_message(
        message.chat.id,
        f"✅ URL: <code>{base_url}</code>\n\n"
        "🗝️ <b>Step 2/2:</b> Send the panel's <b>API Key</b>:\n\n"
        "<i>Copy from panel settings/profile/API section.</i>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _apk_get_key)


def _apk_get_key(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _apk_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    api_key = (message.text or "").strip()
    if not api_key:
        msg = bot.send_message(message.chat.id, "❌ Enter API Key:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _apk_get_key)
        return

    base_url = _apk_state.get(uid, {}).get("base_url", "")
    host     = _apk_state.get(uid, {}).get("host", "")
    _apk_state.pop(uid, None)
    chat_id  = message.chat.id

    wait_msg = bot.send_message(
        chat_id,
        "⏳🔍 <b>Testing API Key...</b>\n"
        "<i>Probing common endpoints, please wait...</i>",
        parse_mode="HTML",
    )

    def _do():
        panel_id   = f"apk{int(time.time()) % 100000}"
        det_path, det_param = _api_key_test(base_url, api_key)
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except Exception:
            pass

        if not det_path:
            # Force-add option — user may know their endpoint
            _apk_state[uid] = {}
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(
                    "⚠️ Force Add (Set Endpoint Manually)",
                    callback_data=f"apkforce:{panel_id}|{base_url}|{api_key}", style="success"
                ),
                types.InlineKeyboardButton("❌ Cancel", callback_data=f"apkforce_cancel", style="primary"),
            )
            bot.send_message(
                chat_id,
        "⚠️ <b>API Endpoint auto-detect failed!</b>\n\n"
                f"🌐 Host: <code>{host}</code>\n"
                f"🗝️ Key: <code>{api_key[:8]}...</code>\n\n"
        "Possible reasons:\n"
        "• This panel has no API\n"
        "• Wrong API key\n"
        "• Panel has a custom endpoint\n\n"
        "You can still force add and set the endpoint later with <b>/editpanel</b>.",
                reply_markup=markup,
                parse_mode="HTML",
            )
            return

        panel = {
            "id": panel_id,
            "host": host,
            "base_url": base_url,
            "url_hint": f"{base_url}{det_path}",
            "username": f"api:{host}",
            "password": "",
            "api_key": api_key,
            "api_key_param": det_param,
            "engine": "api_key",
            "data_path": det_path,
            "admin_id": uid,
        }
        _dynamic_panels.append(panel)
        save_dynamic_panels()
        _start_dynamic_panel(panel)

        bot.send_message(
            chat_id,
            f"✅🔥 <b>API KEY PANEL ADDED!</b> 🔥✅\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🆔 <b>ID       ▸▸</b> <code>{panel_id}</code>\n"
            f"🌐 <b>Host     ▸▸</b> <code>{host}</code>\n"
            f"🗝️ <b>API Key  ▸▸</b> <code>{api_key[:12]}...</code>\n"
            f"📂 <b>Endpoint ▸▸</b> <code>{det_path}</code>\n"
            f"🔐 <b>Auth     ▸▸</b> <code>{det_param}</code>\n\n"
            f"📡 Monitor thread started! Check status with /panels.",
            parse_mode="HTML",
        )

    threading.Thread(target=_do, daemon=True).start()


# ── IVA SMS cookie update command ─────────────────────────────────────────────

_iva_cookie_update_state: dict = {}


def _iva_find_panel(panel_id=None):
    """Find any iva_sms panel — checks dynamic_panels AND _BUILTIN_PANELS."""
    all_panels = list(_dynamic_panels) + [p for p in _BUILTIN_PANELS if p not in _dynamic_panels]
    for p in all_panels:
        if p.get("engine") == "iva_sms" and (not panel_id or p["id"] == panel_id):
            return p
    return None


@bot.message_handler(commands=["ivacookie"])
def _iva_cookie_cmd(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    args = message.text.split()[1:] if message.text else []
    panel_id = args[0] if args else None

    iva_panel = _iva_find_panel(panel_id)

    if not iva_panel:
        bot.send_message(message.chat.id,
            "❌ <b>IVA SMS panel not found.</b>\n"
            "Restart the bot — bp10 will auto-load.",
            parse_mode="HTML")
        return

    _iva_cookie_update_state[uid] = iva_panel["id"]
    msg = bot.send_message(
        message.chat.id,
        f"🍪 <b>IVA SMS — Cookie Login</b>\n"
        f"Panel ID: <code>{iva_panel['id']}</code>\n\n"
        f"📋 <b>Steps:</b>\n"
        f"1. Login to <a href='https://ivasms.com/portal/login'>ivasms.com</a> in Chrome/Firefox\n"
        f"2. F12 → Application → Cookies → ivasms.com\n"
        f"3. Copy <code>laravel_session</code> value\n"
        f"4. Paste below:\n\n"
        f"<code>laravel_session=XXXXXXX</code>\n\n"
        f"<i>(If cf_clearance exists, add it too: <code>cf_clearance=XXX; laravel_session=XXX</code>)</i>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    bot.register_next_step_handler(msg, _iva_cookie_update_step)


def _iva_cookie_update_step(message):
    uid = message.from_user.id
    if _is_back(message.text):
        _iva_cookie_update_state.pop(uid, None)
        _go_admin_panel(message)
        return
    panel_id = _iva_cookie_update_state.pop(uid, None)
    if not panel_id:
        return
    cookie_str = (message.text or "").strip()
    if not cookie_str or "=" not in cookie_str:
        bot.send_message(message.chat.id, "❌ Enter a valid cookie format (laravel_session=XXX).", parse_mode="HTML")
        return

    # Update in dynamic_panels first
    updated = False
    for p in _dynamic_panels:
        if p["id"] == panel_id:
            p["cookie_str"] = cookie_str
            save_dynamic_panels()
            updated = True
            break

    # Also update BUILTIN_PANELS in-memory (so _iva_login picks it up)
    for p in _BUILTIN_PANELS:
        if p["id"] == panel_id:
            p["cookie_str"] = cookie_str
            updated = True
            break

    if not updated:
        bot.send_message(message.chat.id, "❌ Panel not found.", parse_mode="HTML")
        return

    _iva_scrapers.pop(panel_id, None)  # force re-login with new cookie

    wait_msg = bot.send_message(message.chat.id,
        "⏳ <b>Logging in with new cookie...</b>", parse_mode="HTML")

    def _try_reconnect():
        panel = _iva_find_panel(panel_id)
        ok = _iva_login(panel) if panel else False
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass
        if ok:
            bot.send_message(message.chat.id,
                "✅🔥 <b>IVA SMS — Cookie login SUCCESSFUL!</b>\n"
                "Panel ekhon active — OTP ashle group-e pathabe. 🟢",
                parse_mode="HTML")
        else:
            bot.send_message(message.chat.id,
                "❌ <b>That cookie didn't work either!</b>\n\n"
                "Cookie has expired or is invalid.\n"
                "Get a fresh cookie from your browser and send it again: /ivacookie",
                parse_mode="HTML")

    threading.Thread(target=_try_reconnect, daemon=True).start()


# ── IVA SMS test command (/ivatest) ───────────────────────────────────────────

@bot.message_handler(commands=["ivatest"])
def _iva_test_cmd(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return

    # Find ivasms panel (bp10 or any iva_sms engine panel)
    iva_panel = None
    for p in _dynamic_panels:
        if p.get("engine") == "iva_sms":
            iva_panel = p
            break
    # Also check BUILTIN_PANELS
    if not iva_panel:
        for p in _BUILTIN_PANELS:
            if p.get("engine") == "iva_sms":
                iva_panel = p
                break

    if not iva_panel:
        bot.send_message(message.chat.id,
            "❌ <b>IVA SMS panel not found!</b>\n"
            "Restart the bot — bp10 will auto-load.",
            parse_mode="HTML")
        return

    wait_msg = bot.send_message(message.chat.id,
        "⏳ <b>Fetching data from ivasms.com...</b>",
        parse_mode="HTML")

    def _do_test():
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass

        records = _iva_fetch(iva_panel)

        if not records:
            bot.send_message(message.chat.id,
                "⚠️ <b>IVA SMS:</b> Ekhon kono OTP nai panel-e.\n"
                "If there's any SMS on the panel it will show — try /ivatest again in a moment.",
                parse_mode="HTML")
            return

        grp = get_otp_group_id()
        items = list(records.values())[:3]

        bot.send_message(message.chat.id,
            f"✅ <b>Got {len(records)} records from the IVA panel.</b>\n"
            f"Now sending to <b>{len(items)}</b> group(s)...",
            parse_mode="HTML")

        for number, otp, sms_txt, service in items:
            svc = service if service else "IVA"
            if grp:
                send_otp_message(grp, otp, number, 0, svc, sms_txt or "")
            send_otp_message(uid, otp, number, 0, svc, sms_txt or "")

        bot.send_message(message.chat.id,
            f"🔥 <b>Done!</b> {len(items)} OTP(s) sent to group+DM.\n"
            f"IVA panel is <b>OK</b>! 🟢",
            parse_mode="HTML")

    threading.Thread(target=_do_test, daemon=True).start()


# ── Test Panel flow (test without saving) ─────────────────────────────────────

def _tp_get_url(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _testpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    url = (message.text or "").strip()
    base_url = _extract_panel_base_url(url) if re.match(r"https?://", url, re.IGNORECASE) else None
    if not base_url:
        msg = bot.send_message(
            message.chat.id,
            "❌ <b>Enter a valid URL!</b>\n\nExample: <code>http://1.2.3.4/konekta/agent/SMSCDRReports</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _tp_get_url)
        return
    _testpanel_state[uid]["data"]["base_url"] = base_url
    _testpanel_state[uid]["data"]["url_hint"] = url
    msg = bot.send_message(
        message.chat.id,
        f"✅ <b>URL:</b> <code>{base_url}</code>\n\n👤 Username pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _tp_get_user)


def _tp_get_user(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _testpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    username = (message.text or "").strip()
    if not username:
        msg = bot.send_message(message.chat.id, "❌ Enter Username:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _tp_get_user)
        return
    _testpanel_state[uid]["data"]["username"] = username
    msg = bot.send_message(
        message.chat.id,
        f"✅ Username: <code>{username}</code>\n\n🔑 Password pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _tp_get_pass_test)


def _tp_get_pass_test(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _testpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    password = (message.text or "").strip()
    if not password:
        msg = bot.send_message(message.chat.id, "❌ Enter Password:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _tp_get_pass_test)
        return
    data = _testpanel_state.get(uid, {}).get("data", {})
    wait_msg = bot.send_message(
        message.chat.id,
        "⏳🔍 <b>Testing panel...</b>\n"
        "<i>Trying to log in, looking for token, probing data endpoint...</i>",
        parse_mode="HTML",
    )
    panel = {
        "id": f"test_{uid}",
        "host": data.get("base_url", ""),
        "base_url": data.get("base_url", ""),
        "url_hint": data.get("url_hint", ""),
        "username": data.get("username", ""),
        "password": password,
        "engine": "ints_smscdr",
        "data_path": "/agent/res/data_smscdr.php",
    }

    def _do_test():
        sess, token, det_engine, det_path = _universal_login(panel)
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass

        if not sess:
            bot.send_message(
                message.chat.id,
                "❌🔥 <b>TEST FAILED!</b> 🔥❌\n\n"
                "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                f"🌐 <b>URL      ▸▸</b> <code>{data.get('base_url','')}</code>\n"
                f"👤 <b>User     ▸▸</b> <code>{data.get('username','')}</code>\n"
                f"📡 <b>Status   ▸▸</b> ❌ Login failed\n\n"
                "❌ <b>Possible reasons:</b>\n"
                "• URL is incorrect\n"
                "• Username/password is wrong\n"
                "• Panel is offline",
                parse_mode="HTML",
                reply_markup=_back_admin_kb(),
            )
            _testpanel_state.pop(uid, None)
            return

        # ── Login success — now fetch existing OTPs ───────────────────────────
        engine_label = {
            "ints_smscdr":    "✅ INTS — SMSCDRStats",
            "ints_smsranges": "✅ INTS — SMSRanges",
            "xisora":         "✅ Xisora",
            "html_scrape":    "✅ HTML Scrape",
        }.get(det_engine or "", f"✅ {det_engine or 'Auto'}")
        tok_display = f"<code>{token[:12]}...</code>" if token else "<i>cookie-based</i>"

        # Update panel with detected engine/path and store session
        panel["engine"] = det_engine or "ints_smscdr"
        panel["data_path"] = det_path or "/agent/res/data_smscdr.php"
        _dynamic_sessions[panel["id"]] = {"session": sess, "token": token}

        fetch_msg = bot.send_message(
            message.chat.id,
            "⏳ <b>Login OK!</b> Fetching OTP from SMS report...",
            parse_mode="HTML",
        )

        found_otps = _universal_fetch(panel)

        try:
            bot.delete_message(message.chat.id, fetch_msg.message_id)
        except Exception:
            pass

        # Clean up temp session
        _dynamic_sessions.pop(panel["id"], None)

        # ── Send up to 6 OTPs to admin's configured group ────────────────────
        admin_group_id = get_admin_setting(uid, "otp_group_id", None)
        target_group = admin_group_id or get_otp_group_id()

        sent_count = 0
        MAX_SEND = 6
        otp_items = list(found_otps.values())  # [(number, otp, sms_txt, service)]

        if otp_items and target_group:
            for number, otp_val, sms_txt, service in otp_items[:MAX_SEND]:
                try:
                    send_otp_message(target_group, otp_val, number, "—", service, sms_txt or "")
                    sent_count += 1
                    time.sleep(0.4)
                except Exception:
                    pass

        # ── Summary message to admin ──────────────────────────────────────────
        total_found = len(otp_items)
        if total_found == 0:
            otp_summary = "⚠️ <i>Panel e aj kono OTP record nei (empty).</i>"
        elif not target_group:
            otp_summary = (
                f"⚠️ <b>{total_found} OTP(s)</b> found in panel but no group is configured!\n"
                "Set the group from Settings."
            )
        else:
            otp_summary = (
                f"📤 <b>{sent_count} OTP(s)</b> sent to group "
                f"(out of {total_found})."
            )

        bot.send_message(
            message.chat.id,
            "✅🔍 <b>TEST SUCCESS!</b> 🔍✅\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🌐 <b>URL      ▸▸</b> <code>{data.get('base_url','')}</code>\n"
            f"👤 <b>User     ▸▸</b> <code>{data.get('username','')}</code>\n"
            f"🔍 <b>Engine   ▸▸</b> {engine_label}\n"
            f"📂 <b>Endpoint ▸▸</b> <code>{det_path or '/agent/res/data_smscdr.php'}</code>\n"
            f"🔑 <b>Token    ▸▸</b> {tok_display}\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"{otp_summary}\n\n"
            "✅ <i>Panel is working! You can save it using Add Panel.</i>",
            parse_mode="HTML",
            reply_markup=_back_admin_kb(),
        )
        _testpanel_state.pop(uid, None)

    threading.Thread(target=_do_test, daemon=True).start()


def _svc_get_label(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addservice_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    label = _strip_emoji((message.text or "").strip())
    if not label:
        msg = bot.send_message(message.chat.id, "❌ Enter Label:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _svc_get_label)
        return
    _addservice_state[message.from_user.id]["label"] = label
    msg = bot.send_message(
        message.chat.id,
        f"✅ Label: <b>{label}</b>\n\n"
        "🔑 <b>Step 2/2:</b> Enter internal key (lowercase, no space)\n"
        "<i>Example: telegram, binance, tiktok</i>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _svc_get_key)


def _svc_get_key(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addservice_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    key = (message.text or "").strip().lower()
    key = re.sub(r"\s+", "_", key)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", key):
        msg = bot.send_message(
            message.chat.id,
            "❌ Key only a-z, 0-9, _ or - diye likhun.\n"
            "<i>Example: <code>snapchat</code> or <code>my_service</code></i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _svc_get_key)
        return
    if not key:
        msg = bot.send_message(message.chat.id, "❌ Enter Key:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _svc_get_key)
        return
    label = _addservice_state.get(message.from_user.id, {}).get("label", "")
    existing_keys = [s["key"] for s in _services]
    if key in existing_keys:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Key <code>{key}</code> already exists! Enter a different key:",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _svc_get_key)
        return
    _services.append({"label": label, "key": key})
    save_services()
    _addservice_state.pop(message.from_user.id, None)
    _go_admin_panel(
        message,
        f"✅🔥 <b>Service Added!</b>\n\n"
        f"🏷️ Label: <b>{label}</b>\n"
        f"🔑 Key: <code>{key}</code>\n\n"
        f"<i>Service menu-te dekha jabe!</i>",
    )


@bot.message_handler(commands=["listpanels"])
def listpanels_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    caller_uid = message.from_user.id
    my_panels = [
        p for p in _dynamic_panels
        if is_super_admin(caller_uid) or p.get("admin_id") == caller_uid
    ]
    if not my_panels:
        bot.send_message(
            message.chat.id,
            "📋 <b>You have no dynamic panel.</b>\n💡 Use /addpanel to add one.",
            parse_mode="HTML",
        )
        return
    lines = "📋🔥 <b>DYNAMIC PANELS LIST</b> 🔥📋\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
    for p in my_panels:
        pid = p["id"]
        with _stats_lock:
            s = _panel_stats.get(pid, {})
        st = s.get("status", "⏳")
        lines += (
            f"{st} 🆔 <code>{pid}</code>\n"
            f"   🌐 <code>{p.get('host', '?')}</code>\n"
            f"   👤 {p.get('username', '?')}\n\n"
        )
    lines += "🗑️ Remove: <code>/removepanel [ID]</code>"
    bot.send_message(message.chat.id, lines, parse_mode="HTML")


@bot.message_handler(commands=["removepanel"])
def removepanel_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Enter Panel ID:\n<code>/removepanel d12345</code>\n\n"
            "💡 /listpanels diye ID dekho.",
            parse_mode="HTML",
        )
        return
    caller_uid = message.from_user.id
    pid = args[1].strip()
    target = next((p for p in _dynamic_panels if p["id"] == pid), None)
    if not target:
        bot.send_message(message.chat.id, f"❌ Panel <code>{pid}</code> not found.\n💡 Use /listpanels to check the ID.", parse_mode="HTML")
        return
    if not is_super_admin(caller_uid) and target.get("admin_id") != caller_uid:
        bot.send_message(message.chat.id, "❌ <b>This panel isn't yours — you can't remove it!</b>", parse_mode="HTML")
        return
    _dynamic_panels[:] = [p for p in _dynamic_panels if p["id"] != pid]
    save_dynamic_panels()
    with _stats_lock:
        _panel_stats.pop(pid, None)
    _dynamic_sessions.pop(pid, None)
    _dynamic_locks.pop(pid, None)
    bot.send_message(message.chat.id, f"✅🔥 Panel <code>{pid}</code> removed!\n<i>Monitor thread will stop naturally.</i>", parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global stock
    try:
        data = call.data

        if data == "rmcc":
            _handle_remove_cc_callback(call)
            return

        # ── Buy Service callbacks ─────────────────────────────────────────────
        if data == "buy_tg_premium":
            prices = _buy_service_settings.get("premium_prices", {})
            rate = _buy_service_settings.get("dollar_rate", 128)
            markup = types.InlineKeyboardMarkup(row_width=1)
            for plan_key, label in [("3M", "3 Month"), ("6M", "6 Month"), ("1Y", "1 Year")]:
                price_bdt = prices.get(plan_key, 0)
                if price_bdt <= 0:
                    markup.add(types.InlineKeyboardButton(
                        f"{label} — Price not set",
                        callback_data=f"buy_premium:{plan_key}", style="primary",
                        icon_custom_emoji_id="5251378413133919079"
                    ))
                else:
                    price_usd = round(price_bdt / rate, 2) if rate else 0
                    markup.add(types.InlineKeyboardButton(
                        f"{label} — {price_bdt} BDT / ${price_usd}",
                        callback_data=f"buy_premium:{plan_key}", style="primary",
                        icon_custom_emoji_id="5251378413133919079"
                    ))
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="buy_svc_back", style="danger"))
            try:
                bot.edit_message_text(
                    '<tg-emoji emoji-id="5269368858610793668">💎</tg-emoji> <b>Telegram Premium</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> select: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                bot.send_message(call.message.chat.id,
                    '<tg-emoji emoji-id="5269368858610793668">💎</tg-emoji> <b>Telegram Premium</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> select: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id)
            return

        if data.startswith("buy_premium:"):
            plan = data.split(":", 1)[1]
            prices = _buy_service_settings.get("premium_prices", {})
            rate = _buy_service_settings.get("dollar_rate", 128)
            binance_id = _buy_service_settings.get("binance_id", "1138284235")
            bkash_num = _buy_service_settings.get("bkash_number", "01340670062")
            bkash_emoji_id = _buy_service_settings.get("bkash_emoji_id", "")
            binance_emoji_id = _buy_service_settings.get("binance_emoji_id", "")
            plan_labels = {"3M": "3 Month", "6M": "6 Month", "1Y": "1 Year"}
            label = f"Telegram Premium {plan_labels.get(plan, plan)}"
            price_bdt = prices.get(plan, 0)
            price_usd = round(price_bdt / rate, 2) if rate else 0
            uid_buyer = call.from_user.id
            _buy_pending[uid_buyer] = {"type": "premium", "label": label, "price": price_bdt}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(
                binance_id, copy_text=types.CopyTextButton(text=binance_id), style="primary",
                icon_custom_emoji_id="5298716928490120985"
            ))
            markup.add(types.InlineKeyboardButton(
                bkash_num, copy_text=types.CopyTextButton(text=bkash_num), style="success",
                icon_custom_emoji_id="6120493521112669316"
            ))
            bot.send_message(
                call.message.chat.id,
                f'<tg-emoji emoji-id="5269368858610793668">💎</tg-emoji> <b>{label}</b> <tg-emoji emoji-id="5269368858610793668">💎</tg-emoji>\n\n'
                f'<tg-emoji emoji-id="5296591052822585948">💰</tg-emoji> Price: <b>{price_bdt} BDT</b> / <tg-emoji emoji-id="5409048419211682843">💱</tg-emoji> {price_usd}\n'
                f'<tg-emoji emoji-id="5296780065743350163">💱</tg-emoji> Rate: 1 <tg-emoji emoji-id="5409048419211682843">💱</tg-emoji> = {rate} BDT\n\n'
                f'<tg-emoji emoji-id="5253742260054409879">✅</tg-emoji> After paying, send a <b>screenshot</b> in this chat. <tg-emoji emoji-id="5253742260054409879">✅</tg-emoji>\n\n'
                f"─────────────────\n"
                f'<tg-emoji emoji-id="5325547803936572038">💳</tg-emoji> <b>Payment Options:</b>\n'
                f'•<tg-emoji emoji-id="5298716928490120985">💎</tg-emoji> Binance ID: <code>{binance_id}</code>\n'
                f'•<tg-emoji emoji-id="6120493521112669316">💎</tg-emoji> bKash: <code>{bkash_num}</code>\n'
                f"─────────────────\n\n"
                f'<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Click the button to copy the ID: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                reply_markup=markup, parse_mode="HTML"
            )
            bot.answer_callback_query(call.id, f"✅ {label} selected!")
            return

        if data == "buy_vpn_menu":
            vpns = _buy_service_settings.get("vpn_services", [])
            if not vpns:
                bot.answer_callback_query(call.id, "❌ Kono VPN service nei!", show_alert=True)
                return
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, v in enumerate(vpns):
                emoji_id = v.get("emoji_id", "")
                name = v.get("name", "")
                dur = v.get("duration", "")
                price = v.get("price", 0)
                vid = v.get("id") or str(i)
                btn_kwargs = {"icon_custom_emoji_id": emoji_id} if emoji_id else {}
                markup.add(types.InlineKeyboardButton(
                    f"{name} | {dur} | {price} BDT",
                    callback_data=f"buy_vpn:{vid}",
                    style="success",
                    **btn_kwargs
                ))
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="buy_svc_back", style="danger"))
            try:
                bot.edit_message_text(
                    "🔒 <b>Buy VPN</b>\n\nSelect a plan:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                bot.send_message(call.message.chat.id,
                    "🔒 <b>Buy VPN</b>\n\nSelect a plan:",
                    reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id)
            return

        if data.startswith("buy_vpn:"):
            vid = data.split(":", 1)[1]
            vpns = _buy_service_settings.get("vpn_services", [])
            v = None
            for _vpn in vpns:
                if _vpn.get("id", "") == vid:
                    v = _vpn
                    break
            if v is None:
                # fallback: try as integer index for old buttons
                try:
                    v = vpns[int(vid)]
                except (ValueError, IndexError):
                    v = None
            if v is None:
                bot.answer_callback_query(call.id, "❌ Service pawa jay ni!", show_alert=True)
                return
            bkash_num = _buy_service_settings.get("bkash_number", "01340670062")
            bkash_emoji_id = _buy_service_settings.get("bkash_emoji_id", "")
            nagad_num = _buy_service_settings.get("nagad_number", "01320750520")
            nagad_emoji_id = _buy_service_settings.get(
                "nagad_emoji_id", "6190392842544748430"
            )
            emoji_id = v.get("emoji_id", "")
            name = v.get("name", "")
            dur = v.get("duration", "")
            price = v.get("price", 0)
            label = f"VPN — {name} | {dur}"
            uid_buyer = call.from_user.id
            _buy_pending[uid_buyer] = {"type": "vpn", "label": label, "price": price}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(
                bkash_num, copy_text=types.CopyTextButton(text=bkash_num), style="success",
                icon_custom_emoji_id="6120493521112669316"
            ))
            markup.add(types.InlineKeyboardButton(
                nagad_num,
                copy_text=types.CopyTextButton(text=nagad_num),
                style="danger",
                icon_custom_emoji_id=nagad_emoji_id,
            ))
            vpn_emoji_tag = f'<tg-emoji emoji-id="{emoji_id}">🔒</tg-emoji> ' if emoji_id else "🔒 "
            # Answer first — prevents button timeout even if send_message fails
            bot.answer_callback_query(call.id, f"✅ {name} selected!")
            try:
                bot.send_message(
                    call.message.chat.id,
                    f"{vpn_emoji_tag}<b>{name}</b>\n"
                    f'<tg-emoji emoji-id="5413879192267805083">📅</tg-emoji> Duration: <b>{dur}</b>\n'
                    f'<tg-emoji emoji-id="5296591052822585948">💰</tg-emoji> Price: <b>{price} BDT</b>\n\n'
                    f'<tg-emoji emoji-id="5251316745993481601">✅</tg-emoji> After paying, send a <b>screenshot</b> in this chat. <tg-emoji emoji-id="5251316745993481601">✅</tg-emoji>\n\n'
                    f"─────────────────\n"
                    f'<tg-emoji emoji-id="5352638632278660622">💳</tg-emoji> <b>Payment:</b> <tg-emoji emoji-id="6120493521112669316">💎</tg-emoji> bKash Personal\n'
                    f'<tg-emoji emoji-id="5355208818017999139">📱</tg-emoji> Number: <code>{bkash_num}</code>\n'
                    f'<tg-emoji emoji-id="{nagad_emoji_id}">💳</tg-emoji> <b>Payment:</b> Nagad Personal\n'
                    f'<tg-emoji emoji-id="{nagad_emoji_id}">📱</tg-emoji> Number: <code>{nagad_num}</code>\n'
                    f"─────────────────\n\n"
                    f'<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Click a button to copy the payment number: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception as _bvpn_err:
                print(f"[BUY_VPN] send_message error: {_bvpn_err}")
            return

        if data.startswith("copy_bin:"):
            val = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, f"✅ Binance ID: {val}", show_alert=True)
            return

        if data.startswith("copy_bk:"):
            val = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, f"✅ bKash: {val}", show_alert=True)
            return

        if data == "buy_svc_back":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("Telegram Premium", callback_data="buy_tg_premium", style="primary", icon_custom_emoji_id="5251390031020455583"),
                types.InlineKeyboardButton("Buy VPN", callback_data="buy_vpn_menu", style="success", icon_custom_emoji_id="5269759232483303288"),
            )
            try:
                bot.edit_message_text(
                    '<tg-emoji emoji-id="5375338737028841420">🛒</tg-emoji> <b>BUY SERVICE</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Select any service from below: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id)
            return

        if data.startswith("buy_set_vpn_price:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            vpn_id = data.split(":", 1)[1]
            if vpn_id == "cancel":
                bot.answer_callback_query(call.id, "❌ Cancelled")
                _show_buy_service_admin(call.message)
                return
            bot.answer_callback_query(call.id, "✅ VPN selected")
            prompt = bot.send_message(
                call.message.chat.id,
                "💰 <b>Enter new price in BDT:</b>\n"
                "<i>Example: <code>50</code></i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(
                prompt,
                lambda m, vid=vpn_id: _buy_set_vpn_price_step(m, vid),
            )
            return

        if data.startswith("buy_del_vpn:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            val = data.split(":", 1)[1]
            if val == "cancel":
                bot.answer_callback_query(call.id, "Cancelled")
                try:
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except Exception:
                    pass
                return
            vpns = _buy_service_settings.get("vpn_services", [])
            # Find by id first, then fallback to integer index for old buttons
            removed_idx = None
            for j, _vpn in enumerate(vpns):
                if _vpn.get("id", str(j)) == val:
                    removed_idx = j
                    break
            if removed_idx is None:
                try:
                    candidate = int(val)
                    if 0 <= candidate < len(vpns):
                        removed_idx = candidate
                except ValueError:
                    pass
            if removed_idx is None:
                bot.answer_callback_query(call.id, "❌ Error! VPN list has been updated, try again.", show_alert=True)
                return
            removed = vpns.pop(removed_idx)
            save_buy_service_settings()
            bot.answer_callback_query(call.id, f"✅ {removed['name']} removed!")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                try:
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except Exception:
                    pass
            # Show updated remove list or done message
            remaining = _buy_service_settings.get("vpn_services", [])
            if remaining:
                new_markup = types.InlineKeyboardMarkup(row_width=1)
                for jj, rv in enumerate(remaining):
                    eid = rv.get("emoji_id", "")
                    rvid = rv.get("id") or str(jj)
                    rlabel = f"{rv.get('name','')} | {rv.get('duration','')} | {rv.get('price',0)} BDT"
                    rkw = {"icon_custom_emoji_id": eid} if eid else {}
                    new_markup.add(types.InlineKeyboardButton(
                        f"🗑️ {rlabel}", callback_data=f"buy_del_vpn:{rvid}", style="danger", **rkw
                    ))
                new_markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="buy_del_vpn:cancel"))
                bot.send_message(call.message.chat.id,
                    f"✅ <b>{removed['name']}</b> removed!\n\n"
                    f"🗑️ <b>Remove VPN Service</b>\n\nAro remove korbe?",
                    reply_markup=new_markup, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id,
                    f"✅ <b>{removed['name']}</b> removed!\n\n❌ Aar kono VPN service nei.",
                    parse_mode="HTML")
            return

        if data.startswith("order_complete:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            try:
                _, target_uid_raw, order_id = data.split(":", 2)
                target_uid = int(target_uid_raw)
            except (TypeError, ValueError):
                bot.answer_callback_query(call.id, "❌ Invalid order.", show_alert=True)
                return

            _update_buy_order_status(order_id, "completed", completed_by=uid_cb)
            bot.answer_callback_query(call.id, "✅ Order Complete")
            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=None,
                )
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id,
                f"✅ <b>Order Complete</b>\n\n"
                f"🆔 Order: <code>{order_id}</code>\n"
                f"👤 User: <code>{target_uid}</code>",
                parse_mode="HTML",
            )
            try:
                bot.send_message(
                    target_uid,
                    "✅ <b>Your order is complete.</b>\n"
                    "Admin has delivered/processed your service.",
                    parse_mode="HTML",
                )
            except Exception as _order_user_notify_error:
                print(
                    f"[BUY-ORDER] User completion notify failed "
                    f"for {target_uid}: {_order_user_notify_error}"
                )
            return

        if data.startswith("admin_dmu:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            target = int(data.split(":", 1)[1])
            _admin_dmu_state[uid_cb] = target
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                f"📨 <b>User <code>{target}</code>-ke message pathao:</b>\n\n"
                f"Text, photo, video, sticker — all accepted.\n"
                f"To use a custom emoji, write the emoji ID in the text.\n\n"
                f"🔙 Back: Press the <b>Admin Panel</b> button.",
                reply_markup=_back_admin_kb(), parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, _buy_send_msg_step)
            return


        # ── Admin Number Add — service selection ─────────────────────────────
        if data.startswith("admin_add_svc:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            svc = data.split(":", 1)[1]
            if svc == "cancel":
                bot.answer_callback_query(call.id, "❌ Cancelled")
                try:
                    bot.edit_message_reply_markup(
                        call.message.chat.id, call.message.message_id, reply_markup=None
                    )
                except Exception:
                    pass
                _go_admin_panel(call.message)
                return
            bot.answer_callback_query(call.id, f"✅ {svc.upper()}")
            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id, call.message.message_id, reply_markup=None
                )
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"🔥 <b>{svc.upper()}</b>\n\n"
                f"📝 <b>Enter Slot name:</b>\n"
                f"<i>Example: Mali 1, Germany 2, India 3</i>",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m, s=svc: ask_numbers_for_slot(m, s))
            return

        # ── Force Add Panel (Railway IP blocked) ─────────────────────────────
        if data.startswith("forceadd:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            pid = data.split(":", 1)[1]
            panel = _pending_force_add.pop(pid, None)
            if not panel:
                bot.answer_callback_query(call.id, "❌ Panel data expired. Please try again.")
                return
            _dynamic_panels.append(panel)
            save_dynamic_panels()
            _start_dynamic_panel(panel)
            bot.answer_callback_query(call.id, "✅ Panel Force Added!")
            try:
                bot.edit_message_text(
                    f"✅🔥 <b>PANEL FORCE ADDED!</b>\n\n"
                    f"🆔 <b>ID:</b> <code>{pid}</code>\n"
                    f"🌐 <b>Host:</b> <code>{panel.get('host', '')}</code>\n"
                    f"👤 <b>User:</b> <code>{panel.get('username', '')}</code>\n\n"
        f"⚠️ Login not verified yet — the panel will try to login automatically.\n"
        f"Check status with /panels.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        if data.startswith("forceadd_cancel:"):
            pid = data.split(":", 1)[1]
            _pending_force_add.pop(pid, None)
            bot.answer_callback_query(call.id, "Cancelled.")
            try:
                bot.edit_message_text(
        "❌ Panel add cancelled.\n/addpanel to try again.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        # ── V2 Panel API Key change ───────────────────────────────────────────
        if data.startswith("chgkey:"):
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            pid = data.split(":", 1)[1]   # fastx | stex | voltex | mk
            _PANEL_LABELS = {
                "fastx": "⚡ FastX SMS",
                "stex": "🌐 STEX SMS",
                "voltex": "🔮 Voltex SMS",
                "mk": "🟢 MK Panel",
                "augestel": "🌐 Augestel SMS",
            }
            label = _PANEL_LABELS.get(pid, pid.upper())
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"🔑 <b>{label} — Enter new API Key:</b>\n\n"
                f"<i>Send only the API key text (no extra characters)</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m, p=pid: _chgkey_receive(m, p))
            return

        # ── API Key Panel type selection ──────────────────────────────────────
        if data == "aptype:pass":
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            _addpanel_state[uid] = {"step": "url", "data": {}}
            msg = bot.send_message(
                call.message.chat.id,
                "🔧🔥 <b>ADD NEW PANEL</b> 🔥🔧\n\n"
        "📡 <b>Step 1/3:</b> Send the Panel URL\n\n"
        "✅ <b>Any format accepted:</b>\n"
                "• <code>http://1.2.3.4</code>\n"
                "• <code>http://1.2.3.4/ints</code>\n"
                "• <code>http://1.2.3.4/konekta</code>\n"
                "• <code>https://truesms.net</code>\n\n"
                "🤖 <i>Login, captcha, and endpoint will all be auto-detected!</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _ap_get_url)
            return

        if data == "aptype:apikey":
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            _apk_state[uid] = {}
            msg = bot.send_message(
                call.message.chat.id,
        "🗝️🔥 <b>ADD PANEL WITH API KEY</b> 🔥🗝️\n\n"
        "📡 <b>Step 1/2:</b> Send the Panel URL\n\n"
        "✅ <b>Any format accepted:</b>\n"
                "• <code>http://1.2.3.4</code>\n"
                "• <code>http://1.2.3.4/api</code>\n"
                "• <code>https://mypanel.com</code>\n"
                "• <code>https://mypanel.com/api/sms</code>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _apk_get_url)
            return

        if data.startswith("apkforce:"):
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            bot.answer_callback_query(call.id, "✅ Force Adding...")
            try:
                rest = data[len("apkforce:"):].split("|", 2)
                panel_id = rest[0]
                base_url = rest[1] if len(rest) > 1 else ""
                api_key  = rest[2] if len(rest) > 2 else ""
            except Exception:
                bot.send_message(call.message.chat.id, "❌ Data parse error।", parse_mode="HTML")
                return
            host_m = re.search(r"//([^/]+)", base_url)
            host   = host_m.group(1) if host_m else base_url
            panel = {
                "id": panel_id,
                "host": host,
                "base_url": base_url,
                "url_hint": f"{base_url}/api/sms",
                "username": f"api:{host}",
                "password": "",
                "api_key": api_key,
                "api_key_param": "api_key",
                "engine": "api_key",
                "data_path": "/api/sms",
                "admin_id": uid,
            }
            _dynamic_panels.append(panel)
            save_dynamic_panels()
            _start_dynamic_panel(panel)
            try:
                bot.edit_message_text(
                    f"✅ <b>API KEY PANEL FORCE ADDED!</b>\n\n"
                    f"🆔 <b>ID:</b> <code>{panel_id}</code>\n"
                    f"🌐 <b>Host:</b> <code>{host}</code>\n"
                    f"🗝️ <b>Key:</b> <code>{api_key[:12]}...</code>\n\n"
        f"⚠️ Endpoint auto-detect failed — using default <code>/api/sms</code>.\n"
        f"Check status with /panels.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        if data == "apkforce_cancel":
            bot.answer_callback_query(call.id, "Cancelled.")
            try:
                bot.edit_message_text(
        "❌ API Key panel add cancelled.\n/addpanel to try again.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return
        # ─────────────────────────────────────────────────────────────────────

        if data == "v":
            uid = call.from_user.id

            grp_id = get_otp_group_id()
            grp_link = get_otp_group_link()
            ch2_link = get_channel2()
            ch2_ref = _extract_username(ch2_link)

            not_joined = []

            grp_ok = _check_member(grp_id, uid) if grp_id else None
            if grp_ok is False:
                not_joined.append(("🔥 OTP Group", grp_link))

            ch2_ok = _check_member(ch2_ref, uid) if ch2_ref else None
            if ch2_ok is False:
                not_joined.append(("📢 Main Channel", ch2_link))

            if not_joined:
                bot.answer_callback_query(call.id, "❌ Sob jagay join hao nai!", show_alert=False)
                lines = "❌ <b>Verify hote parcho na!</b>\n\n"
                lines += "⛔ Tumi ekhono nicher jagay join hao nai:\n\n"
                for name, _ in not_joined:
                    lines += f"  🚫 <b>{name}</b>\n"
                lines += "\n👇 Join and click <b>Verify</b>:"
                err_markup = types.InlineKeyboardMarkup(row_width=1)
                for name, lnk in not_joined:
                    err_markup.add(types.InlineKeyboardButton(
                        f"👉 JOIN {name}", url=lnk, style="danger"
                    ))
                err_markup.add(types.InlineKeyboardButton(
                    "🔄 Verify", callback_data="v", style="success"
                ))
                try:
                    bot.edit_message_text(
                        lines,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=err_markup,
                        parse_mode="HTML",
                    )
                except Exception:
                    bot.send_message(
                        call.message.chat.id,
                        lines,
                        reply_markup=err_markup,
                        parse_mode="HTML",
                    )
            else:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                vname = call.from_user.first_name or call.from_user.username or "User"
                bot.send_message(
                    call.message.chat.id,
                    get_template("verify_success").format(vname=vname, uid=uid),
                    reply_markup=main_menu(call.from_user.id),
                    parse_mode="HTML",
                )

        elif data == "back_to_services":
            # Cancel any active countdown so it stops re-editing this message
            cid = call.message.chat.id
            if cid in _countdowns:
                _countdowns[cid].set()
            markup, has_btns = _build_combined_service_markup()
            if has_btns:
                try:
                    bot.edit_message_text(
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        cid,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                except Exception:
                    bot.send_message(
                        cid,
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ No stock available in any service.", show_alert=True)

        elif data.startswith("v1svc:"):
            svc_key = data.split(":", 1)[1]
            markup = types.InlineKeyboardMarkup(row_width=2)
            btns = []
            svc_stock = dict(stock.get(svc_key, {}))   # snapshot to avoid race
            for cnt, nums in svc_stock.items():
                if nums:
                    _, flag = get_country_details(nums[0])
                    btns.append(types.InlineKeyboardButton(
                        f"{cnt}",
                        callback_data=f"n:{svc_key}:{cnt}",
                        style="primary",
                        **_flag_btn_kwargs(flag)
                    ))
            if btns:
                markup.add(*btns)
            markup.add(types.InlineKeyboardButton("⬅️ 𝗕𝗮𝗰𝗸", callback_data="back_to_services", style="danger"))
            if btns:
                try:
                    bot.edit_message_text(
                        "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b>",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                except Exception:
                    bot.send_message(
                        call.message.chat.id,
                        "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b>",
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ No stock in this service!", show_alert=True)

        elif data.startswith("s:"):
            svc = data.split(":")[1]
            markup = types.InlineKeyboardMarkup(row_width=2)
            btns = []
            if svc in stock:
                for cnt, nums in stock[svc].items():
                    if nums:
                        _, flag = get_country_details(nums[0])
                        btns.append(
                            types.InlineKeyboardButton(
                                f"{cnt}", callback_data=f"n:{svc}:{cnt}", style="primary",
                                **_flag_btn_kwargs(flag)
                            )
                        )
            if btns:
                markup.add(*btns)
            markup.add(
                types.InlineKeyboardButton("⬅️ 𝗕𝗮𝗰𝗸", callback_data="back_to_services", style="danger")
            )
            bot.edit_message_text(
                f"🔥 <b>{svc.upper()} — COUNTRY</b> 🔥",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("n:"):
            _, svc, scnt = data.split(":")
            if scnt in stock.get(svc, {}) and stock[svc][scnt]:
                n_batch = get_numbers_per_batch()
                available = stock[svc][scnt]
                count = min(n_batch, len(available))
                nums = [available.pop(0) for _ in range(count)]
                save_stock()
                c_name, flag = get_country_details(nums[0])
                uid_n = call.from_user.id
                cid_n = call.message.chat.id
                # Release any previously assigned number for this user
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_n]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                    print(f"[N:] Released old number(s) {old_nums} for user {uid_n}")
                for _rnum in nums:
                    register_number(cid_n, _rnum)
                display_nums = [n if n.startswith("+") else "+" + n for n in nums]
                _remember_number_view(uid_n, svc, scnt, display_nums, flag, c_name)
                init_kb = _build_numbers_display_kb(svc, scnt, display_nums, flag, c_name)
                # Track service/country for this user so OTP message buttons work
                _user_last_svc[uid_n] = (svc, scnt)
                # Cancel any running countdown for this chat before starting new one
                if cid_n in _countdowns:
                    _countdowns[cid_n].set()
                # V2-style: edit the CURRENT message in place (no new message sent)
                msg_id = call.message.message_id
                try:
                    bot.edit_message_text(
                        ".",
                        cid_n, msg_id,
                        reply_markup=init_kb,
                    )
                except Exception:
                    # Fallback: send new message if edit fails
                    sent = bot.send_message(cid_n, ".", reply_markup=init_kb)
                    msg_id = sent.message_id
                # Track so "Change Number" handler can find it
                _user_last_num_msg[uid_n] = msg_id
                _start_countdown(cid_n, msg_id, svc, flag, c_name, display_nums, scnt)
            else:
                bot.answer_callback_query(call.id, " STOCK SHESH! ", show_alert=True)

        elif data == "clr_menu":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.edit_message_text(
                "🗑️🔥 <b>STOCK CLEAR PANEL</b> 🔥🗑️\n\n"
                " <b>Kon service-er stock clear korbe?</b>\n"
                "⬇️ Choose a service:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=_clr_service_markup(),
                parse_mode="HTML",
            )

        elif data.startswith("clr_s:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            svc = data[6:]
            markup = types.InlineKeyboardMarkup(row_width=1)
            svc_stock = stock.get(svc, {})
            has_any = False
            for cnt, nums in svc_stock.items():
                if nums:
                    has_any = True
                    _, flag = get_country_details(nums[0])
                    cb = f"clr_c:{svc}:{cnt}"
                    if len(cb.encode()) <= 64:
                        markup.add(
                            types.InlineKeyboardButton(
                                f"🗑️ {cnt}  ({len(nums)} )", callback_data=cb, style="success",
                                **_flag_btn_kwargs(flag)
                            )
                        )
            if not has_any:
                markup.add(
                    types.InlineKeyboardButton("⚠️ Stock nai!", callback_data="clr_menu", style="primary")
                )
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="clr_menu", style="danger"))
            bot.edit_message_text(
                f"🔥 <b>{svc.upper()} — Kon desh clear korbe?</b> 🔥\n\n"
                f"⬇️ Choose a country:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("clr_c:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            _, svc, cnt = data.split(":", 2)
            count = len(stock.get(svc, {}).get(cnt, []))
            _, flag = get_country_details(stock[svc][cnt][0]) if count else ("", "🌐")
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    "✅ Yes, Delete", callback_data=f"clr_y:{svc}:{cnt}", style="success"
                ),
                types.InlineKeyboardButton("❌ Cancel", callback_data=f"clr_s:{svc}", style="primary"),
            )
            bot.edit_message_text(
                f"⚠️ <b>CONFIRM DELETE</b> ⚠️\n\n"
                f"💬 <b>Service ▸▸</b>  {svc.upper()}\n"
                f"🌍 <b>Country ▸▸</b>  {_resolve_flag(flag)} {cnt}\n"
                f"📱 <b>Numbers ▸▸</b>  {count} \n\n"
                f" Sure? Ei {count}  numbers will be deleted!",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("clr_y:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            _, svc, cnt = data.split(":", 2)
            removed = len(stock.get(svc, {}).get(cnt, []))
            if svc in stock and cnt in stock[svc]:
                del stock[svc][cnt]
                save_stock()
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🗑️ Aro Clear", callback_data=f"clr_s:{svc}", style="danger"),
                types.InlineKeyboardButton("🔙 Services", callback_data="clr_menu", style="success"),
            )
            bot.edit_message_text(
                f"✅🔥 <b>DELETE COMPLETE!</b> 🔥✅\n\n"
                f"💬 <b>Service ▸▸</b>  {svc.upper()}\n"
                f"🌍 <b>Country ▸▸</b>  {cnt}\n"
                f"📱 <b>Deleted  ▸▸</b>  {removed} number(s)\n\n"
                f"⚡ <i>Stock updated!</i>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data == "clr_all":
            if call.from_user.id not in ADMIN_IDS:
                return
            total = sum(
                len(nums) for svc_d in stock.values() for nums in svc_d.values()
            )
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    " Haa, SOB Clear", callback_data="clr_allok", style="primary"
                ),
                types.InlineKeyboardButton("❌ Cancel", callback_data="clr_menu", style="danger"),
            )
            bot.edit_message_text(
                f"☠️⚠️ <b>CLEAR ALL CONFIRM</b> ⚠️☠️\n\n"
                f" Total <b>{total}</b> numbers will be deleted!\n"
                f"⚡ Sob service-er sob country mochhe jabe!\n\n"
                f"🔥 Sure? Eta undo kora jabe na!",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data == "clr_allok":
            if call.from_user.id not in ADMIN_IDS:
                return
            stock = {
                "whatsapp": {},
                "facebook": {},
                "telegram": {},
                "instagram": {},
                "pc clone": {},
                "binance": {},
            }
            save_stock()
            bot.edit_message_text(
                "🔥 <b>ALL STOCK CLEARED!</b> 🔥\n <i>Now add new numbers!</i> ",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
            )

        elif data.startswith("rmpanel:"):
            caller_uid = call.from_user.id
            if caller_uid not in ADMIN_IDS:
                return
            pid = data.split(":", 1)[1]
            target = next((p for p in _dynamic_panels if p["id"] == pid), None)
            if not target:
                bot.answer_callback_query(call.id, "❌ Panel pawa jaini!", show_alert=True)
            elif not is_super_admin(caller_uid) and target.get("admin_id") != caller_uid:
                bot.answer_callback_query(call.id, "❌ Ei panel tomar na!", show_alert=True)
            else:
                _dynamic_panels[:] = [p for p in _dynamic_panels if p["id"] != pid]
                save_dynamic_panels()
                with _stats_lock:
                    _panel_stats.pop(pid, None)
                _dynamic_sessions.pop(pid, None)
                _dynamic_locks.pop(pid, None)
                try:
                    bot.edit_message_text(
                        f"✅🔥 <b>Panel <code>{pid}</code> removed!</b>\n"
                        f"<i>Monitor thread will stop naturally.</i>",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

        elif data.startswith("rmsvc:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            key = data.split(":", 1)[1]
            before = len(_services)
            _services[:] = [s for s in _services if s["key"] != key]
            if len(_services) < before:
                save_services()
                bot.edit_message_text(
                    f"✅🔥 <b>Service <code>{key}</code> removed!</b>\n"
                    f"<i>Removed from the service menu.</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            else:
                bot.answer_callback_query(call.id, "❌ Service pawa jaini!", show_alert=True)

        elif data.startswith("aadur:"):
            if not is_super_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Permission nei!", show_alert=True)
                return
            parts = data.split(":")
            new_uid = int(parts[1])
            months = int(parts[2])
            add_admin(new_uid, months=months)
            exp_ts = _admin_expiry.get(str(new_uid))
            exp_str = datetime.datetime.fromtimestamp(exp_ts).strftime("%d %b %Y") if exp_ts else "—"
            raw_n = user_names.get(str(new_uid), "")
            name_str = raw_n if isinstance(raw_n, str) else raw_n.get("first_name", str(new_uid))
            name_str = name_str or str(new_uid)
            try:
                bot.edit_message_text(
                    f"✅ <b>ADMIN ADDED!</b>\n\n"
                    f"👑 <b>New Admin:</b> {name_str} [<code>{new_uid}</code>]\n"
                    f"📅 <b>Meiad:</b> {months} Mash\n"
                    f"🗓️ <b>Expire Date:</b> {exp_str}\n\n"
                    f"<i>From now on this user will have admin panel access.</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id, f"✅ Admin added ({months} mash)!", show_alert=False)
            try:
                bot.send_message(
                    new_uid,
                    f"🎉 <b>Congratulations! Tumi Admin hoyecho!</b>\n\n"
                    f"📅 <b>Admin Meiad:</b> {months} Mash\n"
                    f"🗓️ <b>Expire:</b> {exp_str}\n\n"
                    f"Use the /admin command for admin panel access.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data == "aadur_cancel":
            bot.answer_callback_query(call.id, "❌ Cancelled.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass

        elif data.startswith("rmadmin:"):
            if not is_super_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Only Super Admin can remove!", show_alert=True)
                return
            target = int(data.split(":")[1])
            if remove_admin(target):
                raw_n = user_names.get(str(target), "")
                name = raw_n if isinstance(raw_n, str) else raw_n.get("first_name", str(target))
                name = name or str(target)
                bot.answer_callback_query(call.id, f"✅ {name} removed!", show_alert=False)
                try:
                    bot.edit_message_text(
                        f"✅ <b>ADMIN REMOVED!</b>\n\n"
                        f"🗑️ <b>Removed:</b> {name} [<code>{target}</code>]\n\n"
                        f"<i>From now on this user will lose admin access.</i>",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            else:
                bot.answer_callback_query(call.id, "❌ Remove kora gelo na (Super Admin)!", show_alert=True)

        elif data.startswith("cfg_toggle:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            parts = data.split(":")
            try:
                cid = int(parts[1])
                action = parts[2]
            except (IndexError, ValueError):
                bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)
                return
            with _demo_lock:
                for cfg in _demo_configs:
                    if cfg["id"] == cid:
                        cfg["active"] = (action == "start")
                        cfg_name = cfg["name"]
                        break
                else:
                    bot.answer_callback_query(call.id, "❌ Config not found!", show_alert=True)
                    return
            if action == "start":
                _demo_next_fire[cid] = 0
                status_msg = f"🟢 <b>{cfg_name} started!</b>"
            else:
                _demo_next_fire.pop(cid, None)
                status_msg = f"🔴 <b>{cfg_name} stopped!</b>"
            bot.answer_callback_query(call.id, status_msg.replace("<b>", "").replace("</b>", ""), show_alert=False)
            try:
                bot.edit_message_text(
                    "⚡ <b>Config Start/Stop:</b>",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=demo_cfg_inline_markup(),
                    parse_mode="HTML",
                )
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id,
                status_msg + "\n\n" + demo_status_text(),
                parse_mode="HTML",
            )

        elif data.startswith("rmcfg:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            try:
                cid = int(data.split(":", 1)[1])
            except ValueError:
                bot.answer_callback_query(call.id, "❌ Invalid config!", show_alert=True)
                return
            with _demo_lock:
                before = len(_demo_configs)
                _demo_configs[:] = [c for c in _demo_configs if c["id"] != cid]
                removed = before > len(_demo_configs)
            if removed:
                _demo_next_fire.pop(cid, None)
                try:
                    bot.edit_message_text(
                        f"✅🔥 <b>Config deleted!</b>\n\n" + demo_status_text(),
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            else:
                bot.answer_callback_query(call.id, "❌ Config not found!", show_alert=True)

        elif data.startswith("msgicon_set:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            slot_key = data.split(":", 1)[1]
            if slot_key not in _MSG_ICON_SLOTS:
                bot.answer_callback_query(call.id, "❌ Unknown slot!", show_alert=True)
                return
            default_char, label = _MSG_ICON_SLOTS[slot_key]
            uid = call.from_user.id
            _msg_icon_set_state[uid] = {"key": slot_key}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"✨ <b>Message Icon Set</b>\n\n"
                f"📌 <b>Slot:</b> <code>{{emoji_{slot_key}}}</code>\n"
                f"🏷️ <b>Label:</b> {label}\n"
                f"🔘 <b>Default:</b> {default_char}\n\n"
                f"Custom emoji sticker send (Telegram premium emoji), or enter the emoji ID:\n"
                f"<i>Type /back to cancel</i>",
                parse_mode="HTML",
                reply_markup=_back_admin_kb(),
            )
            bot.register_next_step_handler(msg, _set_msg_icon_step)
            bot.answer_callback_query(call.id)

        elif data.startswith("msgicon_reset:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            slot_key = data.split(":", 1)[1]
            with _custom_emoji_lock:
                removed = _custom_emojis.get("msg_slots", {}).pop(slot_key, None)
            if removed:
                _save_custom_emojis()
                bot.answer_callback_query(call.id, f"✅ '{slot_key}' reset to default!", show_alert=False)
            else:
                bot.answer_callback_query(call.id, "Already at default.", show_alert=False)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            _show_edit_messages_menu(call.message)

        # ── Withdraw / Payment callbacks ──────────────────────────────────────
        elif data == "wd_start":
            bot.answer_callback_query(call.id)
            _start_withdraw(call.message)

        elif data == "wd_cancel":
            uid = call.from_user.id
            _withdraw_state.pop(uid, None)
            bot.answer_callback_query(call.id, "❌ Cancelled.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(call.message.chat.id, "❌ Withdraw cancelled.",
                             reply_markup=main_menu(uid), parse_mode="HTML")

        elif data.startswith("wd_method:"):
            uid = call.from_user.id
            method = data.split(":", 1)[1]
            state = _withdraw_state.get(uid)
            if not state:
                bot.answer_callback_query(call.id, "❌ Session expired. Please try again.")
                return
            state["method"] = method
            bot.answer_callback_query(call.id, f"✅ {method} selected.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"📲 <b>{method}</b> account number/address:\n\n"
                f"Example bKash: <code>01XXXXXXXXX</code>",
                parse_mode="HTML",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
            )
            bot.register_next_step_handler(msg, _wd_account_step)

        elif data == "wd_confirm_submit":
            uid = call.from_user.id
            state = _withdraw_state.pop(uid, None)
            if not state:
                bot.answer_callback_query(call.id, "❌ Session expired. Please try again.")
                return
            amount  = state.get("amount", 0)
            method  = state.get("method", "?")
            account = state.get("account", "?")
            ok, new_bal = deduct_balance(uid, amount)
            if not ok:
                bot.answer_callback_query(call.id, "❌ Insufficient balance!", show_alert=True)
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                return
            cur = get_currency()
            import time as _time
            req_id = f"{uid}_{int(_time.time())}"
            req = {
                "id": req_id, "uid": uid, "amount": amount,
                "method": method, "account": account,
                "status": "pending", "timestamp": _time.time(),
            }
            with _withdraw_lock:
                _withdraw_requests.append(req)
            _save_withdraws()
            bot.answer_callback_query(call.id, "✅ Request submitted!")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id,
                f"✅ <b>Withdraw Request Submitted!</b>\n\n"
                f"💵 Amount: <code>{cur}{amount:.2f}</code>\n"
                f"📲 Method: <b>{method}</b>\n"
                f"📋 Account: <code>{account}</code>\n"
                f"💰 Remaining Balance: <code>{cur}{new_bal:.2f}</code>\n\n"
                f"Payment will be made after admin approval.",
                parse_mode="HTML",
                reply_markup=main_menu(uid),
            )
            # Notify all admins
            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve:{req_id}"),
                types.InlineKeyboardButton("❌ Reject",  callback_data=f"wd_reject:{req_id}"),
            )
            uname = call.from_user.username or call.from_user.first_name or str(uid)
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(
                        admin_id,
                        f"⏳ <b>New Withdraw Request!</b>\n\n"
                        f"👤 User: @{uname} (<code>{uid}</code>)\n"
                        f"💵 Amount: <code>{cur}{amount:.2f}</code>\n"
                        f"📲 Method: <b>{method}</b>\n"
                        f"📋 Account: <code>{account}</code>\n"
                        f"🔑 ID: <code>{req_id}</code>",
                        parse_mode="HTML",
                        reply_markup=admin_markup,
                    )
                except Exception:
                    pass

        elif data.startswith("wd_approve:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            req_id = data.split(":", 1)[1]
            req = None
            with _withdraw_lock:
                for r in _withdraw_requests:
                    if r["id"] == req_id and r["status"] == "pending":
                        r["status"] = "approved"
                        req = r
                        break
            if not req:
                bot.answer_callback_query(call.id, "❌ Request not found or already processed.", show_alert=True)
                return
            _save_withdraws()
            cur = get_currency()
            bot.answer_callback_query(call.id, "✅ Approved!")
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                bot.edit_message_text(
                    call.message.text + "\n\n✅ <b>Approved!</b>",
                    call.message.chat.id, call.message.message_id, parse_mode="HTML"
                )
            except Exception:
                pass
            try:
                bot.send_message(
                    req["uid"],
                    f"✅ <b>Withdraw Approved!</b>\n\n"
                    f"💵 Amount: <code>{cur}{req['amount']:.2f}</code>\n"
                    f"📲 Method: <b>{req['method']}</b>\n"
                    f"📋 Account: <code>{req['account']}</code>\n\n"
                    f"Payment will be sent shortly. Thank you! 🎉",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data.startswith("wd_reject:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            req_id = data.split(":", 1)[1]
            req = None
            with _withdraw_lock:
                for r in _withdraw_requests:
                    if r["id"] == req_id and r["status"] == "pending":
                        r["status"] = "rejected"
                        req = r
                        break
            if not req:
                bot.answer_callback_query(call.id, "❌ Request not found or already processed.", show_alert=True)
                return
            # Refund the balance
            add_reward(req["uid"], req["amount"])
            _save_withdraws()
            cur = get_currency()
            bot.answer_callback_query(call.id, "❌ Rejected, balance refunded.")
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                bot.edit_message_text(
                    call.message.text + "\n\n❌ <b>Rejected.</b>",
                    call.message.chat.id, call.message.message_id, parse_mode="HTML"
                )
            except Exception:
                pass
            try:
                bot.send_message(
                    req["uid"],
                    f"❌ <b>Withdraw Rejected.</b>\n\n"
                    f"💵 Amount: <code>{cur}{req['amount']:.2f}</code> has been refunded to your balance.\n\n"
                    f"Please contact the admin for assistance.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data in ("msgicon_close", "msgicon_noop"):
            if data == "msgicon_close":
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
            bot.answer_callback_query(call.id)

        elif data.startswith("editmsg:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            key = data.split(":", 1)[1]
            if key in _TEMPLATE_LABELS:
                _ask_new_template(call, key)
            else:
                bot.answer_callback_query(call.id, "❌ Unknown template!", show_alert=True)

        elif data.startswith("editmsg_reset:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            key = data.split(":", 1)[1]
            if key in _DEFAULT_TEMPLATES:
                _templates[key] = _DEFAULT_TEMPLATES[key]
                save_templates()
                bot.answer_callback_query(call.id, f"✅ '{key}' reset to default!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ Unknown template!", show_alert=True)

        elif data == "editmsg_reset_all":
            if call.from_user.id not in ADMIN_IDS:
                return
            _templates.update(_DEFAULT_TEMPLATES)
            save_templates()
            try:
                bot.edit_message_text(
        "✅🔥 <b>All messages reset to default!</b>\n\n"
        "<i>All messages will now use the default format.</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data == "grp_info":
            if call.from_user.id not in ADMIN_IDS:
                return
            _show_settings_inline(call)

        elif data == "set_autodel":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("auto_delete", True)
            _group_settings["auto_delete"] = not cur
            save_group_settings()
            bot.answer_callback_query(
                call.id,
                "✅ Auto Delete: " + ("🟢 ON" if not cur else "🔴 OFF"),
                show_alert=False,
            )
            _show_settings_inline(call)

        elif data == "toggle_v3":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("v3_enabled", True)
            _group_settings["v3_enabled"] = not cur
            save_group_settings()
            bot.answer_callback_query(
                call.id,
                "✅ V3 Panel: " + ("🟢 ON" if not cur else "🔴 OFF"),
                show_alert=False,
            )
            _show_settings_inline(call)

        elif data == "toggle_v2_mode":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("v2_user_mode", False)
            _group_settings["v2_user_mode"] = not cur
            save_group_settings()
            bot.answer_callback_query(
                call.id,
                "✅ Get Number Mode: " + ("🟢 ON" if not cur else "🔴 OFF"),
                show_alert=False,
            )
            _show_settings_inline(call)

        elif data == "toggle_grp_send":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("group_otp_send", True)
            _group_settings["group_otp_send"] = not cur
            save_group_settings()
            new_state = not cur
            bot.answer_callback_query(
                call.id,
                "✅ Group OTP Send: " + ("🟢 ON — OTP will go to the group" if new_state else "🔴 OFF — Will go to inbox only"),
                show_alert=True,
            )
            _show_settings_inline(call)

        elif data == "set_channel2":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "📢 <b>Enter new Join Channel link:</b>\n\n"
                "<i>Example: https://t.me/aR_OTP_rcv</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_channel2)

        elif data == "set_botlink":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "🤖 <b>Enter new Bot link:</b>\n\n"
                "<i>Example: https://t.me/ar_otp_bot</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_botlink)

        elif data == "grp_setlink":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "🔗 <b>Enter new OTP Group Link:</b>\n\n"
                "<i>Example: https://t.me/aR_OTP_rcv</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _grp_get_link)

        elif data == "grp_setid":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "🆔 <b>Enter new OTP Group Chat ID:</b>\n\n"
                "<i>Example: -1001234567890</i>\n"
                "⚠️ Must be a negative number (group ID is always negative)",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _grp_get_id)

        elif data == "grp_remove":
            if call.from_user.id not in ADMIN_IDS:
                return
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("✅ Haa, Remove", callback_data="grp_removeok", style="success"),
                types.InlineKeyboardButton("❌ Cancel", callback_data="grp_info", style="primary"),
            )
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "⚠️ <b>CONFIRM GROUP REMOVE</b> ⚠️\n\n"
                "OTP Group setting will be reset!\n"
                "Sending OTPs to the group will stop.\n\n"
                "Sure?",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("v2svc:"):
            sid = data.split(":", 1)[1]
            services = _v2_active_liveaccess()
            svc_data = next((s for s in services if s.get("sid") == sid), None)
            if not svc_data:
                bot.answer_callback_query(call.id, "❌ Service not found!", show_alert=True)
                return
            ranges = svc_data.get("ranges", [])
            markup = types.InlineKeyboardMarkup(row_width=2)
            rng_btns = []
            for rng in ranges:
                prefix = rng.rstrip("X")
                c_name, flag = get_country_details(prefix)
                short = c_name.split()[0] if c_name and c_name != "Unknown" else ""
                label = f"{short} | {rng}" if short else f"{rng}"
                rng_btns.append(types.InlineKeyboardButton(
                    label, callback_data=f"v2rng:{prefix}:{sid}", style="danger",
                    **_flag_btn_kwargs(flag)
                ))
            if rng_btns:
                markup.add(*rng_btns)
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="v2back", style="success"))
            bot.edit_message_text(
                f"📡 <b>V2 — {_v2_svc_emoji(sid)} {sid}</b>\n\n"
                f"🔢 <b>Select a range:</b>\n"
                f"<i>Live OTP available in this range — click to get a number</i>",
                call.message.chat.id, call.message.message_id,
                reply_markup=markup, parse_mode="HTML"
            )
            bot.answer_callback_query(call.id)

        elif data.startswith("v2rng:"):
            parts = data.split(":")
            prefix = parts[1] if len(parts) > 1 else ""
            sid = parts[2] if len(parts) > 2 else "?"
            bot.answer_callback_query(call.id, "⏳ Getting number...", show_alert=False)
            uid_v2 = call.from_user.id
            n_batch = get_numbers_per_batch()
            v2_nums = []
            for _ in range(n_batch):
                n = _v2_active_getnum(prefix, sid=sid)
                if n:
                    v2_nums.append(n)
            if v2_nums:
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_v2]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                for vn in v2_nums:
                    register_number(uid_v2, vn)
                c_name, flag = get_country_details(v2_nums[0])
                display_nums = [n if n.startswith("+") else "+" + n for n in v2_nums]
                _user_last_svc[uid_v2] = (sid.lower(), c_name)
                _remember_number_view(
                    uid_v2, sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                refresh_kb = _build_numbers_display_kb(
                    sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                bot.edit_message_text(
                    ".",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=refresh_kb
                )
                _user_last_num_msg[uid_v2] = call.message.message_id
            else:
                bot.answer_callback_query(call.id, "❌ Number not found! Try again later.", show_alert=True)

        elif data == "v2back":
            markup, has_btns = _build_combined_service_markup()
            if has_btns:
                try:
                    bot.edit_message_text(
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        call.message.chat.id, call.message.message_id,
                        reply_markup=markup, parse_mode="HTML"
                    )
                except Exception:
                    bot.send_message(
                        call.message.chat.id,
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        reply_markup=markup, parse_mode="HTML"
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ No service available.", show_alert=True)

        elif data.startswith("v2svc_cc:"):
            sid = data.split(":", 1)[1]
            markup, has_btns = _v2_build_country_markup(sid)
            emoji = _v2_svc_emoji(sid)
            if has_btns:
                bot.edit_message_text(
                    "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>SELECT COUNTRY</b>",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            else:
                bot.answer_callback_query(call.id, "❌ No range in this service.", show_alert=True)
            bot.answer_callback_query(call.id)

        elif data.startswith("v2csvc:"):
            parts = data.split(":")
            sid    = parts[1] if len(parts) > 1 else "?"
            prefix = parts[2] if len(parts) > 2 else ""
            bot.answer_callback_query(call.id, "⏳ Getting number...", show_alert=False)
            uid_v2  = call.from_user.id
            n_batch = get_numbers_per_batch()
            v2_nums = []
            for _ in range(n_batch):
                n = _v2_active_getnum(prefix, sid=sid)
                if n:
                    v2_nums.append(n)
            if v2_nums:
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_v2]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                for vn in v2_nums:
                    register_number(uid_v2, vn)
                c_name, flag = get_country_details(v2_nums[0])
                display_nums = [n if n.startswith("+") else "+" + n for n in v2_nums]
                _user_last_svc[uid_v2] = (sid.lower(), c_name)
                _remember_number_view(
                    uid_v2, sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                refresh_kb = _build_numbers_display_kb(
                    sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                bot.edit_message_text(
                    ".",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=refresh_kb
                )
                _user_last_num_msg[uid_v2] = call.message.message_id
            else:
                bot.answer_callback_query(call.id, "❌ Number not found! Try again later.", show_alert=True)

        elif data == "cc_back" or data == "cc_show":
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            try:
                bot.edit_message_text(
                    "📡 <b>Live Console Config</b>\n"
                    "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    "Select service — toggle or add/delete range:\n"
                    "✅ = enabled  ⭕ = disabled",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_services_markup(), parse_mode="HTML"
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id)

        elif data.startswith("cc_svc:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            sid = data.split(":", 1)[1]
            cfg = _console_config.get(sid, {})
            enabled = cfg.get("enabled", False)
            ranges  = cfg.get("ranges", [])
            status  = "✅ Enabled" if enabled else "⭕ Disabled"
            range_txt = "\n".join(
                f"  • {get_country_details(p)[1]} {get_country_details(p)[0]} ({p})"
                for p in ranges
            ) if ranges else "  (no range)"
            try:
                bot.edit_message_text(
                    f"📡 <b>{_v2_svc_emoji(sid)} {sid}</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    f"📌 Status: <b>{status}</b>\n"
                    f"🔢 Ranges:\n{range_txt}\n\n"
                    f"Use the buttons below to configure:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_service_detail_markup(sid), parse_mode="HTML"
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id)

        elif data.startswith("cc_toggle:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            sid = data.split(":", 1)[1]
            cfg = _console_config.setdefault(sid, {"enabled": False, "ranges": []})
            cfg["enabled"] = not cfg.get("enabled", False)
            save_console_config()
            status = "✅ Enabled" if cfg["enabled"] else "⭕ Disabled"
            bot.answer_callback_query(call.id, f"{status}!", show_alert=False)
            ranges = cfg.get("ranges", [])
            range_txt = "\n".join(
                f"  • {get_country_details(p)[1]} {get_country_details(p)[0]} ({p})"
                for p in ranges
            ) if ranges else "  (no range)"
            try:
                bot.edit_message_text(
                    f"📡 <b>{_v2_svc_emoji(sid)} {sid}</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    f"📌 Status: <b>{status}</b>\n"
                    f"🔢 Ranges:\n{range_txt}\n\n"
                    f"Use the buttons below to configure:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_service_detail_markup(sid), parse_mode="HTML"
                )
            except Exception:
                pass

        elif data.startswith("cc_addrange:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            sid = data.split(":", 1)[1]
            _cc_addrange_state[call.from_user.id] = sid
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                f"📲 <b>{sid}</b>  range prefix:\n"
                f"<i>Example: <code>880</code> (Bangladesh), <code>91</code> (India)</i>\n\n"
                f"Numbers only:",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, _cc_addrange_step)

        elif data.startswith("cc_delrange:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            parts = data.split(":")
            sid    = parts[1] if len(parts) > 1 else ""
            prefix = parts[2] if len(parts) > 2 else ""
            cfg = _console_config.get(sid, {})
            if prefix in cfg.get("ranges", []):
                cfg["ranges"].remove(prefix)
                save_console_config()
                bot.answer_callback_query(call.id, f"🗑️ ({prefix}) deleted!", show_alert=False)
            else:
                bot.answer_callback_query(call.id, "❌ Range not found!", show_alert=True)
                return
            ranges = cfg.get("ranges", [])
            range_txt = "\n".join(
                f"  • {get_country_details(p)[1]} {get_country_details(p)[0]} ({p})"
                for p in ranges
            ) if ranges else "  (no range)"
            status = "✅ Enabled" if cfg.get("enabled") else "⭕ Disabled"
            try:
                bot.edit_message_text(
                    f"📡 <b>{_v2_svc_emoji(sid)} {sid}</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    f"📌 Status: <b>{status}</b>\n"
                    f"🔢 Ranges:\n{range_txt}\n\n"
                    f"Use the buttons below to configure:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_service_detail_markup(sid), parse_mode="HTML"
                )
            except Exception:
                pass

        elif data.startswith("v2panel_set:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            new_pid = data.split(":", 1)[1]
            valid_ids = {p["id"] for p in _V2_PANELS_REGISTRY}
            if new_pid not in valid_ids:
                bot.answer_callback_query(call.id, "❌ Invalid panel!", show_alert=True)
                return
            _group_settings["v2_active_panel"] = new_pid
            save_group_settings()
            pname = _v2_active_panel_name()
            bot.answer_callback_query(call.id, f"✅ {pname} started!", show_alert=False)
            try:
                bot.edit_message_text(
                    f"📡 <b>V2 Active Panel</b>\n\n"
        f"✅ <b>{pname}</b> is now active.\n\n"
        f"<i>V2 LIVE RANGE and OTP forwarding will come from this panel.</i>",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_v2_panel_toggle_markup(),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        elif data.startswith("v3svc:"):
            sid = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, "⏳ Getting number...", show_alert=False)
            uid_v3 = call.from_user.id
            n_batch = get_numbers_per_batch()
            v3_nums = []
            for _ in range(n_batch):
                n = _v3_getnum(sid)
                if n:
                    v3_nums.append(n)
            if v3_nums:
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_v3]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                for vn in v3_nums:
                    register_number(uid_v3, vn)
                c_name, flag = get_country_details(v3_nums[0])
                display_nums = [n if n.startswith("+") else "+" + n for n in v3_nums]
                _user_last_svc[uid_v3] = (sid.lower(), c_name)
                _remember_number_view(
                    uid_v3, sid.lower(), c_name, display_nums, flag, c_name
                )
                refresh_kb = _build_numbers_display_kb(
                    sid.lower(), c_name, display_nums, flag, c_name
                )
                bot.edit_message_text(
                    ".",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=refresh_kb
                )
                _user_last_num_msg[uid_v3] = call.message.message_id
            else:
                bot.answer_callback_query(call.id, "❌ Number not found! Try again later.", show_alert=True)

        elif data == "v3back":
            services = _v3_get_services()
            markup, has = _v3_build_console_markup(services)
            text = (
                "🆕 <b>V3 PANEL</b>\n"
                "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                "🔴 <b>Select a service:</b>\n"
                "<i>Click a service to get a number</i>\n\n"
                "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>"
                if has else
                "🆕 <b>V3 PANEL</b>\n\n⚠️ No service available."
            )
            try:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                      reply_markup=markup, parse_mode="HTML")
            except Exception:
                pass
            bot.answer_callback_query(call.id)

        elif data == "eg_add":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id,
                "➕ <b>Extra Group Add</b>\n\n"
                "Enter the group's <b>Chat ID</b>:\n"
                "<i>Example: <code>-1001234567890</code></i>\n\n"
                "💡 To get Chat ID, add @userinfobot to the group.",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            bot.register_next_step_handler(msg, _eg_add_step1)

        elif data.startswith("eg_del:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            extra = _group_settings.get("extra_groups", [])
            if 0 <= idx < len(extra):
                removed = extra.pop(idx)
                save_group_settings()
                bot.answer_callback_query(call.id, f"✅ Group {removed.get('id')} removed!", show_alert=True)
                _show_extra_groups(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ Group not found.", show_alert=True)

        elif data.startswith("eg_setbot:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            bot.answer_callback_query(call.id)
            _eg_state[call.from_user.id] = {"_edit_idx": idx, "_field": "bot_link"}
            msg = bot.send_message(call.message.chat.id,
                f"🤖 <b>Group #{idx+1} Bot Link</b>\n\nEnter new bot link (skip = <code>skip</code>):",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            bot.register_next_step_handler(msg, _eg_edit_link_step)

        elif data.startswith("eg_setch:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            bot.answer_callback_query(call.id)
            _eg_state[call.from_user.id] = {"_edit_idx": idx, "_field": "channel_link"}
            msg = bot.send_message(call.message.chat.id,
                f"📢 <b>Group #{idx+1} Channel Link</b>\n\nEnter new channel link (skip = <code>skip</code>):",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            bot.register_next_step_handler(msg, _eg_edit_link_step)

        elif data.startswith("eg_test:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            extra = _group_settings.get("extra_groups", [])
            if 0 <= idx < len(extra):
                g = extra[idx]
                gid = g.get("id")
                bot.answer_callback_query(call.id, "🧪 Sending test message...")
                try:
                    bot.send_message(
                        gid,
                        f"🧪 <b>Test Message</b>\n\n"
                        f"✅ Bot is successfully sending messages to this group!\n"
                        f"🆔 Group ID: <code>{gid}</code>\n\n"
                        f"<i>OTP will be sent here when received.</i>",
                        parse_mode="HTML",
                    )
                    bot.send_message(
                        call.message.chat.id,
                        f"✅ <b>Group #{idx+1} Test Successful!</b>\n\n"
                        f"🆔 ID: <code>{gid}</code>\n"
                        f"Bot can send messages to that group. OTP will be sent there.",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    bot.send_message(
                        call.message.chat.id,
                        f"❌ <b>Group #{idx+1} Test Failed!</b>\n\n"
                        f"🆔 ID: <code>{gid}</code>\n"
                        f"⚠️ Error: <code>{str(e)[:200]}</code>\n\n"
                        f"<b>Solution:</b>\n"
                        f"• Add the bot as <b>Admin</b> in that group\n"
                        f"• Check if the Group ID is correct\n"
                        f"• Group ID is usually in <code>-100XXXXXXXXXX</code> format",
                        parse_mode="HTML",
                    )
            else:
                bot.answer_callback_query(call.id, "❌ Group not found.", show_alert=True)

        elif data.startswith("eg_info:"):
            idx = int(data.split(":", 1)[1])
            extra = _group_settings.get("extra_groups", [])
            if 0 <= idx < len(extra):
                g = extra[idx]
                bot.answer_callback_query(
                    call.id,
                    f"ID: {g.get('id')}\nBot: {g.get('bot_link') or '—'}\nCh: {g.get('channel_link') or '—'}",
                    show_alert=True
                )
            else:
                bot.answer_callback_query(call.id, "❌ Not found", show_alert=True)

        elif data == "grp_removeok":
            if call.from_user.id not in ADMIN_IDS:
                return
            _group_settings["otp_group_id"] = None
            _group_settings["otp_group_link"] = ""
            save_group_settings()
            bot.answer_callback_query(call.id, "✅ Group removed!")
            _show_settings_inline(call)

        elif data == "set_group_tag":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            cur_tag = _group_settings.get("group_tag", "BOT")
            msg = bot.send_message(
                call.message.chat.id,
                f"🌸 <b>Number Tag Set/Change</b>\n\n"
                f"🔹 <b>Bortoman Tag:</b> <code>{cur_tag}</code>\n"
                f'📱 Preview: <b>245<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{cur_tag}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>5660</b>\n\n'
                f"Enter new tag (text only, no emoji):\n"
                f"<i>Example: ATIK, BOT, OTP, KING</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_group_tag)

        elif data == "set_num_batch":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            cur_batch = _group_settings.get("numbers_per_batch", 1)
            msg = bot.send_message(
                call.message.chat.id,
                f"🔢 <b>Numbers Per User — Set</b>\n\n"
                f"🔹 <b>Current Setting:</b> <code>{cur_batch}</code>\n\n"
                f"How many numbers can a user get at once?\n"
                f"<i>Example: 1, 2, 3, 5 (max 10)</i>\n\n"
                f"⚠️ This setting applies to all V1, V2.",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_num_batch)

    except Exception as e:
        print(f"Callback Error: {e}")


# ── Excel / CSV helpers ───────────────────────────────────────────────────────

def _get_valid_services():
    """Return list of valid service keys from live _services list."""
    return [s["key"] for s in _services]

VALID_SERVICES = [
    "facebook",
    "instagram",
    "whatsapp",
    "telegram",
    "binance",
    "pc clone",
]


def _parse_spreadsheet(data: bytes, filename: str):
    """
    Parse Excel (.xlsx / .xls) or CSV file.
    Returns:
      - (rows, mode)
        mode='two_col' → rows = list of (service, number)
        mode='one_col' → rows = list of number strings
    Accepts header rows with 'service'/'number' labels.
    Falls back: 2-column files = service+number, 1-column = numbers only.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    raw_rows = []

    if ext == "csv":
        text = data.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            cleaned = [c.strip() for c in row if c.strip()]
            if cleaned:
                raw_rows.append(cleaned)
    elif ext == "xlsx":
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        def _xlsx_cell_str(c):
            if isinstance(c, float) and c.is_integer():
                return str(int(c))
            return str(c)
        for row in ws.iter_rows(values_only=True):
            cleaned = [_xlsx_cell_str(c).strip() for c in row if c is not None and _xlsx_cell_str(c).strip()]
            if cleaned:
                raw_rows.append(cleaned)
    elif ext == "xls":
        wb = xlrd.open_workbook(file_contents=data)
        ws = wb.sheet_by_index(0)
        def _xls_cell_str(cv):
            if isinstance(cv, float) and cv.is_integer():
                return str(int(cv))
            return str(cv)
        for ri in range(ws.nrows):
            cleaned = [
                _xls_cell_str(ws.cell_value(ri, ci)).strip()
                for ci in range(ws.ncols)
                if _xls_cell_str(ws.cell_value(ri, ci)).strip()
            ]
            if cleaned:
                raw_rows.append(cleaned)
    else:
        return [], "unknown"

    if not raw_rows:
        return [], "empty"

    # Detect header row
    start = 0
    first = [c.lower() for c in raw_rows[0]]
    if any(h in first for h in ("service", "number", "phone", "mobile")):
        start = 1

    data_rows = raw_rows[start:]
    if not data_rows:
        return [], "empty"

    # Detect mode by column count of the majority of rows
    two_col_count = sum(1 for r in data_rows if len(r) >= 2)
    one_col_count = len(data_rows) - two_col_count

    if two_col_count > one_col_count:
        result = []
        for r in data_rows:
            if len(r) < 2:
                continue
            col0, col1 = r[0], r[1]
            # Determine which column is service and which is number
            col0_is_num = re.match(r"^\+?\d{6,15}$", re.sub(r"\s", "", col0))
            col1_is_num = re.match(r"^\+?\d{6,15}$", re.sub(r"\s", "", col1))
            if col0_is_num and not col1_is_num:
                svc = col1.lower().strip()
                num = re.sub(r"\D", "", col0)
            elif col1_is_num and not col0_is_num:
                svc = col0.lower().strip()
                num = re.sub(r"\D", "", col1)
            else:
                svc = col0.lower().strip()
                num = re.sub(r"\D", "", col1)
            if num and len(num) >= 7:
                result.append((svc, num))
        return result, "two_col"
    else:
        result = []
        for r in data_rows:
            num = re.sub(r"\D", "", r[0])
            if len(num) >= 7:
                result.append(num)
        return result, "one_col"


def _notify_new_numbers(svc, c_name, flag, total_added):
    """Broadcast NEW NUMBERS notification to all registered users + main group + extra groups."""
    _NEW_SEP = ''.join(['<tg-emoji emoji-id="5870818207383686839">➖</tg-emoji>'] * 8)
    _added_icon = '<tg-emoji emoji-id="5267041999948653482">📤</tg-emoji>'
    _svc_e = _v2_svc_emoji(svc)
    text = (
        f"{_NEW_SEP}\n"
        f'<tg-emoji emoji-id="5296633779157243809">🆕</tg-emoji> 《 NEW NUMBERS 》\n'
        f"{_NEW_SEP}\n"
        f"{_resolve_flag(flag)} {c_name.upper()} {_svc_e} {svc.upper()}\n"
        f"{_NEW_SEP}\n"
        f'{_added_icon} Total Added: {total_added} <tg-emoji emoji-id="5251338246599765890">✅</tg-emoji>\n'
        f"{_NEW_SEP}\n"
        f'<tg-emoji emoji-id="5375338737028841420">🚀</tg-emoji> Use /start to get your numbers! <tg-emoji emoji-id="5251203410396458957">👉</tg-emoji>'
    )
    def _send():
        # Send to main group
        main_grp = get_otp_group_id()
        if main_grp:
            try:
                bot.send_message(main_grp, text, parse_mode="HTML")
            except Exception as _eg:
                print(f"[NEW-NUM] Main group send error: {_eg}")
        # Send to extra groups
        for eg in _group_settings.get("extra_groups", []):
            eg_id = eg.get("id")
            if eg_id:
                try:
                    bot.send_message(eg_id, text, parse_mode="HTML")
                except Exception as _eg:
                    print(f"[NEW-NUM] Extra group {eg_id} send error: {_eg}")
        # Send to all registered users (inbox)
        for uid in list(users):
            try:
                bot.send_message(uid, text, parse_mode="HTML")
                time.sleep(0.05)
            except Exception:
                pass
    threading.Thread(target=_send, daemon=True).start()


def _add_numbers_bulk(svc: str, numbers: list, notify=True):
    """Add a list of number strings to stock[svc]. Returns (added, skipped)."""
    added, skipped = 0, 0
    first_num = None
    svc = svc.lower().strip()
    # Auto-create service in stock if it exists in _services list but not in stock
    if svc not in stock:
        valid_keys = [s["key"] for s in _services]
        if svc not in valid_keys:
            return 0, len(numbers)
        stock[svc] = {}
    for num in numbers:
        num = re.sub(r"\D", "", str(num))
        if not num:
            skipped += 1
            continue
        c_name, _ = get_country_details(num)
        if c_name == "Unknown":
            skipped += 1
            continue
        if first_num is None:
            first_num = num
        if c_name not in stock[svc]:
            stock[svc][c_name] = []
        stock[svc][c_name].append(num)
        added += 1
    if added:
        save_stock()
        if notify and first_num:
            c_name, flag = get_country_details(first_num)
            _notify_new_numbers(svc, c_name, flag, added)
    return added, skipped


def _service_select_markup():
    """Build service selection keyboard from live _services list."""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    labels = [s["label"].split("→")[0].split("💎")[0].strip() for s in _services]
    if labels:
        m.add(*labels)
    else:
        m.add("Facebook", "Instagram", "WhatsApp", "Telegram", "Binance", "PC Clone")
    return m


_SVC_PLAIN_EMOJI = {
    "instagram": "📸", "facebook": "🔵", "telegram": "✈️",
    "whatsapp": "💚", "tiktok": "🎵", "twitter": "🐦",
    "binance": "🟡", "snapchat": "👻", "google": "🔴",
    "youtube": "📺", "linkedin": "💼", "amazon": "🛒",
    "pc clone": "📱",
}


def _admin_add_svc_keyboard():
    """Reply keyboard for admin Number Add — styled KeyboardButtons with custom emoji icons."""
    _colors = ["primary", "success", "danger"]
    KB = types.KeyboardButton
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    svcs = _services if _services else [
        {"key": k, "label": k.title()}
        for k in ["facebook", "instagram", "whatsapp", "telegram", "binance", "pc clone"]
    ]
    btns = []
    for i, svc in enumerate(svcs):
        key = str(svc.get("key", "")).strip().lower()
        label = str(svc.get("label", "")).split("→")[0].split("💎")[0].strip()
        icon_id = _svc_icon_emoji_id(key)
        icon_kwargs = {"icon_custom_emoji_id": icon_id} if icon_id else {}
        btns.append(KB(label, style=_colors[i % 3], **icon_kwargs))
    m.add(*btns)
    m.add(KB("❌ Cancel", style="danger"))
    return m


@bot.message_handler(content_types=["document"])
def document_handler(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    # If user is in finalize_auto_add Excel-wait flow, let the next_step_handler handle it
    if uid in _awaiting_slot_excel:
        return
    register_user(message.chat.id)

    doc = message.document
    name = doc.file_name or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    # ── .txt / .json handler — auto-detect service emoji or flag file ───────────
    if ext in ("txt", "json"):
        wait = bot.send_message(message.chat.id,
            f"⏳ <b>{name}</b> parsing...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
            txt_content = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            bot.edit_message_text(f"❌ File download hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return
        import re as _re

        _KNOWN_SVCS = {
            "INSTAGRAM","FACEBOOK","WHATSAPP","TELEGRAM","TIKTOK","TWITTER",
            "BINANCE","SNAPCHAT","GOOGLE","YOUTUBE","LINKEDIN","AMAZON",
            "TINDER","UBER","NETFLIX","SPOTIFY","VIBER","LINE","WECHAT",
            "DISCORD","REDDIT","PINTEREST","TUMBLR","SIGNAL","SKYPE",
        }

        def _parse_service_emoji_txt(content):
            """Extract {SERVICE_NAME: emoji_id} from any common format."""
            result = {}
            # Try whole-file JSON first
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    for k, v in data.items():
                        svc = str(k).upper().strip()
                        eid_m = _re.search(r'\d{10,}', str(v))
                        if svc and eid_m:
                            result[svc] = eid_m.group(0)
                    return result
            except Exception:
                pass
            # Line-by-line: find first word-like token + any 10-digit number on same line
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                eid_m = _re.search(r'(\d{10,})', line)
                if not eid_m:
                    continue
                eid = eid_m.group(1)
                prefix = line[:line.index(eid)]
                svc_m = _re.search(r'([A-Za-z][A-Za-z0-9 _\-]{1,20})', prefix)
                if svc_m:
                    svc = _re.sub(r'[\s\-_]+', '_', svc_m.group(1).strip()).upper().rstrip('_:→- ')
                    if svc:
                        result[svc] = eid
            return result

        def _is_service_file(content):
            """Return True if any line has a known service keyword + 10-digit number."""
            for line in content.splitlines():
                ul = line.upper()
                if _re.search(r'\d{10,}', ul):
                    for svc in _KNOWN_SVCS:
                        if svc in ul:
                            return True
            # Also detect JSON with service-like keys
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    for k in data:
                        if str(k).upper() in _KNOWN_SVCS:
                            return True
            except Exception:
                pass
            return False

        # Auto-detect: service emoji file or flag file?
        if ext == "json" or _is_service_file(txt_content):
            # ── Service emoji file ──────────────────────────────────────────
            svc_loaded = _parse_service_emoji_txt(txt_content)
            try:
                bot.delete_message(message.chat.id, wait.message_id)
            except Exception:
                pass
            if not svc_loaded:
                bot.send_message(message.chat.id,
                    "❌ <b>Service emoji data parse hoyni!</b>\n\n"
                    "<b>TXT format:</b>\n"
                    "<code>WHATSAPP 5334998226636390258\nINSTAGRAM 5319160079465857105</code>\n\n"
                    "<b>JSON format:</b>\n"
                    "<code>{\"WHATSAPP\": \"5334998226636390258\"}</code>",
                    parse_mode="HTML")
                return
            with _custom_emoji_lock:
                _custom_emojis.setdefault("services", {}).update(svc_loaded)
            _save_custom_emojis()
            lines_preview = "\n".join(
                f"  🎯 <b>{k}</b> → <code>{v}</code>"
                for k, v in list(svc_loaded.items())[:20])
            extra = f"\n  <i>...and {len(svc_loaded)-20} more</i>" if len(svc_loaded) > 20 else ""
            bot.send_message(message.chat.id,
                f"✅ <b>{len(svc_loaded)} service emojis set!</b>\n\n"
                f"{lines_preview}{extra}\n\n"
                f"🎉 Ekhon OTP message-e custom emoji dekhabe.",
                parse_mode="HTML")
            return
        # ── Flag emoji file (original .txt handler) ─────────────────────────
        parsed = {}
        for line in txt_content.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _re.search(r'([🇠-🇿]{2}).*?"id"\s*:\s*"(\d+)"', line)
            if m:
                parsed[m.group(1)] = m.group(2)
                continue
            tokens = line.split()
            if len(tokens) >= 2 and tokens[-1].isdigit() and len(tokens[-1]) >= 10:
                flag_tok = next((t for t in tokens if len(t) == 2 and
                    all('🇠' <= c <= '🇿' for c in t)), None)
                if flag_tok:
                    parsed[flag_tok] = tokens[-1]
        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass
        if not parsed:
            bot.send_message(message.chat.id,
                "❌ <b>Flag data parse hoyni!</b>\n\n"
                "Flag file format:\n"
                "<code>(1)(US)🇺🇸 United States {\"emoji\": \"🇺🇸\", \"id\": \"123...\"}</code>\n\n"
                "Service emoji file format:\n"
                "<code>WHATSAPP 5334998226636390258\nINSTAGRAM 5319160079465857105</code>",
                parse_mode="HTML")
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        lines_preview = "\n".join(
            f"  {k} → <code>{v}</code>" for k, v in list(parsed.items())[:10]
        )
        extra = f"\n  <i>...and {len(parsed)-10} more</i>" if len(parsed) > 10 else ""
        bot.send_message(message.chat.id,
            f"✅ <b>{len(parsed)} custom flag emoji(s) loaded!</b>\n\n"
            f"{lines_preview}{extra}\n\n"
            f"🎉 Custom flags will now appear in all OTP/number messages.",
            parse_mode="HTML")
        return
    # ────────────────────────────────────────────────────────────────────────────

    # ── .json service emoji file handler ────────────────────────────────────────
    if ext == "json":
        wait = bot.send_message(message.chat.id,
            f"⏳ <b>{name}</b> parsing...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
            data = json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception as e:
            bot.edit_message_text(f"❌ File load/parse hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return

        if not isinstance(data, dict):
            bot.edit_message_text(
                "❌ <b>Invalid format!</b>\n\n"
                "The JSON file should be:\n"
                "<code>{\n"
                '  "WHATSAPP": "5334998226636390258",\n'
                '  "INSTAGRAM": "5319160079465857105",\n'
                '  "FACEBOOK": "5323261730283863478"\n'
                "}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return

        loaded = {}
        skipped = []
        for svc_raw, eid in data.items():
            svc = str(svc_raw).upper().strip()
            eid = str(eid).strip()
            if not svc or not eid.isdigit():
                skipped.append(f"{svc_raw}: {eid}")
                continue
            loaded[svc] = eid

        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass

        if not loaded:
            bot.send_message(message.chat.id,
                "❌ <b>Kono valid service emoji ID pawa jayni!</b>\n\n"
                "Check the format:\n"
                "<code>{\"WHATSAPP\": \"5334998226636390258\"}</code>",
                parse_mode="HTML")
            return

        with _custom_emoji_lock:
            _custom_emojis.setdefault("services", {}).update(loaded)
        _save_custom_emojis()

        lines_preview = "\n".join(
            f"  🎯 <b>{k}</b> → <code>{v}</code>" for k, v in list(loaded.items())[:20]
        )
        extra = f"\n  <i>...and {len(loaded)-20} more</i>" if len(loaded) > 20 else ""
        skip_txt = ""
        if skipped:
            skip_txt = f"\n\n⚠️ <b>Skipped ({len(skipped)}):</b> {', '.join(skipped[:5])}"

        bot.send_message(message.chat.id,
            f"✅ <b>{len(loaded)} service emoji IDs set!</b>\n\n"
            f"{lines_preview}{extra}{skip_txt}\n\n"
            f"🎉 From now on, custom service emojis will show in OTP messages.",
            parse_mode="HTML")
        return
    # ────────────────────────────────────────────────────────────────────────────

    if ext not in ("xlsx", "xls", "csv"):
        bot.send_message(
            message.chat.id,
            "❌ <b>Unsupported file!</b>\n\n"
            "📎 Supported formats:\n"
            "  • <b>.txt</b>  — Premium Flag file\n"
            "  • <b>.json</b> — Service Emoji ID file\n"
            "  • <b>.xlsx</b> — Excel (new)\n"
            "  • <b>.xls</b>  — Excel (old)\n"
            "  • <b>.csv</b>  — CSV\n\n"
            "💡 File pathao abar!",
            parse_mode="HTML",
        )
        return

    wait = bot.send_message(
        message.chat.id, f"⏳🔥 <b>{name}</b> parsing...", parse_mode="HTML"
    )

    try:
        file_info = bot.get_file(doc.file_id)
        raw = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.edit_message_text(
            f"❌ File download hoyni: {e}",
            message.chat.id,
            wait.message_id,
            parse_mode="HTML",
        )
        return

    rows, mode = _parse_spreadsheet(raw, name)

    try:
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        pass

    if mode in ("unknown", "empty") or not rows:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>File-e kono data paini!</b> ⚠️\n\n"
            "📋 <b>Supported formats:</b>\n"
            "  • <b>2-column:</b>  Service | Number\n"
            "  • <b>1-column:</b>  Number only (add service afterward)\n\n"
            "💡 Sample format:\n"
            "<code>facebook  | 8801700123456\n"
            "whatsapp  | 8801800234567\n"
            "telegram  | 251912345678</code>",
            parse_mode="HTML",
        )
        return

    if mode == "two_col":
        # Group by service and add directly
        service_map = {}
        for svc, num in rows:
            service_map.setdefault(svc, []).append(num)

        total_added, total_skipped = 0, 0
        report_lines = ""
        for svc, nums in service_map.items():
            added, skipped = _add_numbers_bulk(svc, nums)
            total_added += added
            total_skipped += skipped
            icon = "✅" if added else "⚠️"
            report_lines += f"{icon} <b>{svc.upper()}</b>: +{added} added"
            if skipped:
                report_lines += f"  (⚠️ {skipped} skip)"
            report_lines += "\n"

        bot.send_message(
            message.chat.id,
            f"📊🔥 <b>EXCEL IMPORT DONE!</b> 🔥📊\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"📎 <b>File:</b> <code>{name}</code>\n"
            f"📋 <b>Rows parsed:</b> {len(rows)}\n\n"
            f"{report_lines}\n"
            f"✅ <b>Total added:</b> {total_added}\n"
            f"⚠️ <b>Skipped:</b> {total_skipped}\n\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            f"💡 Use /panels to check stock.",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )

    else:
        # one_col: ask which service
        _pending_excel[uid] = {"numbers": rows, "filename": name}
        bot.send_message(
            message.chat.id,
            f"📂🔥 <b>FILE LOADED!</b> 🔥📂\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"📎 <b>File:</b> <code>{name}</code>\n"
            f"📱 <b>Numbers found:</b> {len(rows)}\n\n"
            f" <b>Kon service-e add korbo?</b>\n"
            f"⬇️ Choose:",
            reply_markup=_service_select_markup(),
            parse_mode="HTML",
        )
        msg = bot.send_message(
            message.chat.id, "⬇️ Type a service:", parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, _excel_pick_service)


def _excel_pick_service(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _intercept_menu_btn(message):
        _pending_excel.pop(uid, None)
        return
    svc_raw = (message.text or "").strip().lower()

    # Build dynamic match map from live _services list
    svc = None
    live_valid = _get_valid_services()  # e.g. ["facebook", "instagram", "pc clone", ...]
    # Direct key match first
    for key in live_valid:
        if svc_raw == key:
            svc = key
            break
    # Label match (strip decorators like →, 💎)
    if svc is None:
        for s in _services:
            label_clean = s["label"].split("→")[0].split("💎")[0].strip().lower()
            if svc_raw == label_clean or svc_raw == s["key"]:
                svc = s["key"]
                break
    # Common short aliases (always useful)
    if svc is None:
        _aliases = {
            "fb": "facebook", "ig": "instagram", "wa": "whatsapp",
            "tg": "telegram", "bnb": "binance", "pc": "pc clone", "clone": "pc clone",
        }
        svc = _aliases.get(svc_raw)
        if svc and svc not in live_valid:
            svc = None  # alias exists but service not in list
    # Partial/prefix match as last resort
    if svc is None:
        for key in live_valid:
            if key.startswith(svc_raw) or svc_raw in key:
                svc = key
                break

    if svc is None:
        valid_labels = " / ".join(s["label"].split("→")[0].split("💎")[0].strip() for s in _services)
        msg = bot.send_message(
            message.chat.id,
            f"❌ Choose a valid service:\n<code>{valid_labels}</code>",
            reply_markup=_service_select_markup(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _excel_pick_service)
        return

    pending = _pending_excel.pop(uid, None)
    if not pending:
        bot.send_message(
            message.chat.id,
            "⚠️ Session expired. File abar pathao.",
            reply_markup=main_menu(uid),
        )
        return

    numbers = pending["numbers"]
    filename = pending["filename"]
    added, skipped = _add_numbers_bulk(svc, numbers)

    bot.send_message(
        message.chat.id,
        f"📊🔥 <b>EXCEL IMPORT DONE!</b> 🔥📊\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"📎 <b>File:</b>     <code>{filename}</code>\n"
        f"💬 <b>Service:</b>  <b>{svc.upper()}</b>\n"
        f"📱 <b>Parsed:</b>   {len(numbers)}\n\n"
        f"✅ <b>Added:</b>    {added}\n"
        f"⚠️ <b>Skipped:</b>  {skipped}\n\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        f"💡 Use /panels to check stock.",
        reply_markup=main_menu(uid),
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global stock
    uid = message.from_user.id
    txt = message.text
    register_user(message.chat.id)

    if txt in ("☎️ 𝗩𝟭 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️", "☎️ 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️"):
        show_services(message)

    elif txt in ("📲 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥", "𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥"):
        show_services(message)

    elif txt == "🔄 𝗩𝟮 𝗦𝗪𝗜𝗧𝗖𝗛":
        _v2_users.add(uid)
        _save_v2_users()
        bot.send_message(
            message.chat.id,
            "🔄 <b>V2 SWITCH</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        "Select mode:\n\n"
        "🔴 <b>LIVE RANGE</b> — Shows live OTP range from panel\n"
        "⌨️ <b>CUSTOM RANGE</b> — Enter range manually, get matching number\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=v2_switch_menu(),
            parse_mode="HTML",
        )

    elif txt == "🔴 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗚𝗘":
        _v2_show_console(message.chat.id)

    elif txt == "🆕 𝗩𝟯 𝗣𝗔𝗡𝗘𝗟":
        _v3_show_console(message.chat.id)

    elif txt == "⌨️ 𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘":
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("❌ Cancel"))
        msg = bot.send_message(
            message.chat.id,
            "⌨️ <b>CUSTOM RANGE</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "📲 the range/prefix you want:\n"
            "<i>Example: <code>8801</code>, <code>44</code>, <code>33</code></i>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=cancel_markup,
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _v2_custom_range_step)

    elif txt == "🔙 𝗩𝟭 𝗦𝗪𝗜𝗧𝗖𝗛":
        _v2_users.discard(uid)
        _save_v2_users()
        mname = message.from_user.first_name or message.from_user.username or "User"
        bot.send_message(
            message.chat.id,
            f"╔═════════════════════╗\n"
            f"      USER MENU-te WELCOME!\n"
            f"   👋 <b>{mname}</b>, what would you like to do?\n"
            f"╚═════════════════════╝",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )

    elif txt in _get_svc_map():
        svc = _get_svc_map()[txt]
        show_countries(message.chat.id, svc)

    elif txt in ("🔙 Admin Menu", "🔙 Admin Panel", "🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟") and uid in ADMIN_IDS:
        _go_admin_panel(message)

    elif txt == "🔙 Main Menu":
        mname = message.from_user.first_name or message.from_user.username or "User"
        bot.send_message(
            message.chat.id,
            f"╔═════════════════════╗\n"
            f"      USER MENU-te WELCOME!\n"
            f"   👋 <b>{mname}</b>, what would you like to do?\n"
            f"╚═════════════════════╝",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )

    elif txt in ("📞 𝗦𝗔𝗣𝗢𝗥𝗧", "𝗦𝗔𝗣𝗢𝗥𝗧"):
        markup = types.InlineKeyboardMarkup()
        _sup_id = _group_settings.get("support_id", "").strip()
        if _sup_id:
            # Build proper t.me URL from username or numeric ID
            if _sup_id.startswith("http"):
                _sup_url = _sup_id
            elif _sup_id.startswith("@"):
                _sup_url = f"https://t.me/{_sup_id.lstrip('@')}"
            elif _sup_id.lstrip("-").isdigit():
                _sup_url = f"tg://user?id={_sup_id}"
            else:
                _sup_url = f"https://t.me/{_sup_id}"
            markup.add(types.InlineKeyboardButton(
                "SUPPORT TEAM",
                url=_sup_url,
                style="danger",
                icon_custom_emoji_id="5202216593966244027"
            ))
        else:
            markup.add(types.InlineKeyboardButton(
                "SUPPORT TEAM",
                url="https://t.me/Tom_9805",
                style="danger",
                icon_custom_emoji_id="5202216593966244027"
            ))
        bot.send_message(
            message.chat.id,
            "<tg-emoji emoji-id=\"5202216593966244027\">⚠️</tg-emoji> <b>SUPPORT TEAM</b> <tg-emoji emoji-id=\"5271604874419647061\">⚠️</tg-emoji>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "<tg-emoji emoji-id=\"5391112412445288650\">❓</tg-emoji> Need help? Contact our support team\n"
            "<tg-emoji emoji-id=\"5443038326535759644\">👇</tg-emoji> Click the button below\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=markup,
            parse_mode="HTML",
        )

    elif txt == "📊 𝗦𝗧𝗢𝗖𝗞":
        report = "🔥 <b>LIVE STOCK REPORT</b> 🔥\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        for s, d in stock.items():
            total = sum(len(v) for v in d.values())
            report += f" <b>{s.upper()}</b>: {total}  \n"
        report += "\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n🤖 <b>AR OTP BOT</b> 🔥"
        bot.send_message(message.chat.id, report, parse_mode="HTML")

    elif txt in ("⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 ⚙️", "𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟") and uid in ADMIN_IDS:
        _go_admin_panel(message)

    elif txt == "𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀" and uid in ADMIN_IDS:
        _payment_admin_msg_handler(message)

    elif txt in ("💵 Set Reward", "💱 Set Currency",
                 "📉 Set Minimum Withdraw", "📋 View All Balances",
                 "🔗 Set Refer Commission",
                 "➕ Add Balance Manually", "➖ Deduct Balance Manually") and uid in ADMIN_IDS:
        _payment_admin_msg_handler(message)

    elif txt.startswith("⏳ Pending Withdraw") and uid in ADMIN_IDS:
        _payment_admin_msg_handler(message)

    elif txt == "𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "✍️ <b>Send broadcast content:</b>\n\n"
            "📝 Text, 🖼️ Photo, 🎥 Video, 🎭 Sticker,\n"
            "🎞️ GIF, 🎵 Audio, 🎤 Voice, 📎 Document — all accepted!\n\n"
            "✨ <b>If you want to use a Custom Emoji:</b>\n"
            "Text-er jetukute emoji boshaite chao, sekhane emoji ID lekho:\n"
            "<code>5976350888195791241 Guinea 5319160079465857105 Instagram Method 5325684684544289988</code>\n"
            "<i>Wherever you place the ID, the custom emoji will render there</i>\n\n"
            "🔙 Press the <b>Admin Panel</b> button to go back.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, do_broadcast)

    elif txt == "𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            f" <b>TOTAL USERS</b> \n\n⚡ <b>{len(users)}</b> users! 🔥",
            parse_mode="HTML",
        )

    elif txt == "𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁" and uid in ADMIN_IDS:
        all_ids = list(users)
        total = len(all_ids)
        if total == 0:
            bot.send_message(message.chat.id, "📋 No users yet.", parse_mode="HTML")
        else:
            bot.send_message(
                message.chat.id, "⏳ Loading user names...", parse_mode="HTML"
            )
            updated = False
            for user_id in all_ids:
                key = str(user_id)
                existing = user_names.get(key, "")
                if existing and not existing.strip().lstrip("-").isdigit():
                    continue
                try:
                    chat_info = bot.get_chat(user_id)
                    full = f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
                    uname = chat_info.username or ""
                    if full and uname:
                        display = f"{full} (@{uname})"
                    elif full:
                        display = full
                    elif uname:
                        display = f"@{uname}"
                    else:
                        display = None
                    if display:
                        user_names[key] = display
                        updated = True
                except Exception:
                    pass
            if updated:
                save_json(USER_NAMES_FILE, user_names)

            PAGE = 50
            chunks = [all_ids[i : i + PAGE] for i in range(0, total, PAGE)]
            for idx, chunk in enumerate(chunks):
                lines = (
                    f"📋👥 <b>USER LIST</b> 👥📋\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
                    f"📊 Total: <b>{total}</b> users"
                    + (f"  |  Page {idx + 1}/{len(chunks)}" if len(chunks) > 1 else "")
                    + "\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                )
                for i, user_id in enumerate(chunk, start=idx * PAGE + 1):
                    name = user_names.get(str(user_id), "—")
                    lines += f"{i}. 🆔 <code>{user_id}</code>\n    👤 {name}\n\n"
                bot.send_message(message.chat.id, lines, parse_mode="HTML")

    elif txt == "𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀" and uid in ADMIN_IDS:
        with otp_stats_lock:
            stats_copy = dict(otp_stats)
        if not stats_copy:
            bot.send_message(
                message.chat.id,
                "📈 <b>OTP STATS</b>\n\n"
                "⚠️ No OTP delivered yet.",
                parse_mode="HTML",
            )
        else:
            sorted_stats = sorted(stats_copy.items(), key=lambda x: x[1], reverse=True)
            total_otps = sum(stats_copy.values())
            PAGE = 30
            chunks = [sorted_stats[i:i+PAGE] for i in range(0, len(sorted_stats), PAGE)]
            for idx, chunk in enumerate(chunks):
                lines = (
                    f"📈 <b>OTP STATS</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
                    f"📊 Total OTPs Delivered: <b>{total_otps}</b>"
                    + (f"  |  Page {idx+1}/{len(chunks)}" if len(chunks) > 1 else "")
                    + f"\n👥 Total Users: <b>{len(sorted_stats)}</b> more\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                )
                for rank, (user_id, count) in enumerate(chunk, start=idx*PAGE+1):
                    name = user_names.get(str(user_id), "")
                    if not name or str(name).strip().lstrip("-").isdigit():
                        try:
                            chat_info = bot.get_chat(int(user_id))
                            full = f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
                            uname = chat_info.username or ""
                            name = f"{full} (@{uname})" if full and uname else (full or f"@{uname}" if uname else str(user_id))
                            user_names[str(user_id)] = name
                        except Exception:
                            name = str(user_id)
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                    lines += f"{medal} <code>{user_id}</code> — <b>{count}</b>  OTP(s)\n    👤 {name}\n\n"
                bot.send_message(message.chat.id, lines, parse_mode="HTML")

    elif txt == "🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰" and uid in ADMIN_IDS:
        print(f"[LIVE-TRAFFIC] Triggered by uid={uid} chat={message.chat.id}")
        # Fetch traffic (no blocking send before this)
        try:
            traffic_text = _live_traffic_text()
        except Exception as _lt_err:
            traffic_text = f"❌ Live Traffic Error:\n<code>{_lt_err}</code>"
            print(f"[LIVE-TRAFFIC] _live_traffic_text error: {_lt_err}")
        print(f"[LIVE-TRAFFIC] text ready, len={len(traffic_text)}")
        # Send with retry to survive 429 bursts
        result, rl_secs = _send_with_retry(
            bot.send_message,
            max_retries=5,
            chat_id=message.chat.id,
            text=traffic_text,
            parse_mode="HTML",
        )
        if result is None:
            print(f"[LIVE-TRAFFIC] All retries failed, rate_limit={rl_secs}s")
            # Last-ditch: send plain text without HTML
            try:
                plain = traffic_text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                bot.send_message(message.chat.id, plain)
            except Exception as _plain_err:
                print(f"[LIVE-TRAFFIC] plain send also failed: {_plain_err}")
        else:
            print(f"[LIVE-TRAFFIC] Sent OK")

    elif txt == "𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "🔥 <b>Choose a service:</b> 🔥",
            reply_markup=_admin_add_svc_keyboard(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, process_auto_add)

    elif txt == "📥 𝗖𝗦𝗩 𝗔𝗱𝗱" and uid in ADMIN_IDS:
        svc_list = "\n".join(f"  • <code>{s['key']}</code>" for s in _services) or \
                   "  • <code>facebook</code>\n  • <code>instagram</code>\n  • <code>whatsapp</code>"
        bot.send_message(
            message.chat.id,
            "📥🔥 <b>ADD NUMBER via CSV / EXCEL</b> 🔥📥\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "📎 <b>Supported formats:</b>\n"
            "  • <b>.csv</b>  — CSV file\n"
            "  • <b>.xlsx</b> — Excel (new)\n"
            "  • <b>.xls</b>  — Excel (old)\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "📋 <b>Format 1 — 2 Column (Service + Number):</b>\n"
            "<code>facebook,8801700123456\n"
            "instagram,8801800234567\n"
            "whatsapp,251912345678</code>\n\n"
            "📋 <b>Format 2 — 1 Column (Number only):</b>\n"
            "<code>8801700123456\n"
            "8801800234567\n"
            "251912345678</code>\n"
            "<i>(You'll choose the service afterward)</i>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "✅ <b>Available services:</b>\n"
            f"{svc_list}\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "⬆️ <b>Ekhon CSV/Excel file pathao!</b>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )

    elif txt == "𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "🗑️🔥 <b>STOCK CLEAR PANEL</b> 🔥🗑️\n\n"
            " <b>Kon service-er stock clear korbe?</b>\n"
            "⬇️ Choose a service:",
            reply_markup=_clr_service_markup(),
            parse_mode="HTML",
        )

    elif txt == "𝗗𝗘𝗠𝗢 𝗢𝗧𝗣" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            demo_status_text(),
            reply_markup=demo_menu_markup(),
            parse_mode="HTML",
        )
        with _demo_lock:
            has_configs = len(_demo_configs) > 0
        if has_configs:
            bot.send_message(
                message.chat.id,
                "⚡ <b>Config Start/Stop:</b>",
                reply_markup=demo_cfg_inline_markup(),
                parse_mode="HTML",
            )

    elif txt == "𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹" and uid in ADMIN_IDS:
        _show_addpanel_type_select(message.chat.id, uid)

    elif txt == "𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲" and uid in ADMIN_IDS:
        _addservice_state[uid] = {}
        msg = bot.send_message(
            message.chat.id,
            "📋🔥 <b>ADD NEW SERVICE</b> 🔥📋\n\n"
            "🏷️ <b>Step 1/2:</b> Button-e ki lekha thakbe?\n"
            "<i>Example: Telegram 🔵, Binance 💛, TikTok 🎵</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _svc_get_label)

    elif txt == "𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲" and uid in ADMIN_IDS:
        if not _services:
            bot.send_message(message.chat.id, "📋 Kono service nai!", parse_mode="HTML")
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for s in _services:
                markup.add(types.InlineKeyboardButton(
                    f"🗑️ {s['label']}  [{s['key']}]",
                    callback_data=f"rmsvc:{s['key']}", style="danger"
                ))
            bot.send_message(
                message.chat.id,
                "🗑️🔥 <b>REMOVE SERVICE</b>\n\nKon service remove korbe?",
                reply_markup=markup,
                parse_mode="HTML",
            )

    elif txt == "𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹" and uid in ADMIN_IDS:
        if not _dynamic_panels:
            bot.send_message(
                message.chat.id,
                "📋 <b>No dynamic panel!</b>\n💡 Add one using the Add Panel button.",
                parse_mode="HTML",
            )
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for p in _dynamic_panels:
                pid = p["id"]
                with _stats_lock:
                    s = _panel_stats.get(pid, {})
                st = s.get("status", "⏳")
                markup.add(
                    types.InlineKeyboardButton(
                        f"{st} {p.get('username','?')} — {p.get('host','?')}",
                        callback_data=f"rmpanel:{pid}", style="success"
                    )
                )
            bot.send_message(
                message.chat.id,
                "🗑️🔥 <b>REMOVE PANEL</b>\n\nKon panel remove korbe?",
                reply_markup=markup,
                parse_mode="HTML",
            )


    elif txt == "➕ 𝗖𝗼𝗻𝗳𝗶𝗴 𝗬𝗼𝗴 𝗞𝗼𝗿𝗼" and uid in ADMIN_IDS:
        _demo_cfg_temp[uid] = {}
        msg = bot.send_message(
            message.chat.id,
            "📱 <b>Enter phone number(s):</b>\n\n"
            "• One number: <code>8801700123456</code>\n"
            "• Multiple (newline or comma):\n"
            "<code>8801700123456\n251912345678\n2348012345678</code>\n\n"
            "⚠️ Full country code including number lagbe!",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_number)

    elif txt == "🗑️ 𝗖𝗼𝗻𝗳𝗶𝗴 𝗠𝘂𝗰𝗵𝗼" and uid in ADMIN_IDS:
        with _demo_lock:
            configs = list(_demo_configs)
        if not configs:
            bot.send_message(
                message.chat.id,
                "📋 <b>Kono config nai!</b>",
                reply_markup=demo_menu_markup(),
                parse_mode="HTML",
            )
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for cfg in configs:
                svcs = ", ".join(cfg.get("services") or ["?"])
                markup.add(types.InlineKeyboardButton(
                    f"🗑️ {cfg['name']}  [{svcs}  |  {cfg['interval']}s]",
                    callback_data=f"rmcfg:{cfg['id']}", style="primary"
                ))
            bot.send_message(
                message.chat.id,
        "🗑️🔥 <b>Delete Config</b>\n\nWhich config do you want to delete?",
                reply_markup=markup,
                parse_mode="HTML",
            )

    elif txt == "𝗣𝗮𝗻𝗲𝗹𝘀" and uid in ADMIN_IDS:
        panels_cmd(message)

    elif txt == "𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽𝗲 𝗦𝗲𝗻𝗱" and uid in ADMIN_IDS:
        _resend_old_otps(message)

    elif txt == "𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗕𝗼𝗻𝗱𝗵𝗼" and uid in ADMIN_IDS:
        global _resend_stop, _resend_running
        _resend_stop = True
        if _resend_running:
            bot.send_message(message.chat.id,
                "🛑 <b>Resend stop signal sent!</b>\n"
                "<i>It will stop once the current OTP send finishes.</i>",
                parse_mode="HTML")
        else:
            bot.send_message(message.chat.id,
                "ℹ️ <b>Kono resend cholthechhilo na.</b>",
                parse_mode="HTML")

    elif txt == "𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹" and uid in ADMIN_IDS:
        _testpanel_state[uid] = {"step": "url", "data": {}}
        msg = bot.send_message(
            message.chat.id,
            "🔍🔥 <b>TEST PANEL</b> 🔥🔍\n\n"
            "Panel-er jekono URL pathao — test korbo, <b>save korbo na</b>.\n\n"
            "✅ <b>Jekono format:</b>\n"
            "• <code>http://1.2.3.4/konekta/agent/SMSCDRReports</code>\n"
            "• <code>http://1.2.3.4/ints</code>\n"
            "• <code>https://truesms.net</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _tp_get_url)

    elif txt == "👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻" and uid in ADMIN_IDS:
        if not is_super_admin(uid):
            bot.send_message(message.chat.id, "❌ <b>Only Super Admin can add a new admin!</b>", parse_mode="HTML")
            return
        msg = bot.send_message(
            message.chat.id,
            "👑 <b>New Admin add</b>\n\n"
            "Enter the new admin's Telegram <b>User ID</b>:\n"
            "<i>Example: 123456789</i>\n\n"
            "💡 To find the User ID, forward a message from that user to @userinfobot.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _admin_add_get_id)

    elif txt == "𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻" and uid in ADMIN_IDS:
        if not is_super_admin(uid):
            bot.send_message(message.chat.id, "❌ <b>Only Super Admin can remove an admin!</b>", parse_mode="HTML")
            return
        _show_remove_admin(message)

    elif txt == "𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗" and uid in ADMIN_IDS:
        if not is_super_admin(uid):
            bot.send_message(message.chat.id, "❌ <b>Only Super Admin can set the Support ID!</b>", parse_mode="HTML")
            return
        cur = _group_settings.get("support_id", "") or "❌ Set hoy nai"
        msg = bot.send_message(
            message.chat.id,
            f"📞 <b>Support ID Set/Change</b>\n\n"
            f"🔹 <b>Bortoman Support ID:</b> {cur}\n\n"
            f"Enter new Support Telegram ID\n"
            f"<i>(User ID, username, or t.me link — any one)</i>\n\n"
            f"Example: <code>@support_user</code> ba <code>123456789</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_support_id)

    elif txt == "𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀" and uid in ADMIN_IDS:
        _show_settings(message)

    elif txt == "𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀" and uid in ADMIN_IDS:
        _show_edit_messages_menu(message)

    elif txt == "𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "🎛️ <b>Live Console Config</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "Select service — toggle or add/delete range:\n"
            "✅ = enabled  ⭕ = disabled",
            reply_markup=_cc_services_markup(),
            parse_mode="HTML",
        )

    elif txt == "𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁" and uid in ADMIN_IDS:
        active = _get_v2_active_panel_id()
        pname = _v2_active_panel_name()
        bot.send_message(
            message.chat.id,
            f"🔀 <b>V2 Panel Select</b>\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"✅ <b>Currently Active:</b> {pname}\n\n"
        f"Use the buttons below to enable/disable panel.\n"
        f"The panel with ✅ is active — V2 numbers and OTP will come from there.\n\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=_v2_panel_toggle_markup(),
            parse_mode="HTML",
        )

    elif txt == "📡 𝗩𝟮 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗙𝗼𝗿𝗺𝗮𝘁" and uid in ADMIN_IDS:
        import html as _html
        current = get_template("otp_dm_v2")
        current_esc = _html.escape(current[:600])
        vars_hint = _TEMPLATE_VARS.get("otp_dm_v2", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("✏️ Edit V2 DM Format", callback_data="editmsg:otp_dm_v2", style="danger"))
        markup.add(types.InlineKeyboardButton("🔄 Reset to Default", callback_data="editmsg_reset:otp_dm_v2", style="success"))
        bot.send_message(
            message.chat.id,
            "📡 <b>V2 Message Format</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "📌 <b>Available variables:</b>\n"
            f"<code>{vars_hint}</code>\n\n"
        "📄 <b>Current V2 DM Format:</b>\n"
            f"<code>{current_esc}</code>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "<i>ℹ️ In V2 mode, Get New Number and Change Country buttons are not shown.</i>",
            reply_markup=markup,
            parse_mode="HTML",
        )

    elif txt in ("👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼", "𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼"):
        bot.send_message(
            message.chat.id,
            "<b><tg-emoji emoji-id=\"5202216593966244027\">👨‍💻</tg-emoji> 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼</b>\n\n"
            "<b><tg-emoji emoji-id=\"5325547803936572038\">✨</tg-emoji> Name: 𝗔𝘁𝗶𝗸</b>\n"
            "<b><tg-emoji emoji-id=\"5447644880824181073\">⚡</tg-emoji> Role: Bot Developer</b>\n"
            "<b><tg-emoji emoji-id=\"5341363621572128687\">🤖</tg-emoji> Project: Custom Otp Bot</b>\n"
            "<b><tg-emoji emoji-id=\"5391112412445288650\">📲</tg-emoji> Contact: @Tom_9805</b>\n"
            "<b><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji></b>\n"
            "<b><tg-emoji emoji-id=\"5447644880824181073\">⚡</tg-emoji> Developed &amp; Managed by Atik</b>\n"
            "<b><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji></b>",
            parse_mode="HTML",
        )

    elif txt == "𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀" and uid in ADMIN_IDS:
        _show_extra_groups(message)

    elif txt == "🌐 𝗔𝘂𝗴𝗲𝘀𝘁𝗲𝗹 𝗞𝗲𝘆" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "🌐🔑 <b>Augestel API Key Change</b>\n\n"
            "নতুন Augestel API key পাঠান। Save হওয়ার পর bot পুরোনো history "
            "আবার sync করে configured group-গুলোতে পাঠাবে।",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: _chgkey_receive(m, "augestel"))

    elif txt == "𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲" and uid in ADMIN_IDS:
        current_fastx  = _group_settings.get("fastx_api_key", FASTX_API_KEY)
        current_stex   = _group_settings.get("stex_api_key",  STEX_API_KEY)
        current_voltex = _group_settings.get("voltex_api_key", V3_API_KEY)
        current_mk     = _group_settings.get("mk_api_key", MK_API_KEY)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "🌐 Augestel SMS  |  🔐 configured",
                callback_data="chgkey:augestel",
            ),
            types.InlineKeyboardButton(
                f"⚡ FastX SMS  |  🔑 {current_fastx[:12]}...",
                callback_data="chgkey:fastx",
            ),
            types.InlineKeyboardButton(
                f"🌐 STEX SMS  |  🔑 {current_stex[:12]}...",
                callback_data="chgkey:stex",
            ),
            types.InlineKeyboardButton(
                f"🔮 Voltex SMS  |  🔑 {current_voltex[:12]}...",
                callback_data="chgkey:voltex",
            ),
            types.InlineKeyboardButton(
                f"🟢 MK Panel  |  🔑 {current_mk[:12]}...",
                callback_data="chgkey:mk",
            ),
        )
        bot.send_message(
            message.chat.id,
            "🔑🔥 <b>PANEL API KEY CHANGE</b> 🔥🔑\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "Which panel's API key do you want to change?\n"
            "Select a panel from below:",
            reply_markup=markup,
            parse_mode="HTML",
        )

    elif txt == "𝗖𝘂𝘀𝘁𝗼𝗺 𝗘𝗺𝗼𝗷𝗶" and uid in ADMIN_IDS:
        _show_custom_emoji_menu(message)

    elif txt == "🏳️ Flag Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "flag"
        bot.send_message(
            message.chat.id,
            "🏳️ <b>Flag Emoji Set</b>\n\n"
        "Send flag emoji and its custom emoji ID:\n\n"
        "<b>Single:</b> <code>🇧🇩 5432198765432198765</code>\n\n"
        "<b>Bulk (numbered list):</b>\n"
            "<code>1. 🇧🇩 5432198765432198765\n2. 🇺🇸 5976694588658686266</code>\n\n"
            "<i>Or use 🌍 All Flags JSON Set to add all flags at once.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🌍 All Flags JSON Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "flag_bulk_json"
        with _custom_emoji_lock:
            cur = dict(_custom_emojis.get("flags", {}))
        cur_preview = json.dumps(cur, ensure_ascii=False, indent=2) if cur else "{}"
        bot.send_message(
            message.chat.id,
            "🌍 <b>All Flags JSON Set</b>\n\n"
        "Send a JSON with <b>all</b> flag emojis and their custom IDs.\n\n"
        "<b>Format:</b>\n"
            "<code>{\n"
            '  "🇧🇩": "5432198765432198765",\n'
            '  "🇺🇸": "5976694588658686266",\n'
            '  "🇮🇳": "5195261305332736014"\n'
            "}</code>\n\n"
        "📌 <b>Current flags (JSON):</b>\n"
            f"<pre>{cur_preview}</pre>\n\n"
        "<i>New JSON will be merged with existing (not overwritten).\n"
        "To reset, use 🗑️ Flag Emoji Del first to clear all.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "📋 Flag JSON Export" and uid in ADMIN_IDS:
        with _custom_emoji_lock:
            cur = dict(_custom_emojis.get("flags", {}))
        if not cur:
            bot.send_message(message.chat.id,
                "📋 No flag emoji set yet.\n\n"
                "🌍 Use All Flags JSON Set to add.")
        else:
            exported = json.dumps(cur, ensure_ascii=False, indent=2)
            bot.send_message(
                message.chat.id,
                f"📋 <b>Current Flag Emojis JSON</b>\n\n"
                f"<pre>{exported}</pre>\n\n"
                f"<i>Total {len(cur)} flags set.\n"
                f"Copy, edit, and paste in 🌍 All Flags JSON Set.</i>",
                parse_mode="HTML"
            )
        _show_custom_emoji_menu(message)

    elif txt == "🔢 IDs Only Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "flag_ids_only"
        bot.send_message(
            message.chat.id,
            "🔢 <b>Flag IDs Only Set</b>\n\n"
            "Paste only the custom emoji IDs (one per line).\n"
            "The bot will automatically detect which country each flag belongs to.\n\n"
        "<b>Format:</b>\n"
            "<code>5432198765432198765\n"
            "5976694588658686266\n"
            "5195261305332736014</code>\n\n"
            "<i>You can send up to 200 IDs at once.</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🎯 Service Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "service"
        bot.send_message(
            message.chat.id,
            "🎯 <b>Service Emoji Set</b>\n\n"
            "Send the service name and custom emoji ID:\n\n"
            "<b>Format:</b> <code>INSTAGRAM 5319160079465857105</code>\n\n"
            "<i>Service name must be in ALL CAPS.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Flag Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_flag"
        with _custom_emoji_lock:
            flags_set = dict(_custom_emojis.get("flags", {}))
        if flags_set:
            lines = "\n".join(f"<code>{k}</code>" for k in flags_set)
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Flag Emoji</b>\n\nWhich flag emoji to delete?\n\n{lines}\n\n"
                "Send the flag emoji (emoji only, e.g. <code>🇧🇩</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No flag emoji is set.")

    elif txt == "🗑️ Service Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_service"
        with _custom_emoji_lock:
            svcs_set = dict(_custom_emojis.get("services", {}))
        if svcs_set:
            lines = "\n".join(f"<code>{k}</code>" for k in svcs_set)
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Service Emoji</b>\n\nWhich service to delete?\n\n{lines}\n\n"
                "Send the service name (e.g. <code>INSTAGRAM</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No service emoji is set.")

    elif txt == "🔘 Button Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "btn"
        available = "\n".join(f"  <code>{k}</code> — {v}" for k, v in _BTN_DISPLAY_NAMES.items())
        bot.send_message(
            message.chat.id,
            f"🔘 <b>Button Emoji Set</b>\n\n"
        f"Send button key and custom emoji ID:\n\n"
        f"<b>Format:</b> <code>button_key emoji_id</code>\n\n"
            f"<b>Available buttons:</b>\n{available}\n\n"
        f"<b>Example:</b>\n<code>change_number 5375170473095077321</code>\n\n"
            f"<i>Once custom emoji is set, the plain emoji will automatically be removed from button text.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Button Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_btn"
        with _custom_emoji_lock:
            btns_set = dict(_custom_emojis.get("buttons", {}))
        if btns_set:
            lines = "\n".join(f"<code>{k}</code> → <code>{v}</code>" for k, v in btns_set.items())
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Button Emoji</b>\n\nWhich button to delete?\n\n{lines}\n\n"
                "Send the button key (e.g. <code>change_number</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No button emoji is set.")

    elif txt == "🖥️ Admin Btn Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "admin_btn"
        with _custom_emoji_lock:
            overrides = dict(_custom_emojis.get("admin_btns", {}))
        lines = []
        for k, display in _ADMIN_BTN_DISPLAY_NAMES.items():
            cur_id = overrides.get(k) or _ADMIN_BTN_DEFAULT_ICONS.get(k, "")
            marker = "✏️" if k in overrides else "🔹"
            lines.append(f"  {marker} <code>{k}</code> — {display}\n     ID: <code>{cur_id}</code>")
        available = "\n".join(lines)
        bot.send_message(
            message.chat.id,
            f"🖥️ <b>Admin Panel Button Emoji Set</b>\n\n"
            f"Send button key and new custom emoji ID:\n\n"
            f"<b>Format:</b> <code>key emoji_id</code>\n\n"
            f"<b>Bulk (multiple lines):</b>\n"
            f"<code>num_add 5420323438508155202\nsob_clear 5422557736330106570</code>\n\n"
            f"<b>Buttons (✏️ = overridden, 🔹 = default):</b>\n{available}\n\n"
            f"<i>After saving, admin panel will instantly show new icons.</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Admin Btn Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_admin_btn"
        with _custom_emoji_lock:
            overrides = dict(_custom_emojis.get("admin_btns", {}))
        if overrides:
            lines = "\n".join(f"  <code>{k}</code> → <code>{v}</code>" for k, v in overrides.items())
            bot.send_message(
                message.chat.id,
                f"🗑️ <b>Delete Admin Button Emoji Override</b>\n\n"
                f"Current overrides:\n{lines}\n\n"
                f"Send the key to reset to default\n"
                f"(or send <code>ALL</code> to reset all):",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id,
                "ℹ️ No admin button overrides set. All buttons use default icons.")
            _show_custom_emoji_menu(message)

    elif txt == "💬 Msg Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "msg_slot"
        with _custom_emoji_lock:
            slots_set = dict(_custom_emojis.get("msg_slots", {}))
        slot_list = "\n".join(f"  <code>{{emoji_{k}}}</code> → {v.get('fb','')}" for k, v in slots_set.items()) or "  (none)"
        bot.send_message(
            message.chat.id,
            f"💬 <b>Message Emoji Set</b>\n\n"
            f"Current slots:\n{slot_list}\n\n"
            f"To add a new slot, send:\n\n"
            f"<b>Format:</b> <code>slot_name emoji_id fallback_emoji</code>\n\n"
        f"<b>Example:</b>\n<code>fire 5432198765432198765 🔥</code>\n\n"
        f"Then use <code>{{emoji_fire}}</code> in any message template to show the custom emoji.",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Msg Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_msg_slot"
        with _custom_emoji_lock:
            slots_set = dict(_custom_emojis.get("msg_slots", {}))
        if slots_set:
            lines = "\n".join(f"<code>{k}</code> → {v.get('fb','')}" for k, v in slots_set.items())
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Message Emoji</b>\n\nWhich slot to delete?\n\n{lines}\n\n"
                "Send the slot name (e.g. <code>fire</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No message emoji slot is set.")

    elif txt in ("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", "🔙 Admin Panel") and uid in ADMIN_IDS:
        _go_admin_panel(message)

    elif txt in ("💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲", "𝗕𝗮𝗹𝗮𝗻𝗰𝗲"):
        _show_balance(message)

    elif txt in ("💸 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄", "𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄"):
        _start_withdraw(message)

    elif txt in ("🔗 𝗥𝗲𝗳𝗳𝗲𝗿", "𝗥𝗲𝗳𝗳𝗲𝗿"):
        _show_refer(message)

    elif txt == "𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂":
        mname = message.from_user.first_name or message.from_user.username or "User"
        bot.send_message(
            message.chat.id,
            f"╔═════════════════════╗\n"
            f"      USER MENU-te WELCOME!\n"
            f"   👋 <b>{mname}</b>, what would you like to do?\n"
            f"╚═════════════════════╝",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )



    elif txt == "Buy Service":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Telegram Premium", callback_data="buy_tg_premium", style="primary", icon_custom_emoji_id="5251390031020455583"),
            types.InlineKeyboardButton("Buy VPN", callback_data="buy_vpn_menu", style="success", icon_custom_emoji_id="5269759232483303288"),
        )
        bot.send_message(
            message.chat.id,
            '<tg-emoji emoji-id="5375338737028841420">🛒</tg-emoji> <b>BUY SERVICE</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Select any service from below: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
            reply_markup=markup,
            parse_mode="HTML",
        )

    # ── Buy Service Admin ───────────────────────────────────────────────────────
    elif txt == "𝗕𝘂𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲" and uid in ADMIN_IDS:
        _show_buy_service_admin(message)

    elif txt == "💎 Set Premium Price" and uid in ADMIN_IDS:
        prices = _buy_service_settings["premium_prices"]
        rate = _buy_service_settings.get("dollar_rate", 128)
        msg = bot.send_message(
            message.chat.id,
            f"💎 <b>Telegram Premium Price Set</b>\n\n"
            f"Current prices:\n"
            f"• 3 Month: <b>{prices.get('3M', 0)} BDT</b>\n"
            f"• 6 Month: <b>{prices.get('6M', 0)} BDT</b>\n"
            f"• 1 Year:  <b>{prices.get('1Y', 0)} BDT</b>\n"
            f"• Dollar Rate: <b>1$ = {rate} BDT</b>\n\n"
            "Enter 3 prices — for 3M 6M 1Y in BDT (space-separated):\n"
            "<i>Example: <code>650 1200 2000</code></i>\n\n"
            "To change the dollar rate, enter 4 values:\n"
            "<i>Example: <code>650 1200 2000 130</code></i>\n\n"
            "🔙 Back: Press the <b>Admin Panel</b> button.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_set_premium_step)

    elif txt == "💰 Set VPN Price" and uid in ADMIN_IDS:
        _show_vpn_price_list(message)

    elif txt == "➕ Add VPN Service" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "➕ <b>New VPN Service Add</b>\n\n"
            "Format (space-separated):\n"
            "<code>EMOJI_ID NAME DURATION PRICE_BDT</code>\n\n"
            "Example:\n"
            "<code>5334944492300573096 NORD 7D 300</code>\n\n"
            "🔙 Back: Press the <b>Admin Panel</b> button.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_add_vpn_step)

    elif txt == "🗑️ Remove VPN" and uid in ADMIN_IDS:
        _show_vpn_remove_list(message)

    elif txt == "📨 Send User Message" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "📨 <b>Send Message to User</b>\n\n"
            "Enter the target user's <b>Chat ID</b>:\n"
            "<i>(You can find the ID in the admin screenshot notification)</i>\n\n"
            "🔙 Back: Press the <b>Admin Panel</b> button.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_send_ask_uid_step)

# ── Demo OTP config step handlers ─────────────────────────────────────────────


def _demo_cfg_number(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw_lines = re.split(r"[\n,]+", message.text or "")
    candidates = [re.sub(r"\D", "", ln) for ln in raw_lines if re.sub(r"\D", "", ln)]
    if not candidates:
        msg = bot.send_message(
            message.chat.id,
            "❌ No number found. Enter one or multiple numbers:",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_number)
        return
    valid, invalid = [], []
    result_lines = ""
    for num in candidates:
        if len(num) < 7:
            invalid.append(num)
            continue
        c_name, flag = get_country_details(num)
        if c_name == "Unknown":
            invalid.append(num)
        else:
            valid.append(num)
            result_lines += f"  ✅ <code>{num}</code>  {_resolve_flag(flag)} {c_name}\n"
    if not valid:
        msg = bot.send_message(
            message.chat.id,
            f"⚠️ <b>Kono valid number paini!</b>\n\n"
            f"Enter full international number (including country code):\n"
            f"🇧🇩 Bangladesh → <code>8801700123456</code>\n"
            f"🇪🇹 Ethiopia   → <code>251912345678</code>\n"
            f"🇳🇬 Nigeria    → <code>2348012345678</code>\n\n"
            f"Try again:",
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_number)
        return
    uid = message.from_user.id
    _demo_cfg_temp.setdefault(uid, {})["numbers"] = valid
    SHOW_MAX = 10
    shown = result_lines.split("\n")[:SHOW_MAX]
    preview = "\n".join(shown)
    if len(valid) > SHOW_MAX:
        preview += f"\n  ... +{len(valid) - SHOW_MAX} more"
    feedback = f"✅ <b>{len(valid)} number(s) set:</b>\n{preview}\n"
    if invalid:
        inv_preview = invalid[:5]
        feedback += (
            f"\n⚠️ Skip (invalid): {', '.join(f'<code>{x}</code>' for x in inv_preview)}"
        )
        if len(invalid) > 5:
            feedback += f" +{len(invalid) - 5} more"
        feedback += "\n"
    svc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    svc_markup.add("4", "5", "6", "7", "8")
    svc_markup.add("🔙 Admin Panel")
    msg = bot.send_message(
        message.chat.id,
        feedback + "\n🔢 <b>Choose OTP digit count:</b>",
        reply_markup=svc_markup,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _demo_cfg_digits)


def _demo_cfg_digits(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    try:
        d = int(message.text.strip())
        if d < 4 or d > 8:
            raise ValueError
    except ValueError:
        svc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        svc_markup.add("4", "5", "6", "7", "8")
        svc_markup.add("🔙 Admin Panel")
        msg = bot.send_message(message.chat.id, "❌ Enter a number between 4 and 8:", reply_markup=svc_markup)
        bot.register_next_step_handler(msg, _demo_cfg_digits)
        return
    uid = message.from_user.id
    _demo_cfg_temp.setdefault(uid, {})["digits"] = d
    _demo_svc_state[uid] = []
    _demo_cfg_service_ask(message)


def _demo_cfg_service_ask(message):
    uid = message.from_user.id
    current = _demo_svc_state.get(uid, [])
    svc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    svc_markup.add("Facebook", "Instagram", "WhatsApp")
    svc_markup.add("Telegram", "PC Clone", "Twitter")
    svc_markup.add("Tiktok", "Snapchat", "Gmail")
    if current:
        svc_markup.add("✅ Done")
    svc_markup.add("🔙 Admin Panel")
    if current:
        svc_list = "\n".join(f"  ✅ {s}" for s in current)
        prompt = (
            f"✅ <b>Selected services ({len(current)}):</b>\n{svc_list}\n\n"
            f"➕ <b>Add more services</b> or press <b>✅ Done</b>:"
        )
    else:
        prompt = (
            "💬 <b>Choose a service</b>\n\n"
            "<i>You can add multiple services — press '✅ Done' when finished.</i>"
        )
    msg = bot.send_message(message.chat.id, prompt, reply_markup=svc_markup, parse_mode="HTML")
    bot.register_next_step_handler(msg, _demo_cfg_service_multi)


def _demo_cfg_service_multi(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    uid = message.from_user.id
    txt = (message.text or "").strip()

    if txt in ("✅ Done", "✅ Done"):
        svcs = _demo_svc_state.get(uid, [])
        if not svcs:
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Please select at least one service!</b>",
                parse_mode="HTML",
            )
            _demo_cfg_service_ask(message)
            return
        uid2 = message.from_user.id
        _demo_cfg_temp.setdefault(uid2, {})["services"] = svcs
        intvl_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        intvl_markup.add("5", "10", "15", "30", "60", "120", "300")
        intvl_markup.add("🔙 Admin Panel")
        svc_list = ", ".join(svcs)
        msg = bot.send_message(
            message.chat.id,
            f"✅ <b>Services set:</b> {svc_list}\n\n⏱️ <b>Enter interval (seconds):</b>",
            reply_markup=intvl_markup,
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_interval)
        return

    if not txt:
        _demo_cfg_service_ask(message)
        return

    current = _demo_svc_state.setdefault(uid, [])
    if txt in current:
        bot.send_message(
            message.chat.id,
            f"⚠️ <b>{txt}</b> is already added! Add more or press <b>✅ Done</b>.",
            parse_mode="HTML",
        )
    else:
        current.append(txt)
    _demo_cfg_service_ask(message)


def _demo_cfg_interval(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    try:
        iv = int(message.text.strip())
        if iv < 5:
            raise ValueError
    except ValueError:
        intvl_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        intvl_markup.add("5", "10", "15", "30", "60", "120", "300")
        intvl_markup.add("🔙 Admin Panel")
        msg = bot.send_message(message.chat.id, "❌ Minimum 5 seconds. Enter more:", reply_markup=intvl_markup)
        bot.register_next_step_handler(msg, _demo_cfg_interval)
        return
    global _demo_cfg_id_counter
    uid = message.from_user.id
    tmp = _demo_cfg_temp.pop(uid, {})
    numbers = tmp.get("numbers", ["8801700000000"])
    digits = tmp.get("digits", 6)
    services = tmp.get("services", ["Facebook"])
    with _demo_lock:
        _demo_cfg_id_counter += 1
        cid = _demo_cfg_id_counter
        cfg_name = f"Config {cid}"
        _demo_configs.clear()
        _demo_next_fire.clear()
        _demo_configs.append({
            "id": cid,
            "name": cfg_name,
            "active": True,
            "numbers": numbers,
            "digits": digits,
            "services": services,
            "interval": iv,
        })
    svcs_str = ", ".join(services)
    bot.send_message(
        message.chat.id,
        f"✅🔥 <b>{cfg_name} added!</b>\n\n"
        f"  📱 Numbers: {len(numbers)}\n"
        f"  🔢 Digits: {digits}\n"
        f"  💬 Services: {svcs_str}\n"
        f"  ⏱️ Interval: {iv}s\n\n"
        + demo_status_text(),
        reply_markup=demo_menu_markup(),
        parse_mode="HTML",
    )


def _inject_custom_emojis(text):
    """Replace every 17-20 digit numeric ID in text with a <tg-emoji> tag.
    Example: '5976350888195791241 Guinea' → '<tg-emoji ...>✨</tg-emoji> Guinea'
    """
    if not text:
        return text
    import re as _re
    return _re.sub(
        r'\b(\d{17,20})\b',
        lambda m: f'<tg-emoji emoji-id="{m.group(1)}">✨</tg-emoji>',
        text,
    )


def make_broadcast_msg(text):
    # Send exactly what admin typed — just inject custom emoji IDs, no header/footer wrapper
    return _inject_custom_emojis(text or "")


def do_broadcast(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    has_text = bool(message.text)
    has_photo = bool(message.photo)
    has_video = bool(message.video)
    has_sticker = bool(message.sticker)
    has_animation = bool(message.animation)
    has_audio = bool(message.audio)
    has_voice = bool(message.voice)
    has_document = bool(message.document)
    has_video_note = bool(message.video_note)

    if not any(
        [
            has_text,
            has_photo,
            has_video,
            has_sticker,
            has_animation,
            has_audio,
            has_voice,
            has_document,
            has_video_note,
        ]
    ):
        bot.send_message(
            message.chat.id,
            "⚠️ <b>No content found!</b> ⚠️\n"
            "Text, Photo, Video, GIF, Audio, Voice, Document ba Sticker pathao.",
            parse_mode="HTML",
        )
        return

    _raw_cap = message.caption or ""

    def cap(m):
        return make_broadcast_msg(_raw_cap)

    bot.send_message(
        message.chat.id,
        f"⏳🔥 <b>Sending to {len(users)} users...</b> 🔥⏳",
        parse_mode="HTML",
    )

    def _bc_send_one(chat_id):
        try:
            if has_photo:
                bot.send_photo(chat_id, message.photo[-1].file_id, caption=cap(message), parse_mode="HTML")
            elif has_animation:
                bot.send_animation(chat_id, message.animation.file_id, caption=cap(message), parse_mode="HTML")
            elif has_video:
                bot.send_video(chat_id, message.video.file_id, caption=cap(message), parse_mode="HTML")
            elif has_video_note:
                bot.send_video_note(chat_id, message.video_note.file_id)
            elif has_sticker:
                bot.send_sticker(chat_id, message.sticker.file_id)
            elif has_audio:
                bot.send_audio(chat_id, message.audio.file_id, caption=cap(message), parse_mode="HTML")
            elif has_voice:
                bot.send_voice(chat_id, message.voice.file_id, caption=cap(message), parse_mode="HTML")
            elif has_document:
                bot.send_document(chat_id, message.document.file_id, caption=cap(message), parse_mode="HTML")
            else:
                bot.send_message(chat_id, make_broadcast_msg(message.text), parse_mode="HTML")
            return True
        except Exception:
            return False

    # Send to main group
    main_grp = get_otp_group_id()
    if main_grp:
        try:
            _bc_send_one(main_grp)
        except Exception:
            pass
    # Send to extra groups
    for eg in _group_settings.get("extra_groups", []):
        eg_id = eg.get("id")
        if eg_id:
            try:
                _bc_send_one(eg_id)
            except Exception:
                pass

    # Send to all registered users
    success, fail = 0, 0
    for uid in list(users):
        if _bc_send_one(uid):
            success += 1
        else:
            fail += 1
        time.sleep(0.03)

    bot.send_message(
        message.chat.id,
        f" <b>BROADCAST COMPLETE!</b> \n\n"
        f"✅ <b>𝗦𝗼𝗳𝗼𝗹:</b> {success} more 🔥\n"
        f"❌ <b>𝗕𝗮𝗿𝘁𝗵𝗼:</b> {fail} more ",
        parse_mode="HTML",
    )
    _go_admin_panel(message)


_pending_add = {}


def _start_countdown(chat_id, msg_id, svc, flag, c_name, display_nums, scnt):
    # Accept list or single string
    if isinstance(display_nums, list):
        _nums_list = display_nums
    else:
        _nums_list = [display_nums]

    if chat_id in _countdowns:
        _countdowns[chat_id].set()
    cancel = threading.Event()
    _countdowns[chat_id] = cancel

    def _make_kb():
        view = _user_number_views.get(chat_id, {})
        return _build_numbers_display_kb(
            svc, scnt, _nums_list, flag, c_name,
            cc_removed=view.get("cc_removed", False),
        )

    def run():
        TICK = 5            # update every 5s
        DURATION = 600      # 10 minutes
        deadline = time.time() + DURATION
        current_msg_id = [msg_id]  # list so inner scope can mutate

        def _parse_retry_after(err_str):
            try:
                return int(re.search(r"retry after (\d+)", err_str).group(1))
            except Exception:
                return 60

        def try_update(text):
            """Try edit, fall back to send+delete.
            Returns: True=ok, False=skip tick, None=stop, int=rate-limited (seconds to wait)."""
            # 1. try edit
            try:
                bot.edit_message_text(
                    text, chat_id, current_msg_id[0],
                    reply_markup=_make_kb(),
                )
                return True
            except Exception as e:
                err = str(e)
                if "message is not modified" in err:
                    return True
                if "message to edit not found" in err or "MESSAGE_ID_INVALID" in err:
                    return None
                if "429" in err or "Too Many Requests" in err:
                    return _parse_retry_after(err)  # int → caller will wait

            # 2. edit failed (non-429) — try send+delete
            try:
                sent = bot.send_message(
                    chat_id, text,
                    reply_markup=_make_kb(),
                )
                try:
                    bot.delete_message(chat_id, current_msg_id[0])
                except Exception:
                    pass
                current_msg_id[0] = sent.message_id
                _user_last_num_msg[chat_id] = sent.message_id
                return True
            except Exception as e2:
                err2 = str(e2)
                if "429" in err2 or "Too Many Requests" in err2:
                    return _parse_retry_after(err2)
                print(f"[COUNTDOWN] tick failed: {e2}")
                return False

        while not cancel.is_set():
            remaining = int(deadline - time.time())
            if remaining <= 0:
                deadline = time.time() + DURATION
                remaining = DURATION

            mins = remaining // 60
            secs = remaining % 60
            text = "."
            result = try_update(text)
            if result is None:
                break  # message gone, stop
            elif type(result) is int:
                # rate-limited — wait the full retry_after, then resume
                wait = min(result, 3600)
                print(f"[COUNTDOWN] Rate limited for {wait}s, pausing timer for {chat_id}")
                cancel.wait(wait)
            else:
                cancel.wait(TICK)

    threading.Thread(target=run, daemon=True).start()


def _settings_text(uid=None):
    """Per-admin settings. If uid given, show that admin's own settings."""
    grp_link = get_admin_setting(uid, "otp_group_link") if uid else _group_settings.get("otp_group_link", "")
    grp_id = get_admin_setting(uid, "otp_group_id") if uid else _group_settings.get("otp_group_id")
    ch2 = get_admin_setting(uid, "channel2") if uid else _group_settings.get("channel2", "")
    bot_lnk = get_admin_setting(uid, "bot_link") if uid else _group_settings.get("bot_link", "")
    auto_del = _group_settings.get("auto_delete", True)
    del_secs = _group_settings.get("auto_delete_seconds", 3600)
    grp_send = _group_settings.get("group_otp_send", True)
    grp_tag = _group_settings.get("group_tag", "BOT")
    n_batch = _group_settings.get("numbers_per_batch", 1)
    id_str = f"<code>{grp_id}</code>" if grp_id else "❌ Set hoy nai"
    link_str = grp_link or "❌ Set hoy nai"
    auto_str = f"🟢 ON ({del_secs // 60} min)" if auto_del else "🔴 OFF"
    grp_send_str = "🟢 ON (OTP goes to group)" if grp_send else "🔴 OFF (Inbox only)"
    ch2_str = ch2 or "❌ Set hoy nai"
    bot_str = bot_lnk or "❌ Set hoy nai"
    v3_on = _group_settings.get("v3_enabled", True)
    v3_str = "🟢 ON" if v3_on else "🔴 OFF"
    v2_mode = _group_settings.get("v2_user_mode", False)
    v2_mode_str = "🟢 ON (Shows Get Number button)" if v2_mode else "🔴 OFF (Shows V1+V2 Switch)"
    extra_grps = _group_settings.get("extra_groups", [])
    eg_str = f"{len(extra_grps)}extra group(s) added" if extra_grps else "❌ No extra group added"
    return (
        "⚙️ <b>BOT SETTINGS</b> ⚙️\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        "📡 <b>OTP GROUP</b>\n"
        f"🔗 Link: {link_str}\n"
        f"🆔 Chat ID: {id_str}\n"
        f"⏱️ Auto Delete: {auto_str}\n"
        f"📤 Group OTP Send: {grp_send_str}\n"
        f'👑 Number Tag: <b>{grp_tag}</b> (245<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{grp_tag}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>5660)\n'
        f"🔢 Numbers Per User: <b>{n_batch}</b>\n\n"
        "📢 <b>LINKS</b>\n"
        f"📢 Join Channel: {ch2_str}\n"
        f"🤖 Bot Link: {bot_str}\n\n"
        f"📡 Extra Groups: {eg_str}\n\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "⬇️ What do you want to change?"
    )


def _settings_markup():
    auto_del = _group_settings.get("auto_delete", True)
    grp_send = _group_settings.get("group_otp_send", True)
    grp_tag = _group_settings.get("group_tag", "BOT")
    n_batch = _group_settings.get("numbers_per_batch", 1)
    auto_label = "Auto Delete: 🟢 ON" if auto_del else "Auto Delete: 🔴 OFF"
    grp_send_label = "Group Send: 🟢 ON" if grp_send else "Group Send: 🔴 OFF"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Group Link", callback_data="grp_setlink", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("grp_link")),
        types.InlineKeyboardButton("Group Chat ID", callback_data="grp_setid", style="danger", icon_custom_emoji_id=_get_admin_btn_icon("grp_chat_id")),
    )
    markup.add(
        types.InlineKeyboardButton(auto_label, callback_data="set_autodel", style="success", icon_custom_emoji_id=_get_admin_btn_icon("auto_delete")),
        types.InlineKeyboardButton("Remove Group", callback_data="grp_remove", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("remove_group")),
    )
    markup.add(
        types.InlineKeyboardButton(grp_send_label, callback_data="toggle_grp_send", style="danger", icon_custom_emoji_id=_get_admin_btn_icon("grp_send")),
    )
    markup.add(
        types.InlineKeyboardButton(f"Number Tag: {grp_tag}", callback_data="set_group_tag", style="success", icon_custom_emoji_id=_get_admin_btn_icon("num_tag")),
    )
    markup.add(
        types.InlineKeyboardButton(f"Numbers Per User: {n_batch}", callback_data="set_num_batch", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("nums_per_user")),
    )
    markup.add(
        types.InlineKeyboardButton("Join Channel", callback_data="set_channel2", style="danger", icon_custom_emoji_id=_get_admin_btn_icon("join_channel")),
        types.InlineKeyboardButton("Bot Link", callback_data="set_botlink", style="success", icon_custom_emoji_id=_get_admin_btn_icon("bot_link")),
    )
    return markup


def _show_settings(message):
    bot.send_message(
        message.chat.id,
        _settings_text(message.from_user.id),
        reply_markup=_settings_markup(),
        parse_mode="HTML",
    )


def _show_settings_inline(call):
    try:
        bot.edit_message_text(
            _settings_text(call.from_user.id),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=_settings_markup(),
            parse_mode="HTML",
        )
    except Exception:
        pass


def _show_group_settings(message):
    _show_settings(message)


def _show_group_settings_inline(call):
    _show_settings_inline(call)


def _grp_get_link(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    link = (message.text or "").strip()
    if not link.startswith("https://t.me/") and not link.startswith("http://"):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Telegram link:\n<i>Example: https://t.me/aR_OTP_rcv</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _grp_get_link)
        return
    _admin_settings.setdefault(str(uid), {})["otp_group_link"] = link
    save_admin_settings()
    _group_settings["otp_group_link"] = link
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅🔥 <b>GROUP LINK UPDATED!</b>\n\n"
        f"🔗 <b>Notun Link:</b> {link}",
    )


def _grp_get_id(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw = (message.text or "").strip()
    try:
        gid = int(raw)
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Chat ID (number):\n<i>Example: -1001234567890</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _grp_get_id)
        return
    # Save per-admin; also update global if super admin
    _admin_settings.setdefault(str(uid), {})["otp_group_id"] = gid
    save_admin_settings()
    if is_super_admin(uid):
        _group_settings["otp_group_id"] = gid
        save_group_settings()
    _go_admin_panel(
        message,
        f"✅🔥 <b>GROUP CHAT ID UPDATED!</b>\n\n"
        f"🆔 <b>Notun Chat ID:</b> <code>{gid}</code>\n\n"
        f"<i>Only your settings have been updated.</i>",
    )


def _sett_get_channel2(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    link = (message.text or "").strip()
    if not link.startswith("https://") and not link.startswith("http://"):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid link:\n<i>Example: https://t.me/aR_OTP_rcv</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_channel2)
        return
    _admin_settings.setdefault(str(uid), {})["channel2"] = link
    save_admin_settings()
    _group_settings["channel2"] = link
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>JOIN CHANNEL UPDATED!</b>\n\n"
        f"📢 <b>Notun Link:</b> {link}",
    )


def _sett_get_botlink(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    link = (message.text or "").strip()
    if not link.startswith("https://") and not link.startswith("http://"):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid link:\n<i>Example: https://t.me/ar_otp_bot</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_botlink)
        return
    _admin_settings.setdefault(str(uid), {})["bot_link"] = link
    save_admin_settings()
    _group_settings["bot_link"] = link
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>BOT LINK UPDATED!</b>\n\n"
        f"🤖 <b>Notun Link:</b> {link}",
    )


def _sett_get_support_id(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    val = (message.text or "").strip()
    if not val:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Support ID:\n<i>Example: @support_user or 123456789</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_support_id)
        return
    _group_settings["support_id"] = val
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>SUPPORT ID UPDATED!</b>\n\n"
        f"📞 <b>Notun Support ID:</b> <code>{val}</code>",
    )


def _chgkey_receive(message, panel_id):
    """Receive new API key from admin and apply it to the selected V2 panel."""
    global FASTX_API_KEY, STEX_API_KEY, V3_API_KEY
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text) or _intercept_menu_btn(message):
        return
    new_key = (message.text or "").strip()
    if not new_key:
        msg = bot.send_message(
            message.chat.id,
            "❌ API key khali — abar pathao:",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: _chgkey_receive(m, panel_id))
        return

    _PANEL_LABELS = {
        "fastx": "⚡ FastX SMS",
        "stex": "🌐 STEX SMS",
        "voltex": "🔮 Voltex SMS",
        "mk": "🟢 MK Panel",
        "augestel": "🌐 Augestel SMS",
    }
    label = _PANEL_LABELS.get(panel_id, panel_id.upper())

    if panel_id == "augestel":
        _augestel_store_key_from_message(message, new_key)
        return

    if panel_id == "fastx":
        FASTX_API_KEY = new_key
        _group_settings["fastx_api_key"] = new_key
    elif panel_id == "stex":
        STEX_API_KEY = new_key
        _group_settings["stex_api_key"] = new_key
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "stex":
                p["api_key"] = new_key
    elif panel_id == "voltex":
        V3_API_KEY = new_key
        _group_settings["voltex_api_key"] = new_key
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "voltex":
                p["api_key"] = new_key
    elif panel_id == "mk":
        MK_API_KEY = new_key
        _group_settings["mk_api_key"] = new_key
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "mk":
                p["api_key"] = new_key

    save_group_settings()
    _go_admin_panel(
        message,
        f"✅🔑 <b>API KEY UPDATED!</b>\n\n"
        f"📡 <b>Panel:</b> {label}\n"
        f"🔑 <b>New Key:</b> <code>{new_key}</code>\n\n"
        f"✅ From now on, API calls will use the new key.",
    )


def _sett_get_group_tag(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    val = (message.text or "").strip().upper()
    if not val or len(val) > 20:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid tag (max 20 char):\n<i>Example: ATIK, BOT, KING</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_group_tag)
        return
    _group_settings["group_tag"] = val
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>NUMBER TAG UPDATED!</b>\n\n"
        f'👑 <b>New Tag:</b> <code>{val}</code>\n'
        f'📱 Preview: <b>245<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{val}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>5660</b>\n\n'
        f"<i>From now on, numbers will show in this format in the group!</i>",
    )


def _sett_get_num_batch(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    txt = (message.text or "").strip()
    try:
        val = int(txt)
        if val < 1 or val > 10:
            raise ValueError
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
        "❌ Enter a number between 1 and 10:\n<i>Example: 1, 2, 3, 5</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_num_batch)
        return
    _group_settings["numbers_per_batch"] = val
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>NUMBERS PER USER UPDATED!</b>\n\n"
        f"🔢 <b>New Setting:</b> <code>{val}</code>\n\n"
        f"<i>Each user will now get {val} number(s) at a time.</i>",
    )


_pending_admin_uid = {}  # {requester_uid: new_uid}


def _admin_add_get_id(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw = (message.text or "").strip()
    try:
        new_uid = int(raw)
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Telegram User ID (numbers only):\n<i>Example: 123456789</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _admin_add_get_id)
        return
    if new_uid in SUPER_ADMIN_IDS:
        _go_admin_panel(message, "⚠️ <b>This user is already a Super Admin!</b>")
        return
    _pending_admin_uid[uid] = new_uid
    dur_kb = types.InlineKeyboardMarkup(row_width=3)
    dur_kb.add(
        types.InlineKeyboardButton("1 Mash", callback_data=f"aadur:{new_uid}:1", style="success"),
        types.InlineKeyboardButton("2 Mash", callback_data=f"aadur:{new_uid}:2", style="primary"),
        types.InlineKeyboardButton("3 Mash", callback_data=f"aadur:{new_uid}:3", style="danger"),
    )
    dur_kb.add(
        types.InlineKeyboardButton("❌ Cancel", callback_data="aadur_cancel", style="success"),
    )
    raw_n = user_names.get(str(new_uid), "")
    name_str = raw_n if isinstance(raw_n, str) else raw_n.get("first_name", str(new_uid))
    name_str = name_str or str(new_uid)
    bot.send_message(
        message.chat.id,
        f"👑 <b>Select Admin Duration</b>\n\n"
        f"🔹 <b>User:</b> {name_str} [<code>{new_uid}</code>]\n\n"
        f"Koto mash admin thakbe?",
        reply_markup=dur_kb,
        parse_mode="HTML",
    )


def _show_remove_admin(message):
    removable = [a for a in ADMIN_IDS if a not in SUPER_ADMIN_IDS]
    if not removable:
        bot.send_message(
            message.chat.id,
            "ℹ️ <b>Remove korar moto kono extra admin nei.</b>\n\n"
            "<i>Super Admin remove kora jabe na.</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for aid in removable:
        raw = user_names.get(str(aid), "")
        if isinstance(raw, dict):
            name = raw.get("first_name", "") or str(aid)
        else:
            name = raw or str(aid)
        markup.add(types.InlineKeyboardButton(
            f"🗑️ {name} [{aid}]", callback_data=f"rmadmin:{aid}", style="primary"
        ))
    bot.send_message(
        message.chat.id,
        "🗑️ <b>Remove Admin</b>\n\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "Select an admin from below:\n\n"
        "<i>⚠️ Super Admin remove kora jabe na.</i>",
        reply_markup=markup,
        parse_mode="HTML",
    )


_admin_panel_last: dict[int, float] = {}
_admin_panel_lock = threading.Lock()

# ── Resend stop flag ───────────────────────────────────────────────────────────
_resend_running = False
_resend_stop    = False


def _resend_old_otps(message):
    """Fetch today's real OTPs from ALL panels and forward to group (max 50 total)."""
    global _resend_running, _resend_stop
    uid = message.from_user.id
    cid = message.chat.id
    grp = get_admin_setting(uid, "otp_group_id", None) or get_otp_group_id()

    if not grp:
        bot.send_message(cid,
            "❌ <b>Group is not set!</b>\nSet the OTP Group from Settings.",
            parse_mode="HTML")
        return

    if _resend_running:
        bot.send_message(cid,
            "⚠️ <b>Resend already cholche!</b>\n"
            "🛑 Use the <b>Old OTP Stop</b> button to stop first.",
            parse_mode="HTML")
        return

    wait_msg = bot.send_message(
        cid,
        "⏳ <b>Fetching today's OTPs from all panels...</b>\n"
        "<i>(Only real SMS OTPs — fake/range data will be excluded)</i>",
        parse_mode="HTML",
    )

    _resend_running = True
    _resend_stop    = False

    def _do_resend():
        global _resend_running, _resend_stop
        all_found = {}

        static_fetchers = [
            ("P1", fetch_panel1), ("P2", fetch_panel2),
            ("P3", fetch_panel3), ("P4", fetch_panel4),
            ("P5", fetch_panel5), ("P6", fetch_panel6),
        ]
        for pid, fetcher in static_fetchers:
            if _resend_stop:
                break
            try:
                result = fetcher()
                all_found.update(result)
                print(f"[RESEND] {pid}: {len(result)} real OTPs")
            except Exception as e:
                print(f"[RESEND] {pid} error: {e}")

        for panel in list(_dynamic_panels):
            if _resend_stop:
                break
            try:
                result = _universal_fetch(panel)
                all_found.update(result)
                print(f"[RESEND] {panel['id']}: {len(result)} real OTPs")
            except Exception as e:
                print(f"[RESEND] {panel['id']} error: {e}")

        try:
            bot.delete_message(cid, wait_msg.message_id)
        except Exception:
            pass

        if _resend_stop:
            bot.send_message(cid, "🛑 <b>Resend has been stopped!</b>", parse_mode="HTML")
            _resend_running = False
            return

        if not all_found:
            bot.send_message(
                cid,
                "⚠️ <b>Kono real OTP panel e nai!</b>\n"
                "<i>Fake/range data was excluded. Only real SMS OTPs were counted.</i>",
                parse_mode="HTML",
            )
            _resend_running = False
            return

        MAX_SEND = 50
        items  = list(all_found.values())[:MAX_SEND]
        total  = len(all_found)
        sent   = 0
        failed = 0

        bot.send_message(
            cid,
        f"📤 <b>{total} real OTP(s) found!</b>\n"
        f"<i>Max {MAX_SEND} will be sent.</i>",
            parse_mode="HTML",
        )

        for number, otp_val, sms_txt, service in items:
            if _resend_stop:
                break
            try:
                send_otp_message(grp, otp_val, number, "—", service, sms_txt or "")
                sent += 1
                time.sleep(0.4)
            except Exception as e:
                failed += 1
                print(f"[RESEND] Send error {number}: {e}")

        _resend_running = False
        status_icon = "🛑 Stopped!" if _resend_stop else "✅ Done!"
        bot.send_message(
            cid,
            f"{status_icon}\n\n"
            f"📊 <b>Total real OTPs:</b> {total}\n"
            f"?? <b>Sent:</b> {sent}\n"
            f"❌ <b>Failed:</b> {failed}",
            parse_mode="HTML",
        )

    threading.Thread(target=_do_resend, daemon=True).start()


_custom_emoji_state: dict = {}   # uid -> "flag" | "service" | "del_flag" | "del_service"

_MSG_ICON_GROUPS = [
    ("📲 DM Message Emoji", ["dm_number_pre", "dm_country_pre", "dm_country_post"]),
    ("🏳️ Flag Emoji", ["flag_default"]),
    ("📱 OTP Messages", ["otp_phone", "otp_key", "otp_world", "otp_sms"]),
    ("?? Start Screen", ["start_header", "start_crown", "start_user", "start_id", "start_status", "start_workers", "start_powered"]),
    ("✅ Verify Screen", ["verify_title"]),
]

def _show_msg_icons_menu(message, note=""):
    """Inline keyboard menu for setting/resetting predefined message icon slots."""
    with _custom_emoji_lock:
        slots_set = dict(_custom_emojis.get("msg_slots", {}))
    markup = types.InlineKeyboardMarkup(row_width=2)
    lines = []
    for group_label, group_keys in _MSG_ICON_GROUPS:
        lines.append(f"\n<b>{group_label}:</b>")
        for key in group_keys:
            if key not in _MSG_ICON_SLOTS:
                continue
            default_char, label = _MSG_ICON_SLOTS[key]
            custom = slots_set.get(key)
            if custom:
                fb  = custom.get("fb", default_char)
                cid = custom.get("id", "")
                lines.append(f"  ✅ {fb} <b>{label}</b> <code>[{cid[:8]}…]</code>")
                markup.add(
                    types.InlineKeyboardButton(f"✏️ {label}", callback_data=f"msgicon_set:{key}"),
                    types.InlineKeyboardButton("🔄 Reset", callback_data=f"msgicon_reset:{key}"),
                )
            else:
                lines.append(f"  🔘 {default_char} <b>{label}</b> (default)")
                markup.add(
                    types.InlineKeyboardButton(f"✏️ {label}", callback_data=f"msgicon_set:{key}"),
                    types.InlineKeyboardButton("—", callback_data="msgicon_noop"),
                )
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="msgicon_close"))
    text = (
        f"✨ <b>Message Icons</b>\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"<i>✏️ Click to send a custom emoji sticker or type the ID.</i>\n"
        f"<i>🔄 Reset to restore the default emoji.</i>"
        + "\n".join(lines)
        + ("\n\n<i>✅ " + note + "</i>" if note else "")
        + "\n\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
    )
    try:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"[MSG-ICONS] Failed: {e}")


def _set_msg_icon_step(message):
    """Step handler: receive custom emoji for a message icon slot."""
    uid = message.from_user.id
    state = _msg_icon_set_state.pop(uid, None)
    if not state:
        return
    if _is_back(message.text) or _intercept_menu_btn(message):
        return
    slot_key = state["key"]
    default_char, label = _MSG_ICON_SLOTS.get(slot_key, ("", ""))
    custom_emoji_id = None
    fallback_char = default_char
    if message.entities:
        for ent in message.entities:
            if ent.type == "custom_emoji":
                custom_emoji_id = getattr(ent, "custom_emoji_id", None)
                text = message.text or ""
                fallback_char = text[ent.offset:ent.offset + ent.length] or default_char
                break
    if not custom_emoji_id:
        txt = (message.text or "").strip()
        if txt.isdigit() and len(txt) > 10:
            custom_emoji_id = txt
        else:
            msg = bot.send_message(
                message.chat.id,
        "❌ Custom emoji not found!\n\n"
        "Send a Telegram premium custom emoji sticker, or enter the emoji ID.\n\nTry again:",
                parse_mode="HTML",
                reply_markup=_back_admin_kb(),
            )
            _msg_icon_set_state[uid] = state
            bot.register_next_step_handler(msg, _set_msg_icon_step)
            return
    with _custom_emoji_lock:
        _custom_emojis.setdefault("msg_slots", {})[slot_key] = {"id": custom_emoji_id, "fb": fallback_char}
    _save_custom_emojis()
    _show_edit_messages_menu(message, note=f"✅ <b>{label}</b> — custom emoji set!")


def _show_custom_emoji_menu(message, note=""):
    uid = message.from_user.id
    with _custom_emoji_lock:
        flags_set   = dict(_custom_emojis.get("flags", {}))
        svcs_set    = dict(_custom_emojis.get("services", {}))
        btns_set    = dict(_custom_emojis.get("buttons", {}))
        slots_set   = dict(_custom_emojis.get("msg_slots", {}))
        dm_e_set    = dict(_custom_emojis.get("dm_emoji", {}))

    if len(flags_set) > 8:
        flag_lines = f"  ✅ Total <b>{len(flags_set)}</b> flag custom emojis set\n  (📋 Use Flag JSON Export to view all)"
    else:
        flag_lines = "\n".join(f"  {k} → <code>{v}</code>" for k, v in flags_set.items()) or "  (none — use 🏳️ Flag Emoji Set to add)"
    svc_lines  = "\n".join(f"  {k} → <code>{v}</code>" for k, v in svcs_set.items())  or "  (none)"
    btn_lines  = "\n".join(f"  <code>{k}</code> → <code>{v}</code>" for k, v in btns_set.items()) or "  (none)"
    slot_lines = "\n".join(f"  {{emoji_{k}}} → {v.get('fb','?')} (id:<code>{v.get('id','')}</code>)" for k, v in slots_set.items()) or "  (none)"

    dm_emoji_lines = ""
    for key, defs in _DM_EMOJI_DEFAULTS.items():
        cur = dm_e_set.get(key, {})
        cur_id = cur.get("id") or defs["id"]
        cur_fb = cur.get("fb") or defs["fb"]
        label  = _DM_EMOJI_LABELS.get(key, key)
        dm_emoji_lines += f"  {cur_fb} <b>{label}</b> → <code>{cur_id}</code>\n"

    all_btn_keys = "\n".join(
        f"  <code>{k}</code> — {v}" for k, v in _BTN_DISPLAY_NAMES.items()
    )
    text = (
        f"🎨 <b>Custom Emoji Settings</b>\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"📲 <b>DM Message Emoji (number/country):</b>\n{dm_emoji_lines}\n"
        f"🏳️ <b>Flag Emojis:</b>\n{flag_lines}\n\n"
        f"🎯 <b>Service Emojis:</b>\n{svc_lines}\n\n"
        f"🔘 <b>Button Emojis (set):</b>\n{btn_lines}\n\n"
        f"📋 <b>All Button Keys:</b>\n{all_btn_keys}\n\n"
        f"💬 <b>Message Slot Emojis:</b>\n{slot_lines}\n\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        + (f"<i>{note}</i>\n" if note else "")
    )
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("🏳️ Flag Emoji Set", "🎯 Service Emoji Set")
    mk.add("🌍 All Flags JSON Set", "📋 Flag JSON Export")
    mk.add("🔢 IDs Only Set", "🗑️ Flag Emoji Del")
    mk.add("🗑️ Service Emoji Del", "🔘 Button Emoji Set")
    mk.add("🗑️ Button Emoji Del", "💬 Msg Emoji Set")
    mk.add("🗑️ Msg Emoji Del", "🖥️ Admin Btn Set")
    mk.add("🗑️ Admin Btn Del")
    mk.add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟")
    bot.send_message(message.chat.id, text, reply_markup=mk, parse_mode="HTML")


def _custom_emoji_input(message):
    uid = message.from_user.id
    mode = _custom_emoji_state.pop(uid, None)
    if not mode:
        return

    # ── document sent while in "service" mode → parse as Service Emoji ID file ──
    if message.document and mode == "service":
        doc = message.document
        fname = doc.file_name or ""
        fext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        wait = bot.send_message(message.chat.id,
            f"⏳ <b>{fname}</b> parsing...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
            content = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            bot.edit_message_text(f"❌ File download hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return
        loaded = {}
        skipped = []
        if fext == "json":
            try:
                data = json.loads(content)
            except Exception as je:
                bot.edit_message_text(
                    f"❌ JSON parse error: <code>{je}</code>",
                    message.chat.id, wait.message_id, parse_mode="HTML")
                return
            if not isinstance(data, dict):
                bot.edit_message_text(
                    "❌ <b>Invalid format!</b>\n\n"
                    "The JSON file should be:\n"
                    "<code>{\n"
                    '  "WHATSAPP": "5334998226636390258",\n'
                    '  "INSTAGRAM": "5319160079465857105"\n'
                    "}</code>",
                    message.chat.id, wait.message_id, parse_mode="HTML")
                return
            for svc_raw, eid in data.items():
                svc = str(svc_raw).upper().strip()
                eid = str(eid).strip()
                if svc and eid.isdigit():
                    loaded[svc] = eid
                else:
                    skipped.append(f"{svc_raw}")
        else:
            # .txt or any other: robust line-by-line parse
            import re as _re_svc
            # Try whole-file JSON first
            try:
                _jdata = json.loads(content)
                if isinstance(_jdata, dict):
                    for k, v in _jdata.items():
                        svc = str(k).upper().strip()
                        _eid_m = _re_svc.search(r'\d{10,}', str(v))
                        if svc and _eid_m:
                            loaded[svc] = _eid_m.group(0)
                        else:
                            skipped.append(str(k))
            except Exception:
                # Line-by-line: any 10+ digit number + preceding word = service
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    _eid_m = _re_svc.search(r'(\d{10,})', line)
                    if not _eid_m:
                        skipped.append(line)
                        continue
                    eid = _eid_m.group(1)
                    prefix = line[:line.index(eid)]
                    _svc_m = _re_svc.search(r'([A-Za-z][A-Za-z0-9 _\-]{1,20})', prefix)
                    if _svc_m:
                        svc = _re_svc.sub(r'[\s\-_]+', '_', _svc_m.group(1).strip()).upper().rstrip('_:→ ')
                        if svc:
                            loaded[svc] = eid
                        else:
                            skipped.append(line)
                    else:
                        skipped.append(line)
        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass
        if not loaded:
            bot.send_message(message.chat.id,
                "❌ <b>Kono valid service emoji ID pawa jayni!</b>\n\n"
                "JSON format:\n"
                "<code>{\"WHATSAPP\": \"5334998226636390258\"}</code>\n\n"
                "TXT format (line by line):\n"
                "<code>WHATSAPP 5334998226636390258\nINSTAGRAM 5319160079465857105</code>",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("services", {}).update(loaded)
        _save_custom_emojis()
        lines_preview = "\n".join(
            f"  🎯 <b>{k}</b> → <code>{v}</code>" for k, v in list(loaded.items())[:20])
        extra = f"\n  <i>...and {len(loaded)-20} more</i>" if len(loaded) > 20 else ""
        skip_txt = f"\n\n⚠️ Skip: {', '.join(skipped[:5])}" if skipped else ""
        _show_custom_emoji_menu(message,
            note=f"✅ {len(loaded)} service emoji set!\n{lines_preview}{extra}{skip_txt}")
        return
    # ─────────────────────────────────────────────────────────────────────────────

    # ── .txt document sent while in a flag mode → parse as Premium Flag file ──
    if message.document and mode in ("flag", "flag_bulk_json", "flag_ids_only"):
        doc = message.document
        fname = doc.file_name or ""
        if fname.lower().endswith(".txt"):
            wait = bot.send_message(message.chat.id,
                f"⏳ <b>{fname}</b> parsing...", parse_mode="HTML")
            try:
                file_info = bot.get_file(doc.file_id)
                raw = bot.download_file(file_info.file_path)
                txt_content = raw.decode("utf-8", errors="ignore")
            except Exception as e:
                bot.edit_message_text(
                    f"❌ File download hoyni: <code>{e}</code>",
                    message.chat.id, wait.message_id, parse_mode="HTML")
                return
            import re as _re2
            parsed = {}
            for line in txt_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Primary format: (1)(US)🇺🇸 United States {"emoji": "🇺🇸", "id": "591..."}
                m = _re2.search(r'"id"\s*:\s*"(\d+)"', line)
                flag_m = _re2.search(r'[🇠-🇿]{2}', line)
                if m and flag_m:
                    parsed[flag_m.group(0)] = m.group(1)
                    continue
                # Fallback: flag_emoji  numeric_id (or with →)
                clean = _re2.sub(r'^[\d\.\)\-\s]+', '', line).strip()
                clean = clean.replace('→', '').strip()
                tokens = clean.split()
                if len(tokens) >= 2 and tokens[-1].isdigit() and len(tokens[-1]) >= 10:
                    fchar = next((t for t in tokens
                        if len(t) == 2 and all(
                            '🇠' <= c <= '🇿' for c in t)), None)
                    if fchar:
                        parsed[fchar] = tokens[-1]
            try:
                bot.delete_message(message.chat.id, wait.message_id)
            except Exception:
                pass
            if not parsed:
                bot.send_message(message.chat.id,
                    "❌ <b>Couldn't parse flag data from the file!</b>\n\n"
                    "Expected format:\n"
                    "<code>(1)(US)🇺🇸 United States {\"emoji\": \"🇺🇸\", \"id\": \"123...\"}</code>",
                    parse_mode="HTML")
                return
            with _custom_emoji_lock:
                _custom_emojis.setdefault("flags", {}).update(parsed)
            _save_custom_emojis()
            lines_preview = "\n".join(
                f"  {k} → <code>{v}</code>" for k, v in list(parsed.items())[:10])
            extra = f"\n  <i>...and {len(parsed)-10} more</i>" if len(parsed) > 10 else ""
            bot.send_message(message.chat.id,
                f"✅ <b>{len(parsed)} custom flag emoji(s) loaded!</b>\n\n"
                f"{lines_preview}{extra}\n\n"
                f"🎉 Custom flags will now appear in all OTP/number messages.",
                parse_mode="HTML")
            return
    # ─────────────────────────────────────────────────────────────────────────────

    txt = (message.text or "").strip()
    if _is_back(txt) or txt == "🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟":
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return

    parts = txt.split()

    if mode == "flag":
        # Supports: "🇧🇩 ID", "🇧🇩 → ID", numbered "1. 🇧🇩 ID", "1. 🇧🇩 → ID"
        import re as _re
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        parsed = {}
        for line in lines:
            # Strip leading "1." "1)" "1-" numbering
            clean = _re.sub(r'^\d+[\.\)\-]\s*', '', line).strip()
            # Remove → arrow separator
            clean = clean.replace('→', '').replace('->', '')
            tokens = clean.split()
            # First token = flag emoji, last token = numeric ID
            if len(tokens) >= 2 and tokens[-1].isdigit():
                parsed[tokens[0]] = tokens[-1]
        if not parsed:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n"
        "<b>Format (any one):</b>\n"
                "<code>🇧🇩 5432198765432198765</code>\n"
                "<code>🇧🇩 → 5432198765432198765</code>\n\n"
                "<b>Bulk:</b>\n<code>1. 🇧🇩 → 5432198765432198765\n2. 🇺🇸 → 5976694588658686266</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        added = "\n".join(f"  {k} → <code>{v}</code>" for k, v in parsed.items())
        _show_custom_emoji_menu(message, note=f"✅ {len(parsed)}flag(s) set:\n{added}")

    elif mode == "flag_bulk_json":
        # Accept a JSON object: {"🇧🇩": "123456789", "🇺🇸": "987654321", ...}
        # Also accept line-by-line: 🇧🇩 123456789\n🇺🇸 987654321
        import re as _re
        parsed = {}
        err_msg = ""
        # Try JSON first
        raw = txt.strip()
        # Strip markdown code fences if present
        raw = _re.sub(r'^```[a-z]*\n?', '', raw, flags=_re.IGNORECASE)
        raw = _re.sub(r'\n?```$', '', raw)
        raw = raw.strip()
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object/dict")
            for k, v in data.items():
                v_str = str(v).strip()
                if v_str.isdigit():
                    parsed[k.strip()] = v_str
                else:
                    err_msg += f"⚠️ <code>{k}</code> — Invalid ID (<code>{v}</code>), skipped\n"
        except json.JSONDecodeError:
            # Fall back to line-by-line parsing
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            for line in lines:
                clean = _re.sub(r'^\d+[\.\)\-]\s*', '', line).strip()
                tokens = clean.split()
                if len(tokens) == 2 and tokens[1].isdigit():
                    parsed[tokens[0]] = tokens[1]

        if not parsed:
            bot.send_message(message.chat.id,
        "❌ Could not parse anything!\n\n"
        "<b>JSON Format:</b>\n"
                "<code>{\n"
                '  "🇧🇩": "5432198765432198765",\n'
                '  "🇺🇸": "5976694588658686266"\n'
                "}</code>\n\n"
                "<b>Line-by-line format also works:</b>\n"
                "<code>🇧🇩 5432198765432198765\n🇺🇸 5976694588658686266</code>\n\n"
                "Send again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        added_lines = "\n".join(f"  {k} → <code>{v}</code>" for k, v in parsed.items())
        note = f"✅ {len(parsed)}flag(s) set from JSON:\n{added_lines}"
        if err_msg:
            note += f"\n\n{err_msg}"
        _show_custom_emoji_menu(message, note=note)

    elif mode == "flag_ids_only":
        # User pastes only emoji IDs (one per line or space-separated).
        # Bot calls Telegram API to resolve each ID → emoji character, then saves.
        import re as _re
        raw_ids = []
        for token in _re.split(r'[\s,\n]+', txt):
            token = token.strip()
            if token.isdigit() and len(token) >= 10:
                raw_ids.append(token)
        if not raw_ids:
            bot.send_message(message.chat.id,
        "❌ No valid ID found!\n\n"
        "Enter one numeric emoji ID per line:\n"
                "<code>5432198765432198765\n5976694588658686266</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        raw_ids = raw_ids[:200]  # cap at 200
        bot.send_message(message.chat.id,
            f"⏳ {len(raw_ids)}ID(s) being resolved from Telegram...",
            parse_mode="HTML")
        parsed = {}
        failed = []
        # Telegram allows max 200 IDs per call — process in chunks of 100
        chunk_size = 100
        for i in range(0, len(raw_ids), chunk_size):
            chunk = raw_ids[i:i + chunk_size]
            try:
                stickers = bot.get_custom_emoji_stickers(chunk)
                # Zip original IDs with returned stickers (API returns in same order)
                # sticker.custom_emoji_id may be None in some pyTelegramBotAPI versions
                for eid_orig, sticker in zip(chunk, stickers):
                    emoji_char = getattr(sticker, "emoji", None)
                    eid = getattr(sticker, "custom_emoji_id", None) or eid_orig
                    if emoji_char and eid:
                        parsed[emoji_char] = eid
            except Exception as _api_err:
                failed.extend(chunk)
                print(f"[FLAG-IDS] API error for chunk: {_api_err}")
        if not parsed:
            bot.send_message(message.chat.id,
        "❌ No emoji could be resolved from Telegram!\n\n"
        "Check if the IDs are valid. Send again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        added_lines = "\n".join(f"  {k} → <code>{v}</code>" for k, v in parsed.items())
        note = f"✅ {len(parsed)}flag(s) auto-resolved and set:\n{added_lines}"
        if failed:
            note += f"\n\n⚠️ {len(failed)}ID(s) could not be resolved."
        _show_custom_emoji_menu(message, note=note)

    elif mode == "service":
        # Format: INSTAGRAM 5319160079465857105
        if len(parts) != 2:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>INSTAGRAM 5319160079465857105</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        svc_name, emoji_id = parts[0].upper(), parts[1]
        with _custom_emoji_lock:
            _custom_emojis.setdefault("services", {})[svc_name] = emoji_id
        _save_custom_emojis()
        _show_custom_emoji_menu(message, note=f"✅ {svc_name} → {emoji_id} set!")

    elif mode == "del_flag":
        emoji_char = parts[0] if parts else ""
        with _custom_emoji_lock:
            removed = _custom_emojis.get("flags", {}).pop(emoji_char, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ {emoji_char} deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>{emoji_char}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "del_service":
        svc_name = (parts[0] if parts else "").upper()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("services", {}).pop(svc_name, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ {svc_name} deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>{svc_name}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "btn":
        # Format: button_key emoji_id  (e.g. change_number 5375170473095077321)
        if len(parts) != 2:
            available = "\n".join(f"  <code>{k}</code> — {v}" for k, v in _BTN_DISPLAY_NAMES.items())
            bot.send_message(message.chat.id,
        f"❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>button_key emoji_id</code>\n\n"
                f"<b>Available buttons:</b>\n{available}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        btn_key, emoji_id = parts[0].lower(), parts[1]
        if btn_key not in _BTN_DISPLAY_NAMES:
            available = ", ".join(f"<code>{k}</code>" for k in _BTN_DISPLAY_NAMES)
            bot.send_message(message.chat.id,
        f"❌ <code>{btn_key}</code> not found!\n\nValid keys: {available}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("buttons", {})[btn_key] = emoji_id
        _save_custom_emojis()
        _show_custom_emoji_menu(message, note=f"✅ Button <code>{btn_key}</code> → <code>{emoji_id}</code> set!")

    elif mode == "del_btn":
        btn_key = (parts[0] if parts else "").lower()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("buttons", {}).pop(btn_key, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ Button <code>{btn_key}</code> deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>{btn_key}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "admin_btn":
        # Accepts single or bulk lines: key emoji_id
        import re as _re_ab
        lines_in = [l.strip() for l in txt.splitlines() if l.strip()]
        saved = {}
        bad = []
        for line in lines_in:
            m = _re_ab.match(r'^([a-z_]+)\s+(\d{10,})$', line)
            if m:
                key, eid = m.group(1), m.group(2)
                if key in _ADMIN_BTN_DEFAULT_ICONS:
                    saved[key] = eid
                else:
                    bad.append(f"<code>{key}</code> (unknown key)")
            else:
                bad.append(f"<code>{line[:40]}</code>")
        if not saved:
            bot.send_message(
                message.chat.id,
                "❌ <b>Wrong format!</b>\n\n"
                "<b>Format:</b> <code>key emoji_id</code>\n"
                "<b>Example:</b> <code>num_add 5420323438508155202</code>\n\n"
                "Key must be from the list shown. Send again:",
                parse_mode="HTML"
            )
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("admin_btns", {}).update(saved)
        _save_custom_emojis()
        note_lines = "\n".join(f"  ✅ <code>{k}</code> → <code>{v}</code>" for k, v in saved.items())
        bad_txt = ("\n\n⚠️ Skipped: " + ", ".join(bad[:5])) if bad else ""
        _show_custom_emoji_menu(message,
            note=f"✅ {len(saved)} admin button icon(s) updated!\n{note_lines}{bad_txt}")

    elif mode == "del_admin_btn":
        key_in = (parts[0] if parts else "").strip()
        if key_in.upper() == "ALL":
            with _custom_emoji_lock:
                count = len(_custom_emojis.get("admin_btns", {}))
                _custom_emojis["admin_btns"] = {}
            _save_custom_emojis()
            _show_custom_emoji_menu(message,
                note=f"🗑️ All {count} admin button override(s) reset to defaults!")
        else:
            key_in = key_in.lower()
            with _custom_emoji_lock:
                removed = _custom_emojis.get("admin_btns", {}).pop(key_in, None)
            if removed:
                _save_custom_emojis()
                _show_custom_emoji_menu(message,
                    note=f"🗑️ <code>{key_in}</code> reset to default icon!")
            else:
                bot.send_message(
                    message.chat.id,
                    f"❌ <code>{key_in}</code> not found in overrides.",
                    parse_mode="HTML"
                )
                _custom_emoji_state[uid] = mode

    elif mode == "msg_slot":
        # Format: slot_name emoji_id fallback_emoji  (e.g. fire 5432198765432198765 🔥)
        if len(parts) < 3:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>slot_name emoji_id fallback_emoji</code>\n\n"
        "<b>Example:</b>\n<code>fire 5432198765432198765 🔥</code>\n\n"
                "Then use <code>{emoji_fire}</code> in any message template to show the custom emoji.\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        slot_name = parts[0].lower()
        emoji_id  = parts[1]
        fallback  = " ".join(parts[2:])
        with _custom_emoji_lock:
            _custom_emojis.setdefault("msg_slots", {})[slot_name] = {"id": emoji_id, "fb": fallback}
        _save_custom_emojis()
        _show_custom_emoji_menu(message,
            note=f"✅ Slot <code>emoji_{slot_name}</code> set!\n"
                 f"Use <code>{{emoji_{slot_name}}}</code> in templates.")

    elif mode == "del_msg_slot":
        slot_name = (parts[0] if parts else "").lower()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("msg_slots", {}).pop(slot_name, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ Slot <code>emoji_{slot_name}</code> deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>emoji_{slot_name}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "dm_emoji":
        # Format: slot_key emoji_id fallback_emoji  e.g. "number_pre 5422858869372104873 📞"
        if len(parts) < 3:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>slot_key emoji_id fallback_emoji</code>\n\n"
        "<b>Example:</b>\n<code>number_pre 5422858869372104873 📞</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        slot_key = parts[0].lower()
        if slot_key not in _DM_EMOJI_DEFAULTS:
            valid = ", ".join(f"<code>{k}</code>" for k in _DM_EMOJI_DEFAULTS)
            bot.send_message(message.chat.id,
        f"❌ <code>{slot_key}</code> is invalid!\n\nValid keys: {valid}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        emoji_id = parts[1]
        fallback = " ".join(parts[2:])
        with _custom_emoji_lock:
            _custom_emojis.setdefault("dm_emoji", {})[slot_key] = {"id": emoji_id, "fb": fallback}
        _save_custom_emojis()
        label = _DM_EMOJI_LABELS.get(slot_key, slot_key)
        _show_custom_emoji_menu(message,
            note=f"✅ DM emoji <b>{label}</b> → {fallback} <code>{emoji_id}</code> set!")

    elif mode == "del_dm_emoji":
        slot_key = (parts[0] if parts else "").lower()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("dm_emoji", {}).pop(slot_key, None)
        if removed:
            _save_custom_emojis()
            label = _DM_EMOJI_LABELS.get(slot_key, slot_key)
            _show_custom_emoji_menu(message, note=f"🗑️ DM emoji <b>{label}</b> reset to default!")
        else:
            valid = ", ".join(f"<code>{k}</code>" for k in _DM_EMOJI_DEFAULTS)
            bot.send_message(message.chat.id,
        f"❌ <code>{slot_key}</code> was not customized.\nValid keys: {valid}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode


# ── Payment System — User Functions ──────────────────────────────────────────

def _show_balance(message):
    uid = message.from_user.id
    bal = get_balance(uid)
    cur = get_currency()
    rpo = get_reward_per_otp()
    with otp_stats_lock:
        total_otps = otp_stats.get(str(uid), 0)
    # Count this user's pending/approved withdraw requests
    with _withdraw_lock:
        pending = [r for r in _withdraw_requests if r["uid"] == uid and r["status"] == "pending"]
        approved = [r for r in _withdraw_requests if r["uid"] == uid and r["status"] == "approved"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💸 Withdraw", callback_data="wd_start"))
    bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5445353829304387411">💰</tg-emoji> <b>Your Wallet</b>\n'
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        f'<tg-emoji emoji-id="5197434882321567830">💵</tg-emoji> <b>Balance:</b> <code>{cur}{bal:.2f}</code>\n'
        f'<tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji> <b>Per OTP Reward:</b> <code>{cur}{rpo:.2f}</code>\n'
        f'<tg-emoji emoji-id="5451882707875276247">📊</tg-emoji> <b>Total OTPs:</b> <code>{total_otps}</code>\n'
        f'<tg-emoji emoji-id="5386367538735104399">⏳</tg-emoji> <b>Pending Withdraw:</b> <code>{len(pending)}</code>\n'
        f'<tg-emoji emoji-id="5206607081334906820">✅</tg-emoji> <b>Approved Withdraw:</b> <code>{len(approved)}</code>\n'
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
        parse_mode="HTML",
        reply_markup=markup,
    )


def _show_refer(message):
    uid = message.from_user.id
    link = _get_refer_link(uid)
    count = _get_refer_count(uid)
    cur = get_currency()
    commission = get_refer_commission()
    _SEP = '<tg-emoji emoji-id="5870818207383686839">🔗</tg-emoji>' * 8
    bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5420145051336485498">🔗</tg-emoji> <b>Referral Program</b>\n'
        f'{_SEP}\n'
        f'<tg-emoji emoji-id="5352694861990501856">👥</tg-emoji> <b>Your Referrals:</b> <code>{count}</code> people\n'
        f'<tg-emoji emoji-id="5796420706572966288">💰</tg-emoji> <b>Commission per Refer:</b> <code>{cur}{commission:.2f}</code>\n'
        f'{_SEP}\n'
        f'<tg-emoji emoji-id="5420517437885943844">📎</tg-emoji> <b>Your Referral Link:</b>\n'
        f'<code>{link}</code>\n'
        f'{_SEP}\n'
        f'<tg-emoji emoji-id="5267041999948653482">🔗</tg-emoji> <i>Share this link — when someone joins, you\'ll get {cur}{commission:.2f}!</i>',
        parse_mode="HTML",
    )


_withdraw_state: dict = {}


def _start_withdraw(message):
    uid = message.from_user.id
    bal = get_balance(uid)
    cur = get_currency()
    min_wd = get_min_withdraw()
    if bal < min_wd:
        bot.send_message(
            message.chat.id,
            f'❌ <b>Insufficient Balance!</b>\n\n'
            f'<tg-emoji emoji-id="5197434882321567830">💵</tg-emoji> Your Balance: <code>{cur}{bal:.2f}</code>\n'
            f'<tg-emoji emoji-id="5368493177634301681">⚠️</tg-emoji> Minimum Withdraw: <code>{cur}{min_wd:.2f}</code>\n\n'
            f'Get more OTPs and earn rewards to withdraw.',
            parse_mode="HTML",
        )
        return
    msg = bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5386367538735104399">💸</tg-emoji> <b>Withdraw Request</b>\n\n'
        f'<tg-emoji emoji-id="5197434882321567830">💵</tg-emoji> Your Balance: <code>{cur}{bal:.2f}</code> <tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji>\n'
        f'<tg-emoji emoji-id="5368493177634301681">⚠️</tg-emoji> Minimum: <code>{cur}{min_wd:.2f}</code> <tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji>\n\n'
        f'How much do you want to withdraw? (enter a number)\n'
        f'Example: <code>100</code>',
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
    )
    _withdraw_state[uid] = {"step": "amount"}
    bot.register_next_step_handler(msg, _wd_amount_step)


def _wd_amount_step(message):
    uid = message.from_user.id
    txt = (message.text or "").strip()
    if txt in ("❌ Cancel", "❌ Cancel") or _is_back(txt):
        _withdraw_state.pop(uid, None)
        bot.send_message(message.chat.id, "❌ Withdraw cancelled.",
                         reply_markup=main_menu(uid), parse_mode="HTML")
        return
    if _intercept_menu_btn(message):
        _withdraw_state.pop(uid, None)
        return
    try:
        amount = float(txt.replace(",", "").strip())
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Please enter a number! Example: <code>100</code>",
                                parse_mode="HTML")
        bot.register_next_step_handler(msg, _wd_amount_step)
        return
    cur = get_currency()
    bal = get_balance(uid)
    min_wd = get_min_withdraw()
    if amount < min_wd:
        msg = bot.send_message(message.chat.id,
            f"❌ Minimum <code>{cur}{min_wd:.2f}</code> required to withdraw. Please enter again:",
            parse_mode="HTML")
        bot.register_next_step_handler(msg, _wd_amount_step)
        return
    if amount > bal:
        msg = bot.send_message(message.chat.id,
            f"❌ Insufficient balance! You have <code>{cur}{bal:.2f}</code>. Please enter again:",
            parse_mode="HTML")
        bot.register_next_step_handler(msg, _wd_amount_step)
        return
    _withdraw_state[uid]["amount"] = amount
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("bKash",   callback_data="wd_method:bKash",   icon_custom_emoji_id="6084377871265041519", style="danger"),
        types.InlineKeyboardButton("Nagad",   callback_data="wd_method:Nagad",   icon_custom_emoji_id="6082388335039351641", style="success"),
        types.InlineKeyboardButton("Rocket",  callback_data="wd_method:Rocket",  icon_custom_emoji_id="6084843995475742197", style="primary"),
        types.InlineKeyboardButton("Binance", callback_data="wd_method:Binance", icon_custom_emoji_id="5359437015752401733", style="success"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="wd_cancel", style="danger"),
    )
    bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5375135722514685501">💰</tg-emoji> Amount: <code>{cur}{amount:.2f}</code>\n\n<tg-emoji emoji-id="5388632425314140043">💳</tg-emoji> Choose payment method:',
        parse_mode="HTML",
        reply_markup=markup,
    )


def _wd_account_step(message):
    uid = message.from_user.id
    state = _withdraw_state.get(uid, {})
    txt = (message.text or "").strip()
    if txt in ("❌ Cancel", "❌ Cancel") or _is_back(txt):
        _withdraw_state.pop(uid, None)
        bot.send_message(message.chat.id, "❌ Withdraw cancelled.",
                         reply_markup=main_menu(uid), parse_mode="HTML")
        return
    if _intercept_menu_btn(message):
        _withdraw_state.pop(uid, None)
        return
    if not txt:
        msg = bot.send_message(message.chat.id, "❌ Enter account number/address:")
        bot.register_next_step_handler(msg, _wd_account_step)
        return
    state["account"] = txt
    method  = state.get("method", "?")
    amount  = state.get("amount", 0)
    cur = get_currency()
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Confirm", callback_data="wd_confirm_submit"),
        types.InlineKeyboardButton("❌ Cancel",   callback_data="wd_cancel"),
    )
    bot.send_message(
        message.chat.id,
        f"💸 <b>Confirm Withdraw</b>\n\n"
        f"💵 Amount: <code>{cur}{amount:.2f}</code>\n"
        f"📲 Method: <b>{method}</b>\n"
        f"📋 Account: <code>{txt}</code>\n\n"
        f"Are you sure?",
        parse_mode="HTML",
        reply_markup=markup,
    )


# ── Payment System — Admin Functions ──────────────────────────────────────────

def _show_payment_admin(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    cur = get_currency()
    rpo = get_reward_per_otp()
    min_wd = get_min_withdraw()
    with _withdraw_lock:
        pending_wds = [r for r in _withdraw_requests if r["status"] == "pending"]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ref_comm = get_refer_commission()
    markup.add("💵 Set Reward", "💱 Set Currency")
    markup.add("📉 Set Minimum Withdraw", "🔗 Set Refer Commission")
    markup.add("📋 View All Balances")
    markup.add("➕ Add Balance Manually", "➖ Deduct Balance Manually")
    markup.add(f"⏳ Pending Withdraw ({len(pending_wds)})")
    markup.add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟")
    bot.send_message(
        message.chat.id,
        f"💰 <b>Payment Settings</b>\n\n"
        f"🎁 Per OTP Reward: <code>{cur}{rpo:.2f}</code>\n"
        f"💱 Currency: <code>{cur}</code>\n"
        f"📉 Minimum Withdraw: <code>{cur}{min_wd:.2f}</code>\n"
        f"🔗 Refer Commission: <code>{cur}{ref_comm:.2f}</code>\n"
        f"⏳ Pending Withdraw: <code>{len(pending_wds)}</code>",
        parse_mode="HTML",
        reply_markup=markup,
    )


_payment_admin_state: dict = {}


def _payment_admin_msg_handler(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    txt = (message.text or "").strip()

    if txt == "𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀":
        _show_payment_admin(message)

    elif txt == "💵 Set Reward":
        cur = get_currency()
        msg = bot.send_message(
            message.chat.id,
            f"🎁 What is the reward per OTP?\n\n"
            f"Current: <code>{cur}{get_reward_per_otp():.2f}</code>\n"
            f"Enter new amount (e.g. <code>0.50</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_reward"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "💱 Set Currency":
        msg = bot.send_message(
            message.chat.id,
            f"💱 What currency symbol to use?\n\n"
            f"Current: <code>{get_currency()}</code>\n"
            f"Enter new symbol (e.g. <code>৳</code> or <code>$</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_currency"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "📉 Set Minimum Withdraw":
        cur = get_currency()
        msg = bot.send_message(
            message.chat.id,
            f"📉 What is the minimum withdraw amount?\n\n"
            f"Current: <code>{cur}{get_min_withdraw():.2f}</code>\n"
            f"Enter new amount (e.g. <code>50</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_min_withdraw"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "📋 View All Balances":
        with _balances_lock:
            bal_copy = dict(_balances)
        if not bal_copy:
            bot.send_message(message.chat.id, "❌ No balances found.", parse_mode="HTML")
            return
        cur = get_currency()
        lines = []
        for k, v in sorted(bal_copy.items(), key=lambda x: -float(x[1])):
            lines.append(f"<code>{k}</code> → <b>{cur}{float(v):.2f}</b>")
        text = "📋 <b>All User Balances</b>\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n" + "\n".join(lines[:50])
        if len(lines) > 50:
            text += f"\n…and {len(lines)-50} more"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    elif txt in ("➕ Add Balance Manually", "➖ Deduct Balance Manually"):
        action = "add" if "add" in txt.lower() else "deduct"
        msg = bot.send_message(
            message.chat.id,
            f"👤 Which user's balance do you want to {'<b>add</b>' if action=='add' else '<b>deduct</b>'}?\n\n"
            f"Enter the user's <b>Telegram ID</b> (Example: <code>123456789</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = f"manual_uid:{action}"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "🔗 Set Refer Commission":
        cur = get_currency()
        msg = bot.send_message(
            message.chat.id,
            f"🔗 Set Refer Commission amount:\n\n"
            f"Current: <code>{cur}{get_refer_commission():.2f}</code>\n"
            f"Enter new amount (e.g. <code>10</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_refer_commission"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt.startswith("⏳ Pending Withdraw"):
        _show_pending_withdraws(message)


def _payment_admin_input(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    mode = _payment_admin_state.pop(uid, None)
    txt = (message.text or "").strip()
    if _is_back(txt) or _intercept_menu_btn(message):
        return
    if mode == "set_reward":
        try:
            val = float(txt.replace(",", ""))
            if val < 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Enter a positive number:")
            _payment_admin_state[uid] = "set_reward"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["reward_per_otp"] = val
        _save_reward_settings()
        cur = get_currency()
        bot.send_message(message.chat.id,
            f"✅ Per OTP reward set: <code>{cur}{val:.2f}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode == "set_currency":
        if not txt:
            msg = bot.send_message(message.chat.id, "❌ Enter a currency symbol:")
            _payment_admin_state[uid] = "set_currency"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["currency"] = txt
        _save_reward_settings()
        bot.send_message(message.chat.id,
            f"✅ Currency set: <code>{txt}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode == "set_min_withdraw":
        try:
            val = float(txt.replace(",", ""))
            if val < 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Enter a positive number:")
            _payment_admin_state[uid] = "set_min_withdraw"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["min_withdraw"] = val
        _save_reward_settings()
        cur = get_currency()
        bot.send_message(message.chat.id,
            f"✅ Minimum withdraw set: <code>{cur}{val:.2f}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode == "set_refer_commission":
        try:
            val = float(txt.replace(",", ""))
            if val < 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Enter a positive number:")
            _payment_admin_state[uid] = "set_refer_commission"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["refer_commission"] = val
        _save_reward_settings()
        cur = get_currency()
        bot.send_message(message.chat.id,
            f"✅ Refer commission set: <code>{cur}{val:.2f}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode and mode.startswith("manual_uid:"):
        action = mode.split(":", 1)[1]  # "add" or "deduct"
        try:
            target_uid = int(txt.strip())
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "❌ Invalid ID! Numbers only (e.g. <code>123456789</code>):",
                parse_mode="HTML",
            )
            _payment_admin_state[uid] = f"manual_uid:{action}"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        cur = get_currency()
        cur_bal = get_balance(target_uid)
        action_word = "add" if action == "add" else "deduct"
        msg = bot.send_message(
            message.chat.id,
            f"👤 UID: <code>{target_uid}</code>\n"
            f"💰 Current Balance: <code>{cur}{cur_bal:.2f}</code>\n\n"
            f"How much do you want to <b>{action_word}</b>? (enter a number)\n"
            f"Example: <code>50</code>",
            parse_mode="HTML",
        )
        _payment_admin_state[uid] = f"manual_amount:{action}:{target_uid}"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif mode and mode.startswith("manual_amount:"):
        parts = mode.split(":", 2)
        action = parts[1]       # "add" or "deduct"
        target_uid = int(parts[2])
        try:
            amount = float(txt.replace(",", "").strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "❌ Invalid! Enter a positive number:",
                parse_mode="HTML",
            )
            _payment_admin_state[uid] = f"manual_amount:{action}:{target_uid}"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        cur = get_currency()
        if action == "add":
            new_bal = add_reward(target_uid, amount)
            action_label = "Added ✅"
            sign = "+"
        else:
            ok, new_bal = deduct_balance(target_uid, amount)
            if not ok:
                bot.send_message(
                    message.chat.id,
                    f"❌ Insufficient balance! UID <code>{target_uid}</code>'s balance is insufficient.",
                    parse_mode="HTML",
                )
                _show_payment_admin(message)
                return
            action_label = "Deducted ✅"
            sign = "-"
        bot.send_message(
            message.chat.id,
            f"✅ <b>Balance Updated Successfully!</b>\n\n"
            f"👤 UID: <code>{target_uid}</code>\n"
            f"💸 Amount: <b>{sign}{cur}{amount:.2f}</b> {action_label}\n"
            f"💰 New Balance: <code>{cur}{new_bal:.2f}</code>",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        # Notify the user
        try:
            action_msg = "credited" if action == "add" else "debited"
            bot.send_message(
                target_uid,
                f"💰 <b>Balance Updated!</b>\n\n"
                f"Your account has been <b>{sign}{cur}{amount:.2f}</b> {action_msg}।\n"
                f"New Balance: <code>{cur}{new_bal:.2f}</code>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        _show_payment_admin(message)


def _show_pending_withdraws(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    cur = get_currency()
    with _withdraw_lock:
        pending = [r for r in _withdraw_requests if r["status"] == "pending"]
    if not pending:
        bot.send_message(message.chat.id, "✅ No pending withdrawals.", parse_mode="HTML")
        return
    for req in pending[:10]:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve:{req['id']}"),
            types.InlineKeyboardButton("❌ Reject",  callback_data=f"wd_reject:{req['id']}"),
        )
        import datetime as _dt
        ts = req.get("timestamp", 0)
        dt_str = _dt.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else "?"
        bot.send_message(
            message.chat.id,
            f"⏳ <b>Withdraw Request</b>\n\n"
            f"👤 UID: <code>{req['uid']}</code>\n"
            f"💵 Amount: <code>{cur}{req['amount']:.2f}</code>\n"
            f"📲 Method: <b>{req['method']}</b>\n"
            f"📋 Account: <code>{req['account']}</code>\n"
            f"🕐 Time: {dt_str}\n"
            f"🔑 ID: <code>{req['id']}</code>",
            parse_mode="HTML",
            reply_markup=markup,
        )


def _go_admin_panel(message, text="🔥 <b>ADMIN PANEL</b>"):
    uid = message.from_user.id
    chat_id = message.chat.id
    now = time.time()
    with _admin_panel_lock:
        if now - _admin_panel_last.get(chat_id, 0) < 2.0:
            return
        _admin_panel_last[chat_id] = now
    m_admin = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    KB = types.KeyboardButton
    m_admin.add(
        KB("𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱",          style="success", icon_custom_emoji_id=_get_admin_btn_icon("num_add")),
        KB("𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿",             style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("sob_clear")),
    )
    m_admin.add(
        KB("𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁",           style="primary", icon_custom_emoji_id=_get_admin_btn_icon("broadcast")),
        KB("𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁",          style="primary", icon_custom_emoji_id=_get_admin_btn_icon("user_count")),
    )
    m_admin.add(
        KB("𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁",            style="primary", icon_custom_emoji_id=_get_admin_btn_icon("user_list")),
        KB("𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀",             style="primary", icon_custom_emoji_id=_get_admin_btn_icon("otp_stats")),
    )
    m_admin.add(
        KB("𝗗𝗘𝗠𝗢 𝗢𝗧𝗣",              style="primary", icon_custom_emoji_id=_get_admin_btn_icon("demo_otp")),
        KB("𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹",             style="success", icon_custom_emoji_id=_get_admin_btn_icon("add_panel")),
    )
    m_admin.add(
        KB("𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹",         style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("remove_panel")),
        KB("𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲",           style="success", icon_custom_emoji_id=_get_admin_btn_icon("add_service")),
    )
    m_admin.add(
        KB("𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲",       style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("remove_service")),
        KB("𝗣𝗮𝗻𝗲𝗹𝘀",                style="primary", icon_custom_emoji_id=_get_admin_btn_icon("panels")),
    )
    m_admin.add(
        KB("𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹",            style="primary", icon_custom_emoji_id=_get_admin_btn_icon("test_panel")),
        KB("𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽𝗲 𝗦𝗲𝗻𝗱", style="success", icon_custom_emoji_id=_get_admin_btn_icon("purano_send")),
    )
    m_admin.add(
        KB("𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗕𝗼𝗻𝗱𝗵𝗼",    style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("purano_off")),
        KB("𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀",             style="primary", icon_custom_emoji_id=_get_admin_btn_icon("settings")),
    )
    if is_super_admin(uid):
        m_admin.add(
            KB("👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻",         style="success"),
            KB("𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻",     style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("remove_admin")),
        )
        m_admin.add(
            KB("𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗",        style="primary", icon_custom_emoji_id=_get_admin_btn_icon("support_id")),
        )
    m_admin.add(
        KB("𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀",        style="primary", icon_custom_emoji_id=_get_admin_btn_icon("edit_msgs")),
        KB("𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁",       style="primary", icon_custom_emoji_id=_get_admin_btn_icon("v2_panel")),
    )
    m_admin.add(
        KB("𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("live_console")),
        KB("𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀",         style="primary", icon_custom_emoji_id=_get_admin_btn_icon("extra_groups")),
    )
    m_admin.add(
        KB("𝗖𝘂𝘀𝘁𝗼𝗺 𝗘𝗺𝗼𝗷𝗶",         style="primary", icon_custom_emoji_id=_get_admin_btn_icon("custom_emoji")),
        KB("𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲",       style="primary", icon_custom_emoji_id=_get_admin_btn_icon("api_key")),
    )
    m_admin.add(
        KB("🌐 𝗔𝘂𝗴𝗲𝘀𝘁𝗲𝗹 𝗞𝗲𝘆",       style="primary"),
    )
    m_admin.add(
        KB("𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀",    style="primary", icon_custom_emoji_id=_get_admin_btn_icon("payment_settings")),
        KB("𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂",          style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("user_menu")),
    )
    m_admin.add(
        KB("𝗕𝘂𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲", style="success"),
    )
    m_admin.add(
        KB("🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("live_traffic")),
    )
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=m_admin,
        parse_mode="HTML",
    )


# ── Live Console Admin Config ─────────────────────────────────────────────────

def _cc_addrange_step(message):
    """Handle admin input for adding a range prefix to a console service."""
    uid = message.from_user.id
    sid = _cc_addrange_state.pop(uid, None)
    if not sid:
        _go_admin_panel(message)
        return
    txt = (message.text or "").strip()
    if txt in ("❌ Cancel", "❌ cancel") or _is_back(txt):
        _admin_panel_last.pop(message.chat.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        _cc_addrange_state.pop(uid, None)
        return
    prefix = re.sub(r"[^\d]", "", txt)
    if not prefix:
        bot.send_message(
            message.chat.id,
            "❌ Invalid! Numbers only (e.g. <code>880</code>, <code>91</code>). Try again.",
            parse_mode="HTML"
        )
        _cc_addrange_state[uid] = sid
        msg2 = bot.send_message(
            message.chat.id,
            f"📲 Enter range prefix for <b>{sid}</b>:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg2, _cc_addrange_step)
        return
    cfg = _console_config.setdefault(sid, {"enabled": True, "ranges": []})
    if prefix not in cfg["ranges"]:
        cfg["ranges"].append(prefix)
        save_console_config()
    c_name, flag = get_country_details(prefix)
    bot.send_message(
        message.chat.id,
        f"✅ Added <b>{_resolve_flag(flag)} {c_name} ({prefix})</b> to <b>{_v2_svc_emoji(sid)} {sid}</b>!",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    _admin_panel_last.pop(message.chat.id, None)
    _go_admin_panel(message)


# ── Edit Message Templates (combined with icon slots) ────────────────────────────

# Maps each template to its related icon slots (for combined edit menu)
_TEMPLATE_ICON_SLOT_MAP = {
    "otp_group":      ["otp_key", "otp_world", "otp_sms"],
    "otp_dm":         ["dm_number_pre", "dm_country_pre", "dm_country_post"],
    "otp_dm_v2":      ["dm_number_pre", "dm_country_pre", "dm_country_post"],
    "start":          ["start_header", "start_crown", "start_user", "start_id",
                       "start_status", "start_workers", "start_powered"],
    "verify_success": ["verify_title"],
    "number_assigned":[],
    "broadcast":      [],
}


def _show_edit_messages_menu(message, note=""):
    """Combined Message Edit menu: template text editor + per-template icon slots."""
    with _custom_emoji_lock:
        slots_set = dict(_custom_emojis.get("msg_slots", {}))

    markup = types.InlineKeyboardMarkup(row_width=2)
    lines = [
        "✏️ <b>Message Edit</b>\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "<i>Edit message text or set custom emoji icons:</i>"
    ]

    seen_slots: set = set()
    for key, label in _TEMPLATE_LABELS.items():
        lines.append(f"\n📄 <b>{label}</b>")
        markup.add(types.InlineKeyboardButton(f"✏️ Edit: {label}", callback_data=f"editmsg:{key}", style="danger"))

        icon_keys = _TEMPLATE_ICON_SLOT_MAP.get(key, [])
        for slot_key in icon_keys:
            if slot_key not in _MSG_ICON_SLOTS or slot_key in seen_slots:
                continue
            seen_slots.add(slot_key)
            default_char, slot_label = _MSG_ICON_SLOTS[slot_key]
            custom = slots_set.get(slot_key)
            if custom:
                fb = custom.get("fb", default_char)
                lines.append(f"  ✅ {fb} <i>{slot_label}</i>")
            else:
                lines.append(f"  🔘 {default_char} <i>{slot_label}</i>")
            markup.add(
                types.InlineKeyboardButton(f"✏️ {slot_label}", callback_data=f"msgicon_set:{slot_key}"),
                types.InlineKeyboardButton("🔄 Reset", callback_data=f"msgicon_reset:{slot_key}"),
            )

    markup.add(types.InlineKeyboardButton("🔄 Reset All to Default", callback_data="editmsg_reset_all", style="success"))
    text = "\n".join(lines)
    if note:
        text += f"\n\n✅ <i>{note}</i>"
    text += "\n\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>"
    try:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"[MSG-EDIT] Failed: {e}")


def _ask_new_template(call, key):
    import html as _html
    label = _TEMPLATE_LABELS.get(key, key)
    vars_hint = _TEMPLATE_VARS.get(key, "")
    current = get_template(key)
    # Escape HTML so tags inside the template don't break the <code> block display
    current_escaped = _html.escape(current[:600])
    uid = call.from_user.id
    _edit_template_state[uid] = {"key": key, "msg_id": call.message.message_id}
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    try:
        msg = bot.send_message(
            call.message.chat.id,
            f"✏️ <b>{label}</b>\n\n"
            f"📌 <b>Available variables:</b>\n<code>{vars_hint}</code>\n\n"
            f"📄 <b>Current format:</b>\n<code>{current_escaped}</code>\n\n"
            f"⬇️ <b>Enter new format:</b>\n"
            f"<i>(HTML tags supported: &lt;b&gt;, &lt;i&gt;, &lt;code&gt;, &lt;blockquote&gt; — sending a custom emoji directly also works to customize!)</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[TEMPLATE-ASK] ❌ Failed to send prompt for uid={uid}: {e}")
        try:
            msg = bot.send_message(
                call.message.chat.id,
                f"✏️ {label}\n\n⬇️ Enter new format:",
                reply_markup=_back_admin_kb(),
            )
        except Exception:
            return
    bot.register_next_step_handler(msg, _save_new_template)


def _message_to_html(message):
    """Convert message text + entities to HTML string.
    Preserves custom_emoji, bold, italic, code, blockquote etc.
    Also preserves manually typed <tg-emoji> or <b> HTML if no entities override.
    """
    import html as _html
    from collections import defaultdict
    text = message.text or ""
    entities = message.entities or []
    if not entities:
        return text
    chars = list(text)
    n = len(chars)
    opens = defaultdict(list)
    closes = defaultdict(list)
    for ent in sorted(entities, key=lambda e: (e.offset, -e.length)):
        o, l = ent.offset, ent.length
        etype = ent.type
        if etype == "bold":
            opens[o].append("<b>"); closes[o + l].append("</b>")
        elif etype == "italic":
            opens[o].append("<i>"); closes[o + l].append("</i>")
        elif etype == "underline":
            opens[o].append("<u>"); closes[o + l].append("</u>")
        elif etype == "strikethrough":
            opens[o].append("<s>"); closes[o + l].append("</s>")
        elif etype == "code":
            opens[o].append("<code>"); closes[o + l].append("</code>")
        elif etype == "pre":
            opens[o].append("<pre>"); closes[o + l].append("</pre>")
        elif etype == "blockquote":
            opens[o].append("<blockquote>"); closes[o + l].append("</blockquote>")
        elif etype == "custom_emoji":
            eid = getattr(ent, "custom_emoji_id", "") or ""
            opens[o].append(f'<tg-emoji emoji-id="{eid}">')
            closes[o + l].append("</tg-emoji>")
        elif etype == "text_link":
            url = _html.escape(getattr(ent, "url", "") or "")
            opens[o].append(f'<a href="{url}">')
            closes[o + l].append("</a>")
    result = []
    for i in range(n + 1):
        for tag in closes.get(i, []):
            result.append(tag)
        if i < n:
            for tag in opens.get(i, []):
                result.append(tag)
            result.append(chars[i])
    return "".join(result)


def _save_new_template(message):
    uid = message.from_user.id
    try:
        if _is_back(message.text):
            _edit_template_state.pop(uid, None)
            _admin_panel_last.pop(message.chat.id, None)
            _go_admin_panel(message)
            return
        if _intercept_menu_btn(message):
            _edit_template_state.pop(uid, None)
            return
        state = _edit_template_state.pop(uid, None)
        if not state:
            _admin_panel_last.pop(message.chat.id, None)
            _go_admin_panel(message)
            return
        key = state["key"]
        new_text = _message_to_html(message)
        if not new_text.strip():
            msg = bot.send_message(
                message.chat.id,
                "❌ Cannot be empty. Enter again:",
                reply_markup=_back_admin_kb(),
            )
            _edit_template_state[uid] = state
            bot.register_next_step_handler(msg, _save_new_template)
            return

        # ── Validate: only check for broken brace syntax, accept any {variable} ──
        class _PermissiveDict(dict):
            def __missing__(self, k):
                return f"{{{k}}}"
        _DUMMY_VARS = _PermissiveDict({
            "uname": "TestUser", "uid": "123456789",
            "svc": "INSTAGRAM", "number": "8801712345678",
            "tagged_number": "@+8801712345678", "taged_number": "@+8801712345678",
            "sms_body": "Your OTP is 123456",
            "country": "Bangladesh", "flag": "🇧🇩", "otp": "123456",
            "vname": "TestUser", "text": "Test broadcast",
        })
        try:
            new_text.format_map(_DUMMY_VARS)
        except (ValueError, IndexError) as fmt_err:
            msg = bot.send_message(
                message.chat.id,
                f"❌ <b>Template has an error!</b>\n\n"
                f"🔴 <b>Error:</b> <code>{fmt_err}</code>\n\n"
                f"⚠️ <b>Issue:</b> Wrong use of <code>{{</code> <code>}}</code>.\n\n"
                f"💡 If you need literal braces, double them: <code>{{{{</code> and <code>}}}}</code>\n\n"
                f"Enter again:",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            _edit_template_state[uid] = state
            bot.register_next_step_handler(msg, _save_new_template)
            return

        _templates[key] = new_text
        save_templates()
        label = _TEMPLATE_LABELS.get(key, key)
        # Reset rate limiter so admin panel shows immediately after save
        _admin_panel_last.pop(message.chat.id, None)
        _go_admin_panel(
            message,
            f"✅🔥 <b>Message updated!</b>\n\n"
            f"✏️ <b>{label}</b>\n\n"
            f"📄 New format saved.",
        )
    except Exception as e:
        print(f"[TEMPLATE-SAVE] ❌ Error for uid={uid}: {e}")
        try:
            bot.send_message(
                message.chat.id,
                f"❌ <b>Something went wrong!</b>\n<code>{e}</code>\n\nPlease try again.",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
        except Exception:
            pass


def _cancel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Cancel")
    return kb


def _back_admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin Panel")
    return kb


def _is_back(txt):
    return (txt or "").strip() in ("🔙 Admin Panel", "❌ Cancel")


_ALL_MENU_BTNS = {
    "☎️ 𝗩𝟭 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️", "☎️ 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️", "📡 𝗩𝟮 𝗖𝗼𝗻𝘀𝗼𝗹𝗲",
    "🔄 𝗩𝟮 𝗦𝗪𝗜𝗧𝗖𝗛", "🔴 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗚𝗘", "⌨️ 𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘", "🔙 𝗩𝟭 𝗦𝗪𝗜𝗧𝗖𝗛",
    "📊 𝗦𝗧𝗢𝗖𝗞", "📞 𝗦𝗔𝗣𝗢𝗥𝗧",
    "⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 ⚙️", "🔙 Main Menu",
    "𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱", "𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿",
    "𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁", "𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁",
    "𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁", "𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀", "𝗗𝗘𝗠𝗢 𝗢𝗧𝗣",
    "𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹", "𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹",
    "𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲", "𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲",
    "𝗣𝗮𝗻𝗲𝗹𝘀", "𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹", "👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻", "𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻",
    "𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗",
    "𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀", "𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀", "📡 𝗩𝟮 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗙𝗼𝗿𝗺𝗮𝘁", "𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁",
    "𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴", "𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀", "👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼", "𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂",
    "🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", "🔙 Admin Panel", "🔙 Admin Menu", "✨ 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗜𝗰𝗼𝗻𝘀",
    "🔘 Button Emoji Set", "🗑️ Button Emoji Del",
    "💬 Msg Emoji Set", "🗑️ Msg Emoji Del",
    "🖥️ Admin Btn Set", "🗑️ Admin Btn Del",
    "🏳️ Flag Emoji Set", "🎯 Service Emoji Set",
    "🌍 All Flags JSON Set", "📋 Flag JSON Export",
    "🔢 IDs Only Set", "🗑️ Flag Emoji Del",
    "🗑️ Service Emoji Del",
    "𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲",
    "🌐 𝗔𝘂𝗴𝗲𝘀𝘁𝗲𝗹 𝗞𝗲𝘆",
    "🔗 𝗥𝗲𝗳𝗳𝗲𝗿", "𝗥𝗲𝗳𝗳𝗲𝗿", "🔗 Set Refer Commission",
    "Buy Service",
    "𝗕𝘂𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲", "💎 Set Premium Price", "💰 Set VPN Price", "➕ Add VPN Service",
    "🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰",
    "🗑️ Remove VPN", "📨 Send User Message",
}


def _intercept_menu_btn(message):
    """If user pressed any known menu/admin button while in a step flow,
    route it to text_handler so it is handled correctly.
    Returns True if intercepted, False otherwise."""
    txt = (message.text or "").strip()
    if txt in _ALL_MENU_BTNS:
        text_handler(message)
        return True
    return False


def _admin_service_key_from_button(raw):
    """Resolve a displayed service label back to its exact configured key."""
    raw = (raw or "").strip()
    raw_plain = _strip_emoji(raw).casefold()
    raw_compact = re.sub(r"[^\w]+", "", raw_plain, flags=re.UNICODE)
    configured = _services or [
        {"key": k, "label": k.title()}
        for k in ["facebook", "instagram", "whatsapp", "telegram", "binance", "pc clone"]
    ]
    for svc in configured:
        key = str(svc.get("key", "")).strip().lower()
        label = _strip_emoji(
            str(svc.get("label", "")).split("→")[0].split("💎")[0]
        ).casefold()
        if raw_plain in {key.casefold(), label}:
            return key
        if raw_compact and raw_compact in {
            re.sub(r"[^\w]+", "", key.casefold(), flags=re.UNICODE),
            re.sub(r"[^\w]+", "", label, flags=re.UNICODE),
        }:
            return key
    return None


def process_auto_add(message):
    raw = (message.text or "").strip()
    if raw == "❌ Cancel":
        _go_admin_panel(message)
        return
    svc = _admin_service_key_from_button(raw)
    if not svc:
        msg = bot.send_message(
            message.chat.id,
            "⚠️ <b>Wrong service! Choose again:</b>",
            reply_markup=_admin_add_svc_keyboard(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, process_auto_add)
        return
    # A newly created service may not have a stock bucket yet. Create it
    # instead of rejecting the valid service or falling back to another key.
    stock.setdefault(svc, {})
    msg = bot.send_message(
        message.chat.id,
        f"🔥 <b>{svc.upper()}</b>\n\n"
        f"📝 <b>Enter Slot name:</b>\n"
        f"<i>Example: Mali 1, Germany 2, India 3</i>",
        reply_markup=_cancel_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, lambda m: ask_numbers_for_slot(m, svc))


def ask_numbers_for_slot(message, svc):
    slot_name = (message.text or "").strip()
    if slot_name == "❌ Cancel":
        _go_admin_panel(message)
        return
    if not slot_name:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter Slot name:",
            reply_markup=_cancel_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: ask_numbers_for_slot(m, svc))
        return
    msg = bot.send_message(
        message.chat.id,
        f"✅ Slot: <b>{slot_name}</b>\n\n"
        f"📊 Ekhon <b>{svc.upper()}</b> er number er Excel file pathao:\n"
        f"<i>(.xlsx / .xls / .csv — numbers should be in one column)</i>",
        reply_markup=_cancel_kb(),
        parse_mode="HTML",
    )
    _awaiting_slot_excel.add(message.from_user.id)
    bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))


def finalize_auto_add(message, svc, slot_name=None):
    global stock
    uid = message.from_user.id
    _awaiting_slot_excel.discard(uid)  # clear guard — document_handler will now ignore this UID
    if (message.text or "").strip() == "❌ Cancel":
        _go_admin_panel(message)
        return

    # ── Excel / CSV file upload ───────────────────────────────────────────────
    if message.document:
        doc = message.document
        fname = doc.file_name or "file"
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        if ext not in ("xlsx", "xls", "csv"):
            msg = bot.send_message(
                message.chat.id,
                "❌ Only send <b>.xlsx / .xls / .csv</b> files!\n\n"
                "📊 Try again — send the Excel file:",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))
            return
        wait = bot.send_message(message.chat.id, "⏳ Parsing file...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.edit_message_text(f"❌ File download hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return
        rows, mode = _parse_spreadsheet(raw, fname)
        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass
        if not rows:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ File-e kono number paini!\n"
                "Numbers in the Excel file should be in one column.\n\n"
                "📊 Try again — send the Excel file:",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))
            return
        # Extract number list from parsed rows
        if mode == "two_col":
            nums = [num for _, num in rows]
        else:
            nums = list(rows)
    else:
        # ── Text fallback (newline / comma) ───────────────────────────────────
        if not message.text:
            msg = bot.send_message(
                message.chat.id,
                "❌ Excel file pathao (.xlsx / .xls / .csv):",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))
            return
        nums = [n.strip() for n in re.split(r"[,\n\r]", message.text) if n.strip()]

    # ── Add numbers to stock ──────────────────────────────────────────────────
    _first_added_num = None
    if slot_name:
        if svc not in stock:
            stock[svc] = {}
        if slot_name not in stock[svc]:
            stock[svc][slot_name] = []
        added_count = 0
        for num in nums:
            clean = re.sub(r"\D", "", str(num))
            if clean:
                stock[svc][slot_name].append(clean)
                if _first_added_num is None:
                    _first_added_num = clean
                added_count += 1
    else:
        added_count = 0
        for num in nums:
            c_name, _ = get_country_details(num)
            if c_name == "Unknown":
                continue
            if c_name not in stock[svc]:
                stock[svc][c_name] = []
            stock[svc][c_name].append(num)
            if _first_added_num is None:
                _first_added_num = re.sub(r"\D", "", str(num))
            added_count += 1
    save_stock()
    # Notify all users about new numbers
    if added_count and _first_added_num:
        _nc, _nf = get_country_details(_first_added_num)
        if _nc == "Unknown":
            _nc, _nf = "UNKNOWN", "🌐"
        _notify_new_numbers(svc, _nc, _nf, added_count)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add More", "🔙 Admin Menu")
    bot.send_message(
        message.chat.id,
        f"✅🔥 <b>DONE!</b>\n\n"
        f"🗂 <b>Slot:</b> {slot_name or 'Auto'}\n"
        f"📱 <b>Added:</b> {added_count} number(s)",
        reply_markup=markup,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, "⬇️ Ki korbe?", parse_mode="HTML"),
        lambda m: _after_add_handler(m, svc),
    )


def _after_add_handler(message, last_svc):
    txt = (message.text or "").strip()
    if txt == "➕ Add More":
        msg = bot.send_message(
            message.chat.id,
            f"📝 <b>Enter new slot name:</b>\n<i>Example: Mali 2, Germany 3</i>",
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: ask_numbers_for_slot(m, last_svc))
    else:
        _go_admin_panel(message)


# ── Heartbeat / watchdog ───────────────────────────────────────────────────────



# ── Start ─────────────────────────────────────────────────────────────────────

try:
    requests.get(
        f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook?drop_pending_updates=true",
        timeout=10,
    )
    print("[START] Webhook cleared.")
except Exception as e:
    print(f"[START] Webhook clear failed: {e}")

time.sleep(3)

threading.Thread(target=panel1_monitor, daemon=True).start()
threading.Thread(target=panel2_monitor, daemon=True).start()
threading.Thread(target=panel3_monitor, daemon=True).start()
threading.Thread(target=panel4_monitor, daemon=True).start()
threading.Thread(target=panel5_monitor, daemon=True).start()
threading.Thread(target=panel6_monitor, daemon=True).start()
threading.Thread(target=demo_monitor, daemon=True).start()

_dedupe_dynamic_panels()
for _dp in _dynamic_panels:
    _start_dynamic_panel(_dp)
    print(f"[DYN] Loaded saved panel: {_dp['id']} ({_dp['host']})")

# ── Load builtin extra panels (hardcoded) ─────────────────────────────────────
_existing_bp_ids = {p["id"] for p in _dynamic_panels}
_existing_bp_keys = {(p.get("host", ""), p.get("username", ""), p.get("password", "")) for p in _dynamic_panels}
_new_builtins_added = False
for _bp in _BUILTIN_PANELS:
    _bp_key = (_bp.get("host", ""), _bp.get("username", ""), _bp.get("password", ""))
    if _bp["id"] not in _existing_bp_ids and _bp_key not in _existing_bp_keys:
        _dynamic_panels.append(_bp)
        _existing_bp_keys.add(_bp_key)
        _new_builtins_added = True
    _start_dynamic_panel(_bp)
    print(f"[BUILTIN] Loaded panel: {_bp['id']} ({_bp['host']} / {_bp['username']})")
# Always persist so new BUILTIN panels (like fastx1) survive across restarts
save_dynamic_panels()

# ── IVA SMS startup login check ───────────────────────────────────────────────
def _iva_startup_check():
    """After bot starts, try to login to IVA panel. If fails, notify admins."""
    time.sleep(15)  # wait for bot polling to start
    iva = _iva_find_panel()
    if not iva:
        return
    pid = iva["id"]
    # If already logged in (scraper exists), skip
    if _iva_scrapers.get(pid):
        return
    print(f"[IVA-STARTUP] Trying initial login for {pid}...")
    ok = _iva_login(iva)
    if ok:
        print(f"[IVA-STARTUP] ✅ IVA panel login OK")
        return
    # Login failed — notify all super admins (max once per 6 hours to avoid flooding)
    _iva_notify_flag = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".iva_notify_ts")
    _now_ts = time.time()
    _should_notify = True
    try:
        with open(_iva_notify_flag, "r") as _f:
            _last_notify = float(_f.read().strip())
            if _now_ts - _last_notify < 21600:  # 6 hours cooldown
                _should_notify = False
                print(f"[IVA-STARTUP] ❌ Login FAILED — skipping notify (cooldown active)")
    except Exception:
        pass

    if _should_notify:
        print(f"[IVA-STARTUP] ❌ IVA panel login FAILED — notifying admins")
        try:
            with open(_iva_notify_flag, "w") as _f:
                _f.write(str(_now_ts))
        except Exception:
            pass
        for admin_uid in SUPER_ADMIN_IDS:
            try:
                bot.send_message(
                    admin_uid,
                    "⚠️ <b>IVA SMS Panel (bp10) login hoi nai!</b>\n\n"
                    "Email/password login is blocked from Railway's IP (Cloudflare).\n\n"
                    "🍪 <b>Fix it using a cookie:</b>\n"
                    "1. Log in to <b>ivasms.com</b> in Chrome on your phone/PC\n"
                    "2. Open the browser's Developer Tools\n"
                    "   • PC: F12 → Application → Cookies → ivasms.com\n"
                    "   • Phone: Chrome menu → Desktop site, tahole F12\n"
                    "3. Copy the <code>laravel_session</code> cookie's value\n"
                    "4. Bot-e pathao: /ivacookie\n\n"
                    "<i>Command: <code>/ivacookie bp10</code></i>",
                    parse_mode="HTML",
                )
            except Exception as e:
                print(f"[IVA-STARTUP] Notify error for {admin_uid}: {e}")

threading.Thread(target=_iva_startup_check, daemon=True).start()


# ── Web helper cookie watcher ──────────────────────────────────────────────
import json as _json_mod

_IVA_COOKIE_PENDING_FILE = os.path.join(os.path.dirname(__file__), "iva_cookie_pending.txt")


def _iva_web_cookie_watcher():
    """Watches for cookie file written by the web helper page and applies it."""
    while True:
        try:
            if os.path.exists(_IVA_COOKIE_PENDING_FILE):
                with open(_IVA_COOKIE_PENDING_FILE, "r") as _f:
                    _data = _json_mod.load(_f)
                os.remove(_IVA_COOKIE_PENDING_FILE)
                _panel_id = _data.get("panel", "bp10")
                _cookie_str = _data.get("cookie", "").strip()
                if _cookie_str and "=" in _cookie_str:
                    print(f"[WEB-COOKIE] Got cookie for {_panel_id} via helper page")
                    # Update dynamic_panels
                    for _p in _dynamic_panels:
                        if _p["id"] == _panel_id:
                            _p["cookie_str"] = _cookie_str
                            save_dynamic_panels()
                            break
                    # Update BUILTIN_PANELS in-memory
                    for _p in _BUILTIN_PANELS:
                        if _p["id"] == _panel_id:
                            _p["cookie_str"] = _cookie_str
                            break
                    _iva_scrapers.pop(_panel_id, None)
                    # Try to reconnect
                    _panel_obj = _iva_find_panel(_panel_id)
                    if _panel_obj:
                        ok = _iva_login(_panel_obj)
                        status = "✅ Login SUCCESSFUL! OTPs will be sent to the group when they arrive." if ok else "❌ Cookie didn't work — try again."
                        print(f"[WEB-COOKIE] {_panel_id}: {status}")
                        for _admin in SUPER_ADMIN_IDS:
                            try:
                                bot.send_message(_admin,
                                    f"🍪 <b>Web Helper Cookie — {_panel_id}</b>\n{status}",
                                    parse_mode="HTML")
                            except Exception:
                                pass
        except Exception as _e:
            print(f"[WEB-COOKIE] Error: {_e}")
        time.sleep(10)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Buy Service: Helper Functions ──────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

def _show_buy_service_admin(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💎 Set Premium Price", "➕ Add VPN Service")
    markup.add("💰 Set VPN Price", "🗑️ Remove VPN")
    markup.add("📨 Send User Message")
    markup.add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟")
    prices = _buy_service_settings["premium_prices"]
    rate = _buy_service_settings.get("dollar_rate", 128)
    vpn_count = len(_buy_service_settings.get("vpn_services", []))
    bot.send_message(
        message.chat.id,
        f"🛒 <b>Buy Service Admin Panel</b>\n\n"
        f"💎 Premium Prices:\n"
        f"  • 3 Month: <b>{prices.get('3M', 0)} BDT</b>\n"
        f"  • 6 Month: <b>{prices.get('6M', 0)} BDT</b>\n"
        f"  • 1 Year:  <b>{prices.get('1Y', 0)} BDT</b>\n"
        f"  • Dollar Rate: <b>1$ = {rate} BDT</b>\n\n"
        f"🔒 VPN Services: <b>{vpn_count}</b> ta\n\n"
        f"Choose an option from below:",
        reply_markup=markup,
        parse_mode="HTML",
    )


def _show_vpn_remove_list(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    vpns = _buy_service_settings.get("vpn_services", [])
    if not vpns:
        bot.send_message(message.chat.id, "❌ Kono VPN service nei.")
        _show_buy_service_admin(message)
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, v in enumerate(vpns):
        emoji_id = v.get("emoji_id", "")
        name = v.get("name", "")
        dur = v.get("duration", "")
        price = v.get("price", 0)
        vid = v.get("id") or str(i)
        label = f"{name} | {dur} | {price} BDT"
        btn_kwargs = {"icon_custom_emoji_id": emoji_id} if emoji_id else {}
        markup.add(types.InlineKeyboardButton(
            f"🗑️ {label}", callback_data=f"buy_del_vpn:{vid}", style="danger", **btn_kwargs
        ))
    markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="buy_del_vpn:cancel"))
    bot.send_message(
        message.chat.id,
        "🗑️ <b>Remove VPN Service</b>\n\nKonTa remove korbe?",
        reply_markup=markup,
        parse_mode="HTML",
    )


def _show_vpn_price_list(message):
    """Show each VPN separately so an admin can edit one price at a time."""
    if message.from_user.id not in ADMIN_IDS:
        return
    vpns = _buy_service_settings.get("vpn_services", [])
    if not vpns:
        bot.send_message(message.chat.id, "❌ Kono VPN service nei.")
        _show_buy_service_admin(message)
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, vpn in enumerate(vpns):
        vid = str(vpn.get("id") or i)
        emoji_id = vpn.get("emoji_id", "")
        label = (
            f"{vpn.get('name', 'VPN')} | {vpn.get('duration', '')} | "
            f"{vpn.get('price', 0)} BDT"
        )
        btn_kwargs = {"icon_custom_emoji_id": emoji_id} if emoji_id else {}
        markup.add(types.InlineKeyboardButton(
            f"💰 {label}",
            callback_data=f"buy_set_vpn_price:{vid}",
            style="primary",
            **btn_kwargs,
        ))
    markup.add(types.InlineKeyboardButton(
        "❌ Cancel", callback_data="buy_set_vpn_price:cancel", style="danger"
    ))
    bot.send_message(
        message.chat.id,
        "💰 <b>Set VPN Price</b>\n\nKon VPN service-er price change korbe?",
        reply_markup=markup,
        parse_mode="HTML",
    )


def _buy_set_premium_step(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    parts = (message.text or "").strip().split()
    if len(parts) < 3:
        msg = bot.send_message(message.chat.id,
            "❌ Wrong format! Enter 3 values (3M 6M 1Y BDT):\n"
            "<i>Example: <code>650 1200 2000</code></i>",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_set_premium_step)
        return
    try:
        p3m = int(parts[0]); p6m = int(parts[1]); p1y = int(parts[2])
        rate = int(parts[3]) if len(parts) >= 4 else _buy_service_settings.get("dollar_rate", 128)
    except ValueError:
        msg = bot.send_message(message.chat.id,
            "❌ Enter numbers only!\n<i>Example: <code>650 1200 2000</code></i>",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_set_premium_step)
        return
    _buy_service_settings["premium_prices"] = {"3M": p3m, "6M": p6m, "1Y": p1y}
    _buy_service_settings["dollar_rate"] = rate
    save_buy_service_settings()
    bot.send_message(message.chat.id,
        f"✅ <b>Premium prices updated!</b>\n\n"
        f"• 3 Month: <b>{p3m} BDT</b>\n"
        f"• 6 Month: <b>{p6m} BDT</b>\n"
        f"• 1 Year:  <b>{p1y} BDT</b>\n"
        f"• Dollar Rate: <b>1$ = {rate} BDT</b>",
        parse_mode="HTML")
    _show_buy_service_admin(message)


def _buy_set_vpn_price_step(message, vpn_id):
    """Validate and persist the price for the selected VPN only."""
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _show_buy_service_admin(message)
        return
    if _intercept_menu_btn(message):
        return
    raw_price = (message.text or "").strip()
    try:
        price = int(raw_price)
        if price < 0:
            raise ValueError
    except ValueError:
        prompt = bot.send_message(
            message.chat.id,
            "❌ Price must be a whole number (0 or more BDT):",
            reply_markup=_back_admin_kb(),
        )
        bot.register_next_step_handler(
            prompt, lambda m, vid=vpn_id: _buy_set_vpn_price_step(m, vid)
        )
        return

    selected = None
    for vpn in _buy_service_settings.get("vpn_services", []):
        if str(vpn.get("id", "")) == str(vpn_id):
            selected = vpn
            break
    if selected is None:
        bot.send_message(
            message.chat.id,
            "❌ Ei VPN service-ti আর নেই. List abar open korun.",
        )
        _show_buy_service_admin(message)
        return

    selected["price"] = price
    save_buy_service_settings()
    bot.send_message(
        message.chat.id,
        f"✅ <b>{selected.get('name', 'VPN')}</b> price updated: "
        f"<b>{price} BDT</b>",
        parse_mode="HTML",
    )
    _show_buy_service_admin(message)


def _buy_add_vpn_step(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    parts = (message.text or "").strip().split()
    if len(parts) < 4:
        msg = bot.send_message(message.chat.id,
            "❌ Wrong format!\n"
            "<code>EMOJI_ID NAME DURATION PRICE_BDT</code>\n"
            "<i>Example: <code>5334944492300573096 NORD 7D 300</code></i>",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_add_vpn_step)
        return
    try:
        emoji_id = parts[0]
        price = int(parts[-1])
        duration = parts[-2]
        name = " ".join(parts[1:-2])
    except ValueError:
        msg = bot.send_message(message.chat.id,
            "❌ Price must be numbers only!",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_add_vpn_step)
        return
    # Validate: emoji_id must be numeric (Telegram custom emoji ID)
    if not emoji_id.strip().isdigit():
        msg = bot.send_message(message.chat.id,
            "❌ <b>Wrong format!</b> EMOJI_ID must be numbers only (Telegram custom emoji ID).\n\n"
            "Sothik format:\n"
            "<code>EMOJI_ID NAME DURATION PRICE_BDT</code>\n\n"
            "Example:\n"
            "<code>5334944492300573096 NORD 7D 300</code>\n\n"
            "⚠️ The first value should be the Emoji ID (digits only), then name, duration, price.",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_add_vpn_step)
        return
    if not name.strip():
        msg = bot.send_message(message.chat.id,
            "❌ VPN name daw!",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_add_vpn_step)
        return
    vpn_id = f"vpn_{int(time.time() * 1000)}"
    new_svc = {"id": vpn_id, "emoji_id": emoji_id, "name": name, "duration": duration, "price": price}
    _buy_service_settings.setdefault("vpn_services", []).append(new_svc)
    save_buy_service_settings()
    bot.send_message(message.chat.id,
        f"✅ <b>VPN added!</b>\n"
        f"Name: <b>{name}</b> | Duration: <b>{duration}</b> | Price: <b>{price} BDT</b>",
        parse_mode="HTML")
    _show_buy_service_admin(message)


def _buy_send_ask_uid_step(message):
    uid = message.from_user.id
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw = re.sub(r"\D", "", (message.text or "").strip())
    if not raw:
        msg = bot.send_message(message.chat.id,
            "❌ Enter a valid Chat ID (only numbers).",
            reply_markup=_back_admin_kb(), parse_mode="HTML")
        bot.register_next_step_handler(msg, _buy_send_ask_uid_step)
        return
    target_uid = int(raw)
    _admin_dmu_state[uid] = target_uid
    msg = bot.send_message(
        message.chat.id,
        f"✅ Target: <code>{target_uid}</code>\n\n"
        f"📝 Now send the message content (text, photo, video all accepted):\n"
        f"To use a custom emoji, write the emoji ID in the message.\n\n"
        f"🔙 Back: Press the <b>Admin Panel</b> button.",
        reply_markup=_back_admin_kb(), parse_mode="HTML")
    bot.register_next_step_handler(msg, _buy_send_msg_step)


def _buy_send_msg_step(message):
    uid = message.from_user.id
    if _is_back(message.text):
        _admin_dmu_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        _admin_dmu_state.pop(uid, None)
        return
    target_uid = _admin_dmu_state.pop(uid, None)
    if not target_uid:
        _go_admin_panel(message)
        return

    def _resolve_custom_emoji_in_text(text):
        """Replace bare 18-19 digit IDs in text with tg-emoji tags."""
        import re as _re2
        def _repl(m):
            eid = m.group(1)
            return f'<tg-emoji emoji-id="{eid}">⭐</tg-emoji>'
        return _re2.sub(r'(?<![/\d])(\d{18,19})(?![\d])', _repl, text or "")

    try:
        if message.photo:
            cap = _resolve_custom_emoji_in_text(message.caption or "")
            bot.send_photo(target_uid, message.photo[-1].file_id,
                           caption=cap or None, parse_mode="HTML" if cap else None)
        elif message.video:
            cap = _resolve_custom_emoji_in_text(message.caption or "")
            bot.send_video(target_uid, message.video.file_id,
                           caption=cap or None, parse_mode="HTML" if cap else None)
        elif message.document:
            cap = _resolve_custom_emoji_in_text(message.caption or "")
            bot.send_document(target_uid, message.document.file_id,
                              caption=cap or None, parse_mode="HTML" if cap else None)
        elif message.sticker:
            bot.send_sticker(target_uid, message.sticker.file_id)
        elif message.voice:
            bot.send_voice(target_uid, message.voice.file_id)
        elif message.animation:
            cap = _resolve_custom_emoji_in_text(message.caption or "")
            bot.send_animation(target_uid, message.animation.file_id,
                               caption=cap or None, parse_mode="HTML" if cap else None)
        elif message.text:
            txt_out = _resolve_custom_emoji_in_text(message.text)
            bot.send_message(target_uid, txt_out, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Ei content type support hoi na.")
            return
        bot.send_message(message.chat.id,
            f"✅ Message sent to <code>{target_uid}</code>!", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Pathano jay ni: <code>{e}</code>", parse_mode="HTML")
    _show_buy_service_admin(message)


@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    uid = message.from_user.id
    # Screenshot from user who is awaiting payment confirmation
    if uid in _buy_pending:
        pending = _buy_pending.pop(uid)
        svc_type = pending.get("type", "")
        file_id = message.photo[-1].file_id

        if svc_type == "premium":
            # For Telegram Premium: ask which account will receive it
            _buy_screenshot_pending[uid] = {"file_id": file_id, "pending": pending}
            msg = bot.send_message(
                message.chat.id,
                '<tg-emoji emoji-id="5314504236132747481">✅</tg-emoji> <b>Screenshot peyechi!</b> <tg-emoji emoji-id="5314504236132747481">✅</tg-emoji>\n\n'
                '<tg-emoji emoji-id="5269215244810491516">📲</tg-emoji> Kon Telegram account-e Premium nibe?\n'
                "<b>Username or Phone number:</b>\n\n"
                "<i>Example: <code>@username</code> or <code>+8801XXXXXXXXX</code></i>",
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _buy_premium_tg_username_step)
        else:
            # For VPN: notify admins directly
            _notify_admins_screenshot(uid, message.from_user, file_id, pending, tg_target=None)
        return
    # If admin, ignore
    if uid in ADMIN_IDS:
        return


def _notify_admins_screenshot(uid, from_user, file_id, pending, tg_target):
    """Send payment screenshot — guaranteed delivery to PRIMARY_BUY_ADMIN with retry."""
    PRIMARY_BUY_ADMIN = 6664150885  # Must NEVER miss this inbox

    uname = from_user.username
    fname = from_user.first_name or ""
    user_info = f"@{uname}" if uname else fname or str(uid)
    service_label = pending.get("label", "Unknown")
    price = pending.get("price", 0)
    order_id = f"order_{int(time.time() * 1000)}_{uid}"

    tg_line = f"📲 Premium For: <b>{tg_target}</b>\n" if tg_target else ""
    caption = (
        f"📸 <b>PAYMENT SCREENSHOT</b>\n\n"
        f"👤 User: {user_info}\n"
        f"🆔 Chat ID: <code>{uid}</code>\n"
        f"📦 Service: <b>{service_label}</b>\n"
        f"💰 Price: <b>{price} BDT</b>\n"
        f"{tg_line}"
        f"✅ Verify korar por user-ke service pathao."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📨 Send Message to User",
        callback_data=f"admin_dmu:{uid}",
        style="primary",
    ))
    markup.add(types.InlineKeyboardButton(
        "✅ Order Complete",
        callback_data=f"order_complete:{uid}:{order_id}",
        style="success",
    ))

    # ── Save order to backup log (disk) so no order is ever lost ──────────────
    try:
        import json as _json_bs, os as _os_bs
        _order_log = "buy_orders_log.json"
        _orders = []
        if _os_bs.path.exists(_order_log):
            try:
                with open(_order_log, "r") as _f:
                    _orders = _json_bs.load(_f)
            except Exception:
                _orders = []
        _orders.append({
            "order_id": order_id,
            "ts": time.time(),
            "user_id": uid,
            "user_info": user_info,
            "service": service_label,
            "price": price,
            "tg_target": tg_target,
            "file_id": file_id,
            "status": "pending",
        })
        with open(_order_log, "w") as _f:
            _json_bs.dump(_orders, _f, ensure_ascii=False)
    except Exception as _log_err:
        print(f"[BUY-LOG] Could not write order log: {_log_err}")

    # ── Send to PRIMARY_BUY_ADMIN with 3 retries ───────────────────────────────
    _primary_ok = False
    for _attempt in range(1, 4):
        try:
            bot.send_photo(
                PRIMARY_BUY_ADMIN, file_id,
                caption=caption, parse_mode="HTML", reply_markup=markup,
            )
            _primary_ok = True
            print(f"[BUY-ORDER] ✅ Sent to primary admin {PRIMARY_BUY_ADMIN} (attempt {_attempt})")
            break
        except Exception as _e:
            print(f"[BUY-ORDER] ❌ Attempt {_attempt}/3 failed for primary admin {PRIMARY_BUY_ADMIN}: {_e}")
            if _attempt < 3:
                time.sleep(2)

    # ── If photo failed all 3 times, send text fallback ───────────────────────
    if not _primary_ok:
        try:
            fallback_text = (
                f"⚠️ <b>NEW BUY ORDER (photo send failed — manual check needed)</b>\n\n"
                f"👤 User: {user_info}\n"
                f"🆔 Chat ID: <code>{uid}</code>\n"
                f"📦 Service: <b>{service_label}</b>\n"
                f"💰 Price: <b>{price} BDT</b>\n"
                f"{tg_line}"
                f"📎 File ID: <code>{file_id}</code>"
            )
            bot.send_message(PRIMARY_BUY_ADMIN, fallback_text, parse_mode="HTML", reply_markup=markup)
            print(f"[BUY-ORDER] ⚠️ Text fallback sent to primary admin {PRIMARY_BUY_ADMIN}")
        except Exception as _fe:
            print(f"[BUY-ORDER] 🚨 CRITICAL: Could not reach primary admin {PRIMARY_BUY_ADMIN} at all: {_fe}")

    # ── Send to other super admins (best-effort, no retry) ────────────────────
    for admin_uid in SUPER_ADMIN_IDS:
        if admin_uid == PRIMARY_BUY_ADMIN:
            continue
        try:
            bot.send_photo(
                admin_uid, file_id,
                caption=caption, parse_mode="HTML", reply_markup=markup,
            )
        except Exception as _e:
            print(f"[BUY-ORDER] Could not send to secondary admin {admin_uid}: {_e}")

    bot.send_message(
        uid,
        '<tg-emoji emoji-id="5395695537687123235">✅</tg-emoji> <b>Screenshot sent!</b> <tg-emoji emoji-id="5395695537687123235">✅</tg-emoji>\n\n'
        '<tg-emoji emoji-id="5253742260054409879">✅</tg-emoji> Admin will review and send the service soon. Thank you! <tg-emoji emoji-id="5379643836152684738">🙏</tg-emoji>',
        parse_mode="HTML",
    )


def _buy_premium_tg_username_step(message):
    """Receive target Telegram username/phone for premium, then notify admins."""
    uid = message.from_user.id
    if _intercept_menu_btn(message):
        _buy_screenshot_pending.pop(uid, None)
        return
    raw = (message.text or "").strip()
    if not raw:
        msg = bot.send_message(
            message.chat.id,
            "❌ Username or Phone number:\n"
            "<i>Example: <code>@username</code> or <code>+8801XXXXXXXXX</code></i>",
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_premium_tg_username_step)
        return
    saved = _buy_screenshot_pending.pop(uid, None)
    if not saved:
        return
    _notify_admins_screenshot(uid, message.from_user, saved["file_id"], saved["pending"], tg_target=raw)


threading.Thread(target=_iva_web_cookie_watcher, daemon=True).start()

print("🔥 AR OTP BOT is running with 15-PANEL AUTO OTP MONITOR... 🔥")
print("   ▸ Panel 1: Mahofuza        (91.232.105.47)")
print("   ▸ Panel 2: Sagardas50      (94.23.31.29)")
print("   ▸ Panel 3: Rabbi1_FD       (168.119.13.175)")
print("   ▸ Panel 4: Rabbi12         (144.217.71.192)")
print("   ▸ Panel 5: Rabbi12_v2      (51.75.144.178)")
print("   ▸ Panel 6: TrueSMS/Ranges  (truesms.net)")
print("   ▸ BP1: Mahofuza12          (139.99.69.196)")
print("   ▸ BP2: Rabbi12             (139.99.9.4)")
print("   ▸ BP3: Rabbi12             (54.36.173.235)")
print("   ▸ BP4: Rabbi5              (54.39.104.241)")
print("   ▸ BP14: Rabbi5             (54.39.104.241) [OTP]")
print("   ▸ BP5: mahofuza            (213.32.24.208)")
print("   ▸ BP6: Rabbi200            (15.235.182.3 /konekta)")
print("   ▸ BP7: Rabbi12             (nexor-iprn.com)")
print("   ▸ BP8: Rabbi12             (51.77.52.79)")
print("   ▸ BP9: Dasbabu50_FD        (51.210.208.26)")
print("   ▸ BP10: mdrashub2          (ivasms.com)")
print("   ▸ BP11: Rabbi12            (139.99.68.231)")


def _clear_webhook():
    try:
        requests.get(
            f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook?drop_pending_updates=true",
            timeout=10,
        )
    except Exception:
        pass


while True:
    try:
        _clear_webhook()
        time.sleep(3)
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            allowed_updates=["message", "callback_query"],
            none_stop=True,
            restart_on_change=False,
        )
    except requests.exceptions.ReadTimeout:
        print("[POLLING] ReadTimeout — restarting in 5s...")
        time.sleep(5)
    except requests.exceptions.ConnectionError:
        print("[POLLING] ConnectionError — restarting in 10s...")
        time.sleep(10)
    except Exception as e:
        err_str = str(e)
        if "409" in err_str or "Conflict" in err_str:
            print("[POLLING] 409 Conflict (another instance running) — waiting 30s...")
            time.sleep(30)
        else:
            print(f"[POLLING] Error: {e} — restarting in 5s...")
            time.sleep(5)


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

    # V2 live range buttons.  Keep each range as its own button; when the
    # country repeats, add a stable occurrence number so two Laos ranges do
    # not look like the same choice.
    v2_rows = []
    country_totals = {}
    for prefix in cfg.get("ranges", []):
        c_name, flag = get_country_details(prefix)
        if c_name and c_name not in ("Unknown", ""):
            country_name = c_name
        else:
            country_name = "Unknown Country"
        country_totals[country_name] = country_totals.get(country_name, 0) + 1
        v2_rows.append((prefix, country_name, flag))

    country_seen = {}
    for prefix, country_name, flag in v2_rows:
        country_seen[country_name] = country_seen.get(country_name, 0) + 1
        label = (
            f"{country_name} {country_seen[country_name]}"
            if country_totals[country_name] > 1
            else country_name
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
    ranges = list(cfg.get("ranges", []))
    country_totals = {}
    range_rows = []
    for prefix in ranges:
        c_name, flag = get_country_details(prefix)
        country_name = c_name if c_name and c_name not in ("Unknown", "") else "Unknown Country"
        country_totals[country_name] = country_totals.get(country_name, 0) + 1
        range_rows.append((prefix, country_name, flag))
    country_seen = {}
    for prefix, country_name, flag in range_rows:
        country_seen[country_name] = country_seen.get(country_name, 0) + 1
        country_label = (
            f"{country_name} {country_seen[country_name]}"
            if country_totals[country_name] > 1
            else country_name
        )
        rlabel = f"🗑️ {country_label} ({prefix})"
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
    refresh_kb = _build_numbers_display_kb(
        matched_sid.lower(), c_name, display_nums_cr, flag, c_name,
        is_v2=True, v2_prefix=matched_prefix, v2_sid=matched_sid
    )
    bot.send_message(
        message.chat.id,
        ".",
        reply_markup=refresh_kb,
    )
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


# ── Menus ─────────────────────────────────────────────────────────────────────


def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    _gn_text, _gn_icon = _btn_text_and_icon("get_number", "📲 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥")
    markup.add(types.KeyboardButton(_gn_text, style="success", **_gn_icon))
    _sp_text, _sp_icon = _btn_text_and_icon("saport", "📞 𝗦𝗔𝗣𝗢𝗥𝗧")
    _bl_text, _bl_icon = _btn_text_and_icon("balance", "💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲")
    markup.add(types.KeyboardButton(_sp_text, style="danger", **_sp_icon),
               types.KeyboardButton(_bl_text, style="primary", **_bl_icon))
    _dv_text, _dv_icon = _btn_text_and_icon("developer", "👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼")
    _wd_text, _wd_icon = _btn_text_and_icon("withdraw", "💸 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄")
    markup.add(types.KeyboardButton(_dv_text, style="success", **_dv_icon),
               types.KeyboardButton(_wd_text, style="danger", **_wd_icon))
    _rf_text, _rf_icon = _btn_text_and_icon("refer", "🔗 𝗥𝗲𝗳𝗳𝗲𝗿")
    markup.row(
        types.KeyboardButton(_rf_text, style="primary", **_rf_icon),
        types.KeyboardButton("Buy Service", style="success", icon_custom_emoji_id="5251467997561778767"),
    )
    if user_id in ADMIN_IDS:
        _ap_text, _ap_icon = _btn_text_and_icon("admin_panel", "⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 ⚙️")
        markup.add(types.KeyboardButton(_ap_text, style="primary", **_ap_icon))
    return markup


def v2_switch_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🔴 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗚𝗘"))
    markup.add(types.KeyboardButton("⌨️ 𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘"))
    markup.add(types.KeyboardButton("🔙 𝗩𝟭 𝗦𝗪𝗜𝗧𝗖𝗛"))
    return markup


def save_services():
    save_json(SERVICES_FILE, _services)
    _sync_settings_to_botpy()


def _get_svc_map():
    return {s["label"]: s["key"] for s in _services}


SERVICE_BUTTON_MAP = {}


def _v1_build_service_markup():
    """Build V1 service list as inline keyboard — only shows services that have stock.
    Shows all services from _services list that have stock, PLUS any stock key that
    has numbers but is not in _services (e.g. telegram added manually)."""
    _STYLES = ["success", "primary", "danger"]
    btns = []
    idx = 0
    seen_keys = set()

    # First: services defined in _services (preserves ordering/labels)
    for svc_info in _services:
        label = _strip_emoji(svc_info.get("label", ""))
        key   = svc_info.get("key", "")
        total = sum(len(v) for v in stock.get(key, {}).values())
        if not total:
            seen_keys.add(key)
            continue
        seen_keys.add(key)
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    # Second: any stock key with numbers NOT already listed above
    for key, country_map in stock.items():
        if key in seen_keys:
            continue
        total = sum(len(v) for v in country_map.values())
        if not total:
            continue
        label = key.title()  # e.g. "telegram" → "Telegram"
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    markup = types.InlineKeyboardMarkup(row_width=1)
    for btn in btns:
        markup.add(btn)
    return markup, bool(btns)


def _build_combined_service_markup():
    """Build combined V1 (stock) + V2 (live console) service buttons in one markup."""
    _STYLES = ["success", "primary", "danger"]
    btns = []
    idx = 0
    seen_keys = set()

    # Collect enabled V2 service keys (lowercase) to suppress duplicate V1 buttons
    _v2_enabled_keys = {
        sid.lower() for sid in _CONSOLE_SVC_NAMES
        if _console_config.get(sid, {}).get("enabled") and _console_config.get(sid, {}).get("ranges")
    }

    # V1 stock services (skip any that already have a V2 counterpart)
    for svc_info in _services:
        label = _strip_emoji(svc_info.get("label", ""))
        key   = svc_info.get("key", "")
        total = sum(len(v) for v in stock.get(key, {}).values())
        seen_keys.add(key)
        if not total:
            continue
        if key.lower() in _v2_enabled_keys:
            continue  # V2 already covers this service (manual numbers merged there)
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    for key, country_map in stock.items():
        if key in seen_keys:
            continue
        total = sum(len(v) for v in country_map.values())
        if not total:
            continue
        if key.lower() in _v2_enabled_keys:
            continue  # V2 already covers this service
        label = key.title()
        _icon_id = _svc_icon_emoji_id(key)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            label,
            callback_data=f"v1svc:{key}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    # V2 live console services
    for sid in _CONSOLE_SVC_NAMES:
        cfg = _console_config.get(sid, {})
        if not cfg.get("enabled"):
            continue
        if not cfg.get("ranges"):
            continue
        _icon_id = _svc_icon_emoji_id(sid)
        _btn_kwargs = {"icon_custom_emoji_id": _icon_id} if _icon_id else {}
        btns.append(types.InlineKeyboardButton(
            f"{sid}",
            callback_data=f"v2svc_cc:{sid}",
            style=_STYLES[idx % len(_STYLES)],
            **_btn_kwargs
        ))
        idx += 1

    markup = types.InlineKeyboardMarkup(row_width=1)
    for btn in btns:
        markup.add(btn)
    return markup, bool(btns)


def show_services(message):
    markup, has_btns = _build_combined_service_markup()
    if not has_btns:
        bot.send_message(
            message.chat.id,
            "❌ <b>No stock available in any service.</b>\nPlease notify the admin.",
            parse_mode="HTML",
        )
        return
    bot.send_message(
        message.chat.id,
        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
        reply_markup=markup,
        parse_mode="HTML",
    )


def show_countries(chat_id, svc):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    if svc in stock:
        for cnt, nums in stock[svc].items():
            if nums:
                _, flag = get_country_details(nums[0])
                btns.append(
                    types.InlineKeyboardButton(
                        f"{cnt}", callback_data=f"n:{svc}:{cnt}", style="primary",
                        **_flag_btn_kwargs(flag)
                    )
                )
    if btns:
        markup.add(*btns)
    markup.add(
        types.InlineKeyboardButton("⬅️ 𝗕𝗮𝗰𝗸", callback_data="back_to_services", style="danger")
    )
    bot.send_message(
        chat_id,
        "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b>",
        reply_markup=markup,
        parse_mode="HTML",
    )


# ── Handlers ──────────────────────────────────────────────────────────────────


@bot.message_handler(commands=["start"])
def start_cmd(message):
    u = message.from_user
    # ── Referral handling — check BEFORE register_user so we know if new ──────
    _is_new_user = message.chat.id not in users
    _payload = (message.text or "").split(None, 1)[1].strip() if len((message.text or "").split(None, 1)) > 1 else ""
    if _is_new_user and _payload.startswith("ref") and _payload[3:].isdigit():
        _referrer_uid = int(_payload[3:])
        if _referrer_uid != message.from_user.id:
            _claimed = False
            with _referrals_lock:
                if str(message.from_user.id) not in _referrals:
                    _referrals[str(message.from_user.id)] = _referrer_uid
                    _claimed = True
            if _claimed:
                _save_referrals()
                _commission = get_refer_commission()
                _cur = get_currency()
                _new_bal = add_reward(_referrer_uid, _commission)
                try:
                    bot.send_message(
                        _referrer_uid,
                        f'<tg-emoji emoji-id="5267041999948653482">🔗</tg-emoji> <b>Referral Commission!</b>\n\n'
                        f'👤 Ekjon new user tomar link diye join korecho!\n'
                        f'💰 Commission: <b>+{_cur}{_commission:.2f}</b>\n'
                        f'💳 New Balance: <code>{_cur}{_new_bal:.2f}</code>',
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
    register_user(
        message.chat.id,
        first_name=u.first_name or "",
        last_name=u.last_name or "",
        username=u.username or "",
    )
    import html as _html
    uname = f"@{u.username}" if u.username else (u.first_name or "User")
    uname = _html.escape(str(uname))
    uid_str = _html.escape(str(u.id))
    markup = types.InlineKeyboardMarkup()
    _grp = get_otp_group_link() or CHANNEL_1
    if _grp:
        _sog_text, _sog_icon = _btn_text_and_icon("start_otp_group", "🔥 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽 𝗝𝗢𝗜𝗡 🔥")
        markup.add(types.InlineKeyboardButton(_sog_text, url=_grp, style="success", **_sog_icon))
    if get_channel2():
        _sch_text, _sch_icon = _btn_text_and_icon("start_channel", "📢 𝗠𝗮𝗶𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗝𝗢𝗜𝗡 📢")
        markup.add(types.InlineKeyboardButton(_sch_text, url=get_channel2(), style="primary", **_sch_icon))
    _sv_text, _sv_icon = _btn_text_and_icon("start_verify", "✅ 𝗩𝗘𝗥𝗜𝗙𝗬 𝗞𝗢𝗥𝗢 ✅")
    markup.add(types.InlineKeyboardButton(_sv_text, callback_data="v", style="danger", **_sv_icon))
    class _SS(dict):
        def __missing__(self, k): return f"{{{k}}}"
    bot.send_message(
        message.chat.id,
        get_template("start").format_map(_SS(uname=uname, uid=uid_str, **_msg_emoji_vars())),
        reply_markup=markup,
        parse_mode="HTML",
    )


@bot.message_handler(commands=["test"])
def test_cmd(message):
    fake_otp = str(random.randint(100000, 999999))
    fake_number = "8801712345678"
    fake_svc = "Instagram"
    fake_secs = 12
    fake_sms = f"Your Instagram code is {fake_otp}. Don't share this code."
    # Preview with GROUP format (force_group_fmt=True) so admin sees the exact group message
    bot.send_message(message.chat.id, "👁 <b>Group Format Preview:</b>", parse_mode="HTML")
    send_otp_message(message.chat.id, fake_otp, fake_number, fake_secs, fake_svc, fake_sms, force_group_fmt=True)
    try:
        send_otp_message(get_otp_group_id(), fake_otp, fake_number, fake_secs, fake_svc, fake_sms)
        bot.send_message(
            message.chat.id, "✅ Sent to group as well!", parse_mode="HTML"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ Group-e pathate parina: <code>{e}</code>",
            parse_mode="HTML",
        )


@bot.message_handler(commands=["panels"])
def panels_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    with _stats_lock:
        stats = {k: dict(v) for k, v in _panel_stats.items()}
    lines = ""
    for pid in ["p1", "p2", "p3", "p4", "p5", "p6"]:
        s = stats.get(pid, {})
        if s.get("last"):
            ago = int(time.time() - s["last"])
            last_str = f"{ago}s ago"
        else:
            last_str = "never"
        err_str = f"  ⚠️ {s['errors']} err" if s.get("errors") else ""
        lines += (
            f"{s.get('status', '⏳')} <b>{s.get('name', '?')}</b>\n"
            f"   🌐 <code>{s.get('host', '?')}</code>\n"
            f"   📊 {s.get('count', 0)} records  •  🕐 {last_str}{err_str}\n\n"
        )
    with _demo_lock:
        demo_on = _demo_active
    demo_str = "🟢 Running" if demo_on else "🔴 Stopped"
    bot.send_message(
        message.chat.id,
        f"📡 <b>PANEL STATUS</b>\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"{lines}"
        f"🎭 <b>Demo OTP:</b>  {demo_str}\n\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        f"🔄 <i>Updates every {POLL_INTERVAL}s</i>",
        parse_mode="HTML",
    )
    caller_uid = message.from_user.id
    # Super admin sees all, others see only their own panels
    dp_copy = [
        p for p in _dynamic_panels
        if is_super_admin(caller_uid) or p.get("admin_id") == caller_uid
    ]
    if dp_copy:
        dp_lines = ""
        for p in dp_copy:
            pid = p["id"]
            with _stats_lock:
                s = _panel_stats.get(pid, {})
            st = s.get("status", "⏳")
            cnt = s.get("count", 0)
            err = s.get("errors", 0)
            t = s.get("last")
            last_str = f"{int(time.time() - t)}s ago" if t else "never"
            err_str = f"  ⚠️ {err} err" if err else ""
            dp_lines += (
                f"{st} <b>{p.get('username', '?')}</b> <code>[{pid}]</code>\n"
                f"   🌐 <code>{p.get('host', '?')}</code>\n"
                f"   📊 {cnt} records  •  🕐 {last_str}{err_str}\n\n"
            )
        bot.send_message(
            message.chat.id,
            f"📡 <b>DYNAMIC PANELS</b>\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"{dp_lines}"
            f"💡 <i>Use /addpanel to add a new panel</i>",
            parse_mode="HTML",
        )
    else:
        bot.send_message(
            message.chat.id,
            "📋 <b>Tomar kono dynamic panel nei.</b>\n\n"
            "💡 <i>Use /addpanel to add a new panel.</i>",
            parse_mode="HTML",
        )


@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(
        message.chat.id,
        "✍️ <b>Send broadcast content:</b>\n\n"
        "📝 Text, 🖼️ Photo, 🎥 Video, 🎭 Sticker,\n"
        "🎞️ GIF, 🎵 Audio, 🎤 Voice, 📎 Document — all accepted!\n\n"
        "✨ <b>If you want to use a Custom Emoji:</b>\n"
        "Text-er jetukute emoji boshaite chao, sekhane emoji ID lekho:\n"
        "<code>5976350888195791241 Guinea 5319160079465857105 Instagram Method 5325684684544289988</code>\n"
        "<i>Wherever you place the ID, the custom emoji will render there</i>\n\n"
        "🔙 Press the <b>Admin Panel</b> button to go back.",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, do_broadcast)


def _clr_service_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    services = [
        ("facebook", "💬"),
        ("instagram", "📸"),
        ("whatsapp", "📱"),
        ("telegram", "✈️"),
        ("binance", "🪙"),
        ("pc clone", "💻"),
    ]
    for svc, icon in services:
        total = sum(len(v) for v in stock.get(svc, {}).values())
        markup.add(
            types.InlineKeyboardButton(
                f"{icon} {svc.upper()} ({total})", callback_data=f"clr_s:{svc}", style="success"
            )
        )
    markup.add(types.InlineKeyboardButton(" Clear ALL Stock", callback_data="clr_all", style="primary"))
    return markup


@bot.message_handler(commands=["addpanel"])
def addpanel_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    _show_addpanel_type_select(message.chat.id, message.from_user.id)


def _show_addpanel_type_select(chat_id, uid):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔑 Add with Username + Password", callback_data="aptype:pass", style="danger"),
        types.InlineKeyboardButton("🗝️ Add with API Key", callback_data="aptype:apikey", style="success"),
    )
    bot.send_message(
        chat_id,
        "🔧🔥 <b>ADD NEW PANEL</b> 🔥🔧\n\n"
        "How do you want to add the panel?\n\n"
        "🔑 <b>Username + Password</b> — login and add\n"
        "🗝️ <b>API Key</b> — add using panel API key",
        reply_markup=markup,
        parse_mode="HTML",
    )


def _ap_get_url(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addpanel_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    url = (message.text or "").strip()

    # Use the universal base extractor — handles ANY path prefix (/konekta, /ints, etc.)
    base_url = _extract_panel_base_url(url) if re.match(r"https?://", url, re.IGNORECASE) else None

    if not base_url:
        msg = bot.send_message(
            message.chat.id,
            "❌ <b>Enter a valid URL!</b>\n\n"
            "Example:\n"
            "• <code>http://1.2.3.4</code>\n"
            "• <code>http://1.2.3.4/konekta</code>\n"
            "• <code>http://1.2.3.4/konekta/agent/SMSCDRReports</code>\n"
            "• <code>https://mypanel.com</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _ap_get_url)
        return

    host_m = re.search(r"//([^/]+)", base_url)
    uid = message.from_user.id
    _addpanel_state[uid]["data"]["base_url"] = base_url
    _addpanel_state[uid]["data"]["host"] = host_m.group(1) if host_m else base_url
    _addpanel_state[uid]["data"]["url_hint"] = url  # preserve original URL as hint

    # ── IVA SMS special flow (ivasms.com) — cookie only ─────────────────────
    if "ivasms.com" in base_url.lower():
        msg = bot.send_message(
            message.chat.id,
            "🌐 <b>IVA SMS Panel detected!</b>\n\n"
            "⚠️ Cloudflare blocks email/password login from the Railway server IP.\n"
            "<b>You'll need to log in using a browser cookie.</b>\n\n"
        "📋 <b>How to get Cookie:</b>\n"
        "1. Login to <b>ivasms.com</b> in Chrome\n"
        "2. Open this link in browser:\n"
            "   <code>javascript:document.cookie</code>\n"
        "   (paste in address bar)\n"
        "   <b>OR</b> on PC: F12 → Application → Cookies → https://ivasms.com\n"
        "3. Copy <code>laravel_session</code> value\n\n"
        "🍪 Now paste the cookie:\n"
            "<code>laravel_session=eyJ...</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        bot.register_next_step_handler(msg, _iva_ap_get_cookie)
        return
    # ─────────────────────────────────────────────────────────────────────────

    msg = bot.send_message(
        message.chat.id,
        f"✅ <b>URL set:</b> <code>{base_url}</code>\n\n"
        f"👤 <b>Step 2/3:</b> Username pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _ap_get_user)


def _ap_get_user(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addpanel_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    username = (message.text or "").strip()
    if not username:
        msg = bot.send_message(message.chat.id, "❌ Enter Username:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _ap_get_user)
        return
    _addpanel_state[message.from_user.id]["data"]["username"] = username
    msg = bot.send_message(
        message.chat.id,
        f"✅ Username: <code>{username}</code>\n\n🔑 <b>Step 3/3:</b> Password pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _ap_get_pass)


def _ap_get_pass(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    uid = message.from_user.id
    if _is_back(message.text):
        _addpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    password = (message.text or "").strip()
    if not password:
        msg = bot.send_message(message.chat.id, "❌ Enter Password:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _ap_get_pass)
        return
    data = _addpanel_state.get(uid, {}).get("data", {})
    data["password"] = password
    wait_msg = bot.send_message(
        message.chat.id,
        "⏳🔥 <b>Connecting & auto-detecting panel type...</b>\n"
        "<i>Looking for login page, solving captcha, testing data endpoint...</i>",
        parse_mode="HTML",
    )
    panel_id = f"d{int(time.time()) % 100000}"
    panel = {
        "id": panel_id,
        "host": data.get("host", ""),
        "base_url": data.get("base_url", ""),
        "url_hint": data.get("url_hint", ""),
        "username": data.get("username", ""),
        "password": password,
        "engine": "ints_smscdr",
        "data_path": "/agent/res/data_smscdr.php",
        "admin_id": uid,
    }
    chat_id = message.chat.id
    _addpanel_state.pop(uid, None)

    def _do_add():
        sess, token, det_engine, det_path = _universal_login(panel)
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except Exception:
            pass
        if not sess:
            # Save panel data for force-add (Railway IP might be blocked by panel)
            _pending_force_add[panel_id] = panel
            force_markup = types.InlineKeyboardMarkup(row_width=1)
            force_markup.add(
                types.InlineKeyboardButton(
                    "⚠️ Force Add (Skip Login)",
                    callback_data=f"forceadd:{panel_id}", style="primary"
                )
            )
            force_markup.add(
                types.InlineKeyboardButton("❌ Cancel", callback_data=f"forceadd_cancel:{panel_id}", style="danger")
            )
            bot.send_message(
                chat_id,
        "⚠️ <b>Login Verification Failed!</b>\n\n"
        "Many panels block Railway server IPs.\n"
        "If you still want to save the panel credentials,\n"
        "<b>Force Add</b> — the panel will try to login automatically later.\n\n"
                f"🌐 Host: <code>{data.get('host', '')}</code>\n"
                f"👤 User: <code>{data.get('username', '')}</code>",
                reply_markup=force_markup,
                parse_mode="HTML",
            )
            return
        if det_engine:
            panel["engine"] = det_engine
            panel["data_path"] = det_path
        _dynamic_sessions[panel_id] = {"session": sess, "token": token}
        _dynamic_panels.append(panel)
        save_dynamic_panels()
        _start_dynamic_panel(panel)
        engine_label = {
            "ints_smscdr":   "INTS — SMSCDRStats",
            "ints_smsranges":"INTS — SMSRanges",
            "xisora":        "Xisora",
            "html_scrape":   "HTML Scrape",
        }.get(panel.get("engine", ""), panel.get("engine", "Auto"))
        bot.send_message(
            chat_id,
            f"✅🔥 <b>PANEL ADDED & STARTED!</b> 🔥✅\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🆔 <b>ID      ▸▸</b> <code>{panel_id}</code>\n"
            f"🌐 <b>Host    ▸▸</b> <code>{data.get('host','')}</code>\n"
            f"👤 <b>User    ▸▸</b> <code>{data.get('username','')}</code>\n"
            f"🔍 <b>Engine  ▸▸</b> <code>{engine_label}</code>\n"
            f"📂 <b>Endpoint▸▸</b> <code>{panel.get('data_path','')}</code>\n\n"
            f"📡 Monitor thread started! Use /panels to check.",
            parse_mode="HTML",
        )

    threading.Thread(target=_do_add, daemon=True).start()


# ── IVA SMS add-panel flow (cookie only — email/pass blocked by Cloudflare) ───

def _iva_ap_get_email(message):
    """Legacy handler — redirects to cookie flow immediately."""
    _iva_ap_get_cookie(message)


def _iva_ap_get_pass(message):
    """Legacy handler — redirects to cookie flow immediately."""
    _iva_ap_get_cookie(message)


def _iva_ap_get_cookie(message):
    """Collect browser cookie and connect to ivasms.com."""
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    cookie_str = (message.text or "").strip()
    if not cookie_str or "=" not in cookie_str:
        msg = bot.send_message(message.chat.id,
            "❌ <b>Enter Cookie!</b>\n\n"
            "Format: <code>laravel_session=eyJ0...</code>\n\n"
        "📱 <b>How to get on Phone:</b>\n"
        "1. Login to ivasms.com in Chrome\n"
        "2. Type in address bar:\n"
            "   <code>javascript:alert(document.cookie)</code>\n"
        "3. Copy whatever appears in the popup\n\n"
            "💻 <b>On PC:</b> F12 → Application → Cookies → ivasms.com → laravel_session copy",
            reply_markup=_back_admin_kb(), parse_mode="HTML",
            disable_web_page_preview=True)
        bot.register_next_step_handler(msg, _iva_ap_get_cookie)
        return
    _iva_do_connect(message, cookie_str=cookie_str)


def _iva_do_connect(message, cookie_str):
    """Build panel dict and connect using cookie."""
    uid = message.from_user.id
    _addpanel_state.pop(uid, None)
    chat_id = message.chat.id

    panel_id = f"iva{int(time.time()) % 100000}"
    panel = {
        "id": panel_id,
        "host": "ivasms.com",
        "base_url": "https://ivasms.com",
        "url_hint": "https://ivasms.com/portal/sms/received",
        "username": "ivasms",
        "password": "",
        "cookie_str": cookie_str,
        "engine": "iva_sms",
        "data_path": "/portal/sms/received",
        "admin_id": uid,
    }

    wait_msg = bot.send_message(chat_id,
        "⏳ <b>IVA SMS — logging in with cookie...</b>", parse_mode="HTML")

    def _do():
        ok = _iva_login(panel)
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except Exception:
            pass

        if not ok:
            msg2 = bot.send_message(chat_id,
                "❌ <b>Cookie didn't work!</b>\n\n"
                "Possible karon:\n"
                "• Cookie has expired (log in fresh)\n"
                "• Pura cookie copy hoy nai\n\n"
                "Abar fresh cookie pathao:\n"
                "<code>laravel_session=eyJ0...</code>",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            _addpanel_state[uid] = {"step": "iva_cookie", "data": {}}
            bot.register_next_step_handler(msg2, _iva_ap_get_cookie)
            return

        _dynamic_panels.append(panel)
        save_dynamic_panels()
        _start_dynamic_panel(panel)

        bot.send_message(chat_id,
            f"✅🔥 <b>IVA SMS PANEL ADDED!</b> 🔥✅\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🆔 <b>ID     ▸▸</b> <code>{panel_id}</code>\n"
            f"🌐 <b>Host   ▸▸</b> <code>ivasms.com</code>\n"
            f"🔑 <b>Login  ▸▸</b> <code>Cookie ✅</code>\n\n"
            f"📡 Monitor started! New OTP ashle group-e pathabe.\n"
            f"⚠️ Cookie expire hole: <code>/ivacookie</code>",
            parse_mode="HTML")

    threading.Thread(target=_do, daemon=True).start()


# ── API Key Panel Add Flow ─────────────────────────────────────────────────────

_apk_state = {}   # uid → {"url": ..., "api_key": ...}


def _apk_start(message):
    """Ask for panel URL (Step 1 of API key flow)."""
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    _apk_state[uid] = {}
    msg = bot.send_message(
        message.chat.id,
        "🗝️🔥 <b>ADD PANEL WITH API KEY</b> 🔥🗝️\n\n"
        "📡 <b>Step 1/2:</b> Send the Panel URL\n\n"
        "✅ <b>Any format accepted:</b>\n"
        "• <code>http://1.2.3.4</code>\n"
        "• <code>http://1.2.3.4/api</code>\n"
        "• <code>https://mypanel.com</code>\n"
        "• <code>https://mypanel.com/api/sms</code>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _apk_get_url)


def _apk_get_url(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _apk_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    url = (message.text or "").strip()
    if not re.match(r"https?://", url, re.IGNORECASE):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid URL! (must start with http:// or https://)",
            reply_markup=_back_admin_kb(), parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _apk_get_url)
        return
    # Extract base URL
    m = re.match(r"(https?://[^/]+(?:/[^?#]*)?)", url, re.IGNORECASE)
    base_url = m.group(1).rstrip("/") if m else url.rstrip("/")
    # If URL contains known API paths, strip them to get clean base
    for suffix in ["/api/sms", "/api/messages", "/api/received", "/api/v1", "/api"]:
        if base_url.lower().endswith(suffix):
            base_url = base_url[: -len(suffix)]
            break
    _apk_state[uid]["base_url"] = base_url
    host_m = re.search(r"//([^/]+)", base_url)
    _apk_state[uid]["host"] = host_m.group(1) if host_m else base_url

    msg = bot.send_message(
        message.chat.id,
        f"✅ URL: <code>{base_url}</code>\n\n"
        "🗝️ <b>Step 2/2:</b> Send the panel's <b>API Key</b>:\n\n"
        "<i>Copy from panel settings/profile/API section.</i>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _apk_get_key)


def _apk_get_key(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _apk_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    api_key = (message.text or "").strip()
    if not api_key:
        msg = bot.send_message(message.chat.id, "❌ Enter API Key:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _apk_get_key)
        return

    base_url = _apk_state.get(uid, {}).get("base_url", "")
    host     = _apk_state.get(uid, {}).get("host", "")
    _apk_state.pop(uid, None)
    chat_id  = message.chat.id

    wait_msg = bot.send_message(
        chat_id,
        "⏳🔍 <b>Testing API Key...</b>\n"
        "<i>Probing common endpoints, please wait...</i>",
        parse_mode="HTML",
    )

    def _do():
        panel_id   = f"apk{int(time.time()) % 100000}"
        det_path, det_param = _api_key_test(base_url, api_key)
        try:
            bot.delete_message(chat_id, wait_msg.message_id)
        except Exception:
            pass

        if not det_path:
            # Force-add option — user may know their endpoint
            _apk_state[uid] = {}
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(
                    "⚠️ Force Add (Set Endpoint Manually)",
                    callback_data=f"apkforce:{panel_id}|{base_url}|{api_key}", style="success"
                ),
                types.InlineKeyboardButton("❌ Cancel", callback_data=f"apkforce_cancel", style="primary"),
            )
            bot.send_message(
                chat_id,
        "⚠️ <b>API Endpoint auto-detect failed!</b>\n\n"
                f"🌐 Host: <code>{host}</code>\n"
                f"🗝️ Key: <code>{api_key[:8]}...</code>\n\n"
        "Possible reasons:\n"
        "• This panel has no API\n"
        "• Wrong API key\n"
        "• Panel has a custom endpoint\n\n"
        "You can still force add and set the endpoint later with <b>/editpanel</b>.",
                reply_markup=markup,
                parse_mode="HTML",
            )
            return

        panel = {
            "id": panel_id,
            "host": host,
            "base_url": base_url,
            "url_hint": f"{base_url}{det_path}",
            "username": f"api:{host}",
            "password": "",
            "api_key": api_key,
            "api_key_param": det_param,
            "engine": "api_key",
            "data_path": det_path,
            "admin_id": uid,
        }
        _dynamic_panels.append(panel)
        save_dynamic_panels()
        _start_dynamic_panel(panel)

        bot.send_message(
            chat_id,
            f"✅🔥 <b>API KEY PANEL ADDED!</b> 🔥✅\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🆔 <b>ID       ▸▸</b> <code>{panel_id}</code>\n"
            f"🌐 <b>Host     ▸▸</b> <code>{host}</code>\n"
            f"🗝️ <b>API Key  ▸▸</b> <code>{api_key[:12]}...</code>\n"
            f"📂 <b>Endpoint ▸▸</b> <code>{det_path}</code>\n"
            f"🔐 <b>Auth     ▸▸</b> <code>{det_param}</code>\n\n"
            f"📡 Monitor thread started! Check status with /panels.",
            parse_mode="HTML",
        )

    threading.Thread(target=_do, daemon=True).start()


# ── IVA SMS cookie update command ─────────────────────────────────────────────

_iva_cookie_update_state: dict = {}


def _iva_find_panel(panel_id=None):
    """Find any iva_sms panel — checks dynamic_panels AND _BUILTIN_PANELS."""
    all_panels = list(_dynamic_panels) + [p for p in _BUILTIN_PANELS if p not in _dynamic_panels]
    for p in all_panels:
        if p.get("engine") == "iva_sms" and (not panel_id or p["id"] == panel_id):
            return p
    return None


@bot.message_handler(commands=["ivacookie"])
def _iva_cookie_cmd(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    args = message.text.split()[1:] if message.text else []
    panel_id = args[0] if args else None

    iva_panel = _iva_find_panel(panel_id)

    if not iva_panel:
        bot.send_message(message.chat.id,
            "❌ <b>IVA SMS panel not found.</b>\n"
            "Restart the bot — bp10 will auto-load.",
            parse_mode="HTML")
        return

    _iva_cookie_update_state[uid] = iva_panel["id"]
    msg = bot.send_message(
        message.chat.id,
        f"🍪 <b>IVA SMS — Cookie Login</b>\n"
        f"Panel ID: <code>{iva_panel['id']}</code>\n\n"
        f"📋 <b>Steps:</b>\n"
        f"1. Login to <a href='https://ivasms.com/portal/login'>ivasms.com</a> in Chrome/Firefox\n"
        f"2. F12 → Application → Cookies → ivasms.com\n"
        f"3. Copy <code>laravel_session</code> value\n"
        f"4. Paste below:\n\n"
        f"<code>laravel_session=XXXXXXX</code>\n\n"
        f"<i>(If cf_clearance exists, add it too: <code>cf_clearance=XXX; laravel_session=XXX</code>)</i>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    bot.register_next_step_handler(msg, _iva_cookie_update_step)


def _iva_cookie_update_step(message):
    uid = message.from_user.id
    if _is_back(message.text):
        _iva_cookie_update_state.pop(uid, None)
        _go_admin_panel(message)
        return
    panel_id = _iva_cookie_update_state.pop(uid, None)
    if not panel_id:
        return
    cookie_str = (message.text or "").strip()
    if not cookie_str or "=" not in cookie_str:
        bot.send_message(message.chat.id, "❌ Enter a valid cookie format (laravel_session=XXX).", parse_mode="HTML")
        return

    # Update in dynamic_panels first
    updated = False
    for p in _dynamic_panels:
        if p["id"] == panel_id:
            p["cookie_str"] = cookie_str
            save_dynamic_panels()
            updated = True
            break

    # Also update BUILTIN_PANELS in-memory (so _iva_login picks it up)
    for p in _BUILTIN_PANELS:
        if p["id"] == panel_id:
            p["cookie_str"] = cookie_str
            updated = True
            break

    if not updated:
        bot.send_message(message.chat.id, "❌ Panel not found.", parse_mode="HTML")
        return

    _iva_scrapers.pop(panel_id, None)  # force re-login with new cookie

    wait_msg = bot.send_message(message.chat.id,
        "⏳ <b>Logging in with new cookie...</b>", parse_mode="HTML")

    def _try_reconnect():
        panel = _iva_find_panel(panel_id)
        ok = _iva_login(panel) if panel else False
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass
        if ok:
            bot.send_message(message.chat.id,
                "✅🔥 <b>IVA SMS — Cookie login SUCCESSFUL!</b>\n"
                "Panel ekhon active — OTP ashle group-e pathabe. 🟢",
                parse_mode="HTML")
        else:
            bot.send_message(message.chat.id,
                "❌ <b>That cookie didn't work either!</b>\n\n"
                "Cookie has expired or is invalid.\n"
                "Get a fresh cookie from your browser and send it again: /ivacookie",
                parse_mode="HTML")

    threading.Thread(target=_try_reconnect, daemon=True).start()


# ── IVA SMS test command (/ivatest) ───────────────────────────────────────────

@bot.message_handler(commands=["ivatest"])
def _iva_test_cmd(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return

    # Find ivasms panel (bp10 or any iva_sms engine panel)
    iva_panel = None
    for p in _dynamic_panels:
        if p.get("engine") == "iva_sms":
            iva_panel = p
            break
    # Also check BUILTIN_PANELS
    if not iva_panel:
        for p in _BUILTIN_PANELS:
            if p.get("engine") == "iva_sms":
                iva_panel = p
                break

    if not iva_panel:
        bot.send_message(message.chat.id,
            "❌ <b>IVA SMS panel not found!</b>\n"
            "Restart the bot — bp10 will auto-load.",
            parse_mode="HTML")
        return

    wait_msg = bot.send_message(message.chat.id,
        "⏳ <b>Fetching data from ivasms.com...</b>",
        parse_mode="HTML")

    def _do_test():
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass

        records = _iva_fetch(iva_panel)

        if not records:
            bot.send_message(message.chat.id,
                "⚠️ <b>IVA SMS:</b> Ekhon kono OTP nai panel-e.\n"
                "If there's any SMS on the panel it will show — try /ivatest again in a moment.",
                parse_mode="HTML")
            return

        grp = get_otp_group_id()
        items = list(records.values())[:3]

        bot.send_message(message.chat.id,
            f"✅ <b>Got {len(records)} records from the IVA panel.</b>\n"
            f"Now sending to <b>{len(items)}</b> group(s)...",
            parse_mode="HTML")

        for number, otp, sms_txt, service in items:
            svc = service if service else "IVA"
            if grp:
                send_otp_message(grp, otp, number, 0, svc, sms_txt or "")
            send_otp_message(uid, otp, number, 0, svc, sms_txt or "")

        bot.send_message(message.chat.id,
            f"🔥 <b>Done!</b> {len(items)} OTP(s) sent to group+DM.\n"
            f"IVA panel is <b>OK</b>! 🟢",
            parse_mode="HTML")

    threading.Thread(target=_do_test, daemon=True).start()


# ── Test Panel flow (test without saving) ─────────────────────────────────────

def _tp_get_url(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _testpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    url = (message.text or "").strip()
    base_url = _extract_panel_base_url(url) if re.match(r"https?://", url, re.IGNORECASE) else None
    if not base_url:
        msg = bot.send_message(
            message.chat.id,
            "❌ <b>Enter a valid URL!</b>\n\nExample: <code>http://1.2.3.4/konekta/agent/SMSCDRReports</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _tp_get_url)
        return
    _testpanel_state[uid]["data"]["base_url"] = base_url
    _testpanel_state[uid]["data"]["url_hint"] = url
    msg = bot.send_message(
        message.chat.id,
        f"✅ <b>URL:</b> <code>{base_url}</code>\n\n👤 Username pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _tp_get_user)


def _tp_get_user(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _testpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    username = (message.text or "").strip()
    if not username:
        msg = bot.send_message(message.chat.id, "❌ Enter Username:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _tp_get_user)
        return
    _testpanel_state[uid]["data"]["username"] = username
    msg = bot.send_message(
        message.chat.id,
        f"✅ Username: <code>{username}</code>\n\n🔑 Password pathao:",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _tp_get_pass_test)


def _tp_get_pass_test(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _testpanel_state.pop(uid, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    password = (message.text or "").strip()
    if not password:
        msg = bot.send_message(message.chat.id, "❌ Enter Password:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _tp_get_pass_test)
        return
    data = _testpanel_state.get(uid, {}).get("data", {})
    wait_msg = bot.send_message(
        message.chat.id,
        "⏳🔍 <b>Testing panel...</b>\n"
        "<i>Trying to log in, looking for token, probing data endpoint...</i>",
        parse_mode="HTML",
    )
    panel = {
        "id": f"test_{uid}",
        "host": data.get("base_url", ""),
        "base_url": data.get("base_url", ""),
        "url_hint": data.get("url_hint", ""),
        "username": data.get("username", ""),
        "password": password,
        "engine": "ints_smscdr",
        "data_path": "/agent/res/data_smscdr.php",
    }

    def _do_test():
        sess, token, det_engine, det_path = _universal_login(panel)
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass

        if not sess:
            bot.send_message(
                message.chat.id,
                "❌🔥 <b>TEST FAILED!</b> 🔥❌\n\n"
                "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                f"🌐 <b>URL      ▸▸</b> <code>{data.get('base_url','')}</code>\n"
                f"👤 <b>User     ▸▸</b> <code>{data.get('username','')}</code>\n"
                f"📡 <b>Status   ▸▸</b> ❌ Login failed\n\n"
                "❌ <b>Possible reasons:</b>\n"
                "• URL is incorrect\n"
                "• Username/password is wrong\n"
                "• Panel is offline",
                parse_mode="HTML",
                reply_markup=_back_admin_kb(),
            )
            _testpanel_state.pop(uid, None)
            return

        # ── Login success — now fetch existing OTPs ───────────────────────────
        engine_label = {
            "ints_smscdr":    "✅ INTS — SMSCDRStats",
            "ints_smsranges": "✅ INTS — SMSRanges",
            "xisora":         "✅ Xisora",
            "html_scrape":    "✅ HTML Scrape",
        }.get(det_engine or "", f"✅ {det_engine or 'Auto'}")
        tok_display = f"<code>{token[:12]}...</code>" if token else "<i>cookie-based</i>"

        # Update panel with detected engine/path and store session
        panel["engine"] = det_engine or "ints_smscdr"
        panel["data_path"] = det_path or "/agent/res/data_smscdr.php"
        _dynamic_sessions[panel["id"]] = {"session": sess, "token": token}

        fetch_msg = bot.send_message(
            message.chat.id,
            "⏳ <b>Login OK!</b> Fetching OTP from SMS report...",
            parse_mode="HTML",
        )

        found_otps = _universal_fetch(panel)

        try:
            bot.delete_message(message.chat.id, fetch_msg.message_id)
        except Exception:
            pass

        # Clean up temp session
        _dynamic_sessions.pop(panel["id"], None)

        # ── Send up to 6 OTPs to admin's configured group ────────────────────
        admin_group_id = get_admin_setting(uid, "otp_group_id", None)
        target_group = admin_group_id or get_otp_group_id()

        sent_count = 0
        MAX_SEND = 6
        otp_items = list(found_otps.values())  # [(number, otp, sms_txt, service)]

        if otp_items and target_group:
            for number, otp_val, sms_txt, service in otp_items[:MAX_SEND]:
                try:
                    send_otp_message(target_group, otp_val, number, "—", service, sms_txt or "")
                    sent_count += 1
                    time.sleep(0.4)
                except Exception:
                    pass

        # ── Summary message to admin ──────────────────────────────────────────
        total_found = len(otp_items)
        if total_found == 0:
            otp_summary = "⚠️ <i>Panel e aj kono OTP record nei (empty).</i>"
        elif not target_group:
            otp_summary = (
                f"⚠️ <b>{total_found} OTP(s)</b> found in panel but no group is configured!\n"
                "Set the group from Settings."
            )
        else:
            otp_summary = (
                f"📤 <b>{sent_count} OTP(s)</b> sent to group "
                f"(out of {total_found})."
            )

        bot.send_message(
            message.chat.id,
            "✅🔍 <b>TEST SUCCESS!</b> 🔍✅\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"🌐 <b>URL      ▸▸</b> <code>{data.get('base_url','')}</code>\n"
            f"👤 <b>User     ▸▸</b> <code>{data.get('username','')}</code>\n"
            f"🔍 <b>Engine   ▸▸</b> {engine_label}\n"
            f"📂 <b>Endpoint ▸▸</b> <code>{det_path or '/agent/res/data_smscdr.php'}</code>\n"
            f"🔑 <b>Token    ▸▸</b> {tok_display}\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"{otp_summary}\n\n"
            "✅ <i>Panel is working! You can save it using Add Panel.</i>",
            parse_mode="HTML",
            reply_markup=_back_admin_kb(),
        )
        _testpanel_state.pop(uid, None)

    threading.Thread(target=_do_test, daemon=True).start()


def _svc_get_label(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addservice_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    label = _strip_emoji((message.text or "").strip())
    if not label:
        msg = bot.send_message(message.chat.id, "❌ Enter Label:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _svc_get_label)
        return
    _addservice_state[message.from_user.id]["label"] = label
    msg = bot.send_message(
        message.chat.id,
        f"✅ Label: <b>{label}</b>\n\n"
        "🔑 <b>Step 2/2:</b> Enter internal key (lowercase, no space)\n"
        "<i>Example: telegram, binance, tiktok</i>",
        reply_markup=_back_admin_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _svc_get_key)


def _svc_get_key(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _addservice_state.pop(message.from_user.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    key = (message.text or "").strip().lower()
    key = re.sub(r"\s+", "_", key)
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", key):
        msg = bot.send_message(
            message.chat.id,
            "❌ Key only a-z, 0-9, _ or - diye likhun.\n"
            "<i>Example: <code>snapchat</code> or <code>my_service</code></i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _svc_get_key)
        return
    if not key:
        msg = bot.send_message(message.chat.id, "❌ Enter Key:", reply_markup=_back_admin_kb())
        bot.register_next_step_handler(msg, _svc_get_key)
        return
    label = _addservice_state.get(message.from_user.id, {}).get("label", "")
    existing_keys = [s["key"] for s in _services]
    if key in existing_keys:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Key <code>{key}</code> already exists! Enter a different key:",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _svc_get_key)
        return
    _services.append({"label": label, "key": key})
    save_services()
    _addservice_state.pop(message.from_user.id, None)
    _go_admin_panel(
        message,
        f"✅🔥 <b>Service Added!</b>\n\n"
        f"🏷️ Label: <b>{label}</b>\n"
        f"🔑 Key: <code>{key}</code>\n\n"
        f"<i>Service menu-te dekha jabe!</i>",
    )


@bot.message_handler(commands=["listpanels"])
def listpanels_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    caller_uid = message.from_user.id
    my_panels = [
        p for p in _dynamic_panels
        if is_super_admin(caller_uid) or p.get("admin_id") == caller_uid
    ]
    if not my_panels:
        bot.send_message(
            message.chat.id,
            "📋 <b>You have no dynamic panel.</b>\n💡 Use /addpanel to add one.",
            parse_mode="HTML",
        )
        return
    lines = "📋🔥 <b>DYNAMIC PANELS LIST</b> 🔥📋\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
    for p in my_panels:
        pid = p["id"]
        with _stats_lock:
            s = _panel_stats.get(pid, {})
        st = s.get("status", "⏳")
        lines += (
            f"{st} 🆔 <code>{pid}</code>\n"
            f"   🌐 <code>{p.get('host', '?')}</code>\n"
            f"   👤 {p.get('username', '?')}\n\n"
        )
    lines += "🗑️ Remove: <code>/removepanel [ID]</code>"
    bot.send_message(message.chat.id, lines, parse_mode="HTML")


@bot.message_handler(commands=["removepanel"])
def removepanel_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.send_message(
            message.chat.id,
            "❌ Enter Panel ID:\n<code>/removepanel d12345</code>\n\n"
            "💡 /listpanels diye ID dekho.",
            parse_mode="HTML",
        )
        return
    caller_uid = message.from_user.id
    pid = args[1].strip()
    target = next((p for p in _dynamic_panels if p["id"] == pid), None)
    if not target:
        bot.send_message(message.chat.id, f"❌ Panel <code>{pid}</code> not found.\n💡 Use /listpanels to check the ID.", parse_mode="HTML")
        return
    if not is_super_admin(caller_uid) and target.get("admin_id") != caller_uid:
        bot.send_message(message.chat.id, "❌ <b>This panel isn't yours — you can't remove it!</b>", parse_mode="HTML")
        return
    _dynamic_panels[:] = [p for p in _dynamic_panels if p["id"] != pid]
    save_dynamic_panels()
    with _stats_lock:
        _panel_stats.pop(pid, None)
    _dynamic_sessions.pop(pid, None)
    _dynamic_locks.pop(pid, None)
    bot.send_message(message.chat.id, f"✅🔥 Panel <code>{pid}</code> removed!\n<i>Monitor thread will stop naturally.</i>", parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global stock
    try:
        data = call.data

        if data == "rmcc":
            _handle_remove_cc_callback(call)
            return

        # ── Buy Service callbacks ─────────────────────────────────────────────
        if data == "buy_tg_premium":
            prices = _buy_service_settings.get("premium_prices", {})
            rate = _buy_service_settings.get("dollar_rate", 128)
            markup = types.InlineKeyboardMarkup(row_width=1)
            for plan_key, label in [("3M", "3 Month"), ("6M", "6 Month"), ("1Y", "1 Year")]:
                price_bdt = prices.get(plan_key, 0)
                if price_bdt <= 0:
                    markup.add(types.InlineKeyboardButton(
                        f"{label} — Price not set",
                        callback_data=f"buy_premium:{plan_key}", style="primary",
                        icon_custom_emoji_id="5251378413133919079"
                    ))
                else:
                    price_usd = round(price_bdt / rate, 2) if rate else 0
                    markup.add(types.InlineKeyboardButton(
                        f"{label} — {price_bdt} BDT / ${price_usd}",
                        callback_data=f"buy_premium:{plan_key}", style="primary",
                        icon_custom_emoji_id="5251378413133919079"
                    ))
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="buy_svc_back", style="danger"))
            try:
                bot.edit_message_text(
                    '<tg-emoji emoji-id="5269368858610793668">💎</tg-emoji> <b>Telegram Premium</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> select: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                bot.send_message(call.message.chat.id,
                    '<tg-emoji emoji-id="5269368858610793668">💎</tg-emoji> <b>Telegram Premium</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> select: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id)
            return

        if data.startswith("buy_premium:"):
            plan = data.split(":", 1)[1]
            prices = _buy_service_settings.get("premium_prices", {})
            rate = _buy_service_settings.get("dollar_rate", 128)
            binance_id = _buy_service_settings.get("binance_id", "1138284235")
            bkash_num = _buy_service_settings.get("bkash_number", "01340670062")
            bkash_emoji_id = _buy_service_settings.get("bkash_emoji_id", "")
            binance_emoji_id = _buy_service_settings.get("binance_emoji_id", "")
            plan_labels = {"3M": "3 Month", "6M": "6 Month", "1Y": "1 Year"}
            label = f"Telegram Premium {plan_labels.get(plan, plan)}"
            price_bdt = prices.get(plan, 0)
            price_usd = round(price_bdt / rate, 2) if rate else 0
            uid_buyer = call.from_user.id
            _buy_pending[uid_buyer] = {"type": "premium", "label": label, "price": price_bdt}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(
                binance_id, copy_text=types.CopyTextButton(text=binance_id), style="primary",
                icon_custom_emoji_id="5298716928490120985"
            ))
            markup.add(types.InlineKeyboardButton(
                bkash_num, copy_text=types.CopyTextButton(text=bkash_num), style="success",
                icon_custom_emoji_id="6120493521112669316"
            ))
            bot.send_message(
                call.message.chat.id,
                f'<tg-emoji emoji-id="5269368858610793668">💎</tg-emoji> <b>{label}</b> <tg-emoji emoji-id="5269368858610793668">💎</tg-emoji>\n\n'
                f'<tg-emoji emoji-id="5296591052822585948">💰</tg-emoji> Price: <b>{price_bdt} BDT</b> / <tg-emoji emoji-id="5409048419211682843">💱</tg-emoji> {price_usd}\n'
                f'<tg-emoji emoji-id="5296780065743350163">💱</tg-emoji> Rate: 1 <tg-emoji emoji-id="5409048419211682843">💱</tg-emoji> = {rate} BDT\n\n'
                f'<tg-emoji emoji-id="5253742260054409879">✅</tg-emoji> After paying, send a <b>screenshot</b> in this chat. <tg-emoji emoji-id="5253742260054409879">✅</tg-emoji>\n\n'
                f"─────────────────\n"
                f'<tg-emoji emoji-id="5325547803936572038">💳</tg-emoji> <b>Payment Options:</b>\n'
                f'•<tg-emoji emoji-id="5298716928490120985">💎</tg-emoji> Binance ID: <code>{binance_id}</code>\n'
                f'•<tg-emoji emoji-id="6120493521112669316">💎</tg-emoji> bKash: <code>{bkash_num}</code>\n'
                f"─────────────────\n\n"
                f'<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Click the button to copy the ID: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                reply_markup=markup, parse_mode="HTML"
            )
            bot.answer_callback_query(call.id, f"✅ {label} selected!")
            return

        if data == "buy_vpn_menu":
            vpns = _buy_service_settings.get("vpn_services", [])
            if not vpns:
                bot.answer_callback_query(call.id, "❌ Kono VPN service nei!", show_alert=True)
                return
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i, v in enumerate(vpns):
                emoji_id = v.get("emoji_id", "")
                name = v.get("name", "")
                dur = v.get("duration", "")
                price = v.get("price", 0)
                vid = v.get("id") or str(i)
                btn_kwargs = {"icon_custom_emoji_id": emoji_id} if emoji_id else {}
                markup.add(types.InlineKeyboardButton(
                    f"{name} | {dur} | {price} BDT",
                    callback_data=f"buy_vpn:{vid}",
                    style="success",
                    **btn_kwargs
                ))
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="buy_svc_back", style="danger"))
            try:
                bot.edit_message_text(
                    "🔒 <b>Buy VPN</b>\n\nSelect a plan:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                bot.send_message(call.message.chat.id,
                    "🔒 <b>Buy VPN</b>\n\nSelect a plan:",
                    reply_markup=markup, parse_mode="HTML")
            bot.answer_callback_query(call.id)
            return

        if data.startswith("buy_vpn:"):
            vid = data.split(":", 1)[1]
            vpns = _buy_service_settings.get("vpn_services", [])
            v = None
            for _vpn in vpns:
                if _vpn.get("id", "") == vid:
                    v = _vpn
                    break
            if v is None:
                # fallback: try as integer index for old buttons
                try:
                    v = vpns[int(vid)]
                except (ValueError, IndexError):
                    v = None
            if v is None:
                bot.answer_callback_query(call.id, "❌ Service pawa jay ni!", show_alert=True)
                return
            bkash_num = _buy_service_settings.get("bkash_number", "01340670062")
            bkash_emoji_id = _buy_service_settings.get("bkash_emoji_id", "")
            emoji_id = v.get("emoji_id", "")
            name = v.get("name", "")
            dur = v.get("duration", "")
            price = v.get("price", 0)
            label = f"VPN — {name} | {dur}"
            uid_buyer = call.from_user.id
            _buy_pending[uid_buyer] = {"type": "vpn", "label": label, "price": price}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton(
                bkash_num, copy_text=types.CopyTextButton(text=bkash_num), style="success",
                icon_custom_emoji_id="6120493521112669316"
            ))
            vpn_emoji_tag = f'<tg-emoji emoji-id="{emoji_id}">🔒</tg-emoji> ' if emoji_id else "🔒 "
            # Answer first — prevents button timeout even if send_message fails
            bot.answer_callback_query(call.id, f"✅ {name} selected!")
            try:
                bot.send_message(
                    call.message.chat.id,
                    f"{vpn_emoji_tag}<b>{name}</b>\n"
                    f'<tg-emoji emoji-id="5413879192267805083">📅</tg-emoji> Duration: <b>{dur}</b>\n'
                    f'<tg-emoji emoji-id="5296591052822585948">💰</tg-emoji> Price: <b>{price} BDT</b>\n\n'
                    f'<tg-emoji emoji-id="5251316745993481601">✅</tg-emoji> After paying, send a <b>screenshot</b> in this chat. <tg-emoji emoji-id="5251316745993481601">✅</tg-emoji>\n\n'
                    f"─────────────────\n"
                    f'<tg-emoji emoji-id="5352638632278660622">💳</tg-emoji> <b>Payment:</b> <tg-emoji emoji-id="6120493521112669316">💎</tg-emoji> bKash Personal\n'
                    f'<tg-emoji emoji-id="5355208818017999139">📱</tg-emoji> Number: <code>{bkash_num}</code>\n'
                    f"─────────────────\n\n"
                    f'<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Click the button to copy the number: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception as _bvpn_err:
                print(f"[BUY_VPN] send_message error: {_bvpn_err}")
            return

        if data.startswith("copy_bin:"):
            val = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, f"✅ Binance ID: {val}", show_alert=True)
            return

        if data.startswith("copy_bk:"):
            val = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, f"✅ bKash: {val}", show_alert=True)
            return

        if data == "buy_svc_back":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("Telegram Premium", callback_data="buy_tg_premium", style="primary", icon_custom_emoji_id="5251390031020455583"),
                types.InlineKeyboardButton("Buy VPN", callback_data="buy_vpn_menu", style="success", icon_custom_emoji_id="5269759232483303288"),
            )
            try:
                bot.edit_message_text(
                    '<tg-emoji emoji-id="5375338737028841420">🛒</tg-emoji> <b>BUY SERVICE</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Select any service from below: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id)
            return

        if data.startswith("buy_set_vpn_price:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            vpn_id = data.split(":", 1)[1]
            if vpn_id == "cancel":
                bot.answer_callback_query(call.id, "❌ Cancelled")
                _show_buy_service_admin(call.message)
                return
            bot.answer_callback_query(call.id, "✅ VPN selected")
            prompt = bot.send_message(
                call.message.chat.id,
                "💰 <b>Enter new price in BDT:</b>\n"
                "<i>Example: <code>50</code></i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(
                prompt,
                lambda m, vid=vpn_id: _buy_set_vpn_price_step(m, vid),
            )
            return

        if data.startswith("buy_del_vpn:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            val = data.split(":", 1)[1]
            if val == "cancel":
                bot.answer_callback_query(call.id, "Cancelled")
                try:
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except Exception:
                    pass
                return
            vpns = _buy_service_settings.get("vpn_services", [])
            # Find by id first, then fallback to integer index for old buttons
            removed_idx = None
            for j, _vpn in enumerate(vpns):
                if _vpn.get("id", str(j)) == val:
                    removed_idx = j
                    break
            if removed_idx is None:
                try:
                    candidate = int(val)
                    if 0 <= candidate < len(vpns):
                        removed_idx = candidate
                except ValueError:
                    pass
            if removed_idx is None:
                bot.answer_callback_query(call.id, "❌ Error! VPN list has been updated, try again.", show_alert=True)
                return
            removed = vpns.pop(removed_idx)
            save_buy_service_settings()
            bot.answer_callback_query(call.id, f"✅ {removed['name']} removed!")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                try:
                    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                except Exception:
                    pass
            # Show updated remove list or done message
            remaining = _buy_service_settings.get("vpn_services", [])
            if remaining:
                new_markup = types.InlineKeyboardMarkup(row_width=1)
                for jj, rv in enumerate(remaining):
                    eid = rv.get("emoji_id", "")
                    rvid = rv.get("id") or str(jj)
                    rlabel = f"{rv.get('name','')} | {rv.get('duration','')} | {rv.get('price',0)} BDT"
                    rkw = {"icon_custom_emoji_id": eid} if eid else {}
                    new_markup.add(types.InlineKeyboardButton(
                        f"🗑️ {rlabel}", callback_data=f"buy_del_vpn:{rvid}", style="danger", **rkw
                    ))
                new_markup.add(types.InlineKeyboardButton("❌ Cancel", callback_data="buy_del_vpn:cancel"))
                bot.send_message(call.message.chat.id,
                    f"✅ <b>{removed['name']}</b> removed!\n\n"
                    f"🗑️ <b>Remove VPN Service</b>\n\nAro remove korbe?",
                    reply_markup=new_markup, parse_mode="HTML")
            else:
                bot.send_message(call.message.chat.id,
                    f"✅ <b>{removed['name']}</b> removed!\n\n❌ Aar kono VPN service nei.",
                    parse_mode="HTML")
            return

        if data.startswith("admin_dmu:"):
            uid_cb = call.from_user.id
            if uid_cb not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            target = int(data.split(":", 1)[1])
            _admin_dmu_state[uid_cb] = target
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                f"📨 <b>User <code>{target}</code>-ke message pathao:</b>\n\n"
                f"Text, photo, video, sticker — all accepted.\n"
                f"To use a custom emoji, write the emoji ID in the text.\n\n"
                f"🔙 Back: Press the <b>Admin Panel</b> button.",
                reply_markup=_back_admin_kb(), parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, _buy_send_msg_step)
            return


        # ── Admin Number Add — service selection ─────────────────────────────
        if data.startswith("admin_add_svc:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            svc = data.split(":", 1)[1]
            if svc == "cancel":
                bot.answer_callback_query(call.id, "❌ Cancelled")
                try:
                    bot.edit_message_reply_markup(
                        call.message.chat.id, call.message.message_id, reply_markup=None
                    )
                except Exception:
                    pass
                _go_admin_panel(call.message)
                return
            bot.answer_callback_query(call.id, f"✅ {svc.upper()}")
            try:
                bot.edit_message_reply_markup(
                    call.message.chat.id, call.message.message_id, reply_markup=None
                )
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"🔥 <b>{svc.upper()}</b>\n\n"
                f"📝 <b>Enter Slot name:</b>\n"
                f"<i>Example: Mali 1, Germany 2, India 3</i>",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m, s=svc: ask_numbers_for_slot(m, s))
            return

        # ── Force Add Panel (Railway IP blocked) ─────────────────────────────
        if data.startswith("forceadd:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            pid = data.split(":", 1)[1]
            panel = _pending_force_add.pop(pid, None)
            if not panel:
                bot.answer_callback_query(call.id, "❌ Panel data expired. Please try again.")
                return
            _dynamic_panels.append(panel)
            save_dynamic_panels()
            _start_dynamic_panel(panel)
            bot.answer_callback_query(call.id, "✅ Panel Force Added!")
            try:
                bot.edit_message_text(
                    f"✅🔥 <b>PANEL FORCE ADDED!</b>\n\n"
                    f"🆔 <b>ID:</b> <code>{pid}</code>\n"
                    f"🌐 <b>Host:</b> <code>{panel.get('host', '')}</code>\n"
                    f"👤 <b>User:</b> <code>{panel.get('username', '')}</code>\n\n"
        f"⚠️ Login not verified yet — the panel will try to login automatically.\n"
        f"Check status with /panels.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        if data.startswith("forceadd_cancel:"):
            pid = data.split(":", 1)[1]
            _pending_force_add.pop(pid, None)
            bot.answer_callback_query(call.id, "Cancelled.")
            try:
                bot.edit_message_text(
        "❌ Panel add cancelled.\n/addpanel to try again.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        # ── V2 Panel API Key change ───────────────────────────────────────────
        if data.startswith("chgkey:"):
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            pid = data.split(":", 1)[1]   # fastx | stex | voltex | mk
            _PANEL_LABELS = {
                "fastx": "⚡ FastX SMS",
                "stex": "🌐 STEX SMS",
                "voltex": "🔮 Voltex SMS",
                "mk": "🟢 MK Panel",
                "augestel": "🌐 Augestel SMS",
            }
            label = _PANEL_LABELS.get(pid, pid.upper())
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"🔑 <b>{label} — Enter new API Key:</b>\n\n"
                f"<i>Send only the API key text (no extra characters)</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m, p=pid: _chgkey_receive(m, p))
            return

        # ── API Key Panel type selection ──────────────────────────────────────
        if data == "aptype:pass":
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            _addpanel_state[uid] = {"step": "url", "data": {}}
            msg = bot.send_message(
                call.message.chat.id,
                "🔧🔥 <b>ADD NEW PANEL</b> 🔥🔧\n\n"
        "📡 <b>Step 1/3:</b> Send the Panel URL\n\n"
        "✅ <b>Any format accepted:</b>\n"
                "• <code>http://1.2.3.4</code>\n"
                "• <code>http://1.2.3.4/ints</code>\n"
                "• <code>http://1.2.3.4/konekta</code>\n"
                "• <code>https://truesms.net</code>\n\n"
                "🤖 <i>Login, captcha, and endpoint will all be auto-detected!</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _ap_get_url)
            return

        if data == "aptype:apikey":
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            bot.answer_callback_query(call.id)
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            except Exception:
                pass
            _apk_state[uid] = {}
            msg = bot.send_message(
                call.message.chat.id,
        "🗝️🔥 <b>ADD PANEL WITH API KEY</b> 🔥🗝️\n\n"
        "📡 <b>Step 1/2:</b> Send the Panel URL\n\n"
        "✅ <b>Any format accepted:</b>\n"
                "• <code>http://1.2.3.4</code>\n"
                "• <code>http://1.2.3.4/api</code>\n"
                "• <code>https://mypanel.com</code>\n"
                "• <code>https://mypanel.com/api/sms</code>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _apk_get_url)
            return

        if data.startswith("apkforce:"):
            uid = call.from_user.id
            if uid not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            bot.answer_callback_query(call.id, "✅ Force Adding...")
            try:
                rest = data[len("apkforce:"):].split("|", 2)
                panel_id = rest[0]
                base_url = rest[1] if len(rest) > 1 else ""
                api_key  = rest[2] if len(rest) > 2 else ""
            except Exception:
                bot.send_message(call.message.chat.id, "❌ Data parse error।", parse_mode="HTML")
                return
            host_m = re.search(r"//([^/]+)", base_url)
            host   = host_m.group(1) if host_m else base_url
            panel = {
                "id": panel_id,
                "host": host,
                "base_url": base_url,
                "url_hint": f"{base_url}/api/sms",
                "username": f"api:{host}",
                "password": "",
                "api_key": api_key,
                "api_key_param": "api_key",
                "engine": "api_key",
                "data_path": "/api/sms",
                "admin_id": uid,
            }
            _dynamic_panels.append(panel)
            save_dynamic_panels()
            _start_dynamic_panel(panel)
            try:
                bot.edit_message_text(
                    f"✅ <b>API KEY PANEL FORCE ADDED!</b>\n\n"
                    f"🆔 <b>ID:</b> <code>{panel_id}</code>\n"
                    f"🌐 <b>Host:</b> <code>{host}</code>\n"
                    f"🗝️ <b>Key:</b> <code>{api_key[:12]}...</code>\n\n"
        f"⚠️ Endpoint auto-detect failed — using default <code>/api/sms</code>.\n"
        f"Check status with /panels.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return

        if data == "apkforce_cancel":
            bot.answer_callback_query(call.id, "Cancelled.")
            try:
                bot.edit_message_text(
        "❌ API Key panel add cancelled.\n/addpanel to try again.",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            return
        # ─────────────────────────────────────────────────────────────────────

        if data == "v":
            uid = call.from_user.id

            grp_id = get_otp_group_id()
            grp_link = get_otp_group_link()
            ch2_link = get_channel2()
            ch2_ref = _extract_username(ch2_link)

            not_joined = []

            grp_ok = _check_member(grp_id, uid) if grp_id else None
            if grp_ok is False:
                not_joined.append(("🔥 OTP Group", grp_link))

            ch2_ok = _check_member(ch2_ref, uid) if ch2_ref else None
            if ch2_ok is False:
                not_joined.append(("📢 Main Channel", ch2_link))

            if not_joined:
                bot.answer_callback_query(call.id, "❌ Sob jagay join hao nai!", show_alert=False)
                lines = "❌ <b>Verify hote parcho na!</b>\n\n"
                lines += "⛔ Tumi ekhono nicher jagay join hao nai:\n\n"
                for name, _ in not_joined:
                    lines += f"  🚫 <b>{name}</b>\n"
                lines += "\n👇 Join and click <b>Verify</b>:"
                err_markup = types.InlineKeyboardMarkup(row_width=1)
                for name, lnk in not_joined:
                    err_markup.add(types.InlineKeyboardButton(
                        f"👉 JOIN {name}", url=lnk, style="danger"
                    ))
                err_markup.add(types.InlineKeyboardButton(
                    "🔄 Verify", callback_data="v", style="success"
                ))
                try:
                    bot.edit_message_text(
                        lines,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=err_markup,
                        parse_mode="HTML",
                    )
                except Exception:
                    bot.send_message(
                        call.message.chat.id,
                        lines,
                        reply_markup=err_markup,
                        parse_mode="HTML",
                    )
            else:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                vname = call.from_user.first_name or call.from_user.username or "User"
                bot.send_message(
                    call.message.chat.id,
                    get_template("verify_success").format(vname=vname, uid=uid),
                    reply_markup=main_menu(call.from_user.id),
                    parse_mode="HTML",
                )

        elif data == "back_to_services":
            # Cancel any active countdown so it stops re-editing this message
            cid = call.message.chat.id
            if cid in _countdowns:
                _countdowns[cid].set()
            markup, has_btns = _build_combined_service_markup()
            if has_btns:
                try:
                    bot.edit_message_text(
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        cid,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                except Exception:
                    bot.send_message(
                        cid,
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ No stock available in any service.", show_alert=True)

        elif data.startswith("v1svc:"):
            svc_key = data.split(":", 1)[1]
            markup = types.InlineKeyboardMarkup(row_width=2)
            btns = []
            svc_stock = dict(stock.get(svc_key, {}))   # snapshot to avoid race
            for cnt, nums in svc_stock.items():
                if nums:
                    _, flag = get_country_details(nums[0])
                    btns.append(types.InlineKeyboardButton(
                        f"{cnt}",
                        callback_data=f"n:{svc_key}:{cnt}",
                        style="primary",
                        **_flag_btn_kwargs(flag)
                    ))
            if btns:
                markup.add(*btns)
            markup.add(types.InlineKeyboardButton("⬅️ 𝗕𝗮𝗰𝗸", callback_data="back_to_services", style="danger"))
            if btns:
                try:
                    bot.edit_message_text(
                        "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b>",
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                except Exception:
                    bot.send_message(
                        call.message.chat.id,
                        "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b>",
                        reply_markup=markup,
                        parse_mode="HTML",
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ No stock in this service!", show_alert=True)

        elif data.startswith("s:"):
            svc = data.split(":")[1]
            markup = types.InlineKeyboardMarkup(row_width=2)
            btns = []
            if svc in stock:
                for cnt, nums in stock[svc].items():
                    if nums:
                        _, flag = get_country_details(nums[0])
                        btns.append(
                            types.InlineKeyboardButton(
                                f"{cnt}", callback_data=f"n:{svc}:{cnt}", style="primary",
                                **_flag_btn_kwargs(flag)
                            )
                        )
            if btns:
                markup.add(*btns)
            markup.add(
                types.InlineKeyboardButton("⬅️ 𝗕𝗮𝗰𝗸", callback_data="back_to_services", style="danger")
            )
            bot.edit_message_text(
                f"🔥 <b>{svc.upper()} — COUNTRY</b> 🔥",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("n:"):
            _, svc, scnt = data.split(":")
            if scnt in stock.get(svc, {}) and stock[svc][scnt]:
                n_batch = get_numbers_per_batch()
                available = stock[svc][scnt]
                count = min(n_batch, len(available))
                nums = [available.pop(0) for _ in range(count)]
                save_stock()
                c_name, flag = get_country_details(nums[0])
                uid_n = call.from_user.id
                cid_n = call.message.chat.id
                # Release any previously assigned number for this user
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_n]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                    print(f"[N:] Released old number(s) {old_nums} for user {uid_n}")
                for _rnum in nums:
                    register_number(cid_n, _rnum)
                display_nums = [n if n.startswith("+") else "+" + n for n in nums]
                _remember_number_view(uid_n, svc, scnt, display_nums, flag, c_name)
                init_kb = _build_numbers_display_kb(svc, scnt, display_nums, flag, c_name)
                # Track service/country for this user so OTP message buttons work
                _user_last_svc[uid_n] = (svc, scnt)
                # Cancel any running countdown for this chat before starting new one
                if cid_n in _countdowns:
                    _countdowns[cid_n].set()
                # V2-style: edit the CURRENT message in place (no new message sent)
                msg_id = call.message.message_id
                try:
                    bot.edit_message_text(
                        ".",
                        cid_n, msg_id,
                        reply_markup=init_kb,
                    )
                except Exception:
                    # Fallback: send new message if edit fails
                    sent = bot.send_message(cid_n, ".", reply_markup=init_kb)
                    msg_id = sent.message_id
                # Track so "Change Number" handler can find it
                _user_last_num_msg[uid_n] = msg_id
                _start_countdown(cid_n, msg_id, svc, flag, c_name, display_nums, scnt)
            else:
                bot.answer_callback_query(call.id, " STOCK SHESH! ", show_alert=True)

        elif data == "clr_menu":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.edit_message_text(
                "🗑️🔥 <b>STOCK CLEAR PANEL</b> 🔥🗑️\n\n"
                " <b>Kon service-er stock clear korbe?</b>\n"
                "⬇️ Choose a service:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=_clr_service_markup(),
                parse_mode="HTML",
            )

        elif data.startswith("clr_s:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            svc = data[6:]
            markup = types.InlineKeyboardMarkup(row_width=1)
            svc_stock = stock.get(svc, {})
            has_any = False
            for cnt, nums in svc_stock.items():
                if nums:
                    has_any = True
                    _, flag = get_country_details(nums[0])
                    cb = f"clr_c:{svc}:{cnt}"
                    if len(cb.encode()) <= 64:
                        markup.add(
                            types.InlineKeyboardButton(
                                f"🗑️ {cnt}  ({len(nums)} )", callback_data=cb, style="success",
                                **_flag_btn_kwargs(flag)
                            )
                        )
            if not has_any:
                markup.add(
                    types.InlineKeyboardButton("⚠️ Stock nai!", callback_data="clr_menu", style="primary")
                )
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="clr_menu", style="danger"))
            bot.edit_message_text(
                f"🔥 <b>{svc.upper()} — Kon desh clear korbe?</b> 🔥\n\n"
                f"⬇️ Choose a country:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("clr_c:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            _, svc, cnt = data.split(":", 2)
            count = len(stock.get(svc, {}).get(cnt, []))
            _, flag = get_country_details(stock[svc][cnt][0]) if count else ("", "🌐")
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    "✅ Yes, Delete", callback_data=f"clr_y:{svc}:{cnt}", style="success"
                ),
                types.InlineKeyboardButton("❌ Cancel", callback_data=f"clr_s:{svc}", style="primary"),
            )
            bot.edit_message_text(
                f"⚠️ <b>CONFIRM DELETE</b> ⚠️\n\n"
                f"💬 <b>Service ▸▸</b>  {svc.upper()}\n"
                f"🌍 <b>Country ▸▸</b>  {_resolve_flag(flag)} {cnt}\n"
                f"📱 <b>Numbers ▸▸</b>  {count} \n\n"
                f" Sure? Ei {count}  numbers will be deleted!",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("clr_y:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            _, svc, cnt = data.split(":", 2)
            removed = len(stock.get(svc, {}).get(cnt, []))
            if svc in stock and cnt in stock[svc]:
                del stock[svc][cnt]
                save_stock()
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🗑️ Aro Clear", callback_data=f"clr_s:{svc}", style="danger"),
                types.InlineKeyboardButton("🔙 Services", callback_data="clr_menu", style="success"),
            )
            bot.edit_message_text(
                f"✅🔥 <b>DELETE COMPLETE!</b> 🔥✅\n\n"
                f"💬 <b>Service ▸▸</b>  {svc.upper()}\n"
                f"🌍 <b>Country ▸▸</b>  {cnt}\n"
                f"📱 <b>Deleted  ▸▸</b>  {removed} number(s)\n\n"
                f"⚡ <i>Stock updated!</i>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data == "clr_all":
            if call.from_user.id not in ADMIN_IDS:
                return
            total = sum(
                len(nums) for svc_d in stock.values() for nums in svc_d.values()
            )
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton(
                    " Haa, SOB Clear", callback_data="clr_allok", style="primary"
                ),
                types.InlineKeyboardButton("❌ Cancel", callback_data="clr_menu", style="danger"),
            )
            bot.edit_message_text(
                f"☠️⚠️ <b>CLEAR ALL CONFIRM</b> ⚠️☠️\n\n"
                f" Total <b>{total}</b> numbers will be deleted!\n"
                f"⚡ Sob service-er sob country mochhe jabe!\n\n"
                f"🔥 Sure? Eta undo kora jabe na!",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data == "clr_allok":
            if call.from_user.id not in ADMIN_IDS:
                return
            stock = {
                "whatsapp": {},
                "facebook": {},
                "telegram": {},
                "instagram": {},
                "pc clone": {},
                "binance": {},
            }
            save_stock()
            bot.edit_message_text(
                "🔥 <b>ALL STOCK CLEARED!</b> 🔥\n <i>Now add new numbers!</i> ",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
            )

        elif data.startswith("rmpanel:"):
            caller_uid = call.from_user.id
            if caller_uid not in ADMIN_IDS:
                return
            pid = data.split(":", 1)[1]
            target = next((p for p in _dynamic_panels if p["id"] == pid), None)
            if not target:
                bot.answer_callback_query(call.id, "❌ Panel pawa jaini!", show_alert=True)
            elif not is_super_admin(caller_uid) and target.get("admin_id") != caller_uid:
                bot.answer_callback_query(call.id, "❌ Ei panel tomar na!", show_alert=True)
            else:
                _dynamic_panels[:] = [p for p in _dynamic_panels if p["id"] != pid]
                save_dynamic_panels()
                with _stats_lock:
                    _panel_stats.pop(pid, None)
                _dynamic_sessions.pop(pid, None)
                _dynamic_locks.pop(pid, None)
                try:
                    bot.edit_message_text(
                        f"✅🔥 <b>Panel <code>{pid}</code> removed!</b>\n"
                        f"<i>Monitor thread will stop naturally.</i>",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass

        elif data.startswith("rmsvc:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            key = data.split(":", 1)[1]
            before = len(_services)
            _services[:] = [s for s in _services if s["key"] != key]
            if len(_services) < before:
                save_services()
                bot.edit_message_text(
                    f"✅🔥 <b>Service <code>{key}</code> removed!</b>\n"
                    f"<i>Removed from the service menu.</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            else:
                bot.answer_callback_query(call.id, "❌ Service pawa jaini!", show_alert=True)

        elif data.startswith("aadur:"):
            if not is_super_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Permission nei!", show_alert=True)
                return
            parts = data.split(":")
            new_uid = int(parts[1])
            months = int(parts[2])
            add_admin(new_uid, months=months)
            exp_ts = _admin_expiry.get(str(new_uid))
            exp_str = datetime.datetime.fromtimestamp(exp_ts).strftime("%d %b %Y") if exp_ts else "—"
            raw_n = user_names.get(str(new_uid), "")
            name_str = raw_n if isinstance(raw_n, str) else raw_n.get("first_name", str(new_uid))
            name_str = name_str or str(new_uid)
            try:
                bot.edit_message_text(
                    f"✅ <b>ADMIN ADDED!</b>\n\n"
                    f"👑 <b>New Admin:</b> {name_str} [<code>{new_uid}</code>]\n"
                    f"📅 <b>Meiad:</b> {months} Mash\n"
                    f"🗓️ <b>Expire Date:</b> {exp_str}\n\n"
                    f"<i>From now on this user will have admin panel access.</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id, f"✅ Admin added ({months} mash)!", show_alert=False)
            try:
                bot.send_message(
                    new_uid,
                    f"🎉 <b>Congratulations! Tumi Admin hoyecho!</b>\n\n"
                    f"📅 <b>Admin Meiad:</b> {months} Mash\n"
                    f"🗓️ <b>Expire:</b> {exp_str}\n\n"
                    f"Use the /admin command for admin panel access.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data == "aadur_cancel":
            bot.answer_callback_query(call.id, "❌ Cancelled.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass

        elif data.startswith("rmadmin:"):
            if not is_super_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Only Super Admin can remove!", show_alert=True)
                return
            target = int(data.split(":")[1])
            if remove_admin(target):
                raw_n = user_names.get(str(target), "")
                name = raw_n if isinstance(raw_n, str) else raw_n.get("first_name", str(target))
                name = name or str(target)
                bot.answer_callback_query(call.id, f"✅ {name} removed!", show_alert=False)
                try:
                    bot.edit_message_text(
                        f"✅ <b>ADMIN REMOVED!</b>\n\n"
                        f"🗑️ <b>Removed:</b> {name} [<code>{target}</code>]\n\n"
                        f"<i>From now on this user will lose admin access.</i>",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            else:
                bot.answer_callback_query(call.id, "❌ Remove kora gelo na (Super Admin)!", show_alert=True)

        elif data.startswith("cfg_toggle:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            parts = data.split(":")
            try:
                cid = int(parts[1])
                action = parts[2]
            except (IndexError, ValueError):
                bot.answer_callback_query(call.id, "❌ Error!", show_alert=True)
                return
            with _demo_lock:
                for cfg in _demo_configs:
                    if cfg["id"] == cid:
                        cfg["active"] = (action == "start")
                        cfg_name = cfg["name"]
                        break
                else:
                    bot.answer_callback_query(call.id, "❌ Config not found!", show_alert=True)
                    return
            if action == "start":
                _demo_next_fire[cid] = 0
                status_msg = f"🟢 <b>{cfg_name} started!</b>"
            else:
                _demo_next_fire.pop(cid, None)
                status_msg = f"🔴 <b>{cfg_name} stopped!</b>"
            bot.answer_callback_query(call.id, status_msg.replace("<b>", "").replace("</b>", ""), show_alert=False)
            try:
                bot.edit_message_text(
                    "⚡ <b>Config Start/Stop:</b>",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=demo_cfg_inline_markup(),
                    parse_mode="HTML",
                )
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id,
                status_msg + "\n\n" + demo_status_text(),
                parse_mode="HTML",
            )

        elif data.startswith("rmcfg:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            try:
                cid = int(data.split(":", 1)[1])
            except ValueError:
                bot.answer_callback_query(call.id, "❌ Invalid config!", show_alert=True)
                return
            with _demo_lock:
                before = len(_demo_configs)
                _demo_configs[:] = [c for c in _demo_configs if c["id"] != cid]
                removed = before > len(_demo_configs)
            if removed:
                _demo_next_fire.pop(cid, None)
                try:
                    bot.edit_message_text(
                        f"✅🔥 <b>Config deleted!</b>\n\n" + demo_status_text(),
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML",
                    )
                except Exception:
                    pass
            else:
                bot.answer_callback_query(call.id, "❌ Config not found!", show_alert=True)

        elif data.startswith("msgicon_set:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            slot_key = data.split(":", 1)[1]
            if slot_key not in _MSG_ICON_SLOTS:
                bot.answer_callback_query(call.id, "❌ Unknown slot!", show_alert=True)
                return
            default_char, label = _MSG_ICON_SLOTS[slot_key]
            uid = call.from_user.id
            _msg_icon_set_state[uid] = {"key": slot_key}
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"✨ <b>Message Icon Set</b>\n\n"
                f"📌 <b>Slot:</b> <code>{{emoji_{slot_key}}}</code>\n"
                f"🏷️ <b>Label:</b> {label}\n"
                f"🔘 <b>Default:</b> {default_char}\n\n"
                f"Custom emoji sticker send (Telegram premium emoji), or enter the emoji ID:\n"
                f"<i>Type /back to cancel</i>",
                parse_mode="HTML",
                reply_markup=_back_admin_kb(),
            )
            bot.register_next_step_handler(msg, _set_msg_icon_step)
            bot.answer_callback_query(call.id)

        elif data.startswith("msgicon_reset:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            slot_key = data.split(":", 1)[1]
            with _custom_emoji_lock:
                removed = _custom_emojis.get("msg_slots", {}).pop(slot_key, None)
            if removed:
                _save_custom_emojis()
                bot.answer_callback_query(call.id, f"✅ '{slot_key}' reset to default!", show_alert=False)
            else:
                bot.answer_callback_query(call.id, "Already at default.", show_alert=False)
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            _show_edit_messages_menu(call.message)

        # ── Withdraw / Payment callbacks ──────────────────────────────────────
        elif data == "wd_start":
            bot.answer_callback_query(call.id)
            _start_withdraw(call.message)

        elif data == "wd_cancel":
            uid = call.from_user.id
            _withdraw_state.pop(uid, None)
            bot.answer_callback_query(call.id, "❌ Cancelled.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(call.message.chat.id, "❌ Withdraw cancelled.",
                             reply_markup=main_menu(uid), parse_mode="HTML")

        elif data.startswith("wd_method:"):
            uid = call.from_user.id
            method = data.split(":", 1)[1]
            state = _withdraw_state.get(uid)
            if not state:
                bot.answer_callback_query(call.id, "❌ Session expired. Please try again.")
                return
            state["method"] = method
            bot.answer_callback_query(call.id, f"✅ {method} selected.")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            msg = bot.send_message(
                call.message.chat.id,
                f"📲 <b>{method}</b> account number/address:\n\n"
                f"Example bKash: <code>01XXXXXXXXX</code>",
                parse_mode="HTML",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
            )
            bot.register_next_step_handler(msg, _wd_account_step)

        elif data == "wd_confirm_submit":
            uid = call.from_user.id
            state = _withdraw_state.pop(uid, None)
            if not state:
                bot.answer_callback_query(call.id, "❌ Session expired. Please try again.")
                return
            amount  = state.get("amount", 0)
            method  = state.get("method", "?")
            account = state.get("account", "?")
            ok, new_bal = deduct_balance(uid, amount)
            if not ok:
                bot.answer_callback_query(call.id, "❌ Insufficient balance!", show_alert=True)
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                return
            cur = get_currency()
            import time as _time
            req_id = f"{uid}_{int(_time.time())}"
            req = {
                "id": req_id, "uid": uid, "amount": amount,
                "method": method, "account": account,
                "status": "pending", "timestamp": _time.time(),
            }
            with _withdraw_lock:
                _withdraw_requests.append(req)
            _save_withdraws()
            bot.answer_callback_query(call.id, "✅ Request submitted!")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            bot.send_message(
                call.message.chat.id,
                f"✅ <b>Withdraw Request Submitted!</b>\n\n"
                f"💵 Amount: <code>{cur}{amount:.2f}</code>\n"
                f"📲 Method: <b>{method}</b>\n"
                f"📋 Account: <code>{account}</code>\n"
                f"💰 Remaining Balance: <code>{cur}{new_bal:.2f}</code>\n\n"
                f"Payment will be made after admin approval.",
                parse_mode="HTML",
                reply_markup=main_menu(uid),
            )
            # Notify all admins
            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(
                types.InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve:{req_id}"),
                types.InlineKeyboardButton("❌ Reject",  callback_data=f"wd_reject:{req_id}"),
            )
            uname = call.from_user.username or call.from_user.first_name or str(uid)
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(
                        admin_id,
                        f"⏳ <b>New Withdraw Request!</b>\n\n"
                        f"👤 User: @{uname} (<code>{uid}</code>)\n"
                        f"💵 Amount: <code>{cur}{amount:.2f}</code>\n"
                        f"📲 Method: <b>{method}</b>\n"
                        f"📋 Account: <code>{account}</code>\n"
                        f"🔑 ID: <code>{req_id}</code>",
                        parse_mode="HTML",
                        reply_markup=admin_markup,
                    )
                except Exception:
                    pass

        elif data.startswith("wd_approve:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            req_id = data.split(":", 1)[1]
            req = None
            with _withdraw_lock:
                for r in _withdraw_requests:
                    if r["id"] == req_id and r["status"] == "pending":
                        r["status"] = "approved"
                        req = r
                        break
            if not req:
                bot.answer_callback_query(call.id, "❌ Request not found or already processed.", show_alert=True)
                return
            _save_withdraws()
            cur = get_currency()
            bot.answer_callback_query(call.id, "✅ Approved!")
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                bot.edit_message_text(
                    call.message.text + "\n\n✅ <b>Approved!</b>",
                    call.message.chat.id, call.message.message_id, parse_mode="HTML"
                )
            except Exception:
                pass
            try:
                bot.send_message(
                    req["uid"],
                    f"✅ <b>Withdraw Approved!</b>\n\n"
                    f"💵 Amount: <code>{cur}{req['amount']:.2f}</code>\n"
                    f"📲 Method: <b>{req['method']}</b>\n"
                    f"📋 Account: <code>{req['account']}</code>\n\n"
                    f"Payment will be sent shortly. Thank you! 🎉",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data.startswith("wd_reject:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!")
                return
            req_id = data.split(":", 1)[1]
            req = None
            with _withdraw_lock:
                for r in _withdraw_requests:
                    if r["id"] == req_id and r["status"] == "pending":
                        r["status"] = "rejected"
                        req = r
                        break
            if not req:
                bot.answer_callback_query(call.id, "❌ Request not found or already processed.", show_alert=True)
                return
            # Refund the balance
            add_reward(req["uid"], req["amount"])
            _save_withdraws()
            cur = get_currency()
            bot.answer_callback_query(call.id, "❌ Rejected, balance refunded.")
            try:
                bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
                bot.edit_message_text(
                    call.message.text + "\n\n❌ <b>Rejected.</b>",
                    call.message.chat.id, call.message.message_id, parse_mode="HTML"
                )
            except Exception:
                pass
            try:
                bot.send_message(
                    req["uid"],
                    f"❌ <b>Withdraw Rejected.</b>\n\n"
                    f"💵 Amount: <code>{cur}{req['amount']:.2f}</code> has been refunded to your balance.\n\n"
                    f"Please contact the admin for assistance.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data in ("msgicon_close", "msgicon_noop"):
            if data == "msgicon_close":
                try:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
            bot.answer_callback_query(call.id)

        elif data.startswith("editmsg:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            key = data.split(":", 1)[1]
            if key in _TEMPLATE_LABELS:
                _ask_new_template(call, key)
            else:
                bot.answer_callback_query(call.id, "❌ Unknown template!", show_alert=True)

        elif data.startswith("editmsg_reset:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            key = data.split(":", 1)[1]
            if key in _DEFAULT_TEMPLATES:
                _templates[key] = _DEFAULT_TEMPLATES[key]
                save_templates()
                bot.answer_callback_query(call.id, f"✅ '{key}' reset to default!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ Unknown template!", show_alert=True)

        elif data == "editmsg_reset_all":
            if call.from_user.id not in ADMIN_IDS:
                return
            _templates.update(_DEFAULT_TEMPLATES)
            save_templates()
            try:
                bot.edit_message_text(
        "✅🔥 <b>All messages reset to default!</b>\n\n"
        "<i>All messages will now use the default format.</i>",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML",
                )
            except Exception:
                pass

        elif data == "grp_info":
            if call.from_user.id not in ADMIN_IDS:
                return
            _show_settings_inline(call)

        elif data == "set_autodel":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("auto_delete", True)
            _group_settings["auto_delete"] = not cur
            save_group_settings()
            bot.answer_callback_query(
                call.id,
                "✅ Auto Delete: " + ("🟢 ON" if not cur else "🔴 OFF"),
                show_alert=False,
            )
            _show_settings_inline(call)

        elif data == "toggle_v3":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("v3_enabled", True)
            _group_settings["v3_enabled"] = not cur
            save_group_settings()
            bot.answer_callback_query(
                call.id,
                "✅ V3 Panel: " + ("🟢 ON" if not cur else "🔴 OFF"),
                show_alert=False,
            )
            _show_settings_inline(call)

        elif data == "toggle_v2_mode":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("v2_user_mode", False)
            _group_settings["v2_user_mode"] = not cur
            save_group_settings()
            bot.answer_callback_query(
                call.id,
                "✅ Get Number Mode: " + ("🟢 ON" if not cur else "🔴 OFF"),
                show_alert=False,
            )
            _show_settings_inline(call)

        elif data == "toggle_grp_send":
            if call.from_user.id not in ADMIN_IDS:
                return
            cur = _group_settings.get("group_otp_send", True)
            _group_settings["group_otp_send"] = not cur
            save_group_settings()
            new_state = not cur
            bot.answer_callback_query(
                call.id,
                "✅ Group OTP Send: " + ("🟢 ON — OTP will go to the group" if new_state else "🔴 OFF — Will go to inbox only"),
                show_alert=True,
            )
            _show_settings_inline(call)

        elif data == "set_channel2":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "📢 <b>Enter new Join Channel link:</b>\n\n"
                "<i>Example: https://t.me/aR_OTP_rcv</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_channel2)

        elif data == "set_botlink":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "🤖 <b>Enter new Bot link:</b>\n\n"
                "<i>Example: https://t.me/ar_otp_bot</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_botlink)

        elif data == "grp_setlink":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "🔗 <b>Enter new OTP Group Link:</b>\n\n"
                "<i>Example: https://t.me/aR_OTP_rcv</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _grp_get_link)

        elif data == "grp_setid":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                "🆔 <b>Enter new OTP Group Chat ID:</b>\n\n"
                "<i>Example: -1001234567890</i>\n"
                "⚠️ Must be a negative number (group ID is always negative)",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _grp_get_id)

        elif data == "grp_remove":
            if call.from_user.id not in ADMIN_IDS:
                return
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("✅ Haa, Remove", callback_data="grp_removeok", style="success"),
                types.InlineKeyboardButton("❌ Cancel", callback_data="grp_info", style="primary"),
            )
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                "⚠️ <b>CONFIRM GROUP REMOVE</b> ⚠️\n\n"
                "OTP Group setting will be reset!\n"
                "Sending OTPs to the group will stop.\n\n"
                "Sure?",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )

        elif data.startswith("v2svc:"):
            sid = data.split(":", 1)[1]
            services = _v2_active_liveaccess()
            svc_data = next((s for s in services if s.get("sid") == sid), None)
            if not svc_data:
                bot.answer_callback_query(call.id, "❌ Service not found!", show_alert=True)
                return
            ranges = svc_data.get("ranges", [])
            markup = types.InlineKeyboardMarkup(row_width=2)
            rng_btns = []
            for rng in ranges:
                prefix = rng.rstrip("X")
                c_name, flag = get_country_details(prefix)
                short = c_name.split()[0] if c_name and c_name != "Unknown" else ""
                label = f"{short} | {rng}" if short else f"{rng}"
                rng_btns.append(types.InlineKeyboardButton(
                    label, callback_data=f"v2rng:{prefix}:{sid}", style="danger",
                    **_flag_btn_kwargs(flag)
                ))
            if rng_btns:
                markup.add(*rng_btns)
            markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="v2back", style="success"))
            bot.edit_message_text(
                f"📡 <b>V2 — {_v2_svc_emoji(sid)} {sid}</b>\n\n"
                f"🔢 <b>Select a range:</b>\n"
                f"<i>Live OTP available in this range — click to get a number</i>",
                call.message.chat.id, call.message.message_id,
                reply_markup=markup, parse_mode="HTML"
            )
            bot.answer_callback_query(call.id)

        elif data.startswith("v2rng:"):
            parts = data.split(":")
            prefix = parts[1] if len(parts) > 1 else ""
            sid = parts[2] if len(parts) > 2 else "?"
            bot.answer_callback_query(call.id, "⏳ Getting number...", show_alert=False)
            uid_v2 = call.from_user.id
            n_batch = get_numbers_per_batch()
            v2_nums = []
            for _ in range(n_batch):
                n = _v2_active_getnum(prefix, sid=sid)
                if n:
                    v2_nums.append(n)
            if v2_nums:
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_v2]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                for vn in v2_nums:
                    register_number(uid_v2, vn)
                c_name, flag = get_country_details(v2_nums[0])
                display_nums = [n if n.startswith("+") else "+" + n for n in v2_nums]
                _user_last_svc[uid_v2] = (sid.lower(), c_name)
                _remember_number_view(
                    uid_v2, sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                refresh_kb = _build_numbers_display_kb(
                    sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                bot.edit_message_text(
                    ".",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=refresh_kb
                )
                _user_last_num_msg[uid_v2] = call.message.message_id
            else:
                bot.answer_callback_query(call.id, "❌ Number not found! Try again later.", show_alert=True)

        elif data == "v2back":
            markup, has_btns = _build_combined_service_markup()
            if has_btns:
                try:
                    bot.edit_message_text(
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        call.message.chat.id, call.message.message_id,
                        reply_markup=markup, parse_mode="HTML"
                    )
                except Exception:
                    bot.send_message(
                        call.message.chat.id,
                        "<tg-emoji emoji-id=\"5202216593966244027\">👤</tg-emoji> <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗦𝗘𝗥𝗩𝗜𝗖𝗘</b>",
                        reply_markup=markup, parse_mode="HTML"
                    )
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "❌ No service available.", show_alert=True)

        elif data.startswith("v2svc_cc:"):
            sid = data.split(":", 1)[1]
            markup, has_btns = _v2_build_country_markup(sid)
            emoji = _v2_svc_emoji(sid)
            if has_btns:
                bot.edit_message_text(
                    "<tg-emoji emoji-id=\"5447410659077661506\">🌏</tg-emoji> <b>SELECT COUNTRY</b>",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=markup, parse_mode="HTML"
                )
            else:
                bot.answer_callback_query(call.id, "❌ No range in this service.", show_alert=True)
            bot.answer_callback_query(call.id)

        elif data.startswith("v2csvc:"):
            parts = data.split(":")
            sid    = parts[1] if len(parts) > 1 else "?"
            prefix = parts[2] if len(parts) > 2 else ""
            bot.answer_callback_query(call.id, "⏳ Getting number...", show_alert=False)
            uid_v2  = call.from_user.id
            n_batch = get_numbers_per_batch()
            v2_nums = []
            for _ in range(n_batch):
                n = _v2_active_getnum(prefix, sid=sid)
                if n:
                    v2_nums.append(n)
            if v2_nums:
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_v2]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                for vn in v2_nums:
                    register_number(uid_v2, vn)
                c_name, flag = get_country_details(v2_nums[0])
                display_nums = [n if n.startswith("+") else "+" + n for n in v2_nums]
                _user_last_svc[uid_v2] = (sid.lower(), c_name)
                _remember_number_view(
                    uid_v2, sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                refresh_kb = _build_numbers_display_kb(
                    sid.lower(), c_name, display_nums, flag, c_name,
                    is_v2=True, v2_prefix=prefix, v2_sid=sid
                )
                bot.edit_message_text(
                    ".",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=refresh_kb
                )
                _user_last_num_msg[uid_v2] = call.message.message_id
            else:
                bot.answer_callback_query(call.id, "❌ Number not found! Try again later.", show_alert=True)

        elif data == "cc_back" or data == "cc_show":
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            try:
                bot.edit_message_text(
                    "📡 <b>Live Console Config</b>\n"
                    "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    "Select service — toggle or add/delete range:\n"
                    "✅ = enabled  ⭕ = disabled",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_services_markup(), parse_mode="HTML"
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id)

        elif data.startswith("cc_svc:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            sid = data.split(":", 1)[1]
            cfg = _console_config.get(sid, {})
            enabled = cfg.get("enabled", False)
            ranges  = cfg.get("ranges", [])
            status  = "✅ Enabled" if enabled else "⭕ Disabled"
            range_txt = "\n".join(
                f"  • {get_country_details(p)[1]} {get_country_details(p)[0]} ({p})"
                for p in ranges
            ) if ranges else "  (no range)"
            try:
                bot.edit_message_text(
                    f"📡 <b>{_v2_svc_emoji(sid)} {sid}</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    f"📌 Status: <b>{status}</b>\n"
                    f"🔢 Ranges:\n{range_txt}\n\n"
                    f"Use the buttons below to configure:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_service_detail_markup(sid), parse_mode="HTML"
                )
            except Exception:
                pass
            bot.answer_callback_query(call.id)

        elif data.startswith("cc_toggle:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            sid = data.split(":", 1)[1]
            cfg = _console_config.setdefault(sid, {"enabled": False, "ranges": []})
            cfg["enabled"] = not cfg.get("enabled", False)
            save_console_config()
            status = "✅ Enabled" if cfg["enabled"] else "⭕ Disabled"
            bot.answer_callback_query(call.id, f"{status}!", show_alert=False)
            ranges = cfg.get("ranges", [])
            range_txt = "\n".join(
                f"  • {get_country_details(p)[1]} {get_country_details(p)[0]} ({p})"
                for p in ranges
            ) if ranges else "  (no range)"
            try:
                bot.edit_message_text(
                    f"📡 <b>{_v2_svc_emoji(sid)} {sid}</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    f"📌 Status: <b>{status}</b>\n"
                    f"🔢 Ranges:\n{range_txt}\n\n"
                    f"Use the buttons below to configure:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_service_detail_markup(sid), parse_mode="HTML"
                )
            except Exception:
                pass

        elif data.startswith("cc_addrange:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            sid = data.split(":", 1)[1]
            _cc_addrange_state[call.from_user.id] = sid
            bot.answer_callback_query(call.id)
            msg = bot.send_message(
                call.message.chat.id,
                f"📲 <b>{sid}</b>  range prefix:\n"
                f"<i>Example: <code>880</code> (Bangladesh), <code>91</code> (India)</i>\n\n"
                f"Numbers only:",
                reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, _cc_addrange_step)

        elif data.startswith("cc_delrange:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            parts = data.split(":")
            sid    = parts[1] if len(parts) > 1 else ""
            prefix = parts[2] if len(parts) > 2 else ""
            cfg = _console_config.get(sid, {})
            if prefix in cfg.get("ranges", []):
                cfg["ranges"].remove(prefix)
                save_console_config()
                bot.answer_callback_query(call.id, f"🗑️ ({prefix}) deleted!", show_alert=False)
            else:
                bot.answer_callback_query(call.id, "❌ Range not found!", show_alert=True)
                return
            ranges = cfg.get("ranges", [])
            range_txt = "\n".join(
                f"  • {get_country_details(p)[1]} {get_country_details(p)[0]} ({p})"
                for p in ranges
            ) if ranges else "  (no range)"
            status = "✅ Enabled" if cfg.get("enabled") else "⭕ Disabled"
            try:
                bot.edit_message_text(
                    f"📡 <b>{_v2_svc_emoji(sid)} {sid}</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                    f"📌 Status: <b>{status}</b>\n"
                    f"🔢 Ranges:\n{range_txt}\n\n"
                    f"Use the buttons below to configure:",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_cc_service_detail_markup(sid), parse_mode="HTML"
                )
            except Exception:
                pass

        elif data.startswith("v2panel_set:"):
            if call.from_user.id not in ADMIN_IDS:
                bot.answer_callback_query(call.id, "❌ No permission!", show_alert=True)
                return
            new_pid = data.split(":", 1)[1]
            valid_ids = {p["id"] for p in _V2_PANELS_REGISTRY}
            if new_pid not in valid_ids:
                bot.answer_callback_query(call.id, "❌ Invalid panel!", show_alert=True)
                return
            _group_settings["v2_active_panel"] = new_pid
            save_group_settings()
            pname = _v2_active_panel_name()
            bot.answer_callback_query(call.id, f"✅ {pname} started!", show_alert=False)
            try:
                bot.edit_message_text(
                    f"📡 <b>V2 Active Panel</b>\n\n"
        f"✅ <b>{pname}</b> is now active.\n\n"
        f"<i>V2 LIVE RANGE and OTP forwarding will come from this panel.</i>",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=_v2_panel_toggle_markup(),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        elif data.startswith("v3svc:"):
            sid = data.split(":", 1)[1]
            bot.answer_callback_query(call.id, "⏳ Getting number...", show_alert=False)
            uid_v3 = call.from_user.id
            n_batch = get_numbers_per_batch()
            v3_nums = []
            for _ in range(n_batch):
                n = _v3_getnum(sid)
                if n:
                    v3_nums.append(n)
            if v3_nums:
                with user_map_lock:
                    old_nums = [k for k, v in user_map.items() if v == uid_v3]
                    for old_clean in old_nums:
                        user_map.pop(old_clean, None)
                        assigned_time.pop(old_clean, None)
                if old_nums:
                    _save_user_map()
                for vn in v3_nums:
                    register_number(uid_v3, vn)
                c_name, flag = get_country_details(v3_nums[0])
                display_nums = [n if n.startswith("+") else "+" + n for n in v3_nums]
                _user_last_svc[uid_v3] = (sid.lower(), c_name)
                _remember_number_view(
                    uid_v3, sid.lower(), c_name, display_nums, flag, c_name
                )
                refresh_kb = _build_numbers_display_kb(
                    sid.lower(), c_name, display_nums, flag, c_name
                )
                bot.edit_message_text(
                    ".",
                    call.message.chat.id, call.message.message_id,
                    reply_markup=refresh_kb
                )
                _user_last_num_msg[uid_v3] = call.message.message_id
            else:
                bot.answer_callback_query(call.id, "❌ Number not found! Try again later.", show_alert=True)

        elif data == "v3back":
            services = _v3_get_services()
            markup, has = _v3_build_console_markup(services)
            text = (
                "🆕 <b>V3 PANEL</b>\n"
                "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                "🔴 <b>Select a service:</b>\n"
                "<i>Click a service to get a number</i>\n\n"
                "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>"
                if has else
                "🆕 <b>V3 PANEL</b>\n\n⚠️ No service available."
            )
            try:
                bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                      reply_markup=markup, parse_mode="HTML")
            except Exception:
                pass
            bot.answer_callback_query(call.id)

        elif data == "eg_add":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            msg = bot.send_message(call.message.chat.id,
                "➕ <b>Extra Group Add</b>\n\n"
                "Enter the group's <b>Chat ID</b>:\n"
                "<i>Example: <code>-1001234567890</code></i>\n\n"
                "💡 To get Chat ID, add @userinfobot to the group.",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            bot.register_next_step_handler(msg, _eg_add_step1)

        elif data.startswith("eg_del:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            extra = _group_settings.get("extra_groups", [])
            if 0 <= idx < len(extra):
                removed = extra.pop(idx)
                save_group_settings()
                bot.answer_callback_query(call.id, f"✅ Group {removed.get('id')} removed!", show_alert=True)
                _show_extra_groups(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ Group not found.", show_alert=True)

        elif data.startswith("eg_setbot:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            bot.answer_callback_query(call.id)
            _eg_state[call.from_user.id] = {"_edit_idx": idx, "_field": "bot_link"}
            msg = bot.send_message(call.message.chat.id,
                f"🤖 <b>Group #{idx+1} Bot Link</b>\n\nEnter new bot link (skip = <code>skip</code>):",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            bot.register_next_step_handler(msg, _eg_edit_link_step)

        elif data.startswith("eg_setch:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            bot.answer_callback_query(call.id)
            _eg_state[call.from_user.id] = {"_edit_idx": idx, "_field": "channel_link"}
            msg = bot.send_message(call.message.chat.id,
                f"📢 <b>Group #{idx+1} Channel Link</b>\n\nEnter new channel link (skip = <code>skip</code>):",
                reply_markup=_back_admin_kb(), parse_mode="HTML")
            bot.register_next_step_handler(msg, _eg_edit_link_step)

        elif data.startswith("eg_test:"):
            if call.from_user.id not in ADMIN_IDS:
                return
            idx = int(data.split(":", 1)[1])
            extra = _group_settings.get("extra_groups", [])
            if 0 <= idx < len(extra):
                g = extra[idx]
                gid = g.get("id")
                bot.answer_callback_query(call.id, "🧪 Sending test message...")
                try:
                    bot.send_message(
                        gid,
                        f"🧪 <b>Test Message</b>\n\n"
                        f"✅ Bot is successfully sending messages to this group!\n"
                        f"🆔 Group ID: <code>{gid}</code>\n\n"
                        f"<i>OTP will be sent here when received.</i>",
                        parse_mode="HTML",
                    )
                    bot.send_message(
                        call.message.chat.id,
                        f"✅ <b>Group #{idx+1} Test Successful!</b>\n\n"
                        f"🆔 ID: <code>{gid}</code>\n"
                        f"Bot can send messages to that group. OTP will be sent there.",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    bot.send_message(
                        call.message.chat.id,
                        f"❌ <b>Group #{idx+1} Test Failed!</b>\n\n"
                        f"🆔 ID: <code>{gid}</code>\n"
                        f"⚠️ Error: <code>{str(e)[:200]}</code>\n\n"
                        f"<b>Solution:</b>\n"
                        f"• Add the bot as <b>Admin</b> in that group\n"
                        f"• Check if the Group ID is correct\n"
                        f"• Group ID is usually in <code>-100XXXXXXXXXX</code> format",
                        parse_mode="HTML",
                    )
            else:
                bot.answer_callback_query(call.id, "❌ Group not found.", show_alert=True)

        elif data.startswith("eg_info:"):
            idx = int(data.split(":", 1)[1])
            extra = _group_settings.get("extra_groups", [])
            if 0 <= idx < len(extra):
                g = extra[idx]
                bot.answer_callback_query(
                    call.id,
                    f"ID: {g.get('id')}\nBot: {g.get('bot_link') or '—'}\nCh: {g.get('channel_link') or '—'}",
                    show_alert=True
                )
            else:
                bot.answer_callback_query(call.id, "❌ Not found", show_alert=True)

        elif data == "grp_removeok":
            if call.from_user.id not in ADMIN_IDS:
                return
            _group_settings["otp_group_id"] = None
            _group_settings["otp_group_link"] = ""
            save_group_settings()
            bot.answer_callback_query(call.id, "✅ Group removed!")
            _show_settings_inline(call)

        elif data == "set_group_tag":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            cur_tag = _group_settings.get("group_tag", "BOT")
            msg = bot.send_message(
                call.message.chat.id,
                f"🌸 <b>Number Tag Set/Change</b>\n\n"
                f"🔹 <b>Bortoman Tag:</b> <code>{cur_tag}</code>\n"
                f'📱 Preview: <b>245<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{cur_tag}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>5660</b>\n\n'
                f"Enter new tag (text only, no emoji):\n"
                f"<i>Example: ATIK, BOT, OTP, KING</i>",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_group_tag)

        elif data == "set_num_batch":
            if call.from_user.id not in ADMIN_IDS:
                return
            bot.answer_callback_query(call.id)
            cur_batch = _group_settings.get("numbers_per_batch", 1)
            msg = bot.send_message(
                call.message.chat.id,
                f"🔢 <b>Numbers Per User — Set</b>\n\n"
                f"🔹 <b>Current Setting:</b> <code>{cur_batch}</code>\n\n"
                f"How many numbers can a user get at once?\n"
                f"<i>Example: 1, 2, 3, 5 (max 10)</i>\n\n"
                f"⚠️ This setting applies to all V1, V2.",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, _sett_get_num_batch)

    except Exception as e:
        print(f"Callback Error: {e}")


# ── Excel / CSV helpers ───────────────────────────────────────────────────────

def _get_valid_services():
    """Return list of valid service keys from live _services list."""
    return [s["key"] for s in _services]

VALID_SERVICES = [
    "facebook",
    "instagram",
    "whatsapp",
    "telegram",
    "binance",
    "pc clone",
]


def _parse_spreadsheet(data: bytes, filename: str):
    """
    Parse Excel (.xlsx / .xls) or CSV file.
    Returns:
      - (rows, mode)
        mode='two_col' → rows = list of (service, number)
        mode='one_col' → rows = list of number strings
    Accepts header rows with 'service'/'number' labels.
    Falls back: 2-column files = service+number, 1-column = numbers only.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    raw_rows = []

    if ext == "csv":
        text = data.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            cleaned = [c.strip() for c in row if c.strip()]
            if cleaned:
                raw_rows.append(cleaned)
    elif ext == "xlsx":
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        def _xlsx_cell_str(c):
            if isinstance(c, float) and c.is_integer():
                return str(int(c))
            return str(c)
        for row in ws.iter_rows(values_only=True):
            cleaned = [_xlsx_cell_str(c).strip() for c in row if c is not None and _xlsx_cell_str(c).strip()]
            if cleaned:
                raw_rows.append(cleaned)
    elif ext == "xls":
        wb = xlrd.open_workbook(file_contents=data)
        ws = wb.sheet_by_index(0)
        def _xls_cell_str(cv):
            if isinstance(cv, float) and cv.is_integer():
                return str(int(cv))
            return str(cv)
        for ri in range(ws.nrows):
            cleaned = [
                _xls_cell_str(ws.cell_value(ri, ci)).strip()
                for ci in range(ws.ncols)
                if _xls_cell_str(ws.cell_value(ri, ci)).strip()
            ]
            if cleaned:
                raw_rows.append(cleaned)
    else:
        return [], "unknown"

    if not raw_rows:
        return [], "empty"

    # Detect header row
    start = 0
    first = [c.lower() for c in raw_rows[0]]
    if any(h in first for h in ("service", "number", "phone", "mobile")):
        start = 1

    data_rows = raw_rows[start:]
    if not data_rows:
        return [], "empty"

    # Detect mode by column count of the majority of rows
    two_col_count = sum(1 for r in data_rows if len(r) >= 2)
    one_col_count = len(data_rows) - two_col_count

    if two_col_count > one_col_count:
        result = []
        for r in data_rows:
            if len(r) < 2:
                continue
            col0, col1 = r[0], r[1]
            # Determine which column is service and which is number
            col0_is_num = re.match(r"^\+?\d{6,15}$", re.sub(r"\s", "", col0))
            col1_is_num = re.match(r"^\+?\d{6,15}$", re.sub(r"\s", "", col1))
            if col0_is_num and not col1_is_num:
                svc = col1.lower().strip()
                num = re.sub(r"\D", "", col0)
            elif col1_is_num and not col0_is_num:
                svc = col0.lower().strip()
                num = re.sub(r"\D", "", col1)
            else:
                svc = col0.lower().strip()
                num = re.sub(r"\D", "", col1)
            if num and len(num) >= 7:
                result.append((svc, num))
        return result, "two_col"
    else:
        result = []
        for r in data_rows:
            num = re.sub(r"\D", "", r[0])
            if len(num) >= 7:
                result.append(num)
        return result, "one_col"


def _notify_new_numbers(svc, c_name, flag, total_added):
    """Broadcast NEW NUMBERS notification to all registered users + main group + extra groups."""
    _NEW_SEP = ''.join(['<tg-emoji emoji-id="5870818207383686839">➖</tg-emoji>'] * 8)
    _added_icon = '<tg-emoji emoji-id="5267041999948653482">📤</tg-emoji>'
    _svc_e = _v2_svc_emoji(svc)
    text = (
        f"{_NEW_SEP}\n"
        f'<tg-emoji emoji-id="5296633779157243809">🆕</tg-emoji> 《 NEW NUMBERS 》\n'
        f"{_NEW_SEP}\n"
        f"{_resolve_flag(flag)} {c_name.upper()} {_svc_e} {svc.upper()}\n"
        f"{_NEW_SEP}\n"
        f'{_added_icon} Total Added: {total_added} <tg-emoji emoji-id="5251338246599765890">✅</tg-emoji>\n'
        f"{_NEW_SEP}\n"
        f'<tg-emoji emoji-id="5375338737028841420">🚀</tg-emoji> Use /start to get your numbers! <tg-emoji emoji-id="5251203410396458957">👉</tg-emoji>'
    )
    def _send():
        # Send to main group
        main_grp = get_otp_group_id()
        if main_grp:
            try:
                bot.send_message(main_grp, text, parse_mode="HTML")
            except Exception as _eg:
                print(f"[NEW-NUM] Main group send error: {_eg}")
        # Send to extra groups
        for eg in _group_settings.get("extra_groups", []):
            eg_id = eg.get("id")
            if eg_id:
                try:
                    bot.send_message(eg_id, text, parse_mode="HTML")
                except Exception as _eg:
                    print(f"[NEW-NUM] Extra group {eg_id} send error: {_eg}")
        # Send to all registered users (inbox)
        for uid in list(users):
            try:
                bot.send_message(uid, text, parse_mode="HTML")
                time.sleep(0.05)
            except Exception:
                pass
    threading.Thread(target=_send, daemon=True).start()


def _add_numbers_bulk(svc: str, numbers: list, notify=True):
    """Add a list of number strings to stock[svc]. Returns (added, skipped)."""
    added, skipped = 0, 0
    first_num = None
    svc = svc.lower().strip()
    # Auto-create service in stock if it exists in _services list but not in stock
    if svc not in stock:
        valid_keys = [s["key"] for s in _services]
        if svc not in valid_keys:
            return 0, len(numbers)
        stock[svc] = {}
    for num in numbers:
        num = re.sub(r"\D", "", str(num))
        if not num:
            skipped += 1
            continue
        c_name, _ = get_country_details(num)
        if c_name == "Unknown":
            skipped += 1
            continue
        if first_num is None:
            first_num = num
        if c_name not in stock[svc]:
            stock[svc][c_name] = []
        stock[svc][c_name].append(num)
        added += 1
    if added:
        save_stock()
        if notify and first_num:
            c_name, flag = get_country_details(first_num)
            _notify_new_numbers(svc, c_name, flag, added)
    return added, skipped


def _service_select_markup():
    """Build service selection keyboard from live _services list."""
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    labels = [s["label"].split("→")[0].split("💎")[0].strip() for s in _services]
    if labels:
        m.add(*labels)
    else:
        m.add("Facebook", "Instagram", "WhatsApp", "Telegram", "Binance", "PC Clone")
    return m


_SVC_PLAIN_EMOJI = {
    "instagram": "📸", "facebook": "🔵", "telegram": "✈️",
    "whatsapp": "💚", "tiktok": "🎵", "twitter": "🐦",
    "binance": "🟡", "snapchat": "👻", "google": "🔴",
    "youtube": "📺", "linkedin": "💼", "amazon": "🛒",
    "pc clone": "📱",
}


def _admin_add_svc_keyboard():
    """Reply keyboard for admin Number Add — styled KeyboardButtons with custom emoji icons."""
    _colors = ["primary", "success", "danger"]
    KB = types.KeyboardButton
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    svcs = _services if _services else [
        {"key": k, "label": k.title()}
        for k in ["facebook", "instagram", "whatsapp", "telegram", "binance", "pc clone"]
    ]
    btns = []
    for i, svc in enumerate(svcs):
        key = svc["key"].lower()
        label = svc["label"].split("→")[0].split("💎")[0].strip()
        icon_id = _svc_icon_emoji_id(key)
        icon_kwargs = {"icon_custom_emoji_id": icon_id} if icon_id else {}
        btns.append(KB(label, style=_colors[i % 3], **icon_kwargs))
    m.add(*btns)
    m.add(KB("❌ Cancel", style="danger"))
    return m


@bot.message_handler(content_types=["document"])
def document_handler(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    # If user is in finalize_auto_add Excel-wait flow, let the next_step_handler handle it
    if uid in _awaiting_slot_excel:
        return
    register_user(message.chat.id)

    doc = message.document
    name = doc.file_name or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    # ── .txt / .json handler — auto-detect service emoji or flag file ───────────
    if ext in ("txt", "json"):
        wait = bot.send_message(message.chat.id,
            f"⏳ <b>{name}</b> parsing...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
            txt_content = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            bot.edit_message_text(f"❌ File download hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return
        import re as _re

        _KNOWN_SVCS = {
            "INSTAGRAM","FACEBOOK","WHATSAPP","TELEGRAM","TIKTOK","TWITTER",
            "BINANCE","SNAPCHAT","GOOGLE","YOUTUBE","LINKEDIN","AMAZON",
            "TINDER","UBER","NETFLIX","SPOTIFY","VIBER","LINE","WECHAT",
            "DISCORD","REDDIT","PINTEREST","TUMBLR","SIGNAL","SKYPE",
        }

        def _parse_service_emoji_txt(content):
            """Extract {SERVICE_NAME: emoji_id} from any common format."""
            result = {}
            # Try whole-file JSON first
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    for k, v in data.items():
                        svc = str(k).upper().strip()
                        eid_m = _re.search(r'\d{10,}', str(v))
                        if svc and eid_m:
                            result[svc] = eid_m.group(0)
                    return result
            except Exception:
                pass
            # Line-by-line: find first word-like token + any 10-digit number on same line
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                eid_m = _re.search(r'(\d{10,})', line)
                if not eid_m:
                    continue
                eid = eid_m.group(1)
                prefix = line[:line.index(eid)]
                svc_m = _re.search(r'([A-Za-z][A-Za-z0-9 _\-]{1,20})', prefix)
                if svc_m:
                    svc = _re.sub(r'[\s\-_]+', '_', svc_m.group(1).strip()).upper().rstrip('_:→- ')
                    if svc:
                        result[svc] = eid
            return result

        def _is_service_file(content):
            """Return True if any line has a known service keyword + 10-digit number."""
            for line in content.splitlines():
                ul = line.upper()
                if _re.search(r'\d{10,}', ul):
                    for svc in _KNOWN_SVCS:
                        if svc in ul:
                            return True
            # Also detect JSON with service-like keys
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    for k in data:
                        if str(k).upper() in _KNOWN_SVCS:
                            return True
            except Exception:
                pass
            return False

        # Auto-detect: service emoji file or flag file?
        if ext == "json" or _is_service_file(txt_content):
            # ── Service emoji file ──────────────────────────────────────────
            svc_loaded = _parse_service_emoji_txt(txt_content)
            try:
                bot.delete_message(message.chat.id, wait.message_id)
            except Exception:
                pass
            if not svc_loaded:
                bot.send_message(message.chat.id,
                    "❌ <b>Service emoji data parse hoyni!</b>\n\n"
                    "<b>TXT format:</b>\n"
                    "<code>WHATSAPP 5334998226636390258\nINSTAGRAM 5319160079465857105</code>\n\n"
                    "<b>JSON format:</b>\n"
                    "<code>{\"WHATSAPP\": \"5334998226636390258\"}</code>",
                    parse_mode="HTML")
                return
            with _custom_emoji_lock:
                _custom_emojis.setdefault("services", {}).update(svc_loaded)
            _save_custom_emojis()
            lines_preview = "\n".join(
                f"  🎯 <b>{k}</b> → <code>{v}</code>"
                for k, v in list(svc_loaded.items())[:20])
            extra = f"\n  <i>...and {len(svc_loaded)-20} more</i>" if len(svc_loaded) > 20 else ""
            bot.send_message(message.chat.id,
                f"✅ <b>{len(svc_loaded)} service emojis set!</b>\n\n"
                f"{lines_preview}{extra}\n\n"
                f"🎉 Ekhon OTP message-e custom emoji dekhabe.",
                parse_mode="HTML")
            return
        # ── Flag emoji file (original .txt handler) ─────────────────────────
        parsed = {}
        for line in txt_content.splitlines():
            line = line.strip()
            if not line:
                continue
            m = _re.search(r'([🇠-🇿]{2}).*?"id"\s*:\s*"(\d+)"', line)
            if m:
                parsed[m.group(1)] = m.group(2)
                continue
            tokens = line.split()
            if len(tokens) >= 2 and tokens[-1].isdigit() and len(tokens[-1]) >= 10:
                flag_tok = next((t for t in tokens if len(t) == 2 and
                    all('🇠' <= c <= '🇿' for c in t)), None)
                if flag_tok:
                    parsed[flag_tok] = tokens[-1]
        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass
        if not parsed:
            bot.send_message(message.chat.id,
                "❌ <b>Flag data parse hoyni!</b>\n\n"
                "Flag file format:\n"
                "<code>(1)(US)🇺🇸 United States {\"emoji\": \"🇺🇸\", \"id\": \"123...\"}</code>\n\n"
                "Service emoji file format:\n"
                "<code>WHATSAPP 5334998226636390258\nINSTAGRAM 5319160079465857105</code>",
                parse_mode="HTML")
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        lines_preview = "\n".join(
            f"  {k} → <code>{v}</code>" for k, v in list(parsed.items())[:10]
        )
        extra = f"\n  <i>...and {len(parsed)-10} more</i>" if len(parsed) > 10 else ""
        bot.send_message(message.chat.id,
            f"✅ <b>{len(parsed)} custom flag emoji(s) loaded!</b>\n\n"
            f"{lines_preview}{extra}\n\n"
            f"🎉 Custom flags will now appear in all OTP/number messages.",
            parse_mode="HTML")
        return
    # ────────────────────────────────────────────────────────────────────────────

    # ── .json service emoji file handler ────────────────────────────────────────
    if ext == "json":
        wait = bot.send_message(message.chat.id,
            f"⏳ <b>{name}</b> parsing...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
            data = json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception as e:
            bot.edit_message_text(f"❌ File load/parse hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return

        if not isinstance(data, dict):
            bot.edit_message_text(
                "❌ <b>Invalid format!</b>\n\n"
                "The JSON file should be:\n"
                "<code>{\n"
                '  "WHATSAPP": "5334998226636390258",\n'
                '  "INSTAGRAM": "5319160079465857105",\n'
                '  "FACEBOOK": "5323261730283863478"\n'
                "}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return

        loaded = {}
        skipped = []
        for svc_raw, eid in data.items():
            svc = str(svc_raw).upper().strip()
            eid = str(eid).strip()
            if not svc or not eid.isdigit():
                skipped.append(f"{svc_raw}: {eid}")
                continue
            loaded[svc] = eid

        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass

        if not loaded:
            bot.send_message(message.chat.id,
                "❌ <b>Kono valid service emoji ID pawa jayni!</b>\n\n"
                "Check the format:\n"
                "<code>{\"WHATSAPP\": \"5334998226636390258\"}</code>",
                parse_mode="HTML")
            return

        with _custom_emoji_lock:
            _custom_emojis.setdefault("services", {}).update(loaded)
        _save_custom_emojis()

        lines_preview = "\n".join(
            f"  🎯 <b>{k}</b> → <code>{v}</code>" for k, v in list(loaded.items())[:20]
        )
        extra = f"\n  <i>...and {len(loaded)-20} more</i>" if len(loaded) > 20 else ""
        skip_txt = ""
        if skipped:
            skip_txt = f"\n\n⚠️ <b>Skipped ({len(skipped)}):</b> {', '.join(skipped[:5])}"

        bot.send_message(message.chat.id,
            f"✅ <b>{len(loaded)} service emoji IDs set!</b>\n\n"
            f"{lines_preview}{extra}{skip_txt}\n\n"
            f"🎉 From now on, custom service emojis will show in OTP messages.",
            parse_mode="HTML")
        return
    # ────────────────────────────────────────────────────────────────────────────

    if ext not in ("xlsx", "xls", "csv"):
        bot.send_message(
            message.chat.id,
            "❌ <b>Unsupported file!</b>\n\n"
            "📎 Supported formats:\n"
            "  • <b>.txt</b>  — Premium Flag file\n"
            "  • <b>.json</b> — Service Emoji ID file\n"
            "  • <b>.xlsx</b> — Excel (new)\n"
            "  • <b>.xls</b>  — Excel (old)\n"
            "  • <b>.csv</b>  — CSV\n\n"
            "💡 File pathao abar!",
            parse_mode="HTML",
        )
        return

    wait = bot.send_message(
        message.chat.id, f"⏳🔥 <b>{name}</b> parsing...", parse_mode="HTML"
    )

    try:
        file_info = bot.get_file(doc.file_id)
        raw = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.edit_message_text(
            f"❌ File download hoyni: {e}",
            message.chat.id,
            wait.message_id,
            parse_mode="HTML",
        )
        return

    rows, mode = _parse_spreadsheet(raw, name)

    try:
        bot.delete_message(message.chat.id, wait.message_id)
    except Exception:
        pass

    if mode in ("unknown", "empty") or not rows:
        bot.send_message(
            message.chat.id,
            "⚠️ <b>File-e kono data paini!</b> ⚠️\n\n"
            "📋 <b>Supported formats:</b>\n"
            "  • <b>2-column:</b>  Service | Number\n"
            "  • <b>1-column:</b>  Number only (add service afterward)\n\n"
            "💡 Sample format:\n"
            "<code>facebook  | 8801700123456\n"
            "whatsapp  | 8801800234567\n"
            "telegram  | 251912345678</code>",
            parse_mode="HTML",
        )
        return

    if mode == "two_col":
        # Group by service and add directly
        service_map = {}
        for svc, num in rows:
            service_map.setdefault(svc, []).append(num)

        total_added, total_skipped = 0, 0
        report_lines = ""
        for svc, nums in service_map.items():
            added, skipped = _add_numbers_bulk(svc, nums)
            total_added += added
            total_skipped += skipped
            icon = "✅" if added else "⚠️"
            report_lines += f"{icon} <b>{svc.upper()}</b>: +{added} added"
            if skipped:
                report_lines += f"  (⚠️ {skipped} skip)"
            report_lines += "\n"

        bot.send_message(
            message.chat.id,
            f"📊🔥 <b>EXCEL IMPORT DONE!</b> 🔥📊\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"📎 <b>File:</b> <code>{name}</code>\n"
            f"📋 <b>Rows parsed:</b> {len(rows)}\n\n"
            f"{report_lines}\n"
            f"✅ <b>Total added:</b> {total_added}\n"
            f"⚠️ <b>Skipped:</b> {total_skipped}\n\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            f"💡 Use /panels to check stock.",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )

    else:
        # one_col: ask which service
        _pending_excel[uid] = {"numbers": rows, "filename": name}
        bot.send_message(
            message.chat.id,
            f"📂🔥 <b>FILE LOADED!</b> 🔥📂\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            f"📎 <b>File:</b> <code>{name}</code>\n"
            f"📱 <b>Numbers found:</b> {len(rows)}\n\n"
            f" <b>Kon service-e add korbo?</b>\n"
            f"⬇️ Choose:",
            reply_markup=_service_select_markup(),
            parse_mode="HTML",
        )
        msg = bot.send_message(
            message.chat.id, "⬇️ Type a service:", parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, _excel_pick_service)


def _excel_pick_service(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _intercept_menu_btn(message):
        _pending_excel.pop(uid, None)
        return
    svc_raw = (message.text or "").strip().lower()

    # Build dynamic match map from live _services list
    svc = None
    live_valid = _get_valid_services()  # e.g. ["facebook", "instagram", "pc clone", ...]
    # Direct key match first
    for key in live_valid:
        if svc_raw == key:
            svc = key
            break
    # Label match (strip decorators like →, 💎)
    if svc is None:
        for s in _services:
            label_clean = s["label"].split("→")[0].split("💎")[0].strip().lower()
            if svc_raw == label_clean or svc_raw == s["key"]:
                svc = s["key"]
                break
    # Common short aliases (always useful)
    if svc is None:
        _aliases = {
            "fb": "facebook", "ig": "instagram", "wa": "whatsapp",
            "tg": "telegram", "bnb": "binance", "pc": "pc clone", "clone": "pc clone",
        }
        svc = _aliases.get(svc_raw)
        if svc and svc not in live_valid:
            svc = None  # alias exists but service not in list
    # Partial/prefix match as last resort
    if svc is None:
        for key in live_valid:
            if key.startswith(svc_raw) or svc_raw in key:
                svc = key
                break

    if svc is None:
        valid_labels = " / ".join(s["label"].split("→")[0].split("💎")[0].strip() for s in _services)
        msg = bot.send_message(
            message.chat.id,
            f"❌ Choose a valid service:\n<code>{valid_labels}</code>",
            reply_markup=_service_select_markup(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _excel_pick_service)
        return

    pending = _pending_excel.pop(uid, None)
    if not pending:
        bot.send_message(
            message.chat.id,
            "⚠️ Session expired. File abar pathao.",
            reply_markup=main_menu(uid),
        )
        return

    numbers = pending["numbers"]
    filename = pending["filename"]
    added, skipped = _add_numbers_bulk(svc, numbers)

    bot.send_message(
        message.chat.id,
        f"📊🔥 <b>EXCEL IMPORT DONE!</b> 🔥📊\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"📎 <b>File:</b>     <code>{filename}</code>\n"
        f"💬 <b>Service:</b>  <b>{svc.upper()}</b>\n"
        f"📱 <b>Parsed:</b>   {len(numbers)}\n\n"
        f"✅ <b>Added:</b>    {added}\n"
        f"⚠️ <b>Skipped:</b>  {skipped}\n\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        f"💡 Use /panels to check stock.",
        reply_markup=main_menu(uid),
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global stock
    uid = message.from_user.id
    txt = message.text
    register_user(message.chat.id)

    if txt in ("☎️ 𝗩𝟭 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️", "☎️ 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️"):
        show_services(message)

    elif txt in ("📲 𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥", "𝗚𝗘𝗧 𝗡𝗨𝗠𝗕𝗘𝗥"):
        show_services(message)

    elif txt == "🔄 𝗩𝟮 𝗦𝗪𝗜𝗧𝗖𝗛":
        _v2_users.add(uid)
        _save_v2_users()
        bot.send_message(
            message.chat.id,
            "🔄 <b>V2 SWITCH</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        "Select mode:\n\n"
        "🔴 <b>LIVE RANGE</b> — Shows live OTP range from panel\n"
        "⌨️ <b>CUSTOM RANGE</b> — Enter range manually, get matching number\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=v2_switch_menu(),
            parse_mode="HTML",
        )

    elif txt == "🔴 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗚𝗘":
        _v2_show_console(message.chat.id)

    elif txt == "🆕 𝗩𝟯 𝗣𝗔𝗡𝗘𝗟":
        _v3_show_console(message.chat.id)

    elif txt == "⌨️ 𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘":
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("❌ Cancel"))
        msg = bot.send_message(
            message.chat.id,
            "⌨️ <b>CUSTOM RANGE</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "📲 the range/prefix you want:\n"
            "<i>Example: <code>8801</code>, <code>44</code>, <code>33</code></i>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=cancel_markup,
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _v2_custom_range_step)

    elif txt == "🔙 𝗩𝟭 𝗦𝗪𝗜𝗧𝗖𝗛":
        _v2_users.discard(uid)
        _save_v2_users()
        mname = message.from_user.first_name or message.from_user.username or "User"
        bot.send_message(
            message.chat.id,
            f"╔═════════════════════╗\n"
            f"      USER MENU-te WELCOME!\n"
            f"   👋 <b>{mname}</b>, what would you like to do?\n"
            f"╚═════════════════════╝",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )

    elif txt in _get_svc_map():
        svc = _get_svc_map()[txt]
        show_countries(message.chat.id, svc)

    elif txt in ("🔙 Admin Menu", "🔙 Admin Panel", "🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟") and uid in ADMIN_IDS:
        _go_admin_panel(message)

    elif txt == "🔙 Main Menu":
        mname = message.from_user.first_name or message.from_user.username or "User"
        bot.send_message(
            message.chat.id,
            f"╔═════════════════════╗\n"
            f"      USER MENU-te WELCOME!\n"
            f"   👋 <b>{mname}</b>, what would you like to do?\n"
            f"╚═════════════════════╝",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )

    elif txt in ("📞 𝗦𝗔𝗣𝗢𝗥𝗧", "𝗦𝗔𝗣𝗢𝗥𝗧"):
        markup = types.InlineKeyboardMarkup()
        _sup_id = _group_settings.get("support_id", "").strip()
        if _sup_id:
            # Build proper t.me URL from username or numeric ID
            if _sup_id.startswith("http"):
                _sup_url = _sup_id
            elif _sup_id.startswith("@"):
                _sup_url = f"https://t.me/{_sup_id.lstrip('@')}"
            elif _sup_id.lstrip("-").isdigit():
                _sup_url = f"tg://user?id={_sup_id}"
            else:
                _sup_url = f"https://t.me/{_sup_id}"
            markup.add(types.InlineKeyboardButton(
                "SUPPORT TEAM",
                url=_sup_url,
                style="danger",
                icon_custom_emoji_id="5202216593966244027"
            ))
        else:
            markup.add(types.InlineKeyboardButton(
                "SUPPORT TEAM",
                url="https://t.me/Tom_9805",
                style="danger",
                icon_custom_emoji_id="5202216593966244027"
            ))
        bot.send_message(
            message.chat.id,
            "<tg-emoji emoji-id=\"5202216593966244027\">⚠️</tg-emoji> <b>SUPPORT TEAM</b> <tg-emoji emoji-id=\"5271604874419647061\">⚠️</tg-emoji>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "<tg-emoji emoji-id=\"5391112412445288650\">❓</tg-emoji> Need help? Contact our support team\n"
            "<tg-emoji emoji-id=\"5443038326535759644\">👇</tg-emoji> Click the button below\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=markup,
            parse_mode="HTML",
        )

    elif txt == "📊 𝗦𝗧𝗢𝗖𝗞":
        report = "🔥 <b>LIVE STOCK REPORT</b> 🔥\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        for s, d in stock.items():
            total = sum(len(v) for v in d.values())
            report += f" <b>{s.upper()}</b>: {total}  \n"
        report += "\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n🤖 <b>AR OTP BOT</b> 🔥"
        bot.send_message(message.chat.id, report, parse_mode="HTML")

    elif txt in ("⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 ⚙️", "𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟") and uid in ADMIN_IDS:
        _go_admin_panel(message)

    elif txt == "𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀" and uid in ADMIN_IDS:
        _payment_admin_msg_handler(message)

    elif txt in ("💵 Set Reward", "💱 Set Currency",
                 "📉 Set Minimum Withdraw", "📋 View All Balances",
                 "🔗 Set Refer Commission",
                 "➕ Add Balance Manually", "➖ Deduct Balance Manually") and uid in ADMIN_IDS:
        _payment_admin_msg_handler(message)

    elif txt.startswith("⏳ Pending Withdraw") and uid in ADMIN_IDS:
        _payment_admin_msg_handler(message)

    elif txt == "𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "✍️ <b>Send broadcast content:</b>\n\n"
            "📝 Text, 🖼️ Photo, 🎥 Video, 🎭 Sticker,\n"
            "🎞️ GIF, 🎵 Audio, 🎤 Voice, 📎 Document — all accepted!\n\n"
            "✨ <b>If you want to use a Custom Emoji:</b>\n"
            "Text-er jetukute emoji boshaite chao, sekhane emoji ID lekho:\n"
            "<code>5976350888195791241 Guinea 5319160079465857105 Instagram Method 5325684684544289988</code>\n"
            "<i>Wherever you place the ID, the custom emoji will render there</i>\n\n"
            "🔙 Press the <b>Admin Panel</b> button to go back.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, do_broadcast)

    elif txt == "𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            f" <b>TOTAL USERS</b> \n\n⚡ <b>{len(users)}</b> users! 🔥",
            parse_mode="HTML",
        )

    elif txt == "𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁" and uid in ADMIN_IDS:
        all_ids = list(users)
        total = len(all_ids)
        if total == 0:
            bot.send_message(message.chat.id, "📋 No users yet.", parse_mode="HTML")
        else:
            bot.send_message(
                message.chat.id, "⏳ Loading user names...", parse_mode="HTML"
            )
            updated = False
            for user_id in all_ids:
                key = str(user_id)
                existing = user_names.get(key, "")
                if existing and not existing.strip().lstrip("-").isdigit():
                    continue
                try:
                    chat_info = bot.get_chat(user_id)
                    full = f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
                    uname = chat_info.username or ""
                    if full and uname:
                        display = f"{full} (@{uname})"
                    elif full:
                        display = full
                    elif uname:
                        display = f"@{uname}"
                    else:
                        display = None
                    if display:
                        user_names[key] = display
                        updated = True
                except Exception:
                    pass
            if updated:
                save_json(USER_NAMES_FILE, user_names)

            PAGE = 50
            chunks = [all_ids[i : i + PAGE] for i in range(0, total, PAGE)]
            for idx, chunk in enumerate(chunks):
                lines = (
                    f"📋👥 <b>USER LIST</b> 👥📋\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
                    f"📊 Total: <b>{total}</b> users"
                    + (f"  |  Page {idx + 1}/{len(chunks)}" if len(chunks) > 1 else "")
                    + "\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                )
                for i, user_id in enumerate(chunk, start=idx * PAGE + 1):
                    name = user_names.get(str(user_id), "—")
                    lines += f"{i}. 🆔 <code>{user_id}</code>\n    👤 {name}\n\n"
                bot.send_message(message.chat.id, lines, parse_mode="HTML")

    elif txt == "𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀" and uid in ADMIN_IDS:
        with otp_stats_lock:
            stats_copy = dict(otp_stats)
        if not stats_copy:
            bot.send_message(
                message.chat.id,
                "📈 <b>OTP STATS</b>\n\n"
                "⚠️ No OTP delivered yet.",
                parse_mode="HTML",
            )
        else:
            sorted_stats = sorted(stats_copy.items(), key=lambda x: x[1], reverse=True)
            total_otps = sum(stats_copy.values())
            PAGE = 30
            chunks = [sorted_stats[i:i+PAGE] for i in range(0, len(sorted_stats), PAGE)]
            for idx, chunk in enumerate(chunks):
                lines = (
                    f"📈 <b>OTP STATS</b>\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
                    f"📊 Total OTPs Delivered: <b>{total_otps}</b>"
                    + (f"  |  Page {idx+1}/{len(chunks)}" if len(chunks) > 1 else "")
                    + f"\n👥 Total Users: <b>{len(sorted_stats)}</b> more\n"
                    f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
                )
                for rank, (user_id, count) in enumerate(chunk, start=idx*PAGE+1):
                    name = user_names.get(str(user_id), "")
                    if not name or str(name).strip().lstrip("-").isdigit():
                        try:
                            chat_info = bot.get_chat(int(user_id))
                            full = f"{chat_info.first_name or ''} {chat_info.last_name or ''}".strip()
                            uname = chat_info.username or ""
                            name = f"{full} (@{uname})" if full and uname else (full or f"@{uname}" if uname else str(user_id))
                            user_names[str(user_id)] = name
                        except Exception:
                            name = str(user_id)
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                    lines += f"{medal} <code>{user_id}</code> — <b>{count}</b>  OTP(s)\n    👤 {name}\n\n"
                bot.send_message(message.chat.id, lines, parse_mode="HTML")

    elif txt == "🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰" and uid in ADMIN_IDS:
        print(f"[LIVE-TRAFFIC] Triggered by uid={uid} chat={message.chat.id}")
        # Fetch traffic (no blocking send before this)
        try:
            traffic_text = _live_traffic_text()
        except Exception as _lt_err:
            traffic_text = f"❌ Live Traffic Error:\n<code>{_lt_err}</code>"
            print(f"[LIVE-TRAFFIC] _live_traffic_text error: {_lt_err}")
        print(f"[LIVE-TRAFFIC] text ready, len={len(traffic_text)}")
        # Send with retry to survive 429 bursts
        result, rl_secs = _send_with_retry(
            bot.send_message,
            max_retries=5,
            chat_id=message.chat.id,
            text=traffic_text,
            parse_mode="HTML",
        )
        if result is None:
            print(f"[LIVE-TRAFFIC] All retries failed, rate_limit={rl_secs}s")
            # Last-ditch: send plain text without HTML
            try:
                plain = traffic_text.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                bot.send_message(message.chat.id, plain)
            except Exception as _plain_err:
                print(f"[LIVE-TRAFFIC] plain send also failed: {_plain_err}")
        else:
            print(f"[LIVE-TRAFFIC] Sent OK")

    elif txt == "𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "🔥 <b>Choose a service:</b> 🔥",
            reply_markup=_admin_add_svc_keyboard(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, process_auto_add)

    elif txt == "📥 𝗖𝗦𝗩 𝗔𝗱𝗱" and uid in ADMIN_IDS:
        svc_list = "\n".join(f"  • <code>{s['key']}</code>" for s in _services) or \
                   "  • <code>facebook</code>\n  • <code>instagram</code>\n  • <code>whatsapp</code>"
        bot.send_message(
            message.chat.id,
            "📥🔥 <b>ADD NUMBER via CSV / EXCEL</b> 🔥📥\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "📎 <b>Supported formats:</b>\n"
            "  • <b>.csv</b>  — CSV file\n"
            "  • <b>.xlsx</b> — Excel (new)\n"
            "  • <b>.xls</b>  — Excel (old)\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "📋 <b>Format 1 — 2 Column (Service + Number):</b>\n"
            "<code>facebook,8801700123456\n"
            "instagram,8801800234567\n"
            "whatsapp,251912345678</code>\n\n"
            "📋 <b>Format 2 — 1 Column (Number only):</b>\n"
            "<code>8801700123456\n"
            "8801800234567\n"
            "251912345678</code>\n"
            "<i>(You'll choose the service afterward)</i>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "✅ <b>Available services:</b>\n"
            f"{svc_list}\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "⬆️ <b>Ekhon CSV/Excel file pathao!</b>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )

    elif txt == "𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "🗑️🔥 <b>STOCK CLEAR PANEL</b> 🔥🗑️\n\n"
            " <b>Kon service-er stock clear korbe?</b>\n"
            "⬇️ Choose a service:",
            reply_markup=_clr_service_markup(),
            parse_mode="HTML",
        )

    elif txt == "𝗗𝗘𝗠𝗢 𝗢𝗧𝗣" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            demo_status_text(),
            reply_markup=demo_menu_markup(),
            parse_mode="HTML",
        )
        with _demo_lock:
            has_configs = len(_demo_configs) > 0
        if has_configs:
            bot.send_message(
                message.chat.id,
                "⚡ <b>Config Start/Stop:</b>",
                reply_markup=demo_cfg_inline_markup(),
                parse_mode="HTML",
            )

    elif txt == "𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹" and uid in ADMIN_IDS:
        _show_addpanel_type_select(message.chat.id, uid)

    elif txt == "𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲" and uid in ADMIN_IDS:
        _addservice_state[uid] = {}
        msg = bot.send_message(
            message.chat.id,
            "📋🔥 <b>ADD NEW SERVICE</b> 🔥📋\n\n"
            "🏷️ <b>Step 1/2:</b> Button-e ki lekha thakbe?\n"
            "<i>Example: Telegram 🔵, Binance 💛, TikTok 🎵</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _svc_get_label)

    elif txt == "𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲" and uid in ADMIN_IDS:
        if not _services:
            bot.send_message(message.chat.id, "📋 Kono service nai!", parse_mode="HTML")
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for s in _services:
                markup.add(types.InlineKeyboardButton(
                    f"🗑️ {s['label']}  [{s['key']}]",
                    callback_data=f"rmsvc:{s['key']}", style="danger"
                ))
            bot.send_message(
                message.chat.id,
                "🗑️🔥 <b>REMOVE SERVICE</b>\n\nKon service remove korbe?",
                reply_markup=markup,
                parse_mode="HTML",
            )

    elif txt == "𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹" and uid in ADMIN_IDS:
        if not _dynamic_panels:
            bot.send_message(
                message.chat.id,
                "📋 <b>No dynamic panel!</b>\n💡 Add one using the Add Panel button.",
                parse_mode="HTML",
            )
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for p in _dynamic_panels:
                pid = p["id"]
                with _stats_lock:
                    s = _panel_stats.get(pid, {})
                st = s.get("status", "⏳")
                markup.add(
                    types.InlineKeyboardButton(
                        f"{st} {p.get('username','?')} — {p.get('host','?')}",
                        callback_data=f"rmpanel:{pid}", style="success"
                    )
                )
            bot.send_message(
                message.chat.id,
                "🗑️🔥 <b>REMOVE PANEL</b>\n\nKon panel remove korbe?",
                reply_markup=markup,
                parse_mode="HTML",
            )


    elif txt == "➕ 𝗖𝗼𝗻𝗳𝗶𝗴 𝗬𝗼𝗴 𝗞𝗼𝗿𝗼" and uid in ADMIN_IDS:
        _demo_cfg_temp[uid] = {}
        msg = bot.send_message(
            message.chat.id,
            "📱 <b>Enter phone number(s):</b>\n\n"
            "• One number: <code>8801700123456</code>\n"
            "• Multiple (newline or comma):\n"
            "<code>8801700123456\n251912345678\n2348012345678</code>\n\n"
            "⚠️ Full country code including number lagbe!",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_number)

    elif txt == "🗑️ 𝗖𝗼𝗻𝗳𝗶𝗴 𝗠𝘂𝗰𝗵𝗼" and uid in ADMIN_IDS:
        with _demo_lock:
            configs = list(_demo_configs)
        if not configs:
            bot.send_message(
                message.chat.id,
                "📋 <b>Kono config nai!</b>",
                reply_markup=demo_menu_markup(),
                parse_mode="HTML",
            )
        else:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for cfg in configs:
                svcs = ", ".join(cfg.get("services") or ["?"])
                markup.add(types.InlineKeyboardButton(
                    f"🗑️ {cfg['name']}  [{svcs}  |  {cfg['interval']}s]",
                    callback_data=f"rmcfg:{cfg['id']}", style="primary"
                ))
            bot.send_message(
                message.chat.id,
        "🗑️🔥 <b>Delete Config</b>\n\nWhich config do you want to delete?",
                reply_markup=markup,
                parse_mode="HTML",
            )

    elif txt == "𝗣𝗮𝗻𝗲𝗹𝘀" and uid in ADMIN_IDS:
        panels_cmd(message)

    elif txt == "𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽𝗲 𝗦𝗲𝗻𝗱" and uid in ADMIN_IDS:
        _resend_old_otps(message)

    elif txt == "𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗕𝗼𝗻𝗱𝗵𝗼" and uid in ADMIN_IDS:
        global _resend_stop, _resend_running
        _resend_stop = True
        if _resend_running:
            bot.send_message(message.chat.id,
                "🛑 <b>Resend stop signal sent!</b>\n"
                "<i>It will stop once the current OTP send finishes.</i>",
                parse_mode="HTML")
        else:
            bot.send_message(message.chat.id,
                "ℹ️ <b>Kono resend cholthechhilo na.</b>",
                parse_mode="HTML")

    elif txt == "𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹" and uid in ADMIN_IDS:
        _testpanel_state[uid] = {"step": "url", "data": {}}
        msg = bot.send_message(
            message.chat.id,
            "🔍🔥 <b>TEST PANEL</b> 🔥🔍\n\n"
            "Panel-er jekono URL pathao — test korbo, <b>save korbo na</b>.\n\n"
            "✅ <b>Jekono format:</b>\n"
            "• <code>http://1.2.3.4/konekta/agent/SMSCDRReports</code>\n"
            "• <code>http://1.2.3.4/ints</code>\n"
            "• <code>https://truesms.net</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _tp_get_url)

    elif txt == "👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻" and uid in ADMIN_IDS:
        if not is_super_admin(uid):
            bot.send_message(message.chat.id, "❌ <b>Only Super Admin can add a new admin!</b>", parse_mode="HTML")
            return
        msg = bot.send_message(
            message.chat.id,
            "👑 <b>New Admin add</b>\n\n"
            "Enter the new admin's Telegram <b>User ID</b>:\n"
            "<i>Example: 123456789</i>\n\n"
            "💡 To find the User ID, forward a message from that user to @userinfobot.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _admin_add_get_id)

    elif txt == "𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻" and uid in ADMIN_IDS:
        if not is_super_admin(uid):
            bot.send_message(message.chat.id, "❌ <b>Only Super Admin can remove an admin!</b>", parse_mode="HTML")
            return
        _show_remove_admin(message)

    elif txt == "𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗" and uid in ADMIN_IDS:
        if not is_super_admin(uid):
            bot.send_message(message.chat.id, "❌ <b>Only Super Admin can set the Support ID!</b>", parse_mode="HTML")
            return
        cur = _group_settings.get("support_id", "") or "❌ Set hoy nai"
        msg = bot.send_message(
            message.chat.id,
            f"📞 <b>Support ID Set/Change</b>\n\n"
            f"🔹 <b>Bortoman Support ID:</b> {cur}\n\n"
            f"Enter new Support Telegram ID\n"
            f"<i>(User ID, username, or t.me link — any one)</i>\n\n"
            f"Example: <code>@support_user</code> ba <code>123456789</code>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_support_id)

    elif txt == "𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀" and uid in ADMIN_IDS:
        _show_settings(message)

    elif txt == "𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀" and uid in ADMIN_IDS:
        _show_edit_messages_menu(message)

    elif txt == "𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴" and uid in ADMIN_IDS:
        bot.send_message(
            message.chat.id,
            "🎛️ <b>Live Console Config</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "Select service — toggle or add/delete range:\n"
            "✅ = enabled  ⭕ = disabled",
            reply_markup=_cc_services_markup(),
            parse_mode="HTML",
        )

    elif txt == "𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁" and uid in ADMIN_IDS:
        active = _get_v2_active_panel_id()
        pname = _v2_active_panel_name()
        bot.send_message(
            message.chat.id,
            f"🔀 <b>V2 Panel Select</b>\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"✅ <b>Currently Active:</b> {pname}\n\n"
        f"Use the buttons below to enable/disable panel.\n"
        f"The panel with ✅ is active — V2 numbers and OTP will come from there.\n\n"
            f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
            reply_markup=_v2_panel_toggle_markup(),
            parse_mode="HTML",
        )

    elif txt == "📡 𝗩𝟮 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗙𝗼𝗿𝗺𝗮𝘁" and uid in ADMIN_IDS:
        import html as _html
        current = get_template("otp_dm_v2")
        current_esc = _html.escape(current[:600])
        vars_hint = _TEMPLATE_VARS.get("otp_dm_v2", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("✏️ Edit V2 DM Format", callback_data="editmsg:otp_dm_v2", style="danger"))
        markup.add(types.InlineKeyboardButton("🔄 Reset to Default", callback_data="editmsg_reset:otp_dm_v2", style="success"))
        bot.send_message(
            message.chat.id,
            "📡 <b>V2 Message Format</b>\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "📌 <b>Available variables:</b>\n"
            f"<code>{vars_hint}</code>\n\n"
        "📄 <b>Current V2 DM Format:</b>\n"
            f"<code>{current_esc}</code>\n\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
            "<i>ℹ️ In V2 mode, Get New Number and Change Country buttons are not shown.</i>",
            reply_markup=markup,
            parse_mode="HTML",
        )

    elif txt in ("👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼", "𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼"):
        bot.send_message(
            message.chat.id,
            "<b><tg-emoji emoji-id=\"5202216593966244027\">👨‍💻</tg-emoji> 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼</b>\n\n"
            "<b><tg-emoji emoji-id=\"5325547803936572038\">✨</tg-emoji> Name: 𝗔𝘁𝗶𝗸</b>\n"
            "<b><tg-emoji emoji-id=\"5447644880824181073\">⚡</tg-emoji> Role: Bot Developer</b>\n"
            "<b><tg-emoji emoji-id=\"5341363621572128687\">🤖</tg-emoji> Project: Custom Otp Bot</b>\n"
            "<b><tg-emoji emoji-id=\"5391112412445288650\">📲</tg-emoji> Contact: @Tom_9805</b>\n"
            "<b><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji></b>\n"
            "<b><tg-emoji emoji-id=\"5447644880824181073\">⚡</tg-emoji> Developed &amp; Managed by Atik</b>\n"
            "<b><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji></b>",
            parse_mode="HTML",
        )

    elif txt == "𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀" and uid in ADMIN_IDS:
        _show_extra_groups(message)

    elif txt == "🌐 𝗔𝘂𝗴𝗲𝘀𝘁𝗲𝗹 𝗞𝗲𝘆" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "🌐🔑 <b>Augestel API Key Change</b>\n\n"
            "নতুন Augestel API key পাঠান। Save হওয়ার পর bot পুরোনো history "
            "আবার sync করে configured group-গুলোতে পাঠাবে।",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: _chgkey_receive(m, "augestel"))

    elif txt == "𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲" and uid in ADMIN_IDS:
        current_fastx  = _group_settings.get("fastx_api_key", FASTX_API_KEY)
        current_stex   = _group_settings.get("stex_api_key",  STEX_API_KEY)
        current_voltex = _group_settings.get("voltex_api_key", V3_API_KEY)
        current_mk     = _group_settings.get("mk_api_key", MK_API_KEY)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(
                "🌐 Augestel SMS  |  🔐 configured",
                callback_data="chgkey:augestel",
            ),
            types.InlineKeyboardButton(
                f"⚡ FastX SMS  |  🔑 {current_fastx[:12]}...",
                callback_data="chgkey:fastx",
            ),
            types.InlineKeyboardButton(
                f"🌐 STEX SMS  |  🔑 {current_stex[:12]}...",
                callback_data="chgkey:stex",
            ),
            types.InlineKeyboardButton(
                f"🔮 Voltex SMS  |  🔑 {current_voltex[:12]}...",
                callback_data="chgkey:voltex",
            ),
            types.InlineKeyboardButton(
                f"🟢 MK Panel  |  🔑 {current_mk[:12]}...",
                callback_data="chgkey:mk",
            ),
        )
        bot.send_message(
            message.chat.id,
            "🔑🔥 <b>PANEL API KEY CHANGE</b> 🔥🔑\n"
            "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
            "Which panel's API key do you want to change?\n"
            "Select a panel from below:",
            reply_markup=markup,
            parse_mode="HTML",
        )

    elif txt == "𝗖𝘂𝘀𝘁𝗼𝗺 𝗘𝗺𝗼𝗷𝗶" and uid in ADMIN_IDS:
        _show_custom_emoji_menu(message)

    elif txt == "🏳️ Flag Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "flag"
        bot.send_message(
            message.chat.id,
            "🏳️ <b>Flag Emoji Set</b>\n\n"
        "Send flag emoji and its custom emoji ID:\n\n"
        "<b>Single:</b> <code>🇧🇩 5432198765432198765</code>\n\n"
        "<b>Bulk (numbered list):</b>\n"
            "<code>1. 🇧🇩 5432198765432198765\n2. 🇺🇸 5976694588658686266</code>\n\n"
            "<i>Or use 🌍 All Flags JSON Set to add all flags at once.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🌍 All Flags JSON Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "flag_bulk_json"
        with _custom_emoji_lock:
            cur = dict(_custom_emojis.get("flags", {}))
        cur_preview = json.dumps(cur, ensure_ascii=False, indent=2) if cur else "{}"
        bot.send_message(
            message.chat.id,
            "🌍 <b>All Flags JSON Set</b>\n\n"
        "Send a JSON with <b>all</b> flag emojis and their custom IDs.\n\n"
        "<b>Format:</b>\n"
            "<code>{\n"
            '  "🇧🇩": "5432198765432198765",\n'
            '  "🇺🇸": "5976694588658686266",\n'
            '  "🇮🇳": "5195261305332736014"\n'
            "}</code>\n\n"
        "📌 <b>Current flags (JSON):</b>\n"
            f"<pre>{cur_preview}</pre>\n\n"
        "<i>New JSON will be merged with existing (not overwritten).\n"
        "To reset, use 🗑️ Flag Emoji Del first to clear all.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "📋 Flag JSON Export" and uid in ADMIN_IDS:
        with _custom_emoji_lock:
            cur = dict(_custom_emojis.get("flags", {}))
        if not cur:
            bot.send_message(message.chat.id,
                "📋 No flag emoji set yet.\n\n"
                "🌍 Use All Flags JSON Set to add.")
        else:
            exported = json.dumps(cur, ensure_ascii=False, indent=2)
            bot.send_message(
                message.chat.id,
                f"📋 <b>Current Flag Emojis JSON</b>\n\n"
                f"<pre>{exported}</pre>\n\n"
                f"<i>Total {len(cur)} flags set.\n"
                f"Copy, edit, and paste in 🌍 All Flags JSON Set.</i>",
                parse_mode="HTML"
            )
        _show_custom_emoji_menu(message)

    elif txt == "🔢 IDs Only Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "flag_ids_only"
        bot.send_message(
            message.chat.id,
            "🔢 <b>Flag IDs Only Set</b>\n\n"
            "Paste only the custom emoji IDs (one per line).\n"
            "The bot will automatically detect which country each flag belongs to.\n\n"
        "<b>Format:</b>\n"
            "<code>5432198765432198765\n"
            "5976694588658686266\n"
            "5195261305332736014</code>\n\n"
            "<i>You can send up to 200 IDs at once.</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🎯 Service Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "service"
        bot.send_message(
            message.chat.id,
            "🎯 <b>Service Emoji Set</b>\n\n"
            "Send the service name and custom emoji ID:\n\n"
            "<b>Format:</b> <code>INSTAGRAM 5319160079465857105</code>\n\n"
            "<i>Service name must be in ALL CAPS.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Flag Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_flag"
        with _custom_emoji_lock:
            flags_set = dict(_custom_emojis.get("flags", {}))
        if flags_set:
            lines = "\n".join(f"<code>{k}</code>" for k in flags_set)
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Flag Emoji</b>\n\nWhich flag emoji to delete?\n\n{lines}\n\n"
                "Send the flag emoji (emoji only, e.g. <code>🇧🇩</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No flag emoji is set.")

    elif txt == "🗑️ Service Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_service"
        with _custom_emoji_lock:
            svcs_set = dict(_custom_emojis.get("services", {}))
        if svcs_set:
            lines = "\n".join(f"<code>{k}</code>" for k in svcs_set)
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Service Emoji</b>\n\nWhich service to delete?\n\n{lines}\n\n"
                "Send the service name (e.g. <code>INSTAGRAM</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No service emoji is set.")

    elif txt == "🔘 Button Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "btn"
        available = "\n".join(f"  <code>{k}</code> — {v}" for k, v in _BTN_DISPLAY_NAMES.items())
        bot.send_message(
            message.chat.id,
            f"🔘 <b>Button Emoji Set</b>\n\n"
        f"Send button key and custom emoji ID:\n\n"
        f"<b>Format:</b> <code>button_key emoji_id</code>\n\n"
            f"<b>Available buttons:</b>\n{available}\n\n"
        f"<b>Example:</b>\n<code>change_number 5375170473095077321</code>\n\n"
            f"<i>Once custom emoji is set, the plain emoji will automatically be removed from button text.</i>",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Button Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_btn"
        with _custom_emoji_lock:
            btns_set = dict(_custom_emojis.get("buttons", {}))
        if btns_set:
            lines = "\n".join(f"<code>{k}</code> → <code>{v}</code>" for k, v in btns_set.items())
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Button Emoji</b>\n\nWhich button to delete?\n\n{lines}\n\n"
                "Send the button key (e.g. <code>change_number</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No button emoji is set.")

    elif txt == "🖥️ Admin Btn Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "admin_btn"
        with _custom_emoji_lock:
            overrides = dict(_custom_emojis.get("admin_btns", {}))
        lines = []
        for k, display in _ADMIN_BTN_DISPLAY_NAMES.items():
            cur_id = overrides.get(k) or _ADMIN_BTN_DEFAULT_ICONS.get(k, "")
            marker = "✏️" if k in overrides else "🔹"
            lines.append(f"  {marker} <code>{k}</code> — {display}\n     ID: <code>{cur_id}</code>")
        available = "\n".join(lines)
        bot.send_message(
            message.chat.id,
            f"🖥️ <b>Admin Panel Button Emoji Set</b>\n\n"
            f"Send button key and new custom emoji ID:\n\n"
            f"<b>Format:</b> <code>key emoji_id</code>\n\n"
            f"<b>Bulk (multiple lines):</b>\n"
            f"<code>num_add 5420323438508155202\nsob_clear 5422557736330106570</code>\n\n"
            f"<b>Buttons (✏️ = overridden, 🔹 = default):</b>\n{available}\n\n"
            f"<i>After saving, admin panel will instantly show new icons.</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Admin Btn Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_admin_btn"
        with _custom_emoji_lock:
            overrides = dict(_custom_emojis.get("admin_btns", {}))
        if overrides:
            lines = "\n".join(f"  <code>{k}</code> → <code>{v}</code>" for k, v in overrides.items())
            bot.send_message(
                message.chat.id,
                f"🗑️ <b>Delete Admin Button Emoji Override</b>\n\n"
                f"Current overrides:\n{lines}\n\n"
                f"Send the key to reset to default\n"
                f"(or send <code>ALL</code> to reset all):",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id,
                "ℹ️ No admin button overrides set. All buttons use default icons.")
            _show_custom_emoji_menu(message)

    elif txt == "💬 Msg Emoji Set" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "msg_slot"
        with _custom_emoji_lock:
            slots_set = dict(_custom_emojis.get("msg_slots", {}))
        slot_list = "\n".join(f"  <code>{{emoji_{k}}}</code> → {v.get('fb','')}" for k, v in slots_set.items()) or "  (none)"
        bot.send_message(
            message.chat.id,
            f"💬 <b>Message Emoji Set</b>\n\n"
            f"Current slots:\n{slot_list}\n\n"
            f"To add a new slot, send:\n\n"
            f"<b>Format:</b> <code>slot_name emoji_id fallback_emoji</code>\n\n"
        f"<b>Example:</b>\n<code>fire 5432198765432198765 🔥</code>\n\n"
        f"Then use <code>{{emoji_fire}}</code> in any message template to show the custom emoji.",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(message, _custom_emoji_input)

    elif txt == "🗑️ Msg Emoji Del" and uid in ADMIN_IDS:
        _custom_emoji_state[uid] = "del_msg_slot"
        with _custom_emoji_lock:
            slots_set = dict(_custom_emojis.get("msg_slots", {}))
        if slots_set:
            lines = "\n".join(f"<code>{k}</code> → {v.get('fb','')}" for k, v in slots_set.items())
            bot.send_message(
                message.chat.id,
        f"🗑️ <b>Delete Message Emoji</b>\n\nWhich slot to delete?\n\n{lines}\n\n"
                "Send the slot name (e.g. <code>fire</code>):",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(message, _custom_emoji_input)
        else:
            bot.send_message(message.chat.id, "❌ No message emoji slot is set.")

    elif txt in ("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", "🔙 Admin Panel") and uid in ADMIN_IDS:
        _go_admin_panel(message)

    elif txt in ("💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲", "𝗕𝗮𝗹𝗮𝗻𝗰𝗲"):
        _show_balance(message)

    elif txt in ("💸 𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄", "𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄"):
        _start_withdraw(message)

    elif txt in ("🔗 𝗥𝗲𝗳𝗳𝗲𝗿", "𝗥𝗲𝗳𝗳𝗲𝗿"):
        _show_refer(message)

    elif txt == "𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂":
        mname = message.from_user.first_name or message.from_user.username or "User"
        bot.send_message(
            message.chat.id,
            f"╔═════════════════════╗\n"
            f"      USER MENU-te WELCOME!\n"
            f"   👋 <b>{mname}</b>, what would you like to do?\n"
            f"╚═════════════════════╝",
            reply_markup=main_menu(uid),
            parse_mode="HTML",
        )



    elif txt == "Buy Service":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("Telegram Premium", callback_data="buy_tg_premium", style="primary", icon_custom_emoji_id="5251390031020455583"),
            types.InlineKeyboardButton("Buy VPN", callback_data="buy_vpn_menu", style="success", icon_custom_emoji_id="5269759232483303288"),
        )
        bot.send_message(
            message.chat.id,
            '<tg-emoji emoji-id="5375338737028841420">🛒</tg-emoji> <b>BUY SERVICE</b>\n\n<tg-emoji emoji-id="5447183459602669338">👆</tg-emoji> Select any service from below: <tg-emoji emoji-id="5447183459602669338">👆</tg-emoji>',
            reply_markup=markup,
            parse_mode="HTML",
        )

    # ── Buy Service Admin ───────────────────────────────────────────────────────
    elif txt == "𝗕𝘂𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲" and uid in ADMIN_IDS:
        _show_buy_service_admin(message)

    elif txt == "💎 Set Premium Price" and uid in ADMIN_IDS:
        prices = _buy_service_settings["premium_prices"]
        rate = _buy_service_settings.get("dollar_rate", 128)
        msg = bot.send_message(
            message.chat.id,
            f"💎 <b>Telegram Premium Price Set</b>\n\n"
            f"Current prices:\n"
            f"• 3 Month: <b>{prices.get('3M', 0)} BDT</b>\n"
            f"• 6 Month: <b>{prices.get('6M', 0)} BDT</b>\n"
            f"• 1 Year:  <b>{prices.get('1Y', 0)} BDT</b>\n"
            f"• Dollar Rate: <b>1$ = {rate} BDT</b>\n\n"
            "Enter 3 prices — for 3M 6M 1Y in BDT (space-separated):\n"
            "<i>Example: <code>650 1200 2000</code></i>\n\n"
            "To change the dollar rate, enter 4 values:\n"
            "<i>Example: <code>650 1200 2000 130</code></i>\n\n"
            "🔙 Back: Press the <b>Admin Panel</b> button.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_set_premium_step)

    elif txt == "💰 Set VPN Price" and uid in ADMIN_IDS:
        _show_vpn_price_list(message)

    elif txt == "➕ Add VPN Service" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "➕ <b>New VPN Service Add</b>\n\n"
            "Format (space-separated):\n"
            "<code>EMOJI_ID NAME DURATION PRICE_BDT</code>\n\n"
            "Example:\n"
            "<code>5334944492300573096 NORD 7D 300</code>\n\n"
            "🔙 Back: Press the <b>Admin Panel</b> button.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_add_vpn_step)

    elif txt == "🗑️ Remove VPN" and uid in ADMIN_IDS:
        _show_vpn_remove_list(message)

    elif txt == "📨 Send User Message" and uid in ADMIN_IDS:
        msg = bot.send_message(
            message.chat.id,
            "📨 <b>Send Message to User</b>\n\n"
            "Enter the target user's <b>Chat ID</b>:\n"
            "<i>(You can find the ID in the admin screenshot notification)</i>\n\n"
            "🔙 Back: Press the <b>Admin Panel</b> button.",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _buy_send_ask_uid_step)

# ── Demo OTP config step handlers ─────────────────────────────────────────────


def _demo_cfg_number(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw_lines = re.split(r"[\n,]+", message.text or "")
    candidates = [re.sub(r"\D", "", ln) for ln in raw_lines if re.sub(r"\D", "", ln)]
    if not candidates:
        msg = bot.send_message(
            message.chat.id,
            "❌ No number found. Enter one or multiple numbers:",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_number)
        return
    valid, invalid = [], []
    result_lines = ""
    for num in candidates:
        if len(num) < 7:
            invalid.append(num)
            continue
        c_name, flag = get_country_details(num)
        if c_name == "Unknown":
            invalid.append(num)
        else:
            valid.append(num)
            result_lines += f"  ✅ <code>{num}</code>  {_resolve_flag(flag)} {c_name}\n"
    if not valid:
        msg = bot.send_message(
            message.chat.id,
            f"⚠️ <b>Kono valid number paini!</b>\n\n"
            f"Enter full international number (including country code):\n"
            f"🇧🇩 Bangladesh → <code>8801700123456</code>\n"
            f"🇪🇹 Ethiopia   → <code>251912345678</code>\n"
            f"🇳🇬 Nigeria    → <code>2348012345678</code>\n\n"
            f"Try again:",
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_number)
        return
    uid = message.from_user.id
    _demo_cfg_temp.setdefault(uid, {})["numbers"] = valid
    SHOW_MAX = 10
    shown = result_lines.split("\n")[:SHOW_MAX]
    preview = "\n".join(shown)
    if len(valid) > SHOW_MAX:
        preview += f"\n  ... +{len(valid) - SHOW_MAX} more"
    feedback = f"✅ <b>{len(valid)} number(s) set:</b>\n{preview}\n"
    if invalid:
        inv_preview = invalid[:5]
        feedback += (
            f"\n⚠️ Skip (invalid): {', '.join(f'<code>{x}</code>' for x in inv_preview)}"
        )
        if len(invalid) > 5:
            feedback += f" +{len(invalid) - 5} more"
        feedback += "\n"
    svc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    svc_markup.add("4", "5", "6", "7", "8")
    svc_markup.add("🔙 Admin Panel")
    msg = bot.send_message(
        message.chat.id,
        feedback + "\n🔢 <b>Choose OTP digit count:</b>",
        reply_markup=svc_markup,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, _demo_cfg_digits)


def _demo_cfg_digits(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    try:
        d = int(message.text.strip())
        if d < 4 or d > 8:
            raise ValueError
    except ValueError:
        svc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        svc_markup.add("4", "5", "6", "7", "8")
        svc_markup.add("🔙 Admin Panel")
        msg = bot.send_message(message.chat.id, "❌ Enter a number between 4 and 8:", reply_markup=svc_markup)
        bot.register_next_step_handler(msg, _demo_cfg_digits)
        return
    uid = message.from_user.id
    _demo_cfg_temp.setdefault(uid, {})["digits"] = d
    _demo_svc_state[uid] = []
    _demo_cfg_service_ask(message)


def _demo_cfg_service_ask(message):
    uid = message.from_user.id
    current = _demo_svc_state.get(uid, [])
    svc_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    svc_markup.add("Facebook", "Instagram", "WhatsApp")
    svc_markup.add("Telegram", "PC Clone", "Twitter")
    svc_markup.add("Tiktok", "Snapchat", "Gmail")
    if current:
        svc_markup.add("✅ Done")
    svc_markup.add("🔙 Admin Panel")
    if current:
        svc_list = "\n".join(f"  ✅ {s}" for s in current)
        prompt = (
            f"✅ <b>Selected services ({len(current)}):</b>\n{svc_list}\n\n"
            f"➕ <b>Add more services</b> or press <b>✅ Done</b>:"
        )
    else:
        prompt = (
            "💬 <b>Choose a service</b>\n\n"
            "<i>You can add multiple services — press '✅ Done' when finished.</i>"
        )
    msg = bot.send_message(message.chat.id, prompt, reply_markup=svc_markup, parse_mode="HTML")
    bot.register_next_step_handler(msg, _demo_cfg_service_multi)


def _demo_cfg_service_multi(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    uid = message.from_user.id
    txt = (message.text or "").strip()

    if txt in ("✅ Done", "✅ Done"):
        svcs = _demo_svc_state.get(uid, [])
        if not svcs:
            bot.send_message(
                message.chat.id,
                "⚠️ <b>Please select at least one service!</b>",
                parse_mode="HTML",
            )
            _demo_cfg_service_ask(message)
            return
        uid2 = message.from_user.id
        _demo_cfg_temp.setdefault(uid2, {})["services"] = svcs
        intvl_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        intvl_markup.add("5", "10", "15", "30", "60", "120", "300")
        intvl_markup.add("🔙 Admin Panel")
        svc_list = ", ".join(svcs)
        msg = bot.send_message(
            message.chat.id,
            f"✅ <b>Services set:</b> {svc_list}\n\n⏱️ <b>Enter interval (seconds):</b>",
            reply_markup=intvl_markup,
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _demo_cfg_interval)
        return

    if not txt:
        _demo_cfg_service_ask(message)
        return

    current = _demo_svc_state.setdefault(uid, [])
    if txt in current:
        bot.send_message(
            message.chat.id,
            f"⚠️ <b>{txt}</b> is already added! Add more or press <b>✅ Done</b>.",
            parse_mode="HTML",
        )
    else:
        current.append(txt)
    _demo_cfg_service_ask(message)


def _demo_cfg_interval(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    try:
        iv = int(message.text.strip())
        if iv < 5:
            raise ValueError
    except ValueError:
        intvl_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        intvl_markup.add("5", "10", "15", "30", "60", "120", "300")
        intvl_markup.add("🔙 Admin Panel")
        msg = bot.send_message(message.chat.id, "❌ Minimum 5 seconds. Enter more:", reply_markup=intvl_markup)
        bot.register_next_step_handler(msg, _demo_cfg_interval)
        return
    global _demo_cfg_id_counter
    uid = message.from_user.id
    tmp = _demo_cfg_temp.pop(uid, {})
    numbers = tmp.get("numbers", ["8801700000000"])
    digits = tmp.get("digits", 6)
    services = tmp.get("services", ["Facebook"])
    with _demo_lock:
        _demo_cfg_id_counter += 1
        cid = _demo_cfg_id_counter
        cfg_name = f"Config {cid}"
        _demo_configs.clear()
        _demo_next_fire.clear()
        _demo_configs.append({
            "id": cid,
            "name": cfg_name,
            "active": True,
            "numbers": numbers,
            "digits": digits,
            "services": services,
            "interval": iv,
        })
    svcs_str = ", ".join(services)
    bot.send_message(
        message.chat.id,
        f"✅🔥 <b>{cfg_name} added!</b>\n\n"
        f"  📱 Numbers: {len(numbers)}\n"
        f"  🔢 Digits: {digits}\n"
        f"  💬 Services: {svcs_str}\n"
        f"  ⏱️ Interval: {iv}s\n\n"
        + demo_status_text(),
        reply_markup=demo_menu_markup(),
        parse_mode="HTML",
    )


def _inject_custom_emojis(text):
    """Replace every 17-20 digit numeric ID in text with a <tg-emoji> tag.
    Example: '5976350888195791241 Guinea' → '<tg-emoji ...>✨</tg-emoji> Guinea'
    """
    if not text:
        return text
    import re as _re
    return _re.sub(
        r'\b(\d{17,20})\b',
        lambda m: f'<tg-emoji emoji-id="{m.group(1)}">✨</tg-emoji>',
        text,
    )


def make_broadcast_msg(text):
    # Send exactly what admin typed — just inject custom emoji IDs, no header/footer wrapper
    return _inject_custom_emojis(text or "")


def do_broadcast(message):
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    has_text = bool(message.text)
    has_photo = bool(message.photo)
    has_video = bool(message.video)
    has_sticker = bool(message.sticker)
    has_animation = bool(message.animation)
    has_audio = bool(message.audio)
    has_voice = bool(message.voice)
    has_document = bool(message.document)
    has_video_note = bool(message.video_note)

    if not any(
        [
            has_text,
            has_photo,
            has_video,
            has_sticker,
            has_animation,
            has_audio,
            has_voice,
            has_document,
            has_video_note,
        ]
    ):
        bot.send_message(
            message.chat.id,
            "⚠️ <b>No content found!</b> ⚠️\n"
            "Text, Photo, Video, GIF, Audio, Voice, Document ba Sticker pathao.",
            parse_mode="HTML",
        )
        return

    _raw_cap = message.caption or ""

    def cap(m):
        return make_broadcast_msg(_raw_cap)

    bot.send_message(
        message.chat.id,
        f"⏳🔥 <b>Sending to {len(users)} users...</b> 🔥⏳",
        parse_mode="HTML",
    )

    def _bc_send_one(chat_id):
        try:
            if has_photo:
                bot.send_photo(chat_id, message.photo[-1].file_id, caption=cap(message), parse_mode="HTML")
            elif has_animation:
                bot.send_animation(chat_id, message.animation.file_id, caption=cap(message), parse_mode="HTML")
            elif has_video:
                bot.send_video(chat_id, message.video.file_id, caption=cap(message), parse_mode="HTML")
            elif has_video_note:
                bot.send_video_note(chat_id, message.video_note.file_id)
            elif has_sticker:
                bot.send_sticker(chat_id, message.sticker.file_id)
            elif has_audio:
                bot.send_audio(chat_id, message.audio.file_id, caption=cap(message), parse_mode="HTML")
            elif has_voice:
                bot.send_voice(chat_id, message.voice.file_id, caption=cap(message), parse_mode="HTML")
            elif has_document:
                bot.send_document(chat_id, message.document.file_id, caption=cap(message), parse_mode="HTML")
            else:
                bot.send_message(chat_id, make_broadcast_msg(message.text), parse_mode="HTML")
            return True
        except Exception:
            return False

    # Send to main group
    main_grp = get_otp_group_id()
    if main_grp:
        try:
            _bc_send_one(main_grp)
        except Exception:
            pass
    # Send to extra groups
    for eg in _group_settings.get("extra_groups", []):
        eg_id = eg.get("id")
        if eg_id:
            try:
                _bc_send_one(eg_id)
            except Exception:
                pass

    # Send to all registered users
    success, fail = 0, 0
    for uid in list(users):
        if _bc_send_one(uid):
            success += 1
        else:
            fail += 1
        time.sleep(0.03)

    bot.send_message(
        message.chat.id,
        f" <b>BROADCAST COMPLETE!</b> \n\n"
        f"✅ <b>𝗦𝗼𝗳𝗼𝗹:</b> {success} more 🔥\n"
        f"❌ <b>𝗕𝗮𝗿𝘁𝗵𝗼:</b> {fail} more ",
        parse_mode="HTML",
    )
    _go_admin_panel(message)


_pending_add = {}


def _start_countdown(chat_id, msg_id, svc, flag, c_name, display_nums, scnt):
    # Accept list or single string
    if isinstance(display_nums, list):
        _nums_list = display_nums
    else:
        _nums_list = [display_nums]

    if chat_id in _countdowns:
        _countdowns[chat_id].set()
    cancel = threading.Event()
    _countdowns[chat_id] = cancel

    def _make_kb():
        view = _user_number_views.get(chat_id, {})
        return _build_numbers_display_kb(
            svc, scnt, _nums_list, flag, c_name,
            cc_removed=view.get("cc_removed", False),
        )

    def run():
        TICK = 5            # update every 5s
        DURATION = 600      # 10 minutes
        deadline = time.time() + DURATION
        current_msg_id = [msg_id]  # list so inner scope can mutate

        def _parse_retry_after(err_str):
            try:
                return int(re.search(r"retry after (\d+)", err_str).group(1))
            except Exception:
                return 60

        def try_update(text):
            """Try edit, fall back to send+delete.
            Returns: True=ok, False=skip tick, None=stop, int=rate-limited (seconds to wait)."""
            # 1. try edit
            try:
                bot.edit_message_text(
                    text, chat_id, current_msg_id[0],
                    reply_markup=_make_kb(),
                )
                return True
            except Exception as e:
                err = str(e)
                if "message is not modified" in err:
                    return True
                if "message to edit not found" in err or "MESSAGE_ID_INVALID" in err:
                    return None
                if "429" in err or "Too Many Requests" in err:
                    return _parse_retry_after(err)  # int → caller will wait

            # 2. edit failed (non-429) — try send+delete
            try:
                sent = bot.send_message(
                    chat_id, text,
                    reply_markup=_make_kb(),
                )
                try:
                    bot.delete_message(chat_id, current_msg_id[0])
                except Exception:
                    pass
                current_msg_id[0] = sent.message_id
                _user_last_num_msg[chat_id] = sent.message_id
                return True
            except Exception as e2:
                err2 = str(e2)
                if "429" in err2 or "Too Many Requests" in err2:
                    return _parse_retry_after(err2)
                print(f"[COUNTDOWN] tick failed: {e2}")
                return False

        while not cancel.is_set():
            remaining = int(deadline - time.time())
            if remaining <= 0:
                deadline = time.time() + DURATION
                remaining = DURATION

            mins = remaining // 60
            secs = remaining % 60
            text = "."
            result = try_update(text)
            if result is None:
                break  # message gone, stop
            elif type(result) is int:
                # rate-limited — wait the full retry_after, then resume
                wait = min(result, 3600)
                print(f"[COUNTDOWN] Rate limited for {wait}s, pausing timer for {chat_id}")
                cancel.wait(wait)
            else:
                cancel.wait(TICK)

    threading.Thread(target=run, daemon=True).start()


def _settings_text(uid=None):
    """Per-admin settings. If uid given, show that admin's own settings."""
    grp_link = get_admin_setting(uid, "otp_group_link") if uid else _group_settings.get("otp_group_link", "")
    grp_id = get_admin_setting(uid, "otp_group_id") if uid else _group_settings.get("otp_group_id")
    ch2 = get_admin_setting(uid, "channel2") if uid else _group_settings.get("channel2", "")
    bot_lnk = get_admin_setting(uid, "bot_link") if uid else _group_settings.get("bot_link", "")
    auto_del = _group_settings.get("auto_delete", True)
    del_secs = _group_settings.get("auto_delete_seconds", 3600)
    grp_send = _group_settings.get("group_otp_send", True)
    grp_tag = _group_settings.get("group_tag", "BOT")
    n_batch = _group_settings.get("numbers_per_batch", 1)
    id_str = f"<code>{grp_id}</code>" if grp_id else "❌ Set hoy nai"
    link_str = grp_link or "❌ Set hoy nai"
    auto_str = f"🟢 ON ({del_secs // 60} min)" if auto_del else "🔴 OFF"
    grp_send_str = "🟢 ON (OTP goes to group)" if grp_send else "🔴 OFF (Inbox only)"
    ch2_str = ch2 or "❌ Set hoy nai"
    bot_str = bot_lnk or "❌ Set hoy nai"
    v3_on = _group_settings.get("v3_enabled", True)
    v3_str = "🟢 ON" if v3_on else "🔴 OFF"
    v2_mode = _group_settings.get("v2_user_mode", False)
    v2_mode_str = "🟢 ON (Shows Get Number button)" if v2_mode else "🔴 OFF (Shows V1+V2 Switch)"
    extra_grps = _group_settings.get("extra_groups", [])
    eg_str = f"{len(extra_grps)}extra group(s) added" if extra_grps else "❌ No extra group added"
    return (
        "⚙️ <b>BOT SETTINGS</b> ⚙️\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        "📡 <b>OTP GROUP</b>\n"
        f"🔗 Link: {link_str}\n"
        f"🆔 Chat ID: {id_str}\n"
        f"⏱️ Auto Delete: {auto_str}\n"
        f"📤 Group OTP Send: {grp_send_str}\n"
        f'👑 Number Tag: <b>{grp_tag}</b> (245<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{grp_tag}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>5660)\n'
        f"🔢 Numbers Per User: <b>{n_batch}</b>\n\n"
        "📢 <b>LINKS</b>\n"
        f"📢 Join Channel: {ch2_str}\n"
        f"🤖 Bot Link: {bot_str}\n\n"
        f"📡 Extra Groups: {eg_str}\n\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "⬇️ What do you want to change?"
    )


def _settings_markup():
    auto_del = _group_settings.get("auto_delete", True)
    grp_send = _group_settings.get("group_otp_send", True)
    grp_tag = _group_settings.get("group_tag", "BOT")
    n_batch = _group_settings.get("numbers_per_batch", 1)
    auto_label = "Auto Delete: 🟢 ON" if auto_del else "Auto Delete: 🔴 OFF"
    grp_send_label = "Group Send: 🟢 ON" if grp_send else "Group Send: 🔴 OFF"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Group Link", callback_data="grp_setlink", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("grp_link")),
        types.InlineKeyboardButton("Group Chat ID", callback_data="grp_setid", style="danger", icon_custom_emoji_id=_get_admin_btn_icon("grp_chat_id")),
    )
    markup.add(
        types.InlineKeyboardButton(auto_label, callback_data="set_autodel", style="success", icon_custom_emoji_id=_get_admin_btn_icon("auto_delete")),
        types.InlineKeyboardButton("Remove Group", callback_data="grp_remove", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("remove_group")),
    )
    markup.add(
        types.InlineKeyboardButton(grp_send_label, callback_data="toggle_grp_send", style="danger", icon_custom_emoji_id=_get_admin_btn_icon("grp_send")),
    )
    markup.add(
        types.InlineKeyboardButton(f"Number Tag: {grp_tag}", callback_data="set_group_tag", style="success", icon_custom_emoji_id=_get_admin_btn_icon("num_tag")),
    )
    markup.add(
        types.InlineKeyboardButton(f"Numbers Per User: {n_batch}", callback_data="set_num_batch", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("nums_per_user")),
    )
    markup.add(
        types.InlineKeyboardButton("Join Channel", callback_data="set_channel2", style="danger", icon_custom_emoji_id=_get_admin_btn_icon("join_channel")),
        types.InlineKeyboardButton("Bot Link", callback_data="set_botlink", style="success", icon_custom_emoji_id=_get_admin_btn_icon("bot_link")),
    )
    return markup


def _show_settings(message):
    bot.send_message(
        message.chat.id,
        _settings_text(message.from_user.id),
        reply_markup=_settings_markup(),
        parse_mode="HTML",
    )


def _show_settings_inline(call):
    try:
        bot.edit_message_text(
            _settings_text(call.from_user.id),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=_settings_markup(),
            parse_mode="HTML",
        )
    except Exception:
        pass


def _show_group_settings(message):
    _show_settings(message)


def _show_group_settings_inline(call):
    _show_settings_inline(call)


def _grp_get_link(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    link = (message.text or "").strip()
    if not link.startswith("https://t.me/") and not link.startswith("http://"):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Telegram link:\n<i>Example: https://t.me/aR_OTP_rcv</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _grp_get_link)
        return
    _admin_settings.setdefault(str(uid), {})["otp_group_link"] = link
    save_admin_settings()
    _group_settings["otp_group_link"] = link
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅🔥 <b>GROUP LINK UPDATED!</b>\n\n"
        f"🔗 <b>Notun Link:</b> {link}",
    )


def _grp_get_id(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw = (message.text or "").strip()
    try:
        gid = int(raw)
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Chat ID (number):\n<i>Example: -1001234567890</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _grp_get_id)
        return
    # Save per-admin; also update global if super admin
    _admin_settings.setdefault(str(uid), {})["otp_group_id"] = gid
    save_admin_settings()
    if is_super_admin(uid):
        _group_settings["otp_group_id"] = gid
        save_group_settings()
    _go_admin_panel(
        message,
        f"✅🔥 <b>GROUP CHAT ID UPDATED!</b>\n\n"
        f"🆔 <b>Notun Chat ID:</b> <code>{gid}</code>\n\n"
        f"<i>Only your settings have been updated.</i>",
    )


def _sett_get_channel2(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    link = (message.text or "").strip()
    if not link.startswith("https://") and not link.startswith("http://"):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid link:\n<i>Example: https://t.me/aR_OTP_rcv</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_channel2)
        return
    _admin_settings.setdefault(str(uid), {})["channel2"] = link
    save_admin_settings()
    _group_settings["channel2"] = link
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>JOIN CHANNEL UPDATED!</b>\n\n"
        f"📢 <b>Notun Link:</b> {link}",
    )


def _sett_get_botlink(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    link = (message.text or "").strip()
    if not link.startswith("https://") and not link.startswith("http://"):
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid link:\n<i>Example: https://t.me/ar_otp_bot</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_botlink)
        return
    _admin_settings.setdefault(str(uid), {})["bot_link"] = link
    save_admin_settings()
    _group_settings["bot_link"] = link
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>BOT LINK UPDATED!</b>\n\n"
        f"🤖 <b>Notun Link:</b> {link}",
    )


def _sett_get_support_id(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    val = (message.text or "").strip()
    if not val:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Support ID:\n<i>Example: @support_user or 123456789</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_support_id)
        return
    _group_settings["support_id"] = val
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>SUPPORT ID UPDATED!</b>\n\n"
        f"📞 <b>Notun Support ID:</b> <code>{val}</code>",
    )


def _chgkey_receive(message, panel_id):
    """Receive new API key from admin and apply it to the selected V2 panel."""
    global FASTX_API_KEY, STEX_API_KEY, V3_API_KEY
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text) or _intercept_menu_btn(message):
        return
    new_key = (message.text or "").strip()
    if not new_key:
        msg = bot.send_message(
            message.chat.id,
            "❌ API key khali — abar pathao:",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: _chgkey_receive(m, panel_id))
        return

    _PANEL_LABELS = {
        "fastx": "⚡ FastX SMS",
        "stex": "🌐 STEX SMS",
        "voltex": "🔮 Voltex SMS",
        "mk": "🟢 MK Panel",
        "augestel": "🌐 Augestel SMS",
    }
    label = _PANEL_LABELS.get(panel_id, panel_id.upper())

    if panel_id == "augestel":
        _augestel_store_key_from_message(message, new_key)
        return

    if panel_id == "fastx":
        FASTX_API_KEY = new_key
        _group_settings["fastx_api_key"] = new_key
    elif panel_id == "stex":
        STEX_API_KEY = new_key
        _group_settings["stex_api_key"] = new_key
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "stex":
                p["api_key"] = new_key
    elif panel_id == "voltex":
        V3_API_KEY = new_key
        _group_settings["voltex_api_key"] = new_key
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "voltex":
                p["api_key"] = new_key
    elif panel_id == "mk":
        MK_API_KEY = new_key
        _group_settings["mk_api_key"] = new_key
        for p in _V2_PANELS_REGISTRY:
            if p["id"] == "mk":
                p["api_key"] = new_key

    save_group_settings()
    _go_admin_panel(
        message,
        f"✅🔑 <b>API KEY UPDATED!</b>\n\n"
        f"📡 <b>Panel:</b> {label}\n"
        f"🔑 <b>New Key:</b> <code>{new_key}</code>\n\n"
        f"✅ From now on, API calls will use the new key.",
    )


def _sett_get_group_tag(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    val = (message.text or "").strip().upper()
    if not val or len(val) > 20:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid tag (max 20 char):\n<i>Example: ATIK, BOT, KING</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_group_tag)
        return
    _group_settings["group_tag"] = val
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>NUMBER TAG UPDATED!</b>\n\n"
        f'👑 <b>New Tag:</b> <code>{val}</code>\n'
        f'📱 Preview: <b>245<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>{val}<tg-emoji emoji-id="5267295703666824255">👑</tg-emoji>5660</b>\n\n'
        f"<i>From now on, numbers will show in this format in the group!</i>",
    )


def _sett_get_num_batch(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    txt = (message.text or "").strip()
    try:
        val = int(txt)
        if val < 1 or val > 10:
            raise ValueError
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
        "❌ Enter a number between 1 and 10:\n<i>Example: 1, 2, 3, 5</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _sett_get_num_batch)
        return
    _group_settings["numbers_per_batch"] = val
    save_group_settings()
    _go_admin_panel(
        message,
        f"✅ <b>NUMBERS PER USER UPDATED!</b>\n\n"
        f"🔢 <b>New Setting:</b> <code>{val}</code>\n\n"
        f"<i>Each user will now get {val} number(s) at a time.</i>",
    )


_pending_admin_uid = {}  # {requester_uid: new_uid}


def _admin_add_get_id(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    if _is_back(message.text):
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return
    raw = (message.text or "").strip()
    try:
        new_uid = int(raw)
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter a valid Telegram User ID (numbers only):\n<i>Example: 123456789</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, _admin_add_get_id)
        return
    if new_uid in SUPER_ADMIN_IDS:
        _go_admin_panel(message, "⚠️ <b>This user is already a Super Admin!</b>")
        return
    _pending_admin_uid[uid] = new_uid
    dur_kb = types.InlineKeyboardMarkup(row_width=3)
    dur_kb.add(
        types.InlineKeyboardButton("1 Mash", callback_data=f"aadur:{new_uid}:1", style="success"),
        types.InlineKeyboardButton("2 Mash", callback_data=f"aadur:{new_uid}:2", style="primary"),
        types.InlineKeyboardButton("3 Mash", callback_data=f"aadur:{new_uid}:3", style="danger"),
    )
    dur_kb.add(
        types.InlineKeyboardButton("❌ Cancel", callback_data="aadur_cancel", style="success"),
    )
    raw_n = user_names.get(str(new_uid), "")
    name_str = raw_n if isinstance(raw_n, str) else raw_n.get("first_name", str(new_uid))
    name_str = name_str or str(new_uid)
    bot.send_message(
        message.chat.id,
        f"👑 <b>Select Admin Duration</b>\n\n"
        f"🔹 <b>User:</b> {name_str} [<code>{new_uid}</code>]\n\n"
        f"Koto mash admin thakbe?",
        reply_markup=dur_kb,
        parse_mode="HTML",
    )


def _show_remove_admin(message):
    removable = [a for a in ADMIN_IDS if a not in SUPER_ADMIN_IDS]
    if not removable:
        bot.send_message(
            message.chat.id,
            "ℹ️ <b>Remove korar moto kono extra admin nei.</b>\n\n"
            "<i>Super Admin remove kora jabe na.</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for aid in removable:
        raw = user_names.get(str(aid), "")
        if isinstance(raw, dict):
            name = raw.get("first_name", "") or str(aid)
        else:
            name = raw or str(aid)
        markup.add(types.InlineKeyboardButton(
            f"🗑️ {name} [{aid}]", callback_data=f"rmadmin:{aid}", style="primary"
        ))
    bot.send_message(
        message.chat.id,
        "🗑️ <b>Remove Admin</b>\n\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "Select an admin from below:\n\n"
        "<i>⚠️ Super Admin remove kora jabe na.</i>",
        reply_markup=markup,
        parse_mode="HTML",
    )


_admin_panel_last: dict[int, float] = {}
_admin_panel_lock = threading.Lock()

# ── Resend stop flag ───────────────────────────────────────────────────────────
_resend_running = False
_resend_stop    = False


def _resend_old_otps(message):
    """Fetch today's real OTPs from ALL panels and forward to group (max 50 total)."""
    global _resend_running, _resend_stop
    uid = message.from_user.id
    cid = message.chat.id
    grp = get_admin_setting(uid, "otp_group_id", None) or get_otp_group_id()

    if not grp:
        bot.send_message(cid,
            "❌ <b>Group is not set!</b>\nSet the OTP Group from Settings.",
            parse_mode="HTML")
        return

    if _resend_running:
        bot.send_message(cid,
            "⚠️ <b>Resend already cholche!</b>\n"
            "🛑 Use the <b>Old OTP Stop</b> button to stop first.",
            parse_mode="HTML")
        return

    wait_msg = bot.send_message(
        cid,
        "⏳ <b>Fetching today's OTPs from all panels...</b>\n"
        "<i>(Only real SMS OTPs — fake/range data will be excluded)</i>",
        parse_mode="HTML",
    )

    _resend_running = True
    _resend_stop    = False

    def _do_resend():
        global _resend_running, _resend_stop
        all_found = {}

        static_fetchers = [
            ("P1", fetch_panel1), ("P2", fetch_panel2),
            ("P3", fetch_panel3), ("P4", fetch_panel4),
            ("P5", fetch_panel5), ("P6", fetch_panel6),
        ]
        for pid, fetcher in static_fetchers:
            if _resend_stop:
                break
            try:
                result = fetcher()
                all_found.update(result)
                print(f"[RESEND] {pid}: {len(result)} real OTPs")
            except Exception as e:
                print(f"[RESEND] {pid} error: {e}")

        for panel in list(_dynamic_panels):
            if _resend_stop:
                break
            try:
                result = _universal_fetch(panel)
                all_found.update(result)
                print(f"[RESEND] {panel['id']}: {len(result)} real OTPs")
            except Exception as e:
                print(f"[RESEND] {panel['id']} error: {e}")

        try:
            bot.delete_message(cid, wait_msg.message_id)
        except Exception:
            pass

        if _resend_stop:
            bot.send_message(cid, "🛑 <b>Resend has been stopped!</b>", parse_mode="HTML")
            _resend_running = False
            return

        if not all_found:
            bot.send_message(
                cid,
                "⚠️ <b>Kono real OTP panel e nai!</b>\n"
                "<i>Fake/range data was excluded. Only real SMS OTPs were counted.</i>",
                parse_mode="HTML",
            )
            _resend_running = False
            return

        MAX_SEND = 50
        items  = list(all_found.values())[:MAX_SEND]
        total  = len(all_found)
        sent   = 0
        failed = 0

        bot.send_message(
            cid,
        f"📤 <b>{total} real OTP(s) found!</b>\n"
        f"<i>Max {MAX_SEND} will be sent.</i>",
            parse_mode="HTML",
        )

        for number, otp_val, sms_txt, service in items:
            if _resend_stop:
                break
            try:
                send_otp_message(grp, otp_val, number, "—", service, sms_txt or "")
                sent += 1
                time.sleep(0.4)
            except Exception as e:
                failed += 1
                print(f"[RESEND] Send error {number}: {e}")

        _resend_running = False
        status_icon = "🛑 Stopped!" if _resend_stop else "✅ Done!"
        bot.send_message(
            cid,
            f"{status_icon}\n\n"
            f"📊 <b>Total real OTPs:</b> {total}\n"
            f"?? <b>Sent:</b> {sent}\n"
            f"❌ <b>Failed:</b> {failed}",
            parse_mode="HTML",
        )

    threading.Thread(target=_do_resend, daemon=True).start()


_custom_emoji_state: dict = {}   # uid -> "flag" | "service" | "del_flag" | "del_service"

_MSG_ICON_GROUPS = [
    ("📲 DM Message Emoji", ["dm_number_pre", "dm_country_pre", "dm_country_post"]),
    ("🏳️ Flag Emoji", ["flag_default"]),
    ("📱 OTP Messages", ["otp_phone", "otp_key", "otp_world", "otp_sms"]),
    ("?? Start Screen", ["start_header", "start_crown", "start_user", "start_id", "start_status", "start_workers", "start_powered"]),
    ("✅ Verify Screen", ["verify_title"]),
]

def _show_msg_icons_menu(message, note=""):
    """Inline keyboard menu for setting/resetting predefined message icon slots."""
    with _custom_emoji_lock:
        slots_set = dict(_custom_emojis.get("msg_slots", {}))
    markup = types.InlineKeyboardMarkup(row_width=2)
    lines = []
    for group_label, group_keys in _MSG_ICON_GROUPS:
        lines.append(f"\n<b>{group_label}:</b>")
        for key in group_keys:
            if key not in _MSG_ICON_SLOTS:
                continue
            default_char, label = _MSG_ICON_SLOTS[key]
            custom = slots_set.get(key)
            if custom:
                fb  = custom.get("fb", default_char)
                cid = custom.get("id", "")
                lines.append(f"  ✅ {fb} <b>{label}</b> <code>[{cid[:8]}…]</code>")
                markup.add(
                    types.InlineKeyboardButton(f"✏️ {label}", callback_data=f"msgicon_set:{key}"),
                    types.InlineKeyboardButton("🔄 Reset", callback_data=f"msgicon_reset:{key}"),
                )
            else:
                lines.append(f"  🔘 {default_char} <b>{label}</b> (default)")
                markup.add(
                    types.InlineKeyboardButton(f"✏️ {label}", callback_data=f"msgicon_set:{key}"),
                    types.InlineKeyboardButton("—", callback_data="msgicon_noop"),
                )
    markup.add(types.InlineKeyboardButton("❌ Close", callback_data="msgicon_close"))
    text = (
        f"✨ <b>Message Icons</b>\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"<i>✏️ Click to send a custom emoji sticker or type the ID.</i>\n"
        f"<i>🔄 Reset to restore the default emoji.</i>"
        + "\n".join(lines)
        + ("\n\n<i>✅ " + note + "</i>" if note else "")
        + "\n\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
    )
    try:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"[MSG-ICONS] Failed: {e}")


def _set_msg_icon_step(message):
    """Step handler: receive custom emoji for a message icon slot."""
    uid = message.from_user.id
    state = _msg_icon_set_state.pop(uid, None)
    if not state:
        return
    if _is_back(message.text) or _intercept_menu_btn(message):
        return
    slot_key = state["key"]
    default_char, label = _MSG_ICON_SLOTS.get(slot_key, ("", ""))
    custom_emoji_id = None
    fallback_char = default_char
    if message.entities:
        for ent in message.entities:
            if ent.type == "custom_emoji":
                custom_emoji_id = getattr(ent, "custom_emoji_id", None)
                text = message.text or ""
                fallback_char = text[ent.offset:ent.offset + ent.length] or default_char
                break
    if not custom_emoji_id:
        txt = (message.text or "").strip()
        if txt.isdigit() and len(txt) > 10:
            custom_emoji_id = txt
        else:
            msg = bot.send_message(
                message.chat.id,
        "❌ Custom emoji not found!\n\n"
        "Send a Telegram premium custom emoji sticker, or enter the emoji ID.\n\nTry again:",
                parse_mode="HTML",
                reply_markup=_back_admin_kb(),
            )
            _msg_icon_set_state[uid] = state
            bot.register_next_step_handler(msg, _set_msg_icon_step)
            return
    with _custom_emoji_lock:
        _custom_emojis.setdefault("msg_slots", {})[slot_key] = {"id": custom_emoji_id, "fb": fallback_char}
    _save_custom_emojis()
    _show_edit_messages_menu(message, note=f"✅ <b>{label}</b> — custom emoji set!")


def _show_custom_emoji_menu(message, note=""):
    uid = message.from_user.id
    with _custom_emoji_lock:
        flags_set   = dict(_custom_emojis.get("flags", {}))
        svcs_set    = dict(_custom_emojis.get("services", {}))
        btns_set    = dict(_custom_emojis.get("buttons", {}))
        slots_set   = dict(_custom_emojis.get("msg_slots", {}))
        dm_e_set    = dict(_custom_emojis.get("dm_emoji", {}))

    if len(flags_set) > 8:
        flag_lines = f"  ✅ Total <b>{len(flags_set)}</b> flag custom emojis set\n  (📋 Use Flag JSON Export to view all)"
    else:
        flag_lines = "\n".join(f"  {k} → <code>{v}</code>" for k, v in flags_set.items()) or "  (none — use 🏳️ Flag Emoji Set to add)"
    svc_lines  = "\n".join(f"  {k} → <code>{v}</code>" for k, v in svcs_set.items())  or "  (none)"
    btn_lines  = "\n".join(f"  <code>{k}</code> → <code>{v}</code>" for k, v in btns_set.items()) or "  (none)"
    slot_lines = "\n".join(f"  {{emoji_{k}}} → {v.get('fb','?')} (id:<code>{v.get('id','')}</code>)" for k, v in slots_set.items()) or "  (none)"

    dm_emoji_lines = ""
    for key, defs in _DM_EMOJI_DEFAULTS.items():
        cur = dm_e_set.get(key, {})
        cur_id = cur.get("id") or defs["id"]
        cur_fb = cur.get("fb") or defs["fb"]
        label  = _DM_EMOJI_LABELS.get(key, key)
        dm_emoji_lines += f"  {cur_fb} <b>{label}</b> → <code>{cur_id}</code>\n"

    all_btn_keys = "\n".join(
        f"  <code>{k}</code> — {v}" for k, v in _BTN_DISPLAY_NAMES.items()
    )
    text = (
        f"🎨 <b>Custom Emoji Settings</b>\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n\n"
        f"📲 <b>DM Message Emoji (number/country):</b>\n{dm_emoji_lines}\n"
        f"🏳️ <b>Flag Emojis:</b>\n{flag_lines}\n\n"
        f"🎯 <b>Service Emojis:</b>\n{svc_lines}\n\n"
        f"🔘 <b>Button Emojis (set):</b>\n{btn_lines}\n\n"
        f"📋 <b>All Button Keys:</b>\n{all_btn_keys}\n\n"
        f"💬 <b>Message Slot Emojis:</b>\n{slot_lines}\n\n"
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        + (f"<i>{note}</i>\n" if note else "")
    )
    mk = types.ReplyKeyboardMarkup(resize_keyboard=True)
    mk.add("🏳️ Flag Emoji Set", "🎯 Service Emoji Set")
    mk.add("🌍 All Flags JSON Set", "📋 Flag JSON Export")
    mk.add("🔢 IDs Only Set", "🗑️ Flag Emoji Del")
    mk.add("🗑️ Service Emoji Del", "🔘 Button Emoji Set")
    mk.add("🗑️ Button Emoji Del", "💬 Msg Emoji Set")
    mk.add("🗑️ Msg Emoji Del", "🖥️ Admin Btn Set")
    mk.add("🗑️ Admin Btn Del")
    mk.add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟")
    bot.send_message(message.chat.id, text, reply_markup=mk, parse_mode="HTML")


def _custom_emoji_input(message):
    uid = message.from_user.id
    mode = _custom_emoji_state.pop(uid, None)
    if not mode:
        return

    # ── document sent while in "service" mode → parse as Service Emoji ID file ──
    if message.document and mode == "service":
        doc = message.document
        fname = doc.file_name or ""
        fext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        wait = bot.send_message(message.chat.id,
            f"⏳ <b>{fname}</b> parsing...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
            content = raw.decode("utf-8", errors="ignore")
        except Exception as e:
            bot.edit_message_text(f"❌ File download hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return
        loaded = {}
        skipped = []
        if fext == "json":
            try:
                data = json.loads(content)
            except Exception as je:
                bot.edit_message_text(
                    f"❌ JSON parse error: <code>{je}</code>",
                    message.chat.id, wait.message_id, parse_mode="HTML")
                return
            if not isinstance(data, dict):
                bot.edit_message_text(
                    "❌ <b>Invalid format!</b>\n\n"
                    "The JSON file should be:\n"
                    "<code>{\n"
                    '  "WHATSAPP": "5334998226636390258",\n'
                    '  "INSTAGRAM": "5319160079465857105"\n'
                    "}</code>",
                    message.chat.id, wait.message_id, parse_mode="HTML")
                return
            for svc_raw, eid in data.items():
                svc = str(svc_raw).upper().strip()
                eid = str(eid).strip()
                if svc and eid.isdigit():
                    loaded[svc] = eid
                else:
                    skipped.append(f"{svc_raw}")
        else:
            # .txt or any other: robust line-by-line parse
            import re as _re_svc
            # Try whole-file JSON first
            try:
                _jdata = json.loads(content)
                if isinstance(_jdata, dict):
                    for k, v in _jdata.items():
                        svc = str(k).upper().strip()
                        _eid_m = _re_svc.search(r'\d{10,}', str(v))
                        if svc and _eid_m:
                            loaded[svc] = _eid_m.group(0)
                        else:
                            skipped.append(str(k))
            except Exception:
                # Line-by-line: any 10+ digit number + preceding word = service
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    _eid_m = _re_svc.search(r'(\d{10,})', line)
                    if not _eid_m:
                        skipped.append(line)
                        continue
                    eid = _eid_m.group(1)
                    prefix = line[:line.index(eid)]
                    _svc_m = _re_svc.search(r'([A-Za-z][A-Za-z0-9 _\-]{1,20})', prefix)
                    if _svc_m:
                        svc = _re_svc.sub(r'[\s\-_]+', '_', _svc_m.group(1).strip()).upper().rstrip('_:→ ')
                        if svc:
                            loaded[svc] = eid
                        else:
                            skipped.append(line)
                    else:
                        skipped.append(line)
        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass
        if not loaded:
            bot.send_message(message.chat.id,
                "❌ <b>Kono valid service emoji ID pawa jayni!</b>\n\n"
                "JSON format:\n"
                "<code>{\"WHATSAPP\": \"5334998226636390258\"}</code>\n\n"
                "TXT format (line by line):\n"
                "<code>WHATSAPP 5334998226636390258\nINSTAGRAM 5319160079465857105</code>",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("services", {}).update(loaded)
        _save_custom_emojis()
        lines_preview = "\n".join(
            f"  🎯 <b>{k}</b> → <code>{v}</code>" for k, v in list(loaded.items())[:20])
        extra = f"\n  <i>...and {len(loaded)-20} more</i>" if len(loaded) > 20 else ""
        skip_txt = f"\n\n⚠️ Skip: {', '.join(skipped[:5])}" if skipped else ""
        _show_custom_emoji_menu(message,
            note=f"✅ {len(loaded)} service emoji set!\n{lines_preview}{extra}{skip_txt}")
        return
    # ─────────────────────────────────────────────────────────────────────────────

    # ── .txt document sent while in a flag mode → parse as Premium Flag file ──
    if message.document and mode in ("flag", "flag_bulk_json", "flag_ids_only"):
        doc = message.document
        fname = doc.file_name or ""
        if fname.lower().endswith(".txt"):
            wait = bot.send_message(message.chat.id,
                f"⏳ <b>{fname}</b> parsing...", parse_mode="HTML")
            try:
                file_info = bot.get_file(doc.file_id)
                raw = bot.download_file(file_info.file_path)
                txt_content = raw.decode("utf-8", errors="ignore")
            except Exception as e:
                bot.edit_message_text(
                    f"❌ File download hoyni: <code>{e}</code>",
                    message.chat.id, wait.message_id, parse_mode="HTML")
                return
            import re as _re2
            parsed = {}
            for line in txt_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Primary format: (1)(US)🇺🇸 United States {"emoji": "🇺🇸", "id": "591..."}
                m = _re2.search(r'"id"\s*:\s*"(\d+)"', line)
                flag_m = _re2.search(r'[🇠-🇿]{2}', line)
                if m and flag_m:
                    parsed[flag_m.group(0)] = m.group(1)
                    continue
                # Fallback: flag_emoji  numeric_id (or with →)
                clean = _re2.sub(r'^[\d\.\)\-\s]+', '', line).strip()
                clean = clean.replace('→', '').strip()
                tokens = clean.split()
                if len(tokens) >= 2 and tokens[-1].isdigit() and len(tokens[-1]) >= 10:
                    fchar = next((t for t in tokens
                        if len(t) == 2 and all(
                            '🇠' <= c <= '🇿' for c in t)), None)
                    if fchar:
                        parsed[fchar] = tokens[-1]
            try:
                bot.delete_message(message.chat.id, wait.message_id)
            except Exception:
                pass
            if not parsed:
                bot.send_message(message.chat.id,
                    "❌ <b>Couldn't parse flag data from the file!</b>\n\n"
                    "Expected format:\n"
                    "<code>(1)(US)🇺🇸 United States {\"emoji\": \"🇺🇸\", \"id\": \"123...\"}</code>",
                    parse_mode="HTML")
                return
            with _custom_emoji_lock:
                _custom_emojis.setdefault("flags", {}).update(parsed)
            _save_custom_emojis()
            lines_preview = "\n".join(
                f"  {k} → <code>{v}</code>" for k, v in list(parsed.items())[:10])
            extra = f"\n  <i>...and {len(parsed)-10} more</i>" if len(parsed) > 10 else ""
            bot.send_message(message.chat.id,
                f"✅ <b>{len(parsed)} custom flag emoji(s) loaded!</b>\n\n"
                f"{lines_preview}{extra}\n\n"
                f"🎉 Custom flags will now appear in all OTP/number messages.",
                parse_mode="HTML")
            return
    # ─────────────────────────────────────────────────────────────────────────────

    txt = (message.text or "").strip()
    if _is_back(txt) or txt == "🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟":
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        return

    parts = txt.split()

    if mode == "flag":
        # Supports: "🇧🇩 ID", "🇧🇩 → ID", numbered "1. 🇧🇩 ID", "1. 🇧🇩 → ID"
        import re as _re
        lines = [l.strip() for l in txt.splitlines() if l.strip()]
        parsed = {}
        for line in lines:
            # Strip leading "1." "1)" "1-" numbering
            clean = _re.sub(r'^\d+[\.\)\-]\s*', '', line).strip()
            # Remove → arrow separator
            clean = clean.replace('→', '').replace('->', '')
            tokens = clean.split()
            # First token = flag emoji, last token = numeric ID
            if len(tokens) >= 2 and tokens[-1].isdigit():
                parsed[tokens[0]] = tokens[-1]
        if not parsed:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n"
        "<b>Format (any one):</b>\n"
                "<code>🇧🇩 5432198765432198765</code>\n"
                "<code>🇧🇩 → 5432198765432198765</code>\n\n"
                "<b>Bulk:</b>\n<code>1. 🇧🇩 → 5432198765432198765\n2. 🇺🇸 → 5976694588658686266</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        added = "\n".join(f"  {k} → <code>{v}</code>" for k, v in parsed.items())
        _show_custom_emoji_menu(message, note=f"✅ {len(parsed)}flag(s) set:\n{added}")

    elif mode == "flag_bulk_json":
        # Accept a JSON object: {"🇧🇩": "123456789", "🇺🇸": "987654321", ...}
        # Also accept line-by-line: 🇧🇩 123456789\n🇺🇸 987654321
        import re as _re
        parsed = {}
        err_msg = ""
        # Try JSON first
        raw = txt.strip()
        # Strip markdown code fences if present
        raw = _re.sub(r'^```[a-z]*\n?', '', raw, flags=_re.IGNORECASE)
        raw = _re.sub(r'\n?```$', '', raw)
        raw = raw.strip()
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object/dict")
            for k, v in data.items():
                v_str = str(v).strip()
                if v_str.isdigit():
                    parsed[k.strip()] = v_str
                else:
                    err_msg += f"⚠️ <code>{k}</code> — Invalid ID (<code>{v}</code>), skipped\n"
        except json.JSONDecodeError:
            # Fall back to line-by-line parsing
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            for line in lines:
                clean = _re.sub(r'^\d+[\.\)\-]\s*', '', line).strip()
                tokens = clean.split()
                if len(tokens) == 2 and tokens[1].isdigit():
                    parsed[tokens[0]] = tokens[1]

        if not parsed:
            bot.send_message(message.chat.id,
        "❌ Could not parse anything!\n\n"
        "<b>JSON Format:</b>\n"
                "<code>{\n"
                '  "🇧🇩": "5432198765432198765",\n'
                '  "🇺🇸": "5976694588658686266"\n'
                "}</code>\n\n"
                "<b>Line-by-line format also works:</b>\n"
                "<code>🇧🇩 5432198765432198765\n🇺🇸 5976694588658686266</code>\n\n"
                "Send again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        added_lines = "\n".join(f"  {k} → <code>{v}</code>" for k, v in parsed.items())
        note = f"✅ {len(parsed)}flag(s) set from JSON:\n{added_lines}"
        if err_msg:
            note += f"\n\n{err_msg}"
        _show_custom_emoji_menu(message, note=note)

    elif mode == "flag_ids_only":
        # User pastes only emoji IDs (one per line or space-separated).
        # Bot calls Telegram API to resolve each ID → emoji character, then saves.
        import re as _re
        raw_ids = []
        for token in _re.split(r'[\s,\n]+', txt):
            token = token.strip()
            if token.isdigit() and len(token) >= 10:
                raw_ids.append(token)
        if not raw_ids:
            bot.send_message(message.chat.id,
        "❌ No valid ID found!\n\n"
        "Enter one numeric emoji ID per line:\n"
                "<code>5432198765432198765\n5976694588658686266</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        raw_ids = raw_ids[:200]  # cap at 200
        bot.send_message(message.chat.id,
            f"⏳ {len(raw_ids)}ID(s) being resolved from Telegram...",
            parse_mode="HTML")
        parsed = {}
        failed = []
        # Telegram allows max 200 IDs per call — process in chunks of 100
        chunk_size = 100
        for i in range(0, len(raw_ids), chunk_size):
            chunk = raw_ids[i:i + chunk_size]
            try:
                stickers = bot.get_custom_emoji_stickers(chunk)
                # Zip original IDs with returned stickers (API returns in same order)
                # sticker.custom_emoji_id may be None in some pyTelegramBotAPI versions
                for eid_orig, sticker in zip(chunk, stickers):
                    emoji_char = getattr(sticker, "emoji", None)
                    eid = getattr(sticker, "custom_emoji_id", None) or eid_orig
                    if emoji_char and eid:
                        parsed[emoji_char] = eid
            except Exception as _api_err:
                failed.extend(chunk)
                print(f"[FLAG-IDS] API error for chunk: {_api_err}")
        if not parsed:
            bot.send_message(message.chat.id,
        "❌ No emoji could be resolved from Telegram!\n\n"
        "Check if the IDs are valid. Send again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("flags", {}).update(parsed)
        _save_custom_emojis()
        added_lines = "\n".join(f"  {k} → <code>{v}</code>" for k, v in parsed.items())
        note = f"✅ {len(parsed)}flag(s) auto-resolved and set:\n{added_lines}"
        if failed:
            note += f"\n\n⚠️ {len(failed)}ID(s) could not be resolved."
        _show_custom_emoji_menu(message, note=note)

    elif mode == "service":
        # Format: INSTAGRAM 5319160079465857105
        if len(parts) != 2:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>INSTAGRAM 5319160079465857105</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        svc_name, emoji_id = parts[0].upper(), parts[1]
        with _custom_emoji_lock:
            _custom_emojis.setdefault("services", {})[svc_name] = emoji_id
        _save_custom_emojis()
        _show_custom_emoji_menu(message, note=f"✅ {svc_name} → {emoji_id} set!")

    elif mode == "del_flag":
        emoji_char = parts[0] if parts else ""
        with _custom_emoji_lock:
            removed = _custom_emojis.get("flags", {}).pop(emoji_char, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ {emoji_char} deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>{emoji_char}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "del_service":
        svc_name = (parts[0] if parts else "").upper()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("services", {}).pop(svc_name, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ {svc_name} deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>{svc_name}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "btn":
        # Format: button_key emoji_id  (e.g. change_number 5375170473095077321)
        if len(parts) != 2:
            available = "\n".join(f"  <code>{k}</code> — {v}" for k, v in _BTN_DISPLAY_NAMES.items())
            bot.send_message(message.chat.id,
        f"❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>button_key emoji_id</code>\n\n"
                f"<b>Available buttons:</b>\n{available}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        btn_key, emoji_id = parts[0].lower(), parts[1]
        if btn_key not in _BTN_DISPLAY_NAMES:
            available = ", ".join(f"<code>{k}</code>" for k in _BTN_DISPLAY_NAMES)
            bot.send_message(message.chat.id,
        f"❌ <code>{btn_key}</code> not found!\n\nValid keys: {available}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("buttons", {})[btn_key] = emoji_id
        _save_custom_emojis()
        _show_custom_emoji_menu(message, note=f"✅ Button <code>{btn_key}</code> → <code>{emoji_id}</code> set!")

    elif mode == "del_btn":
        btn_key = (parts[0] if parts else "").lower()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("buttons", {}).pop(btn_key, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ Button <code>{btn_key}</code> deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>{btn_key}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "admin_btn":
        # Accepts single or bulk lines: key emoji_id
        import re as _re_ab
        lines_in = [l.strip() for l in txt.splitlines() if l.strip()]
        saved = {}
        bad = []
        for line in lines_in:
            m = _re_ab.match(r'^([a-z_]+)\s+(\d{10,})$', line)
            if m:
                key, eid = m.group(1), m.group(2)
                if key in _ADMIN_BTN_DEFAULT_ICONS:
                    saved[key] = eid
                else:
                    bad.append(f"<code>{key}</code> (unknown key)")
            else:
                bad.append(f"<code>{line[:40]}</code>")
        if not saved:
            bot.send_message(
                message.chat.id,
                "❌ <b>Wrong format!</b>\n\n"
                "<b>Format:</b> <code>key emoji_id</code>\n"
                "<b>Example:</b> <code>num_add 5420323438508155202</code>\n\n"
                "Key must be from the list shown. Send again:",
                parse_mode="HTML"
            )
            _custom_emoji_state[uid] = mode
            return
        with _custom_emoji_lock:
            _custom_emojis.setdefault("admin_btns", {}).update(saved)
        _save_custom_emojis()
        note_lines = "\n".join(f"  ✅ <code>{k}</code> → <code>{v}</code>" for k, v in saved.items())
        bad_txt = ("\n\n⚠️ Skipped: " + ", ".join(bad[:5])) if bad else ""
        _show_custom_emoji_menu(message,
            note=f"✅ {len(saved)} admin button icon(s) updated!\n{note_lines}{bad_txt}")

    elif mode == "del_admin_btn":
        key_in = (parts[0] if parts else "").strip()
        if key_in.upper() == "ALL":
            with _custom_emoji_lock:
                count = len(_custom_emojis.get("admin_btns", {}))
                _custom_emojis["admin_btns"] = {}
            _save_custom_emojis()
            _show_custom_emoji_menu(message,
                note=f"🗑️ All {count} admin button override(s) reset to defaults!")
        else:
            key_in = key_in.lower()
            with _custom_emoji_lock:
                removed = _custom_emojis.get("admin_btns", {}).pop(key_in, None)
            if removed:
                _save_custom_emojis()
                _show_custom_emoji_menu(message,
                    note=f"🗑️ <code>{key_in}</code> reset to default icon!")
            else:
                bot.send_message(
                    message.chat.id,
                    f"❌ <code>{key_in}</code> not found in overrides.",
                    parse_mode="HTML"
                )
                _custom_emoji_state[uid] = mode

    elif mode == "msg_slot":
        # Format: slot_name emoji_id fallback_emoji  (e.g. fire 5432198765432198765 🔥)
        if len(parts) < 3:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>slot_name emoji_id fallback_emoji</code>\n\n"
        "<b>Example:</b>\n<code>fire 5432198765432198765 🔥</code>\n\n"
                "Then use <code>{emoji_fire}</code> in any message template to show the custom emoji.\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        slot_name = parts[0].lower()
        emoji_id  = parts[1]
        fallback  = " ".join(parts[2:])
        with _custom_emoji_lock:
            _custom_emojis.setdefault("msg_slots", {})[slot_name] = {"id": emoji_id, "fb": fallback}
        _save_custom_emojis()
        _show_custom_emoji_menu(message,
            note=f"✅ Slot <code>emoji_{slot_name}</code> set!\n"
                 f"Use <code>{{emoji_{slot_name}}}</code> in templates.")

    elif mode == "del_msg_slot":
        slot_name = (parts[0] if parts else "").lower()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("msg_slots", {}).pop(slot_name, None)
        if removed:
            _save_custom_emojis()
            _show_custom_emoji_menu(message, note=f"🗑️ Slot <code>emoji_{slot_name}</code> deleted!")
        else:
            bot.send_message(message.chat.id, f"❌ <code>emoji_{slot_name}</code> not found.", parse_mode="HTML")
            _custom_emoji_state[uid] = mode

    elif mode == "dm_emoji":
        # Format: slot_key emoji_id fallback_emoji  e.g. "number_pre 5422858869372104873 📞"
        if len(parts) < 3:
            bot.send_message(message.chat.id,
        "❌ Wrong format!\n\n<b>Correct Format:</b>\n<code>slot_key emoji_id fallback_emoji</code>\n\n"
        "<b>Example:</b>\n<code>number_pre 5422858869372104873 📞</code>\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        slot_key = parts[0].lower()
        if slot_key not in _DM_EMOJI_DEFAULTS:
            valid = ", ".join(f"<code>{k}</code>" for k in _DM_EMOJI_DEFAULTS)
            bot.send_message(message.chat.id,
        f"❌ <code>{slot_key}</code> is invalid!\n\nValid keys: {valid}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode
            return
        emoji_id = parts[1]
        fallback = " ".join(parts[2:])
        with _custom_emoji_lock:
            _custom_emojis.setdefault("dm_emoji", {})[slot_key] = {"id": emoji_id, "fb": fallback}
        _save_custom_emojis()
        label = _DM_EMOJI_LABELS.get(slot_key, slot_key)
        _show_custom_emoji_menu(message,
            note=f"✅ DM emoji <b>{label}</b> → {fallback} <code>{emoji_id}</code> set!")

    elif mode == "del_dm_emoji":
        slot_key = (parts[0] if parts else "").lower()
        with _custom_emoji_lock:
            removed = _custom_emojis.get("dm_emoji", {}).pop(slot_key, None)
        if removed:
            _save_custom_emojis()
            label = _DM_EMOJI_LABELS.get(slot_key, slot_key)
            _show_custom_emoji_menu(message, note=f"🗑️ DM emoji <b>{label}</b> reset to default!")
        else:
            valid = ", ".join(f"<code>{k}</code>" for k in _DM_EMOJI_DEFAULTS)
            bot.send_message(message.chat.id,
        f"❌ <code>{slot_key}</code> was not customized.\nValid keys: {valid}\n\nSend again:",
                parse_mode="HTML")
            _custom_emoji_state[uid] = mode


# ── Payment System — User Functions ──────────────────────────────────────────

def _show_balance(message):
    uid = message.from_user.id
    bal = get_balance(uid)
    cur = get_currency()
    rpo = get_reward_per_otp()
    with otp_stats_lock:
        total_otps = otp_stats.get(str(uid), 0)
    # Count this user's pending/approved withdraw requests
    with _withdraw_lock:
        pending = [r for r in _withdraw_requests if r["uid"] == uid and r["status"] == "pending"]
        approved = [r for r in _withdraw_requests if r["uid"] == uid and r["status"] == "approved"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💸 Withdraw", callback_data="wd_start"))
    bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5445353829304387411">💰</tg-emoji> <b>Your Wallet</b>\n'
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        f'<tg-emoji emoji-id="5197434882321567830">💵</tg-emoji> <b>Balance:</b> <code>{cur}{bal:.2f}</code>\n'
        f'<tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji> <b>Per OTP Reward:</b> <code>{cur}{rpo:.2f}</code>\n'
        f'<tg-emoji emoji-id="5451882707875276247">📊</tg-emoji> <b>Total OTPs:</b> <code>{total_otps}</code>\n'
        f'<tg-emoji emoji-id="5386367538735104399">⏳</tg-emoji> <b>Pending Withdraw:</b> <code>{len(pending)}</code>\n'
        f'<tg-emoji emoji-id="5206607081334906820">✅</tg-emoji> <b>Approved Withdraw:</b> <code>{len(approved)}</code>\n'
        f"<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>",
        parse_mode="HTML",
        reply_markup=markup,
    )


def _show_refer(message):
    uid = message.from_user.id
    link = _get_refer_link(uid)
    count = _get_refer_count(uid)
    cur = get_currency()
    commission = get_refer_commission()
    _SEP = '<tg-emoji emoji-id="5870818207383686839">🔗</tg-emoji>' * 8
    bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5420145051336485498">🔗</tg-emoji> <b>Referral Program</b>\n'
        f'{_SEP}\n'
        f'<tg-emoji emoji-id="5352694861990501856">👥</tg-emoji> <b>Your Referrals:</b> <code>{count}</code> people\n'
        f'<tg-emoji emoji-id="5796420706572966288">💰</tg-emoji> <b>Commission per Refer:</b> <code>{cur}{commission:.2f}</code>\n'
        f'{_SEP}\n'
        f'<tg-emoji emoji-id="5420517437885943844">📎</tg-emoji> <b>Your Referral Link:</b>\n'
        f'<code>{link}</code>\n'
        f'{_SEP}\n'
        f'<tg-emoji emoji-id="5267041999948653482">🔗</tg-emoji> <i>Share this link — when someone joins, you\'ll get {cur}{commission:.2f}!</i>',
        parse_mode="HTML",
    )


_withdraw_state: dict = {}


def _start_withdraw(message):
    uid = message.from_user.id
    bal = get_balance(uid)
    cur = get_currency()
    min_wd = get_min_withdraw()
    if bal < min_wd:
        bot.send_message(
            message.chat.id,
            f'❌ <b>Insufficient Balance!</b>\n\n'
            f'<tg-emoji emoji-id="5197434882321567830">💵</tg-emoji> Your Balance: <code>{cur}{bal:.2f}</code>\n'
            f'<tg-emoji emoji-id="5368493177634301681">⚠️</tg-emoji> Minimum Withdraw: <code>{cur}{min_wd:.2f}</code>\n\n'
            f'Get more OTPs and earn rewards to withdraw.',
            parse_mode="HTML",
        )
        return
    msg = bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5386367538735104399">💸</tg-emoji> <b>Withdraw Request</b>\n\n'
        f'<tg-emoji emoji-id="5197434882321567830">💵</tg-emoji> Your Balance: <code>{cur}{bal:.2f}</code> <tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji>\n'
        f'<tg-emoji emoji-id="5368493177634301681">⚠️</tg-emoji> Minimum: <code>{cur}{min_wd:.2f}</code> <tg-emoji emoji-id="5417924076503062111">🎁</tg-emoji>\n\n'
        f'How much do you want to withdraw? (enter a number)\n'
        f'Example: <code>100</code>',
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
    )
    _withdraw_state[uid] = {"step": "amount"}
    bot.register_next_step_handler(msg, _wd_amount_step)


def _wd_amount_step(message):
    uid = message.from_user.id
    txt = (message.text or "").strip()
    if txt in ("❌ Cancel", "❌ Cancel") or _is_back(txt):
        _withdraw_state.pop(uid, None)
        bot.send_message(message.chat.id, "❌ Withdraw cancelled.",
                         reply_markup=main_menu(uid), parse_mode="HTML")
        return
    if _intercept_menu_btn(message):
        _withdraw_state.pop(uid, None)
        return
    try:
        amount = float(txt.replace(",", "").strip())
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Please enter a number! Example: <code>100</code>",
                                parse_mode="HTML")
        bot.register_next_step_handler(msg, _wd_amount_step)
        return
    cur = get_currency()
    bal = get_balance(uid)
    min_wd = get_min_withdraw()
    if amount < min_wd:
        msg = bot.send_message(message.chat.id,
            f"❌ Minimum <code>{cur}{min_wd:.2f}</code> required to withdraw. Please enter again:",
            parse_mode="HTML")
        bot.register_next_step_handler(msg, _wd_amount_step)
        return
    if amount > bal:
        msg = bot.send_message(message.chat.id,
            f"❌ Insufficient balance! You have <code>{cur}{bal:.2f}</code>. Please enter again:",
            parse_mode="HTML")
        bot.register_next_step_handler(msg, _wd_amount_step)
        return
    _withdraw_state[uid]["amount"] = amount
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("bKash",   callback_data="wd_method:bKash",   icon_custom_emoji_id="6084377871265041519", style="danger"),
        types.InlineKeyboardButton("Nagad",   callback_data="wd_method:Nagad",   icon_custom_emoji_id="6082388335039351641", style="success"),
        types.InlineKeyboardButton("Rocket",  callback_data="wd_method:Rocket",  icon_custom_emoji_id="6084843995475742197", style="primary"),
        types.InlineKeyboardButton("Binance", callback_data="wd_method:Binance", icon_custom_emoji_id="5359437015752401733", style="success"),
        types.InlineKeyboardButton("❌ Cancel", callback_data="wd_cancel", style="danger"),
    )
    bot.send_message(
        message.chat.id,
        f'<tg-emoji emoji-id="5375135722514685501">💰</tg-emoji> Amount: <code>{cur}{amount:.2f}</code>\n\n<tg-emoji emoji-id="5388632425314140043">💳</tg-emoji> Choose payment method:',
        parse_mode="HTML",
        reply_markup=markup,
    )


def _wd_account_step(message):
    uid = message.from_user.id
    state = _withdraw_state.get(uid, {})
    txt = (message.text or "").strip()
    if txt in ("❌ Cancel", "❌ Cancel") or _is_back(txt):
        _withdraw_state.pop(uid, None)
        bot.send_message(message.chat.id, "❌ Withdraw cancelled.",
                         reply_markup=main_menu(uid), parse_mode="HTML")
        return
    if _intercept_menu_btn(message):
        _withdraw_state.pop(uid, None)
        return
    if not txt:
        msg = bot.send_message(message.chat.id, "❌ Enter account number/address:")
        bot.register_next_step_handler(msg, _wd_account_step)
        return
    state["account"] = txt
    method  = state.get("method", "?")
    amount  = state.get("amount", 0)
    cur = get_currency()
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Confirm", callback_data="wd_confirm_submit"),
        types.InlineKeyboardButton("❌ Cancel",   callback_data="wd_cancel"),
    )
    bot.send_message(
        message.chat.id,
        f"💸 <b>Confirm Withdraw</b>\n\n"
        f"💵 Amount: <code>{cur}{amount:.2f}</code>\n"
        f"📲 Method: <b>{method}</b>\n"
        f"📋 Account: <code>{txt}</code>\n\n"
        f"Are you sure?",
        parse_mode="HTML",
        reply_markup=markup,
    )


# ── Payment System — Admin Functions ──────────────────────────────────────────

def _show_payment_admin(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    cur = get_currency()
    rpo = get_reward_per_otp()
    min_wd = get_min_withdraw()
    with _withdraw_lock:
        pending_wds = [r for r in _withdraw_requests if r["status"] == "pending"]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ref_comm = get_refer_commission()
    markup.add("💵 Set Reward", "💱 Set Currency")
    markup.add("📉 Set Minimum Withdraw", "🔗 Set Refer Commission")
    markup.add("📋 View All Balances")
    markup.add("➕ Add Balance Manually", "➖ Deduct Balance Manually")
    markup.add(f"⏳ Pending Withdraw ({len(pending_wds)})")
    markup.add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟")
    bot.send_message(
        message.chat.id,
        f"💰 <b>Payment Settings</b>\n\n"
        f"🎁 Per OTP Reward: <code>{cur}{rpo:.2f}</code>\n"
        f"💱 Currency: <code>{cur}</code>\n"
        f"📉 Minimum Withdraw: <code>{cur}{min_wd:.2f}</code>\n"
        f"🔗 Refer Commission: <code>{cur}{ref_comm:.2f}</code>\n"
        f"⏳ Pending Withdraw: <code>{len(pending_wds)}</code>",
        parse_mode="HTML",
        reply_markup=markup,
    )


_payment_admin_state: dict = {}


def _payment_admin_msg_handler(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    txt = (message.text or "").strip()

    if txt == "𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀":
        _show_payment_admin(message)

    elif txt == "💵 Set Reward":
        cur = get_currency()
        msg = bot.send_message(
            message.chat.id,
            f"🎁 What is the reward per OTP?\n\n"
            f"Current: <code>{cur}{get_reward_per_otp():.2f}</code>\n"
            f"Enter new amount (e.g. <code>0.50</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_reward"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "💱 Set Currency":
        msg = bot.send_message(
            message.chat.id,
            f"💱 What currency symbol to use?\n\n"
            f"Current: <code>{get_currency()}</code>\n"
            f"Enter new symbol (e.g. <code>৳</code> or <code>$</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_currency"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "📉 Set Minimum Withdraw":
        cur = get_currency()
        msg = bot.send_message(
            message.chat.id,
            f"📉 What is the minimum withdraw amount?\n\n"
            f"Current: <code>{cur}{get_min_withdraw():.2f}</code>\n"
            f"Enter new amount (e.g. <code>50</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_min_withdraw"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "📋 View All Balances":
        with _balances_lock:
            bal_copy = dict(_balances)
        if not bal_copy:
            bot.send_message(message.chat.id, "❌ No balances found.", parse_mode="HTML")
            return
        cur = get_currency()
        lines = []
        for k, v in sorted(bal_copy.items(), key=lambda x: -float(x[1])):
            lines.append(f"<code>{k}</code> → <b>{cur}{float(v):.2f}</b>")
        text = "📋 <b>All User Balances</b>\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n" + "\n".join(lines[:50])
        if len(lines) > 50:
            text += f"\n…and {len(lines)-50} more"
        bot.send_message(message.chat.id, text, parse_mode="HTML")

    elif txt in ("➕ Add Balance Manually", "➖ Deduct Balance Manually"):
        action = "add" if "add" in txt.lower() else "deduct"
        msg = bot.send_message(
            message.chat.id,
            f"👤 Which user's balance do you want to {'<b>add</b>' if action=='add' else '<b>deduct</b>'}?\n\n"
            f"Enter the user's <b>Telegram ID</b> (Example: <code>123456789</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = f"manual_uid:{action}"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt == "🔗 Set Refer Commission":
        cur = get_currency()
        msg = bot.send_message(
            message.chat.id,
            f"🔗 Set Refer Commission amount:\n\n"
            f"Current: <code>{cur}{get_refer_commission():.2f}</code>\n"
            f"Enter new amount (e.g. <code>10</code>):",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟"),
        )
        _payment_admin_state[uid] = "set_refer_commission"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif txt.startswith("⏳ Pending Withdraw"):
        _show_pending_withdraws(message)


def _payment_admin_input(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    mode = _payment_admin_state.pop(uid, None)
    txt = (message.text or "").strip()
    if _is_back(txt) or _intercept_menu_btn(message):
        return
    if mode == "set_reward":
        try:
            val = float(txt.replace(",", ""))
            if val < 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Enter a positive number:")
            _payment_admin_state[uid] = "set_reward"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["reward_per_otp"] = val
        _save_reward_settings()
        cur = get_currency()
        bot.send_message(message.chat.id,
            f"✅ Per OTP reward set: <code>{cur}{val:.2f}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode == "set_currency":
        if not txt:
            msg = bot.send_message(message.chat.id, "❌ Enter a currency symbol:")
            _payment_admin_state[uid] = "set_currency"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["currency"] = txt
        _save_reward_settings()
        bot.send_message(message.chat.id,
            f"✅ Currency set: <code>{txt}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode == "set_min_withdraw":
        try:
            val = float(txt.replace(",", ""))
            if val < 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Enter a positive number:")
            _payment_admin_state[uid] = "set_min_withdraw"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["min_withdraw"] = val
        _save_reward_settings()
        cur = get_currency()
        bot.send_message(message.chat.id,
            f"✅ Minimum withdraw set: <code>{cur}{val:.2f}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode == "set_refer_commission":
        try:
            val = float(txt.replace(",", ""))
            if val < 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Invalid! Enter a positive number:")
            _payment_admin_state[uid] = "set_refer_commission"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        with _reward_settings_lock:
            _reward_settings["refer_commission"] = val
        _save_reward_settings()
        cur = get_currency()
        bot.send_message(message.chat.id,
            f"✅ Refer commission set: <code>{cur}{val:.2f}</code>",
            parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        _show_payment_admin(message)

    elif mode and mode.startswith("manual_uid:"):
        action = mode.split(":", 1)[1]  # "add" or "deduct"
        try:
            target_uid = int(txt.strip())
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "❌ Invalid ID! Numbers only (e.g. <code>123456789</code>):",
                parse_mode="HTML",
            )
            _payment_admin_state[uid] = f"manual_uid:{action}"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        cur = get_currency()
        cur_bal = get_balance(target_uid)
        action_word = "add" if action == "add" else "deduct"
        msg = bot.send_message(
            message.chat.id,
            f"👤 UID: <code>{target_uid}</code>\n"
            f"💰 Current Balance: <code>{cur}{cur_bal:.2f}</code>\n\n"
            f"How much do you want to <b>{action_word}</b>? (enter a number)\n"
            f"Example: <code>50</code>",
            parse_mode="HTML",
        )
        _payment_admin_state[uid] = f"manual_amount:{action}:{target_uid}"
        bot.register_next_step_handler(msg, _payment_admin_input)

    elif mode and mode.startswith("manual_amount:"):
        parts = mode.split(":", 2)
        action = parts[1]       # "add" or "deduct"
        target_uid = int(parts[2])
        try:
            amount = float(txt.replace(",", "").strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(
                message.chat.id,
                "❌ Invalid! Enter a positive number:",
                parse_mode="HTML",
            )
            _payment_admin_state[uid] = f"manual_amount:{action}:{target_uid}"
            bot.register_next_step_handler(msg, _payment_admin_input)
            return
        cur = get_currency()
        if action == "add":
            new_bal = add_reward(target_uid, amount)
            action_label = "Added ✅"
            sign = "+"
        else:
            ok, new_bal = deduct_balance(target_uid, amount)
            if not ok:
                bot.send_message(
                    message.chat.id,
                    f"❌ Insufficient balance! UID <code>{target_uid}</code>'s balance is insufficient.",
                    parse_mode="HTML",
                )
                _show_payment_admin(message)
                return
            action_label = "Deducted ✅"
            sign = "-"
        bot.send_message(
            message.chat.id,
            f"✅ <b>Balance Updated Successfully!</b>\n\n"
            f"👤 UID: <code>{target_uid}</code>\n"
            f"💸 Amount: <b>{sign}{cur}{amount:.2f}</b> {action_label}\n"
            f"💰 New Balance: <code>{cur}{new_bal:.2f}</code>",
            parse_mode="HTML",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        # Notify the user
        try:
            action_msg = "credited" if action == "add" else "debited"
            bot.send_message(
                target_uid,
                f"💰 <b>Balance Updated!</b>\n\n"
                f"Your account has been <b>{sign}{cur}{amount:.2f}</b> {action_msg}।\n"
                f"New Balance: <code>{cur}{new_bal:.2f}</code>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        _show_payment_admin(message)


def _show_pending_withdraws(message):
    uid = message.from_user.id
    if uid not in ADMIN_IDS:
        return
    cur = get_currency()
    with _withdraw_lock:
        pending = [r for r in _withdraw_requests if r["status"] == "pending"]
    if not pending:
        bot.send_message(message.chat.id, "✅ No pending withdrawals.", parse_mode="HTML")
        return
    for req in pending[:10]:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"wd_approve:{req['id']}"),
            types.InlineKeyboardButton("❌ Reject",  callback_data=f"wd_reject:{req['id']}"),
        )
        import datetime as _dt
        ts = req.get("timestamp", 0)
        dt_str = _dt.datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else "?"
        bot.send_message(
            message.chat.id,
            f"⏳ <b>Withdraw Request</b>\n\n"
            f"👤 UID: <code>{req['uid']}</code>\n"
            f"💵 Amount: <code>{cur}{req['amount']:.2f}</code>\n"
            f"📲 Method: <b>{req['method']}</b>\n"
            f"📋 Account: <code>{req['account']}</code>\n"
            f"🕐 Time: {dt_str}\n"
            f"🔑 ID: <code>{req['id']}</code>",
            parse_mode="HTML",
            reply_markup=markup,
        )


def _go_admin_panel(message, text="🔥 <b>ADMIN PANEL</b>"):
    uid = message.from_user.id
    chat_id = message.chat.id
    now = time.time()
    with _admin_panel_lock:
        if now - _admin_panel_last.get(chat_id, 0) < 2.0:
            return
        _admin_panel_last[chat_id] = now
    m_admin = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    KB = types.KeyboardButton
    m_admin.add(
        KB("𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱",          style="success", icon_custom_emoji_id=_get_admin_btn_icon("num_add")),
        KB("𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿",             style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("sob_clear")),
    )
    m_admin.add(
        KB("𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁",           style="primary", icon_custom_emoji_id=_get_admin_btn_icon("broadcast")),
        KB("𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁",          style="primary", icon_custom_emoji_id=_get_admin_btn_icon("user_count")),
    )
    m_admin.add(
        KB("𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁",            style="primary", icon_custom_emoji_id=_get_admin_btn_icon("user_list")),
        KB("𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀",             style="primary", icon_custom_emoji_id=_get_admin_btn_icon("otp_stats")),
    )
    m_admin.add(
        KB("𝗗𝗘𝗠𝗢 𝗢𝗧𝗣",              style="primary", icon_custom_emoji_id=_get_admin_btn_icon("demo_otp")),
        KB("𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹",             style="success", icon_custom_emoji_id=_get_admin_btn_icon("add_panel")),
    )
    m_admin.add(
        KB("𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹",         style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("remove_panel")),
        KB("𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲",           style="success", icon_custom_emoji_id=_get_admin_btn_icon("add_service")),
    )
    m_admin.add(
        KB("𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲",       style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("remove_service")),
        KB("𝗣𝗮𝗻𝗲𝗹𝘀",                style="primary", icon_custom_emoji_id=_get_admin_btn_icon("panels")),
    )
    m_admin.add(
        KB("𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹",            style="primary", icon_custom_emoji_id=_get_admin_btn_icon("test_panel")),
        KB("𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗚𝗿𝘂𝗽𝗲 𝗦𝗲𝗻𝗱", style="success", icon_custom_emoji_id=_get_admin_btn_icon("purano_send")),
    )
    m_admin.add(
        KB("𝗣𝘂𝗿𝗮𝗻𝗼 𝗢𝗧𝗣 𝗕𝗼𝗻𝗱𝗵𝗼",    style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("purano_off")),
        KB("𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀",             style="primary", icon_custom_emoji_id=_get_admin_btn_icon("settings")),
    )
    if is_super_admin(uid):
        m_admin.add(
            KB("👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻",         style="success"),
            KB("𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻",     style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("remove_admin")),
        )
        m_admin.add(
            KB("𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗",        style="primary", icon_custom_emoji_id=_get_admin_btn_icon("support_id")),
        )
    m_admin.add(
        KB("𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀",        style="primary", icon_custom_emoji_id=_get_admin_btn_icon("edit_msgs")),
        KB("𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁",       style="primary", icon_custom_emoji_id=_get_admin_btn_icon("v2_panel")),
    )
    m_admin.add(
        KB("𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("live_console")),
        KB("𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀",         style="primary", icon_custom_emoji_id=_get_admin_btn_icon("extra_groups")),
    )
    m_admin.add(
        KB("𝗖𝘂𝘀𝘁𝗼𝗺 𝗘𝗺𝗼𝗷𝗶",         style="primary", icon_custom_emoji_id=_get_admin_btn_icon("custom_emoji")),
        KB("𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲",       style="primary", icon_custom_emoji_id=_get_admin_btn_icon("api_key")),
    )
    m_admin.add(
        KB("🌐 𝗔𝘂𝗴𝗲𝘀𝘁𝗲𝗹 𝗞𝗲𝘆",       style="primary"),
    )
    m_admin.add(
        KB("𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀",    style="primary", icon_custom_emoji_id=_get_admin_btn_icon("payment_settings")),
        KB("𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂",          style="danger",  icon_custom_emoji_id=_get_admin_btn_icon("user_menu")),
    )
    m_admin.add(
        KB("𝗕𝘂𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲", style="success"),
    )
    m_admin.add(
        KB("🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰", style="primary", icon_custom_emoji_id=_get_admin_btn_icon("live_traffic")),
    )
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=m_admin,
        parse_mode="HTML",
    )


# ── Live Console Admin Config ─────────────────────────────────────────────────

def _cc_addrange_step(message):
    """Handle admin input for adding a range prefix to a console service."""
    uid = message.from_user.id
    sid = _cc_addrange_state.pop(uid, None)
    if not sid:
        _go_admin_panel(message)
        return
    txt = (message.text or "").strip()
    if txt in ("❌ Cancel", "❌ cancel") or _is_back(txt):
        _admin_panel_last.pop(message.chat.id, None)
        _go_admin_panel(message)
        return
    if _intercept_menu_btn(message):
        _cc_addrange_state.pop(uid, None)
        return
    prefix = re.sub(r"[^\d]", "", txt)
    if not prefix:
        bot.send_message(
            message.chat.id,
            "❌ Invalid! Numbers only (e.g. <code>880</code>, <code>91</code>). Try again.",
            parse_mode="HTML"
        )
        _cc_addrange_state[uid] = sid
        msg2 = bot.send_message(
            message.chat.id,
            f"📲 Enter range prefix for <b>{sid}</b>:",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Cancel"),
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg2, _cc_addrange_step)
        return
    cfg = _console_config.setdefault(sid, {"enabled": True, "ranges": []})
    if prefix not in cfg["ranges"]:
        cfg["ranges"].append(prefix)
        save_console_config()
    c_name, flag = get_country_details(prefix)
    bot.send_message(
        message.chat.id,
        f"✅ Added <b>{_resolve_flag(flag)} {c_name} ({prefix})</b> to <b>{_v2_svc_emoji(sid)} {sid}</b>!",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    _admin_panel_last.pop(message.chat.id, None)
    _go_admin_panel(message)


# ── Edit Message Templates (combined with icon slots) ────────────────────────────

# Maps each template to its related icon slots (for combined edit menu)
_TEMPLATE_ICON_SLOT_MAP = {
    "otp_group":      ["otp_key", "otp_world", "otp_sms"],
    "otp_dm":         ["dm_number_pre", "dm_country_pre", "dm_country_post"],
    "otp_dm_v2":      ["dm_number_pre", "dm_country_pre", "dm_country_post"],
    "start":          ["start_header", "start_crown", "start_user", "start_id",
                       "start_status", "start_workers", "start_powered"],
    "verify_success": ["verify_title"],
    "number_assigned":[],
    "broadcast":      [],
}


def _show_edit_messages_menu(message, note=""):
    """Combined Message Edit menu: template text editor + per-template icon slots."""
    with _custom_emoji_lock:
        slots_set = dict(_custom_emojis.get("msg_slots", {}))

    markup = types.InlineKeyboardMarkup(row_width=2)
    lines = [
        "✏️ <b>Message Edit</b>\n"
        "<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>\n"
        "<i>Edit message text or set custom emoji icons:</i>"
    ]

    seen_slots: set = set()
    for key, label in _TEMPLATE_LABELS.items():
        lines.append(f"\n📄 <b>{label}</b>")
        markup.add(types.InlineKeyboardButton(f"✏️ Edit: {label}", callback_data=f"editmsg:{key}", style="danger"))

        icon_keys = _TEMPLATE_ICON_SLOT_MAP.get(key, [])
        for slot_key in icon_keys:
            if slot_key not in _MSG_ICON_SLOTS or slot_key in seen_slots:
                continue
            seen_slots.add(slot_key)
            default_char, slot_label = _MSG_ICON_SLOTS[slot_key]
            custom = slots_set.get(slot_key)
            if custom:
                fb = custom.get("fb", default_char)
                lines.append(f"  ✅ {fb} <i>{slot_label}</i>")
            else:
                lines.append(f"  🔘 {default_char} <i>{slot_label}</i>")
            markup.add(
                types.InlineKeyboardButton(f"✏️ {slot_label}", callback_data=f"msgicon_set:{slot_key}"),
                types.InlineKeyboardButton("🔄 Reset", callback_data=f"msgicon_reset:{slot_key}"),
            )

    markup.add(types.InlineKeyboardButton("🔄 Reset All to Default", callback_data="editmsg_reset_all", style="success"))
    text = "\n".join(lines)
    if note:
        text += f"\n\n✅ <i>{note}</i>"
    text += "\n\n<tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji><tg-emoji emoji-id=\"5870818207383686839\">〰️</tg-emoji>"
    try:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"[MSG-EDIT] Failed: {e}")


def _ask_new_template(call, key):
    import html as _html
    label = _TEMPLATE_LABELS.get(key, key)
    vars_hint = _TEMPLATE_VARS.get(key, "")
    current = get_template(key)
    # Escape HTML so tags inside the template don't break the <code> block display
    current_escaped = _html.escape(current[:600])
    uid = call.from_user.id
    _edit_template_state[uid] = {"key": key, "msg_id": call.message.message_id}
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    try:
        msg = bot.send_message(
            call.message.chat.id,
            f"✏️ <b>{label}</b>\n\n"
            f"📌 <b>Available variables:</b>\n<code>{vars_hint}</code>\n\n"
            f"📄 <b>Current format:</b>\n<code>{current_escaped}</code>\n\n"
            f"⬇️ <b>Enter new format:</b>\n"
            f"<i>(HTML tags supported: &lt;b&gt;, &lt;i&gt;, &lt;code&gt;, &lt;blockquote&gt; — sending a custom emoji directly also works to customize!)</i>",
            reply_markup=_back_admin_kb(),
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[TEMPLATE-ASK] ❌ Failed to send prompt for uid={uid}: {e}")
        try:
            msg = bot.send_message(
                call.message.chat.id,
                f"✏️ {label}\n\n⬇️ Enter new format:",
                reply_markup=_back_admin_kb(),
            )
        except Exception:
            return
    bot.register_next_step_handler(msg, _save_new_template)


def _message_to_html(message):
    """Convert message text + entities to HTML string.
    Preserves custom_emoji, bold, italic, code, blockquote etc.
    Also preserves manually typed <tg-emoji> or <b> HTML if no entities override.
    """
    import html as _html
    from collections import defaultdict
    text = message.text or ""
    entities = message.entities or []
    if not entities:
        return text
    chars = list(text)
    n = len(chars)
    opens = defaultdict(list)
    closes = defaultdict(list)
    for ent in sorted(entities, key=lambda e: (e.offset, -e.length)):
        o, l = ent.offset, ent.length
        etype = ent.type
        if etype == "bold":
            opens[o].append("<b>"); closes[o + l].append("</b>")
        elif etype == "italic":
            opens[o].append("<i>"); closes[o + l].append("</i>")
        elif etype == "underline":
            opens[o].append("<u>"); closes[o + l].append("</u>")
        elif etype == "strikethrough":
            opens[o].append("<s>"); closes[o + l].append("</s>")
        elif etype == "code":
            opens[o].append("<code>"); closes[o + l].append("</code>")
        elif etype == "pre":
            opens[o].append("<pre>"); closes[o + l].append("</pre>")
        elif etype == "blockquote":
            opens[o].append("<blockquote>"); closes[o + l].append("</blockquote>")
        elif etype == "custom_emoji":
            eid = getattr(ent, "custom_emoji_id", "") or ""
            opens[o].append(f'<tg-emoji emoji-id="{eid}">')
            closes[o + l].append("</tg-emoji>")
        elif etype == "text_link":
            url = _html.escape(getattr(ent, "url", "") or "")
            opens[o].append(f'<a href="{url}">')
            closes[o + l].append("</a>")
    result = []
    for i in range(n + 1):
        for tag in closes.get(i, []):
            result.append(tag)
        if i < n:
            for tag in opens.get(i, []):
                result.append(tag)
            result.append(chars[i])
    return "".join(result)


def _save_new_template(message):
    uid = message.from_user.id
    try:
        if _is_back(message.text):
            _edit_template_state.pop(uid, None)
            _admin_panel_last.pop(message.chat.id, None)
            _go_admin_panel(message)
            return
        if _intercept_menu_btn(message):
            _edit_template_state.pop(uid, None)
            return
        state = _edit_template_state.pop(uid, None)
        if not state:
            _admin_panel_last.pop(message.chat.id, None)
            _go_admin_panel(message)
            return
        key = state["key"]
        new_text = _message_to_html(message)
        if not new_text.strip():
            msg = bot.send_message(
                message.chat.id,
                "❌ Cannot be empty. Enter again:",
                reply_markup=_back_admin_kb(),
            )
            _edit_template_state[uid] = state
            bot.register_next_step_handler(msg, _save_new_template)
            return

        # ── Validate: only check for broken brace syntax, accept any {variable} ──
        class _PermissiveDict(dict):
            def __missing__(self, k):
                return f"{{{k}}}"
        _DUMMY_VARS = _PermissiveDict({
            "uname": "TestUser", "uid": "123456789",
            "svc": "INSTAGRAM", "number": "8801712345678",
            "tagged_number": "@+8801712345678", "taged_number": "@+8801712345678",
            "sms_body": "Your OTP is 123456",
            "country": "Bangladesh", "flag": "🇧🇩", "otp": "123456",
            "vname": "TestUser", "text": "Test broadcast",
        })
        try:
            new_text.format_map(_DUMMY_VARS)
        except (ValueError, IndexError) as fmt_err:
            msg = bot.send_message(
                message.chat.id,
                f"❌ <b>Template has an error!</b>\n\n"
                f"🔴 <b>Error:</b> <code>{fmt_err}</code>\n\n"
                f"⚠️ <b>Issue:</b> Wrong use of <code>{{</code> <code>}}</code>.\n\n"
                f"💡 If you need literal braces, double them: <code>{{{{</code> and <code>}}}}</code>\n\n"
                f"Enter again:",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
            _edit_template_state[uid] = state
            bot.register_next_step_handler(msg, _save_new_template)
            return

        _templates[key] = new_text
        save_templates()
        label = _TEMPLATE_LABELS.get(key, key)
        # Reset rate limiter so admin panel shows immediately after save
        _admin_panel_last.pop(message.chat.id, None)
        _go_admin_panel(
            message,
            f"✅🔥 <b>Message updated!</b>\n\n"
            f"✏️ <b>{label}</b>\n\n"
            f"📄 New format saved.",
        )
    except Exception as e:
        print(f"[TEMPLATE-SAVE] ❌ Error for uid={uid}: {e}")
        try:
            bot.send_message(
                message.chat.id,
                f"❌ <b>Something went wrong!</b>\n<code>{e}</code>\n\nPlease try again.",
                reply_markup=_back_admin_kb(),
                parse_mode="HTML",
            )
        except Exception:
            pass


def _cancel_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Cancel")
    return kb


def _back_admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔙 Admin Panel")
    return kb


def _is_back(txt):
    return (txt or "").strip() in ("🔙 Admin Panel", "❌ Cancel")


_ALL_MENU_BTNS = {
    "☎️ 𝗩𝟭 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️", "☎️ 𝗡𝗨𝗠𝗕𝗔𝗥 ☎️", "📡 𝗩𝟮 𝗖𝗼𝗻𝘀𝗼𝗹𝗲",
    "🔄 𝗩𝟮 𝗦𝗪𝗜𝗧𝗖𝗛", "🔴 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗚𝗘", "⌨️ 𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘", "🔙 𝗩𝟭 𝗦𝗪𝗜𝗧𝗖𝗛",
    "📊 𝗦𝗧𝗢𝗖𝗞", "📞 𝗦𝗔𝗣𝗢𝗥𝗧",
    "⚙️ 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 ⚙️", "🔙 Main Menu",
    "𝗡𝘂𝗺𝗯𝗮𝗿 𝗔𝗱𝗱", "𝗦𝗼𝗯 𝗖𝗹𝗲𝗮𝗿",
    "𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁", "𝗨𝘀𝗲𝗿 𝗖𝗼𝘂𝗻𝘁",
    "𝗨𝘀𝗲𝗿 𝗟𝗶𝘀𝘁", "𝗢𝗧𝗣 𝗦𝘁𝗮𝘁𝘀", "𝗗𝗘𝗠𝗢 𝗢𝗧𝗣",
    "𝗔𝗱𝗱 𝗣𝗮𝗻𝗲𝗹", "𝗥𝗲𝗺𝗼𝘃𝗲 𝗣𝗮𝗻𝗲𝗹",
    "𝗔𝗱𝗱 𝗦𝗲𝗿𝘃𝗶𝗰𝗲", "𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝗲𝗿𝘃𝗶𝗰𝗲",
    "𝗣𝗮𝗻𝗲𝗹𝘀", "𝗧𝗲𝘀𝘁 𝗣𝗮𝗻𝗲𝗹", "👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻", "𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻",
    "𝗦𝘂𝗽𝗽𝗼𝗿𝘁 𝗜𝗗",
    "𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀", "𝗘𝗱𝗶𝘁 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀", "📡 𝗩𝟮 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗙𝗼𝗿𝗺𝗮𝘁", "𝗩𝟮 𝗣𝗮𝗻𝗲𝗹 𝗦𝗲𝗹𝗲𝗰𝘁",
    "𝗟𝗶𝘃𝗲 𝗖𝗼𝗻𝘀𝗼𝗹𝗲 𝗖𝗼𝗻𝗳𝗶𝗴", "𝗘𝘅𝘁𝗿𝗮 𝗚𝗿𝗼𝘂𝗽𝘀", "👨‍💻 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗲𝗿 𝗜𝗻𝗳𝗼", "𝗨𝘀𝗲𝗿 𝗠𝗲𝗻𝘂",
    "🔙 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟", "🔙 Admin Panel", "🔙 Admin Menu", "✨ 𝗠𝗲𝘀𝘀𝗮𝗴𝗲 𝗜𝗰𝗼𝗻𝘀",
    "🔘 Button Emoji Set", "🗑️ Button Emoji Del",
    "💬 Msg Emoji Set", "🗑️ Msg Emoji Del",
    "🖥️ Admin Btn Set", "🗑️ Admin Btn Del",
    "🏳️ Flag Emoji Set", "🎯 Service Emoji Set",
    "🌍 All Flags JSON Set", "📋 Flag JSON Export",
    "🔢 IDs Only Set", "🗑️ Flag Emoji Del",
    "🗑️ Service Emoji Del",
    "𝗔𝗣𝗜 𝗞𝗲𝘆 𝗖𝗵𝗮𝗻𝗴𝗲",
    "🌐 𝗔𝘂𝗴𝗲𝘀𝘁𝗲𝗹 𝗞𝗲𝘆",
    "🔗 𝗥𝗲𝗳𝗳𝗲𝗿", "𝗥𝗲𝗳𝗳𝗲𝗿", "🔗 Set Refer Commission",
    "Buy Service",
    "𝗕𝘂𝘆 𝗦𝗲𝗿𝘃𝗶𝗰𝗲 𝗠𝗮𝗻𝗮𝗴𝗲", "💎 Set Premium Price", "💰 Set VPN Price", "➕ Add VPN Service",
    "🔴 𝗟𝗶𝘃𝗲 𝗧𝗿𝗮𝗳𝗳𝗶𝗰",
    "🗑️ Remove VPN", "📨 Send User Message",
}


def _intercept_menu_btn(message):
    """If user pressed any known menu/admin button while in a step flow,
    route it to text_handler so it is handled correctly.
    Returns True if intercepted, False otherwise."""
    txt = (message.text or "").strip()
    if txt in _ALL_MENU_BTNS:
        text_handler(message)
        return True
    return False


def process_auto_add(message):
    raw = (message.text or "").strip()
    if raw == "❌ Cancel":
        _go_admin_panel(message)
        return
    svc = _admin_service_key_from_button(raw)
    if not svc:
        msg = bot.send_message(
            message.chat.id,
            "⚠️ <b>Wrong service! Choose again:</b>",
            reply_markup=_admin_add_svc_keyboard(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, process_auto_add)
        return
    # A newly created service may not have a stock bucket yet. Create it
    # instead of rejecting the valid service or falling back to another key.
    stock.setdefault(svc, {})
    msg = bot.send_message(
        message.chat.id,
        f"🔥 <b>{svc.upper()}</b>\n\n"
        f"📝 <b>Enter Slot name:</b>\n"
        f"<i>Example: Mali 1, Germany 2, India 3</i>",
        reply_markup=_cancel_kb(),
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, lambda m: ask_numbers_for_slot(m, svc))


def ask_numbers_for_slot(message, svc):
    slot_name = (message.text or "").strip()
    if slot_name == "❌ Cancel":
        _go_admin_panel(message)
        return
    if not slot_name:
        msg = bot.send_message(
            message.chat.id,
            "❌ Enter Slot name:",
            reply_markup=_cancel_kb(),
            parse_mode="HTML",
        )
        bot.register_next_step_handler(msg, lambda m: ask_numbers_for_slot(m, svc))
        return
    msg = bot.send_message(
        message.chat.id,
        f"✅ Slot: <b>{slot_name}</b>\n\n"
        f"📊 Ekhon <b>{svc.upper()}</b> er number er Excel file pathao:\n"
        f"<i>(.xlsx / .xls / .csv — numbers should be in one column)</i>",
        reply_markup=_cancel_kb(),
        parse_mode="HTML",
    )
    _awaiting_slot_excel.add(message.from_user.id)
    bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))


def finalize_auto_add(message, svc, slot_name=None):
    global stock
    uid = message.from_user.id
    _awaiting_slot_excel.discard(uid)  # clear guard — document_handler will now ignore this UID
    if (message.text or "").strip() == "❌ Cancel":
        _go_admin_panel(message)
        return

    # ── Excel / CSV file upload ───────────────────────────────────────────────
    if message.document:
        doc = message.document
        fname = doc.file_name or "file"
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        if ext not in ("xlsx", "xls", "csv"):
            msg = bot.send_message(
                message.chat.id,
                "❌ Only send <b>.xlsx / .xls / .csv</b> files!\n\n"
                "📊 Try again — send the Excel file:",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))
            return
        wait = bot.send_message(message.chat.id, "⏳ Parsing file...", parse_mode="HTML")
        try:
            file_info = bot.get_file(doc.file_id)
            raw = bot.download_file(file_info.file_path)
        except Exception as e:
            bot.edit_message_text(f"❌ File download hoyni: <code>{e}</code>",
                message.chat.id, wait.message_id, parse_mode="HTML")
            return
        rows, mode = _parse_spreadsheet(raw, fname)
        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass
        if not rows:
            msg = bot.send_message(
                message.chat.id,
                "⚠️ File-e kono number paini!\n"
                "Numbers in the Excel file should be in one column.\n\n"
                "📊 Try again — send the Excel file:",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))
            return
        # Extract number list from parsed rows
        if mode == "two_col":
            nums = [num for _, num in rows]
        else:
            nums = list(rows)
    else:
        # ── Text fallback (newline / comma) ───────────────────────────────────
        if not message.text:
            msg = bot.send_message(
                message.chat.id,
                "❌ Excel file pathao (.xlsx / .xls / .csv):",
                reply_markup=_cancel_kb(),
                parse_mode="HTML",
            )
            bot.register_next_step_handler(msg, lambda m: finalize_auto_add(m, svc, slot_name))
            return
        nums = [n.strip() for n in re.split(r"[,\n\r]", message.text) if n.strip()]

    # ── Add numbers to stock ──────────────────────────────────────────────────
    _first_added_num = None
    if slot_name:
        if svc not in stock:
            stock[svc] = {}
        if slot_name not in stock[svc]:
            stock[svc][slot_name] = []
        added_count = 0
        for num in nums:
            clean = re.sub(r"\D", "", str(num))
            if clean:
                stock[svc][slot_name].append(clean)
                if _first_added_num is None:
                    _first_added_num = clean
                added_count += 1
    else:
        added_count = 0
        for num in nums:
            c_name, _ = get_country_details(num)
            if c_name == "Unknown":
                continue
            if c_name not in stock[svc]:
                stock[svc][c_name] = []
            stock[svc][c_name].append(num)
            if _first_added_num is None:
                _first_added_num = re.sub(r"\D", "", str(num))
            added_count += 1
    save_stock()
    # Notify all users about new numbers
    if added_count and _first_added_num:
        _nc, _nf = get_country_details(_first_added_num)
        if _nc == "Unknown":
            _nc, _nf = "UNKNOWN", "🌐"
        _notify_new_numbers(svc, _nc, _nf, added_count)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add More", "🔙 Admin Menu")
    bot.send_message(
        message.chat.id,
        f"✅🔥 <b>DONE!</b>\n\n"
        f"🗂 <b>Slot:</b> {slot_name or 'Auto'}\n"
        f"📱 <b>Added:</b> {added_count} number(s)",
        reply_markup=markup,
        parse_mode="HTML",
    )
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, "⬇️ Ki korbe?", parse_mode="HTML"),
        lambda m: _after_add_handler(m, svc),
    )


