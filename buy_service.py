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
            "ts": time.time(),
            "user_id": uid,
            "user_info": user_info,
            "service": service_label,
            "price": price,
            "tg_target": tg_target,
            "file_id": file_id,
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
