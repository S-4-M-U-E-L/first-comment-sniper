"""
src/youtube_client.py

Fix 3 (Exception Handling & Network Resilience):
Contains all YouTube Data API v3 communication functions. Every network call
uses the shared with_backoff() utility which implements exponential backoff
with jitter for transient errors and raises immediately on fatal errors.

Error classification:
  Transient (retry): socket errors, HttpError 429/5xx, TransportError, ServerNotFoundError
  Fatal (raise):     HttpError 4xx (except 429), RefreshError, misconfiguration errors
"""

import asyncio
import random
import socket
import logging
from typing import Optional, Tuple
import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import TransportError

logger = logging.getLogger(__name__)

# --- Transient HTTP status codes that warrant a retry ---
TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}

# --- Backoff configuration (per strategy.md §7) ---
BACKOFF_INITIAL_DELAY = 2.0    # seconds — matches strategy.md example
BACKOFF_MULTIPLIER    = 2.0    # doubles each attempt: 2s → 4s → 8s → 16s → 32s
BACKOFF_MAX_RETRIES   = 5      # up to ~62s cumulative wait before giving up
BACKOFF_CAP           = 60.0   # never wait longer than 60s per attempt
QUOTA_EXCEEDED_DELAY  = 60.0   # hard minimum on 429 — Google quota resets are coarse

# --- Transient network exceptions to catch ---
_TRANSIENT_NETWORK_ERRORS = (
    socket.timeout,
    socket.gaierror,
    ConnectionResetError,
    ConnectionAbortedError,
    TimeoutError,
    TransportError,
    httplib2.ServerNotFoundError,
)


async def with_backoff(func, *args, max_retries=BACKOFF_MAX_RETRIES, **kwargs):
    """
    Calls func(*args, **kwargs) and retries on transient errors with
    exponential backoff and ±10% jitter.

    - Retries on:  transient network errors, HttpError 429/5xx
    - Raises on:   fatal HttpError 4xx (except 429), all other errors
    - Uses asyncio.sleep (non-blocking) — must be called from async context
    - On exhaustion: re-raises the last caught exception to the caller
    """
    # Note: asyncio.CancelledError is a BaseException (not Exception) and is
    # NOT caught by either 'except HttpError' or 'except _TRANSIENT_NETWORK_ERRORS'.
    # This is intentional — CancelledError propagates freely through this function
    # so that task cancellation during shutdown works correctly. Never add a broad
    # 'except Exception' here; it would silently swallow cancellations and cause
    # the event loop to hang on shutdown.
    delay = BACKOFF_INITIAL_DELAY
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)

        except HttpError as e:
            status = int(e.resp.status)
            if status in TRANSIENT_HTTP_STATUSES:
                last_exception = e
                if attempt == max_retries:
                    break
                if status == 429:
                    # Quota exceeded — hard minimum delay regardless of backoff position
                    actual_delay = QUOTA_EXCEEDED_DELAY
                    logger.warning(f"Quota limit hit (429) — backing off for {actual_delay:.0f}s.")
                else:
                    actual_delay = min(delay * random.uniform(0.9, 1.1), BACKOFF_CAP)
                    logger.warning(
                        f"Transient HTTP {status} — retrying in {actual_delay:.1f}s "
                        f"(attempt {attempt + 1}/{max_retries})."
                    )
                await asyncio.sleep(actual_delay)
                delay = min(delay * BACKOFF_MULTIPLIER, BACKOFF_CAP)
            else:
                # Fatal 4xx — do not retry
                raise

        except _TRANSIENT_NETWORK_ERRORS as e:
            last_exception = e
            if attempt == max_retries:
                break
            actual_delay = min(delay * random.uniform(0.9, 1.1), BACKOFF_CAP)
            logger.warning(
                f"Network error ({type(e).__name__}) — retrying in {actual_delay:.1f}s "
                f"(attempt {attempt + 1}/{max_retries})."
            )
            await asyncio.sleep(actual_delay)
            delay = min(delay * BACKOFF_MULTIPLIER, BACKOFF_CAP)

    # All retries exhausted — raise last exception to caller
    raise last_exception


def build_youtube_service(credentials):
    """
    Builds and returns the YouTube Data API v3 service object.
    Makes a network request to fetch the API discovery document.
    Synchronous — retry is handled by the caller (main.py startup sequence).
    """
    return build("youtube", "v3", credentials=credentials)


async def get_uploads_playlist_id(youtube, channel_id: str) -> str:
    """
    Resolves a channel ID (UC...) to its uploads playlist ID (UU...).
    Called once at startup. Uses exponential backoff on transient errors.

    Raises HttpError on fatal API errors (403, 401) with descriptive messages.
    Raises ValueError if the channel ID returns no results.
    """
    def _call():
        response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
        items = response.get("items", [])
        if not items:
            raise ValueError(f"No channel found for ID: {channel_id!r}. Check TARGET_CHANNEL_ID in .env.")
        return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    try:
        return await with_backoff(_call, max_retries=5)
    except HttpError as e:
        status = int(e.resp.status)
        if status == 403:
            logger.error("Access forbidden (403) — check your OAuth scopes and Google Cloud project configuration.")
        elif status == 401:
            logger.error("Unauthorized (401) — OAuth token may be invalid. Delete credentials/token.json and re-authenticate.")
        raise


async def get_latest_video_id(youtube, uploads_playlist_id: str) -> Tuple[Optional[str], str]:
    """
    Fetches the most recent video ID and title from the channel's uploads playlist.

    Hot-path function — called every poll cycle (~9 seconds).
    On transient error exhaustion: raises to polling_loop(), which catches it
    and continues to the next cycle (bot does not crash on a single bad poll).
    On fatal 401: raises immediately — polling_loop() breaks the while loop.

    Returns: (video_id, title) tuple, or (None, "") if playlist is empty.
    """
    def _call():
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=1
        ).execute()
        items = response.get("items", [])
        if not items:
            return None, ""
        snippet = items[0].get("snippet", {})
        video_id = snippet.get("resourceId", {}).get("videoId")
        title = snippet.get("title", "")
        return video_id, title

    try:
        return await with_backoff(_call, max_retries=5)
    except HttpError as e:
        status = int(e.resp.status)
        if status == 401:
            # Fatal mid-run — the polling loop must stop
            logger.error(
                "Auth token expired or revoked mid-run (401). "
                "Restart the bot and delete credentials/token.json to re-authenticate."
            )
        raise
