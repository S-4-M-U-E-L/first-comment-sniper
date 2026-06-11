# first-comment-sniper 🚧 (Work in Progress)

> [!WARNING]
> ### ⚠️ Disclaimer & Warning
> **This project is for educational and learning purposes only.**
>
> * **Policy Violation:** Using this bot violates YouTube's Terms of Service and automated interaction policies.
> * **High Risk of Penalty:** Running this software carries a **high risk of shadowbanning, comment hiding, or permanent account termination**.
> * **Burner Accounts Required:** **DO NOT** use your personal or main Google/YouTube account. If you choose to run this bot, only use dedicated **burner accounts** that you can afford to lose.
> * **No Liability:** The author(s) and contributors assume no responsibility for any account suspension, loss of data, or consequences resulting from the use of this software. Use at your own risk.

Being first feels good. Telling the world you're first feels even better. Now, you can claim the throne every single time. This Python-powered sniper bot automatically drops a 'First!' comment the millisecond your target YouTuber uploads a video.

---

## 🚧 Project Status: Work In Progress
This project is currently in the initial development and architecture phase. The codebase is actively being written and is not yet ready for deployment.

### Proposed Architecture & Implementation Plan
We are building a robust, single-channel monitoring system using Python and the official Google Data API. The core strategy includes:

- **Asynchronous Polling Engine**: A non-blocking `asyncio` loop that queries the target channel's upload playlist every ~9 seconds, safely utilizing 96% of the daily free quota.
- **Persistent State**: The bot will track the latest video ID in a local `state.json` file to easily recover from crashes or network failures without missing an upload.
- **Behavioral Jitter**: To mimic human reaction times and avoid anti-bot algorithms, the system will apply a randomized delay of 14 to 28 seconds before posting.
- **Dynamic Commenting**: Comments will be pulled from a randomized JSON template list and injected with contextual variables like `{video_title}` and `{timestamp}` to prevent duplicate shadowbans.
- **Official OAuth 2.0 Flow**: Users will authenticate using their own Google Cloud Project credentials, securely managed through auto-refreshing tokens.

*(Detailed installation instructions, configuration guides, and setup steps will be added here once the project reaches a functional build.)*
