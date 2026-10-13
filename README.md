<h1 align="center">🔥 M A S T E R &nbsp; M U S I C &nbsp; D A E M O N 🔥</h1>
<p align="center">
  <em>Enterprise-Grade High-Performance Asynchronous Telegram Audio & Video Streaming Engine</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Telethon-Async-red?style=for-the-badge&logo=telegram&logoColor=white" />
  <img src="https://img.shields.io/badge/PyTgCalls-Voice%20Chat-purple?style=for-the-badge&logo=livejournal&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

---

### ⚙️ SYSTEM ARCHITECTURE & CAPABILITIES

*   **Dual-Client Protocol:** Powered by a high-frequency **Telethon Userbot** for seamless Voice Chat (`VC`) management and a dedicated **Bot Token Client** for rapid command execution, inline keyboards, and telemetry reporting.
*   **Smart Caching Engine:** Features localized chunk storage (`storage/audio` & `storage/videos`) bypassing redundant network bandwidth loops.
*   **Centralized Telemetry & Logging:** Granular event logging via `LOGGER_ID` tracking group additions, removals, admin status health reports, and user-level activities.
*   **Live Metrics Core:** Integrated `psutil` CPU/RAM health reporting alongside low-latency asynchronous internet bandwidth diagnostics.

---

### 🚀 DEPLOYMENT DIRECTIVES (VPS HOSTING)

Execute the following sequential operations in your secure Linux VPS shell environment to deploy the daemon core:

```bash
# 1. Update system package repositories & install system essentials (including FFmpeg)
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git ffmpeg -y

# 2. Clone the core repository and move into the workspace directory
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME

# 3. Initialize an isolated virtual environment and activate it
python3 -m venv venv
source venv/bin/activate

# 4. Upgrade packaging tools and install core dependency requirements
pip install --upgrade pip
pip install -r requirements.txt

# 5. Inject configuration credentials into the runtime environment
nano config.py
# (Input your API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, and LOGGER_ID)
# Save changes: Press Ctrl + O, hit Enter, then exit via Ctrl + X

# 6. Initialize a persistent background screen session for 24/7 daemon uptime
screen -S musicbot

# 7. Activate the virtual environment inside the screen session and launch core execution loop
source venv/bin/activate
python3 main.py

# To detach from screen and keep daemon running in background: 
# Press Ctrl + A, then press D
