# 🚀 Autonomous Cold Outreach Engine (Standalone)

A self-contained, automated cold outreach project for **Rajat Murhe**. 
**100% independent from Antigravity**—runs locally on macOS via native `launchd` and Python 3.11.

---

## 🌟 Key Features

1. **Zero-Touch Morning Schedule**: Automatically executes every weekday morning at **9:30 AM** via native macOS `launchd`.
2. **Silent Background Execution**: Interacts with Brave via Chrome DevTools Protocol (CDP) WebSocket without shifting windows or stealing typing focus.
3. **Auto-Brave Detection**: If Brave isn't running on port 9222, the daemon automatically launches it with `--remote-debugging-port=9222`.
4. **Multi-Account Rotation**: Rotates through authenticated Gmail accounts (`murherajat27@gmail.com`, `murherajat1@gmail.com`) up to safe daily limits (25 emails/day/account).
5. **Resume & Verification**: Automatically attaches `Rajat_Murhe_Resume.pdf`, confirms attachment chip in DOM, and verifies sent delivery.
6. **Zero Duplicate Guarantee**: Cross-checks all historical recipients in `emails_sent.csv` before dispatching.
7. **Desktop Notifications**: Sends native macOS banner notifications upon batch completion.

---

## 📁 Project Structure

```text
LINKEDIN DM/
├── config.json                     # Outreach configuration (accounts, caps, delays)
├── daily_outreach_daemon.py        # Master autonomous daemon script
├── manage_daemon.sh                # Management CLI (status, run-now, logs, install)
├── com.rajatmurhe.outreach.plist   # macOS launchd service definition
├── Rajat_Murhe_Resume.pdf          # Attached resume PDF
├── todays_outreach_queue.csv       # Active lead pool with personalized hooks
├── emails_sent.csv                 # Master tracking and deduplication history
└── logs/                           # Daily execution logs and launchd stdout/err
```

---

## 🖥️ Web Admin Dashboard

Launch your visual control center anytime by running:
```bash
./dashboard.sh
# OR
./manage_daemon.sh dashboard
```
Then open **[http://localhost:8501](http://localhost:8501)** in your browser!

### What You Can Do in the Dashboard:
1. **📄 Resume Manager**: Drag-and-drop a new PDF resume. It automatically backs up the old version, replaces `Rajat_Murhe_Resume.pdf`, and verifies the checksum.
2. **👥 Add & Manage Leads**:
   - Upload Excel (`.xlsx`) or CSV (`.csv`) recruiter lists with auto-mapping.
   - Automatically filters out already-contacted and queued duplicates.
   - Manually add single leads with custom roles and hooks.
   - Search and inspect all waiting leads.
3. **⚙️ Account Settings**: Toggle inboxes on/off, adjust daily caps (e.g. 25/day), adjust delay sliders (45–75s), and save changes directly.
4. **📊 Real-time Stats**: View today's progress bars per account, total delivered, and searchable history.
5. **🚀 Manual Trigger**: Trigger outreach immediately with 1 click or pause/resume the 9:30 AM scheduler.

---

## ⚙️ Quick Management CLI

Use `./manage_daemon.sh` to control the daemon from Terminal:

### 1. Check Status & Today's Sent Stats
```bash
./manage_daemon.sh status
```
Displays whether the macOS schedule is active, how many emails were sent today, account breakdown, and recent logs.

### 2. Trigger Outreach Manually (Run Now)
```bash
./manage_daemon.sh run-now
```
Runs today's batch immediately in the terminal without waiting for 9:30 AM.

### 3. View Live Logs
```bash
./manage_daemon.sh logs
```
Tails today's execution log file in real time.

### 4. Enable / Disable Automated Schedule
```bash
# Enable 9:30 AM weekday schedule:
./manage_daemon.sh install

# Disable schedule:
./manage_daemon.sh uninstall
```

---

## 🛠️ Configuration (`config.json`)

To change accounts, daily caps, or delays, simply edit `config.json`:

```json
{
  "accounts": [
    {
      "account": "murherajat27@gmail.com",
      "user_index": 5,
      "daily_limit": 25,
      "enabled": true
    },
    {
      "account": "murherajat1@gmail.com",
      "user_index": 7,
      "daily_limit": 25,
      "enabled": true
    },
    {
      "account": "rajatmurhe1@gmail.com",
      "user_index": 1,
      "daily_limit": 25,
      "enabled": false
    }
  ],
  "cdp_port": 9222,
  "delays": {
    "min_seconds": 45,
    "max_seconds": 75
  },
  "schedule": {
    "hour": 9,
    "minute": 30,
    "weekdays_only": true
  },
  "desktop_notifications": true
}
```

---

## 📊 Historical Data & Tracking

- All sent applications are recorded in [`emails_sent.csv`](file:///Users/rajatmurhe/Desktop/LINKEDIN%20DM/emails_sent.csv) with timestamp, recipient email, name, company, delivery status, subject, and sender account.
- Unsent leads are pulled from [`todays_outreach_queue.csv`](file:///Users/rajatmurhe/Desktop/LINKEDIN%20DM/todays_outreach_queue.csv). If the queue runs low (<30 leads), the daemon automatically replenishes from master lead files.
