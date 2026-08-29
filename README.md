# AR OTP Bot — Railway package

This folder is the Railway-ready modular version of the bot.

## Deploy

1. Upload the contents of this folder to a Railway service or connect the
   repository.
2. Add the secret environment variable `TELEGRAM_BOT_TOKEN` in Railway.
3. Railway will install `requirements.txt` and run `python -u bot.py`.

## Module layout

- `bot.py` — Railway entrypoint and ordered module loader
- `app/core.py` — imports, bot configuration, persistent state, templates,
  rewards, users, and shared helpers
- `app/otp.py` — OTP formatting, country labels, full-SMS language detection,
  and OTP dispatch
- `app/panels.py` — panel APIs, panel login/fetch functions, and monitors
- `app/ui.py` — Telegram menus, admin controls, callbacks, and user handlers
- `app/buy_service.py` — buy-service workflow, VPN/premium orders, and
  screenshot/order notifications
- `app/runner.py` — startup tasks, webhook cleanup, and polling loop

The sections execute in the same order as the original working bot so existing
global state and Telegram callback registrations remain compatible.

## Important

Do not commit `TELEGRAM_BOT_TOKEN` or any other credentials into this folder.
Railway Secrets should hold the token.