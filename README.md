# AR OTP Bot — Railway package

This folder is the Railway-ready modular version of the bot.

## Deploy

1. Upload the contents of this folder to a Railway service or connect the
   repository.
2. Add the secret environment variable `TELEGRAM_BOT_TOKEN` in Railway.
3. Railway will install `requirements.txt` and run `python -u bot.py`.

## Module layout

- `bot.py` — Railway entrypoint and ordered module loader
- `bot.py` — the complete bot runtime, panels, OTP, Telegram UI, and polling
- `buy_service.py` — buy-service settings, VPN/premium orders, and screenshot/order notifications

The two files execute in the same order as the original working bot. The buy-service
file is loaded into the bot namespace before startup, so existing global state and
Telegram callback registrations remain compatible.

## Important

Do not commit `TELEGRAM_BOT_TOKEN` or any other credentials into this folder.
Railway Secrets should hold the token.