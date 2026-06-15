"""
src/main.py

The asynchronous driver for the YouTube Comment Sniper.
Reads .env, authenticates, resolves the target playlist, and runs the
non-blocking polling loop. Dispatches simulated comment tasks as
independent asyncio background tasks.

Fix 1 (Windows Compatibility): Uses try/except KeyboardInterrupt + async shutdown()
    instead of loop.add_signal_handler(), which raises NotImplementedError on
    Windows ProactorEventLoop (Python 3.8+ default on Windows).

Fix 2 (Path Safety): All file paths are anchored to PROJECT_ROOT using pathlib,
    resolved relative to this script's location — not the working directory.

Fix 3 (Exception Handling): Polling loop uses a cycle-level error boundary
    (transient errors log and continue; fatal errors break the loop).
    All YouTube API calls delegate retries to youtube_client.with_backoff().
"""

import os
import sys
import json
import random
import time
import asyncio
import logging
from pathlib import Path

# Force stdout to UTF-8 to prevent Windows terminal UnicodeEncodeErrors
# when printing video titles containing characters like 'Č'
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

# Fix: Ensure src/ is on sys.path regardless of working directory.
# Satisfies strategy.md §7 Path Safety — the bot must run identically whether
# invoked as `python src/main.py` (from project root) or `python main.py`
# (from inside src/). Without this, bare imports raise ModuleNotFoundError.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from auth import get_credentials
from youtube_client import build_youtube_service, get_uploads_playlist_id, get_latest_video_id

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# --- Fix 2 (Path Safety): Anchor to project root regardless of CWD ---
# __file__ = src/main.py → .parent = src/ → .parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Absolute paths for all persistent files ---
STATE_FILE = PROJECT_ROOT / "data" / "state.json"

# --- Active background snipe tasks (tracked for graceful shutdown) ---
active_tasks: set = set()


# ---------------------------------------------------------------------------
# Environment & Configuration
# ---------------------------------------------------------------------------

def validate_environment():
    """
    Checks that all required environment variables exist.
    Fails fast with a descriptive error if any are missing.
    Fix 2: explicit dotenv_path so .env is found regardless of CWD.
    """
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

    required_vars = [
        "TARGET_CHANNEL_ID",
        "COMMENT_TEMPLATES_JSON",
        "GOOGLE_CLIENT_SECRETS_FILE"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print("[ERROR] Missing required environment variables:")
        for m in missing:
            print(f"  - {m}")
        print("\nPlease copy .env.example to .env and fill in the missing values.")
        sys.exit(1)

    logger.info("Environment validation passed.")


def load_templates() -> list:
    """
    Loads comment templates from the JSON file defined in COMMENT_TEMPLATES_JSON.
    Fix 2: path anchored to PROJECT_ROOT.
    Falls back to ["First!"] on any read or parse error.
    """
    _raw = os.getenv("COMMENT_TEMPLATES_JSON", "config/templates.json")
    templates_file = PROJECT_ROOT / _raw
    try:
        with open(templates_file, "r", encoding="utf-8") as f:
            templates = json.load(f)
            if isinstance(templates, list) and templates:
                return templates
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load templates from {templates_file}: {e}. Using fallback.")
    return ["First!"]


# ---------------------------------------------------------------------------
# Persistent State
# ---------------------------------------------------------------------------

def load_state() -> dict:
    """
    Loads the persistent bot state from state.json.
    Returns an empty dict on first run (file does not exist yet).
    Fix 2: uses absolute STATE_FILE path.
    """
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read state file ({e}). Starting with empty state.")
    return {}


def save_state(state: dict) -> None:
    """
    Persists the current state to state.json.
    Logs loudly on failure but does NOT crash — losing state for one cycle is
    recoverable; crashing the bot is not.
    Fix 2: uses absolute STATE_FILE path.
    """
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except OSError as e:
        logger.error(
            f"CRITICAL: Failed to write state file: {e}. "
            "Bot may re-detect the same video on restart."
        )


# ---------------------------------------------------------------------------
# Timing Helpers
# ---------------------------------------------------------------------------

def get_polling_delay() -> float:
    """Jittered polling interval averaging 9.0s — consumes ~96% of daily API quota."""
    return random.uniform(7.5, 10.5)


def get_execution_delay() -> float:
    """Jittered execution delay simulating human reaction time (14–28s)."""
    return random.uniform(14, 28)


# ---------------------------------------------------------------------------
# Fix 1 (Windows Compatibility): Graceful async shutdown
# ---------------------------------------------------------------------------

async def shutdown(loop: asyncio.AbstractEventLoop) -> None:
    """
    Cancels all running asyncio tasks and awaits their completion.
    Called from main()'s finally block — runs on any exit path.

    Fix 1: Replaces loop.add_signal_handler() (raises NotImplementedError on
    Windows ProactorEventLoop). KeyboardInterrupt in __main__ triggers this
    via CancelledError propagation into main(), which fires the finally block.
    """
    tasks = {t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()}
    if not tasks:
        return

    logger.info(f"Cancelling {len(tasks)} pending task(s)...")
    for task in tasks:
        task.cancel()

    # return_exceptions=True prevents gather() from raising if a task errors
    # during its own cancellation cleanup
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("All tasks cancelled. Shutdown complete.")


# ---------------------------------------------------------------------------
# Snipe Task (background, non-blocking)
# ---------------------------------------------------------------------------

async def print_comment_with_jitter(video_id: str, title: str, templates: list) -> None:
    """
    Background snipe task. Waits execution jitter delay, then prints the
    simulated comment to the console.

    Fix 1: Catches CancelledError, logs the cancellation, then re-raises.
    Re-raising is mandatory — asyncio uses the exception to mark the task as
    properly cancelled. Swallowing it causes the event loop to hang at shutdown.
    """
    delay = get_execution_delay()
    logger.info(f"Target locked: {video_id} ('{title}'). Jittering {delay:.1f}s before output...")
    try:
        await asyncio.sleep(delay)
        template = random.choice(templates)
        comment_text = template.format(
            video_title=title,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        )
        print(f"\n{'=' * 60}", flush=True)
        print(f"  [SIMULATED COMMENT POST]", flush=True)
        print(f"  Video : {video_id}", flush=True)
        print(f"  Title : {title}", flush=True)
        print(f"  Text  : {comment_text}", flush=True)
        print(f"{'=' * 60}\n", flush=True)
        logger.info(f"Snipe simulation complete for video {video_id}.")
    except asyncio.CancelledError:
        logger.info(f"Snipe task for video {video_id} cancelled during jitter.")
        raise  # Must re-raise — see docstring


# ---------------------------------------------------------------------------
# Core Polling Engine
# ---------------------------------------------------------------------------

async def polling_loop(youtube, uploads_playlist_id: str, templates: list) -> None:
    """
    Infinite async polling loop. Queries the YouTube API every 7.5–10.5s.
    Dispatches independent background snipe tasks on new video detection.

    Fix 3: Cycle-level error boundary:
      - Transient errors (network timeouts, quota retries exhausted) → log, continue
      - Fatal errors (401 auth revoked) → log, break the loop
      - asyncio.CancelledError → always propagated (never swallowed)
    The finally block ensures the polling sleep always runs, preventing a tight
    spin-loop that would burn through the 400-unit daily quota buffer instantly.
    """
    state = load_state()
    latest_id = state.get("latest_video_id")

    # Establish baseline on first run so we don't falsely trigger on startup
    if not latest_id:
        logger.info("No prior state found. Fetching baseline video ID...")
        try:
            vid_id, title = await get_latest_video_id(youtube, uploads_playlist_id)
            if vid_id:
                state["latest_video_id"] = vid_id
                save_state(state)
                logger.info(f"Baseline established: {vid_id} ('{title}')")
        except Exception as e:
            logger.warning(f"Could not establish baseline: {e}. Will detect on first successful poll.")

    logger.info("[START] Polling loop started. Watching for new uploads...")

    while True:
        poll_start = time.monotonic()
        try:
            vid_id, title = await get_latest_video_id(youtube, uploads_playlist_id)

            if vid_id and vid_id != state.get("latest_video_id"):
                logger.info(f"[SNIPE] New video detected: {vid_id} ('{title}')")

                # Write state BEFORE spawning the task — prevents duplicate processing
                # if the bot crashes or is restarted during the 14–28s execution jitter
                state["latest_video_id"] = vid_id
                save_state(state)

                # Dispatch non-blocking snipe task; track it for graceful shutdown
                task = asyncio.create_task(
                    print_comment_with_jitter(vid_id, title, templates)
                )
                active_tasks.add(task)
                task.add_done_callback(active_tasks.discard)

        except asyncio.CancelledError:
            # Shutdown signal — never swallow, always propagate
            raise

        except Exception as e:
            # Fix 3: Cycle-level error — log and continue to next poll cycle.
            # A transient outage should not kill a long-running process.
            logger.error(f"Poll cycle error ({type(e).__name__}): {e}")

        finally:
            # Always sleep, even after an error — prevents tight spin-loop.
            # Subtracts time already spent (e.g. in backoff retries) from the
            # remaining interval so the average cadence stays close to 9s.
            elapsed = time.monotonic() - poll_start
            remaining = max(0.0, get_polling_delay() - elapsed)
            await asyncio.sleep(remaining)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

async def main() -> None:
    """Top-level async entry point. Runs startup, then the polling loop."""
    validate_environment()

    # Store a reference to the running loop now — avoids asyncio.get_event_loop()
    # deprecation warning in Python 3.10+ (get_running_loop() is the safe form)
    loop = asyncio.get_running_loop()
    channel_id = os.getenv("TARGET_CHANNEL_ID")
    templates = load_templates()

    logger.info("Authenticating with YouTube API...")
    try:
        creds = get_credentials()
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)

    try:
        youtube = build_youtube_service(creds)
        logger.info("Resolving uploads playlist ID for target channel...")
        uploads_playlist_id = await get_uploads_playlist_id(youtube, channel_id)
        logger.info(f"Target playlist resolved: {uploads_playlist_id}")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

    try:
        await polling_loop(youtube, uploads_playlist_id, templates)
    finally:
        # Fix 1: Shutdown always runs — on normal exit, Ctrl+C, or unhandled error
        await shutdown(loop)


if __name__ == "__main__":
    # Fix 1 (Windows Compatibility):
    # Wrapping asyncio.run() in try/except KeyboardInterrupt is the cross-platform
    # shutdown pattern. On Windows, loop.add_signal_handler() raises NotImplementedError
    # (ProactorEventLoop does not support it). KeyboardInterrupt propagates out of
    # asyncio.run() as a CancelledError into main(), triggering its finally block
    # (which calls shutdown()), then surfaces here for the clean exit message.
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested (Ctrl+C). Exiting cleanly.")
