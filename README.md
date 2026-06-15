# YouTube Comment Sniper 🎯

Being first feels good. Telling the world you're first feels even better. Now, you can claim the throne every single time. This Python-powered sniper bot automatically drops a 'First!' comment the millisecond your target YouTuber uploads a video.

*(... well, almost.)*

### 🚧 Safe Simulation Edition (WIP)

Right now, this project is operating as a **Safe Simulation**. That means it does everything a sniper bot does—detects new uploads in seconds and mimics human reaction times—but it only *simulates* the comment locally on your console instead of actually posting it.

This lets us test the Google Cloud API limits, architecture, and OAuth flows securely without any risk of shadowbans or account termination. It's 100% compliant with YouTube's Terms of Service.

---

## ✨ How it Works (Under the Hood)
* **Zero Risk:** It only uses `readonly` access to your YouTube account, so it physically can't post, edit, or delete anything.
* **Lightning Fast Polling:** An asynchronous engine checks the target channel's upload playlist every ~9 seconds, safely utilizing 96% of the daily free API quota without ever going over. Transient API hiccups (rate limits, server errors) are automatically recovered via a `with_backoff` retry system with exponential backoff and jitter—the engine never crashes on a momentary blip.
* **Persistent Memory:** It tracks the latest video in a local `data/state.json` file. If the script crashes or your network drops, it just picks right back up where it left off.
* **Human-like Jitter:** Anti-bot algorithms hate robotic speed. The system applies a randomized delay (14 to 28 seconds) to simulate someone typing frantically on their keyboard.
* **Dynamic Comments:** It pulls jokes from a custom JSON list and injects real-time variables like `{video_title}` and `{timestamp}` so every comment feels completely organic.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**:
  - **Windows**: `winget install Python.Python.3.11` (or type `python` in cmd to open the Store)
  - **macOS**: `brew install python3`
  - **Linux**: `sudo apt update && sudo apt install python3 python3-venv`
- **Google Cloud Account**: A free account to access the YouTube API (see Setup below).

### 1. Clone and run setup
```bash
git clone https://github.com/S-4-M-U-E-L/first-comment-sniper.git
cd first-comment-sniper
python setup.py
```
The setup script handles everything: creates a virtual environment, installs all dependencies, and walks you through entering your target channel ID interactively. No manual `pip install` needed.

### 2. Set up Google Cloud OAuth (one-time)
The bot connects to YouTube using your own Google Cloud credentials. Follow the guide below — it takes about 5 minutes.

### 3. Run the bot

**Windows:**
```
.venv\Scripts\python src\main.py
```
**macOS / Linux:**
```
.venv/bin/python src/main.py
```
The first run will open a browser window for Google login. After that, `credentials/token.json` is saved automatically and the bot never asks again.

---

## ☁️ Google Cloud Setup (Required — One Time)

The YouTube Data API requires you to authenticate through a Google Cloud Project. Here's the exact steps:

**1. Create a Project**
- Go to [console.cloud.google.com](https://console.cloud.google.com/)
- Click the project dropdown at the top → **New Project**
- Give it any name (e.g. `comment-sniper`) and click **Create**

**2. Enable the YouTube Data API**
- In the left sidebar go to **APIs & Services → Library**
- Search for **YouTube Data API v3** and click **Enable**

**3. Configure the OAuth Consent Screen**
- Go to **APIs & Services → OAuth consent screen**
- Select **External** → **Create**
- Fill in the required fields (App name, support email) — the values don't matter
- On the **Scopes** page, skip (click Save and Continue)
- On the **Test Users** page, click **Add Users** and add your own Google account email
- Click **Save and Continue**

**4. Create OAuth Credentials**
- Go to **APIs & Services → Credentials**
- Click **Create Credentials → OAuth client ID**
- Select **Desktop app** as the application type
- Click **Create**, then **Download JSON**
- Rename the downloaded file to `client_secrets.json` and place it in the `credentials/` folder

**5. Finding Your Channel ID**
Your target YouTube channel ID looks like `UCxxxxxxxxxxxxxxxxxxxxxx`. To find it:
- Go to the channel's YouTube page (e.g. `youtube.com/@MrBeast`)
- Right-click anywhere → **View Page Source**
- Press `Ctrl+F` and search for `channel_id` — it will appear in quotes
- Or use this shortcut tool: [commentpicker.com/youtube-channel-id.php](https://commentpicker.com/youtube-channel-id.php)

---

## 🔮 Future Roadmap: "Hard Mode"
Currently, the bot is locked to "Safe Mode". Once the core polling engine is fully validated, we plan to add an environment variable toggle (e.g., `LIVE_MODE=True`).

When flipped, the bot will transition from local simulation to actually firing `comments().insert()` requests to drop the payload live on YouTube. *(When that day comes, burner accounts will be highly recommended!)*
