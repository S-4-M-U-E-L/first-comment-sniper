# YouTube Comment Sniper 🎯

Being first feels good. Telling the world you're first feels even better. Now, you can claim the throne every single time. This Python-powered sniper bot automatically drops a 'First!' comment the millisecond your target YouTuber uploads a video.

*(... well, almost.)*

### 🚧 Safe Simulation Edition (WIP)

Right now, this project is operating as a **Safe Simulation**. That means it does everything a sniper bot does—detects new uploads in seconds and mimics human reaction times—but it only *simulates* the comment locally on your console instead of actually posting it. 

This lets us test the Google Cloud API limits, architecture, and OAuth flows securely without any risk of shadowbans or account termination. It's 100% compliant with YouTube's Terms of Service.

---

## ✨ How it Works (Under the Hood)
* **Zero Risk:** It only uses `readonly` access to your YouTube account, so it physically can't post, edit, or delete anything.
* **Lightning Fast Polling:** An asynchronous engine checks the target channel's upload playlist every ~9 seconds, safely utilizing 96% of the daily free API quota without ever going over.
* **Persistent Memory:** It tracks the latest video in a local `state.json` file. If the script crashes or your network drops, it just picks right back up where it left off.
* **Human-like Jitter:** Anti-bot algorithms hate robotic speed. The system applies a randomized delay (14 to 28 seconds) to simulate someone typing frantically on their keyboard.
* **Dynamic Comments:** It pulls jokes from a custom JSON list and injects real-time variables like `{video_title}` and `{timestamp}` so every comment feels completely organic.

---

## 🔮 Future Roadmap: "Hard Mode"
Currently, the bot is locked to "Safe Mode". Once the core polling engine is fully validated, we plan to add an environment variable toggle (e.g., `LIVE_MODE=True`). 

When flipped, the bot will transition from local simulation to actually firing `comments().insert()` requests to drop the payload live on YouTube. *(When that day comes, burner accounts will be highly recommended!)*
