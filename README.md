# AR OTP Bot — Railway two-file package

## Source files

- `bot.py` — complete bot runtime, panels, OTP, Telegram UI, and polling
- `buy_service.py` — buy-service configuration, VPN/Premium order callbacks,
  payment instructions, screenshot handling, and admin workflow

The buy-service module is loaded before the first callback handler and before
polling starts. This prevents the Buy VPN button from becoming unresponsive.

## Railway

1. Upload/extract this folder in Railway.
2. Add `TELEGRAM_BOT_TOKEN` as a Railway Secret.
3. Railway runs `python -u bot.py` using the included `Procfile`.

Do not place the real token in a file or commit it to source control.
