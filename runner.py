

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
