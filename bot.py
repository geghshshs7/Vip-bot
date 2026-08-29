"""Railway entrypoint for the modular AR OTP bot.

The runtime sections are kept in logical files and executed in their original
dependency order inside one namespace. This preserves the existing bot's
callback/global-state behavior while making the deployment easier to maintain.
"""

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
MODULES = (
    "app/core.py",
    "app/otp.py",
    "app/panels.py",
    "app/ui.py",
    "app/buy_service.py",
    "app/runner.py",
)


def main() -> None:
    namespace = globals()
    for relative_path in MODULES:
        module_path = BASE_DIR / relative_path
        source = module_path.read_text(encoding="utf-8")
        code = compile(source, str(module_path), "exec")
        exec(code, namespace, namespace)


if __name__ == "__main__":
    main()