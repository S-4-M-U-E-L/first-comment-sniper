 # YouTube Comment Sniper - Programming Strategy & Architecture Plan

This document details the programming strategy, development phases, architectural structure, testing procedures, and YouTube API quota management for building the **YouTube Comment Sniper** application. The system is designed for **single-channel, high-speed monitoring**, utilizing asynchronous execution and intelligent behavioral masking to prevent loop-blocking and shadowbans.

---

## 1. System Requirements & Dependencies

### Runtime Environment

* **Python Version**: Python 3.8 or higher is required.
* **Operating System**: Platform-agnostic (Windows, macOS, Linux).

### Python Packages (`requirements.txt`)

To interact with the YouTube Data API v3 and manage OAuth 2.0 credentials, the following libraries are required:

```text
google-api-python-client>=2.0.0
google-auth-oauthlib>=0.4.0
google-auth-httplib2>=0.1.0
python-dotenv>=0.19.0

```

*Note: The application utilizes Python's built-in `asyncio` for non-blocking concurrency, requiring no external asynchronous frameworks.*

---

## 2. 3-Layer Architecture Layout

The application separates concerns into three distinct layers to ensure execution logic never interrupts the polling rhythm:

### Layer 1: Directives & State (Storage)

* **`directives/strategy.md`**: This guide.
* **`directives/run_comment_sniper.md`**: Operational deployment guide.
* **`state.json`**: Persistent local storage mapping the target channel to its `latest_video_id` to ensure crash recovery.

### Layer 2: Orchestration (Decision & Control)

* **`execution/main.py`**: The asynchronous driver. Reads `.env`, initializes Layer 3 modules, runs the non-blocking polling loop, spawns background execution tasks, and logs statuses.

### Layer 3: Execution (Deterministic Actions)

* **`execution/auth.py`**: Handles OAuth 2.0 flow, token caching (`token.json`), and automatic token refreshes (restricted to the `youtube.readonly` scope).
* **`execution/youtube_client.py`**: Contains strictly defined functions for Data API communications (fetching uploads).

---

## 3. Step-by-Step Programming Phases

### Phase 1: Environment & Requirements Setup

1. **Initialize Requirements**: Write the required packages to `requirements.txt`.
2. **Environment Validation**: Load `.env` variables and assert that all required keys (`TARGET_CHANNEL_ID`, `COMMENT_TEMPLATES_JSON`, `GOOGLE_CLIENT_SECRETS_FILE`) are present.

### Phase 2: OAuth 2.0 Authentication Helper (`execution/auth.py`)

1. Implement the credential resolver function.
2. If `token.json` exists, load and validate.
3. If credentials are expired but have a refresh token, run `creds.refresh(Request())`.
4. If missing/invalid, run the local server OAuth consent flow and save the output to `token.json`.

### Phase 3: Playlist ID Resolution & Persistent State

1. **Channel Mapping**: Convert the `TARGET_CHANNEL_ID` (starts with `UC`) to the uploads playlist ID (starts with `UU`) by replacing the second character.
2. **State Hydration**: On startup, read `state.json`. If it does not exist, fetch the latest video from the `UU` playlist and save its ID to establish a baseline. **Crucial**: The bot must write state to disk immediately after any baseline check or successful snipe.

### Phase 4: The Asynchronous Polling Engine

The core loop must use `asyncio` to ensure polling continues even while a comment is being scheduled or posted.

1. **Polling Jitter (Network Mask)**: The loop queries the API every **7.5 to 10.5 seconds** (averaging 9.0s). This utilizes 96% of the daily quota while creating an unpredictable, organic network signature.
2. **Detection Logic**: If the returned `videoId` differs from the one stored in `state.json`, a new upload is confirmed.
3. **Delegation**: Upon detection, the bot immediately writes the new ID to `state.json`, then spawns an independent background task via `asyncio.create_task()` to handle the execution jitter and posting, while the main loop returns to polling.

### Phase 5: Execution Jitter & Dynamic "First" Contextualization (Console Print Only)

To simulate the speed and variance of a "First!" comment without any risk of suspension, the bot calculates human-like delay and prepares the dynamic text, then prints it to the console.

1. **Execution Jitter (Behavioral Mask)**: Introduce a randomized asynchronous sleep between **14 and 28 seconds** inside the delegated background task.
2. **Dynamic "First" Contextualization**: Never use static, one-word strings. Instead, interpolate variables into templates to demonstrate context (e.g., "First! Can't wait to watch {video_title}." or "Here before the views update! ({timestamp})").
3. **Printing**: Output the finalized comment to the terminal console instead of posting it to YouTube.

*Core Logic Structure Example:*

```python
import asyncio
import random
import time

def get_polling_delay():
    # Averages 9.0 seconds, consuming exactly 96% of the 10,000 daily quota
    return random.uniform(7.5, 10.5)

def get_execution_delay():
    # Behavioral mask: human reaction time buffer
    return random.uniform(14, 28)

async def print_comment_with_jitter(video_id, template, title):
    delay = get_execution_delay()
    print(f"Target locked: {video_id}. Jittering for {round(delay, 2)} seconds...")
    await asyncio.sleep(delay)
    
    # Format contextual template (e.g., inject {title} or {timestamp})
    # Print the comment to terminal instead of posting
    comment_text = template.format(video_title=title, timestamp=int(time.time()))
    print(f"\n[SIMULATED COMMENT POST] Video: {video_id} | Text: '{comment_text}'\n")
    print(f"Snipe print complete on {video_id}!")

async def polling_loop():
    while True:
        # Check API for new video...
        # If new_video_id != state["latest_id"]:
        #    update_state(new_video_id)
        #    asyncio.create_task(print_comment_with_jitter(new_video_id, template, title))
        
        await asyncio.sleep(get_polling_delay())

```

### Phase 6: Graceful Degradation & Error Handling

1. **Network Retries**: Wrap the `YoutubelistItems().list` call in a robust `try-except` block targeting `socket.timeout` and `ConnectionResetError`. Apply an exponential backoff if the network drops.
2. **Signal Handling**: Implement hooks for `SIGINT` and `SIGTERM` to allow the asynchronous loop to finish pending post tasks before fully shutting down the script.

---

## 4. Phase-by-Phase Testing Plan

### Phase 1 Test: OAuth & Refresh

* **Execution**: Run authorization script. Wait 1 hour (or manually expire the token), then run it again.
* **Verification**: Ensure the script uses the refresh token instead of prompting the browser consent screen twice.

### Phase 2 Test: State Persistence Recovery

* **Execution**: Manually modify `state.json` to an older `videoId`. Start the bot.
* **Verification**: The bot should instantly detect a "new" video. Terminate the script mid-execution, restart it, and ensure it correctly resumes based on the updated `state.json`.

### Phase 3 Test: End-to-End Live Snipe (Burner Channel)

* **Execution**:
1. Point `TARGET_CHANNEL_ID` to your own burner channel.
2. Start the bot.
3. Upload an unlisted video.

* **Verification**: Watch the console for the independent `asyncio` task spawning, verify the 14-28 second execution delay, and confirm the simulated comment is logged to the console with the correct delay, timestamp, and video title. (Note: physical comment posting is disabled for safety; the output is verified via local console log).

---

## 5. YouTube API Quota Calculations (Single Channel)

The YouTube Data API v3 enforces a default daily quota limit of **10,000 units**.

* `playlistItems().list` = 1 unit
* Comment Posting = 0 units (Disabled - Console Print Only)

**Quota Math for Single Target ($N=1$):**

* Polling Interval: Average of 9.0 seconds.
* $86,400 \text{ seconds} / 9.0 = 9,600 \text{ daily polling calls}$.
* **Base Quota Cost:** 9,600 units per day.
* **Remaining Buffer:** 400 units

**Status: 100% Safe & Optimized.** The 400-unit buffer allows for API retries and restarts without hitting limits. Because posting is disabled, we consume absolutely no posting quota.

---

## 6. Edge Cases & Anti-Detection Mitigations

| Threat Vector | Bot Impact | System Mitigation |
| --- | --- | --- |
| **Account Termination / Ban** | Risk of losing access to Google account services. | **100% mitigated** by using `youtube.readonly` scope and disabling comment posting entirely. The bot only reads data and prints locally. |
| **Static Traffic Signatures** | IP flagged for bot activity by Google. | **Polling Jitter (7.5-10.5s)** ensures the API request interval is mathematically unpredictable, blurring the metronome effect. |
| **System Crash / Reboot** | Bot loses track of the latest video. | **Persistent Local State** (`state.json`) is updated the millisecond an ID is detected, before the simulation jitter begins. |
| **Blocking the Loop** | While simulation is waiting, bot fails to poll. | The **Asynchronous Architecture** (`asyncio.create_task`) decouples polling from logging, keeping the polling rhythm independent. |

---

## 7. Technical Caveats & Engineering Decisions

### Windows OS Compatibility (SIGINT / Graceful Shutdown)
* **Problem**: Standard Python `asyncio` on Windows (which uses the `ProactorEventLoop` since Python 3.8) does not support registering signal handlers using `loop.add_signal_handler()` for `SIGINT` or `SIGTERM`, resulting in a runtime `NotImplementedError`.
* **Resolution**: Instead of registering signal handlers on the event loop, capture `KeyboardInterrupt` in a standard try-except block wrapping `asyncio.run(main())`. When caught, trigger a graceful shutdown by cancelling all pending asynchronous tasks and gathering their results.

### Path Safety
* **Problem**: Storing or reading files (like `token.json`, `client_secrets.json`, and `state.json`) using relative paths can cause runtime failures or duplicate logins if the bot is executed from a working directory other than the project root.
* **Resolution**: Resolve all paths dynamically using absolute paths relative to the script location (e.g., combining `os.path.dirname(os.path.abspath(__file__))` with relative path traversals). This ensures the application functions identically regardless of where it is invoked.

### Exception Handling & Network Resilience
* **Problem**: Continuous, high-frequency API polling is highly susceptible to temporary network outages, connection resets, and transient API issues. Without explicit error handling, any temporary failure will crash the engine.
* **Resolution**: Wrap external API and network requests (like calling the YouTube Data API) in a retry loop implementing exponential backoff (e.g., retrying after 2s, then 4s, then 8s). This prevents the bot from crashing during transient failures while preserving overall system uptime.