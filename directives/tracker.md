# YouTube First Comment Bot - Project Tracker

## Current State of Progress
The project has completed the core implementation phase. All three execution scripts (`auth.py`, `youtube_client.py`, `main.py`) are written and architecturally sound. The bot is **ready to run** pending two configuration items listed below.

## Checklist

- [x] **Planning & Layout**
  - [x] Draft the warning message for `README.md`
  - [x] Create the project directory layout and skeleton files
  - [x] Plan programming strategy and resolve constraints (`directives/strategy.md`)
  - [x] Simplify `README.md` for initial strategy commit
- [x] **Phase 1 & 2: Environment & Authentication**
  - [x] Initialize `requirements.txt` and `.env.example` configurations
  - [x] Write `execution/auth.py` for OAuth 2.0 flow and credentials refresh
  - [x] Test authentication flow and token generation
- [x] **Phase 3 & 4: API Client & Polling Engine**
  - [x] Write `execution/youtube_client.py` for API interactions
  - [x] Implement `state.json` parsing logic for persistent crash recovery
- [x] **Phase 5 & 6: Orchestration & Execution**
  - [x] Write `execution/main.py` using `asyncio` for the core polling loop
  - [x] Implement asynchronous execution jitter (14-28s) before simulating comment printing
  - [x] Implement dynamic variable substitution in comment templates
- [ ] **Documentation & Deployment**
  - [ ] Create `directives/run_comment_sniper.md`
  - [ ] Expand `README.md` with full Google Cloud setup instructions
- [x] **Safety Verification Testing**
  - [x] Run bot against test channel and verify console log outputs and latency

## To Do / Open Items

- [ ] **Populate `templates.json` with dynamic templates** — Current file contains only the static
  string `"First!"` which never uses `{video_title}` or `{timestamp}` placeholders. Strategy §5
  requires contextual, interpolated templates. Example:
  ```json
  [
    "First! Can't wait to watch {video_title}.",
    "Here before the views update! ({timestamp})",
    "Already here for {video_title} 🔥"
  ]
  ```

- [ ] **Populate `templates.json` with dynamic strings** — The file should contain an array of interpolated comment strings using `{video_title}` and `{timestamp}` variables. Avoid static strings like `"First!"` which look robotic and reduce anti-detection effectiveness.

- [ ] **Draft `directives/run_comment_sniper.md`** — A complete deployment guide covering: how to run the bot locally, how to deploy it to a 24/7 cloud environment (Google Cloud e2-micro or AWS t2.micro free tier), and how to set up the GCP Console OAuth credentials. Also add the GCP Console setup instructions to `README.md`.

- [ ] **Fix the static `"First!"` fallback in `main.py`** — The `load_templates()` function currently falls back to `["First!"]` if `templates.json` fails to load. This is a static, detectable string. Replace it with a dynamic fallback such as `["Here for {video_title}!"]` that still uses the interpolation system.

## Errors Fixed

| Date       | Error                                    | Fix Applied                                                  |
|------------|------------------------------------------|--------------------------------------------------------------|
| 2026-06-12 | Bare module imports in `main.py` failed when bot was invoked from project root (`python execution/main.py`) | Added `sys.path.insert(0, str(Path(__file__).resolve().parent))` before import statements — satisfies strategy.md §7 Path Safety |
| 2026-06-12 | `UnicodeEncodeError` when printing simulated comment with foreign characters (`Č`) on Windows `cp1252` terminal | Forced `sys.stdout.reconfigure(encoding='utf-8')` in `main.py` |
| 2026-06-12 | `auth.py` used standard `print()` statements which mismatched `main.py`'s structured logging | Replaced `print()` with Python's standard `logging` module to standardize output |
