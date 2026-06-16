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
- [x] **Documentation & Deployment**
  - [x] Create `directives/run_comment_sniper.md`
  - [x] Expand `README.md` with full Google Cloud setup instructions
- [x] **Safety Verification Testing**
  - [x] Run bot against test channel and verify console log outputs and latency
- [ ] **Live-run**
- [ ] **Smoke-test**
