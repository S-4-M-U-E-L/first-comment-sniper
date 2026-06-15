#!/usr/bin/env python3
"""
setup.py - One-command bootstrap for YouTube Comment Sniper.

Creates a virtual environment, installs all dependencies, and walks
you through configuring your .env file interactively.

Cross-platform: works identically on Windows, macOS, and Linux.
Run with the system Python (not the venv):
    python setup.py
"""

import sys
import subprocess
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — all resolved via pathlib, never hardcoded separators
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR     = PROJECT_ROOT / ".venv"
ENV_FILE     = PROJECT_ROOT / ".env"
ENV_EXAMPLE  = PROJECT_ROOT / "config" / ".env.example"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"

# Cross-platform: the Python executable lives in different subdirs per OS
VENV_PYTHON = (
    VENV_DIR / "Scripts" / "python.exe"
    if sys.platform == "win32"
    else VENV_DIR / "bin" / "python"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def header(msg: str) -> None:
    print(f"\n  >>> {msg}")

def ok(msg: str) -> None:
    print(f"      [OK]   {msg}")

def skip(msg: str) -> None:
    print(f"      [SKIP] {msg}")

def info(msg: str) -> None:
    print(f"      [INFO] {msg}")

def banner(msg: str) -> None:
    width = 56
    print("\n" + "=" * width)
    print(f"  {msg}")
    print("=" * width)

# ---------------------------------------------------------------------------
# Setup steps
# ---------------------------------------------------------------------------

def create_venv() -> None:
    header("Creating virtual environment (.venv)...")
    if VENV_DIR.exists():
        skip(".venv already exists — skipping creation.")
        return
    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        check=True
    )
    ok("Virtual environment created at .venv/")


def install_dependencies() -> None:
    header("Installing dependencies from requirements.txt...")
    # Upgrade pip silently first to avoid noisy warnings
    subprocess.run(
        [str(VENV_PYTHON), "-m", "pip", "install", "--quiet", "--upgrade", "pip"],
        check=True
    )
    subprocess.run(
        [str(VENV_PYTHON), "-m", "pip", "install", "--quiet", "-r", str(REQUIREMENTS)],
        check=True
    )
    ok("All dependencies installed.")


def configure_env() -> None:
    header("Configuring .env file...")
    if not ENV_FILE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        ok("Created .env from .env.example.")
    else:
        skip(".env already exists — skipping copy.")

    # Read current content
    content = ENV_FILE.read_text(encoding="utf-8")

    # Check if TARGET_CHANNEL_ID is already set
    current_id = ""
    for line in content.splitlines():
        if line.startswith("TARGET_CHANNEL_ID="):
            current_id = line.split("=", 1)[1].strip()
            break

    if current_id:
        skip(f"TARGET_CHANNEL_ID already set: {current_id}")
        return

    # Prompt the user interactively
    print()
    info("Your TARGET_CHANNEL_ID is not set.")
    info("To find your channel ID:")
    info("  1. Go to https://www.youtube.com/@YOURCHANNELNAME/about")
    info("  2. Right-click the page → View Page Source")
    info("  3. Search for 'channel_id' — it starts with 'UC...'")
    info("  Or use: https://commentpicker.com/youtube-channel-id.php")
    print()

    channel_id = input("  Enter YouTube Channel ID (starts with UC...): ").strip()

    if channel_id:
        new_content = content.replace(
            "TARGET_CHANNEL_ID=",
            f"TARGET_CHANNEL_ID={channel_id}",
            1  # Replace only the first occurrence
        )
        ENV_FILE.write_text(new_content, encoding="utf-8")
        ok(f"Channel ID saved to .env.")
    else:
        skip("No Channel ID entered. Edit .env manually before running the bot.")


def print_next_steps() -> None:
    banner("Setup complete! Here's what to do next:")

    run_cmd = (
        r".venv\Scripts\python src\main.py"
        if sys.platform == "win32"
        else ".venv/bin/python src/main.py"
    )

    print("""
  STEP 1 — Set up Google Cloud OAuth credentials
  ------------------------------------------------
  You need a free Google Cloud project to use the YouTube API.
  Full instructions are in README.md under "Google Cloud Setup".

  STEP 2 — Place your credentials file
  --------------------------------------
  Download your OAuth client secret from Google Cloud Console
  and save it as: credentials/client_secrets.json

  STEP 3 — Run the bot
  ----------------------""")
    print(f"      {run_cmd}")
    print("""
  The first run will open a browser window for Google login.
  After that, credentials/token.json is saved and login is fully automatic.

  For 24/7 deployment instructions, see:
      directives/run_comment_sniper.md
""")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    banner("YouTube Comment Sniper — Setup")

    # Verify Python version early
    if sys.version_info < (3, 8):
        print("\n  [ERROR] Python 3.8 or higher is required.")
        print(f"          You are running Python {sys.version}")
        sys.exit(1)

    try:
        create_venv()
        install_dependencies()
        configure_env()
        print_next_steps()
    except subprocess.CalledProcessError as e:
        print(f"\n  [ERROR] A command failed: {e}")
        print("  Please check the error above and re-run setup.py.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
