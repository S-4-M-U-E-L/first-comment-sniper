# YouTube First Comment Bot - Project Tracker

## Current State of Progress
The project is currently in the **Planning and Strategy Phase**. We have successfully established the folder layout, drafted the initial strategy directives (`strategy.md`), and configured the `README.md` to reflect our goals. The next step is to begin the implementation phase (writing code).

## Checklist

- [x] **Planning & Layout**
  - [x] Draft the warning message for `README.md`
  - [x] Create the project directory layout and skeleton files
  - [x] Plan programming strategy and resolve constraints (`directives/strategy.md`)
  - [x] Simplify `README.md` for initial strategy commit
- [ ] **Phase 1 & 2: Environment & Authentication**
  - [ ] Initialize `requirements.txt` and `.env.example` configurations
  - [ ] Write `execution/auth.py` for OAuth 2.0 flow and credentials refresh
  - [ ] Test authentication flow and token generation
- [ ] **Phase 3 & 4: API Client & Polling Engine**
  - [ ] Write `execution/youtube_client.py` for API interactions
  - [ ] Implement `state.json` parsing logic for persistent crash recovery
- [ ] **Phase 5 & 6: Orchestration & Execution**
  - [ ] Write `execution/main.py` using `asyncio` for the core polling loop
  - [ ] Implement asynchronous execution jitter (14-28s) before posting comments
  - [ ] Implement dynamic variable substitution in comment templates
- [ ] **Documentation & Deployment**
  - [ ] Create `directives/run_comment_sniper.md`
  - [ ] Expand `README.md` with full Google Cloud setup instructions
- [ ] **Safety Verification Testing**
  - [ ] Run bot against test channel and verify public comment visibility and latency

## Errors to Fix
*(No active errors at this time)*
