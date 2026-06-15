# Run Guide: YouTube Comment Sniper

This is the operational SOP for running and deploying the YouTube Comment Sniper. For initial project setup, see `README.md` first.

---

## 1. Running Locally

After completing the setup in `README.md`, start the bot with:

**Windows:**
```
.venv\Scripts\python src\main.py
```

**macOS / Linux:**
```bash
.venv/bin/python src/main.py
```

### What You'll See

A successful startup looks like this:

```
2026-06-13 15:00:01 [INFO] Environment validation passed.
2026-06-13 15:00:01 [INFO] Authenticating with YouTube API...
2026-06-13 15:00:02 [INFO] Resolving uploads playlist ID for target channel...
2026-06-13 15:00:02 [INFO] Target playlist resolved: UUxxxxxxxxxxxxxxxxxxxxxxx
2026-06-13 15:00:02 [INFO] [START] Polling loop started. Watching for new uploads...
```

The bot will then silently poll every ~9 seconds. When a new video is detected:

```
2026-06-13 15:31:07 [INFO] [SNIPE] New video detected: dQw4w9WgXcQ ('Never Gonna Give You Up')
2026-06-13 15:31:07 [INFO] Target locked: dQw4w9WgXcQ ('Never Gonna Give You Up'). Jittering 21.4s before output...

============================================================
  [SIMULATED COMMENT POST]
  Video : dQw4w9WgXcQ
  Title : Never Gonna Give You Up
  Text  : Here before the views update! (2026-06-13 15:31:28)
============================================================

2026-06-13 15:31:28 [INFO] Snipe simulation complete for video dQw4w9WgXcQ.
```

### Stopping the Bot

Press `Ctrl+C` at any time. The bot shuts down gracefully — it will cancel any pending tasks and exit cleanly.

---

## 2. Keeping It Running 24/7 (Local Machine)

The bot must stay running to catch uploads. Here's how to keep it alive after you close your terminal.

### macOS / Linux — using `tmux` (recommended)

`tmux` keeps processes running in the background even after you disconnect.

```bash
# Install tmux if you don't have it
# macOS: brew install tmux
# Ubuntu/Debian: sudo apt install tmux

# Start a new named session
tmux new -s sniper

# Run the bot inside the session
.venv/bin/python src/main.py

# Detach from the session (bot keeps running)
# Press: Ctrl+B, then D

# To come back and check the logs later
tmux attach -t sniper
```

### Windows — using Task Scheduler

1. Open **Task Scheduler** (search in Start Menu)
2. Click **Create Basic Task**
3. Name it `YouTube Comment Sniper`
4. Set **Trigger** to: `When the computer starts`
5. Set **Action** to: `Start a program`
6. In **Program/script**, enter the full path to your venv Python:
   ```
   C:\path\to\first-comment-sniper\.venv\Scripts\python.exe
   ```
7. In **Add arguments**, enter:
   ```
   src\main.py
   ```
8. In **Start in**, enter the full project root path:
   ```
   C:\path\to\first-comment-sniper
   ```
9. Click Finish. The bot will now auto-start on every reboot.

---

## 3. Cloud Deployment (Optional — Run 24/7 Without Leaving Your PC On)

For fully hands-off, always-on operation, deploy the bot to a free cloud server.

### Option A: Railway.app (Easiest — No credit card required)

Railway is the simplest option. It deploys directly from your GitHub repo with zero server management.

1. Push your project to a **private** GitHub repository
2. Go to [railway.app](https://railway.app) and sign in with GitHub
3. Click **New Project → Deploy from GitHub repo**
4. Select your `first-comment-sniper` repo
5. In **Settings → Variables**, add your environment variables:
   - `TARGET_CHANNEL_ID` = your channel ID
   - `COMMENT_TEMPLATES_JSON` = `config/templates.json`
   - `GOOGLE_CLIENT_SECRETS_FILE` = `credentials/client_secrets.json`
6. Upload `credentials/client_secrets.json` and `credentials/token.json` via Railway's file storage or as base64-encoded environment variables
7. Set the **Start Command** to:
   ```
   python src/main.py
   ```

> **Note on OAuth:** Because the first-run OAuth flow requires a browser, you need to generate `credentials/token.json` locally first (by running the bot once on your machine) and then upload it to Railway. After the initial token is generated, it refreshes automatically forever.

### Option B: Google Cloud VM e2-micro (Free Tier)

Google Cloud's `e2-micro` instance is permanently free within the always-free limits and runs Linux.

```bash
# After SSH-ing into your VM:
git clone https://github.com/S-4-M-U-E-L/first-comment-sniper.git
cd first-comment-sniper
python3 setup.py

# Upload credentials/ folder (client_secrets.json + token.json) via SCP or the GCP Console file editor
# Then run inside tmux:
tmux new -s sniper
.venv/bin/python src/main.py
# Ctrl+B, D to detach
```

---

## 4. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Missing required environment variables` | `.env` not configured | Run `python setup.py` or manually edit `.env` |
| `Client secrets file not found` | `credentials/client_secrets.json` missing | Download from Google Cloud Console → Credentials and place in `credentials/` |
| `Refresh token revoked or expired` | Token was manually revoked or expired | Delete `credentials/token.json` and run the bot again to re-authenticate |
| `HttpError 403: quota exceeded` | Hit the 10,000 unit daily API limit | Wait until midnight Pacific Time for quota to reset |
| `HttpError 403: access forbidden` | Wrong OAuth scope or revoked access | Re-check GCP Console → OAuth consent screen setup |
| Bot detects the same video twice on restart | `state.json` was deleted | Normal on first restart after state file loss — bot self-corrects after one cycle |
| Garbled characters in video titles on Windows | Terminal encoding issue | Already patched in `main.py` via `sys.stdout.reconfigure(encoding='utf-8')` |
