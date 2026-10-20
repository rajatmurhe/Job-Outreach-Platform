# Pulse Outreach: Autonomous Job Application & Multi-Resume Routing Platform

[![Python](https://img.shields.io/badge/Python-3.11-009688?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Control%20Center-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Brave CDP](https://img.shields.io/badge/Brave-CDP%20Automation-FB542B?style=for-the-badge&logo=brave&logoColor=white)](https://brave.com/)
[![Gmail Multi-Account](https://img.shields.io/badge/Gmail-Multi--Account%20Rotation-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](https://mail.google.com/)
[![Dynamic Resumes](https://img.shields.io/badge/Dynamic-Multi--Resume%20Engine-8E75B2?style=for-the-badge)](resumes/)
[![macOS launchd](https://img.shields.io/badge/macOS-launchd%20Daemon-000000?style=for-the-badge&logo=apple&logoColor=white)](com.rajatmurhe.outreach.plist)

**Pulse Outreach** is an autonomous, background job application and recruiter outreach platform designed to streamline tech and software engineering job searches at scale.

Unlike traditional cold email tools that send through generic SMTP servers—which trigger spam filters, lack personalized attachments, or get domain-flagged—Pulse Outreach operates **directly inside real, authenticated browser sessions via the Chrome DevTools Protocol (CDP)**. It sends authentic 1-to-1 emails directly through Gmail with zero focus disruption, human-like delays, customized product hooks, and an intelligent **dynamic multi-resume router** that automatically selects and attaches the ideal resume based on each company's engineering domain.

> **Design Philosophy:** 100% independent and local. No external SaaS subscriptions, no third-party email blasters, and zero window-focus stealing while you work or code.

---

## Product Walkthrough & Screenshots

### 1. Visual Control Center & Multi-Account Quotas

![Pulse Outreach web admin dashboard with live account quotas, active daemon status, and metrics cards](docs/screenshots/dashboard-overview.png)

The central command dashboard runs locally at `http://localhost:5050`. It tracks real-time progress across all connected sender accounts, monitors all-time vs. daily send counts, displays live browser CDP connectivity status, and provides immediate controls to start, pause, or inspect the background daemon.

### 2. Research-Ranked Priority Lead Queue

![Leads queue table ordered by research fit score with personalized hooks and role alignments](docs/screenshots/leads-priority-queue.png)

Alphabetical outreach wastes daily quotas on generic staffing agencies. Pulse Outreach ingests master lead databases (1,800+ verified recruiters) and ranks them using multi-tier classification:
- **Tier 1 Elite Fit:** High-growth AI unicorns and deep-tech platforms (**SirionLabs, Roboflow, Prodigal, Recro, Claim Genius, Supervity, Ressl AI, SigNoz**) appear at the absolute top of the queue.
- **Contextual Hooks:** Injects custom 1-sentence openers connecting what each company builds to specific matching engineering projects.

### 3. Live Email & Dynamic Resume Preview Modal

![Email preview modal displaying custom body and dynamically selected resume chip](docs/screenshots/email-preview-modal.png)

Before or during any batch, clicking **Preview** renders the exact message that will be delivered to that recruiter. The modal verifies:
- Recruiter first-name resolution (falling back to "Hiring Team" for generic inboxes).
- Tailored subject line prefixed with `Application: <Target_Role> Opportunities at <Company> - Candidate Name`.
- Context-specific body referencing matching projects.
- **Dynamic Resume Badge:** Visually confirms which specialized PDF from the `resumes/` pool will be physically attached.

---

## Dynamic Multi-Resume Routing Engine

Sending one generic CV to every employer lowers interview conversion. Pulse Outreach includes a configurable multi-resume routing engine that automatically matches target roles to specialized resumes:

| Configured Resume | Target Role Category | Emphasized Projects & Technical Focus | Example Target Companies |
| :--- | :--- | :--- | :--- |
| `resume_agentic_ai.pdf` | **Agentic & GenAI Platforms** | Multi-agent workflows, tool calling, MCP integrations, CI/CD eval harnesses | **Shipsy**, **Pixis**, **Secomind.AI**, **Recro**, **Supervity** |
| `resume_voice_conversational.pdf` | **Voice & Conversational AI** | Speech models, ambient clinical AI, conversational dialogue flows, TTS/STT | **Suki**, **Observe.AI**, **BUDDI AI**, **Prodigal**, **Haptik** |
| `resume_computer_vision.pdf` | **Computer Vision & Video AI** | Multimodal video QA, object detection, real-time inference, loss functions | **Detect Technologies**, **Wobot.ai**, **Roboflow**, **Claim Genius** |
| `resume_rag_nlp.pdf` | **RAG, Document AI & LegalTech** | Enterprise vector search, verbatim citation extraction, prompt defense | **SirionLabs**, **Leena AI**, **Lumiq**, **Lentra** |
| `resume_ml_systems.pdf` | **Machine Learning & Systems** | Anomaly detection, classification models, telemetry, AI infrastructure | **Pelican.ai**, **bluCognition**, **SigNoz**, **Zendrive** |
| `resume_general_swe.pdf` | **Full-Stack AI & General SWE** | End-to-end full-stack engineering, FastAPI, Next.js, Docker, CI/CD pipelines | **Trilogy**, **Dassault Systems**, Core Tech & Software firms |

```text
[Role: Contract Intelligence / RAG] ──► Attaches: resume_rag_nlp.pdf
[Role: Computer Vision / Video QA]  ──► Attaches: resume_computer_vision.pdf
[Role: Speech / Conversational AI]  ──► Attaches: resume_voice_conversational.pdf
[Role: Agentic Systems / Workflows] ──► Attaches: resume_agentic_ai.pdf
[Role: Core Software Engineering]   ──► Attaches: resume_general_swe.pdf
```

> [!TIP]
> Place your specialized PDFs into the [`resumes/`](resumes/) directory. The router checks for role-specific matches first, automatically falling back to your default general resume if a specific variant is not configured.

---

## Autonomous Execution & Browser Automation Proof

### Silent Background Tab Activation (`daily_outreach_daemon.py`)
Traditional automation tools (e.g., standard Selenium or Playwright `bring_to_front`) force window switching, stealing macOS keyboard and cursor focus. Pulse Outreach uses low-level Chrome DevTools Protocol targets:
1. **Target Discovery:** Queries `GET http://localhost:9222/json/list` to find the exact browser profile tab.
2. **Silent Activation:** Uses `Target.activateTarget` over WebSocket to unthrottle background execution without bringing the window to the foreground.
3. **Background Compose:** Triggers Gmail's native `Compose` action, populates recipient and subject via DOM value setters, and types the body using `document.execCommand("insertText")` to preserve formatting.
4. **File Attachment Verification:** Selects the dynamically matched PDF via `DOM.setFileInputFiles` and polls the dialog DOM until the visual attachment chip confirms the upload completed.
5. **Send & Alert Validation:** Clicks the native `Send` button and validates that the compose dialog successfully closes and the `"Message sent"` toast appears.

### Multi-Account Round-Robin & Deliverability Guardrails
- **Daily Quota Caps:** Strict 25 emails/day per sender account (total 50 emails/day across accounts). Once Account 1 reaches its limit, the engine switches automatically to Account 2.
- **Human Jitter:** Delays of **45 to 75 seconds** between dispatches protect domain reputation and prevent spam traps.
- **Idempotent Deduplication:** Every dispatch is recorded immediately in `emails_sent.csv`. The engine cross-references past sent emails on every cycle—**zero duplicate applications are ever sent**.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Browser Automation** | Brave Browser, Chrome DevTools Protocol (CDP), WebSockets, JavaScript DOM Injection |
| **Web Control Center** | Python 3.11, FastAPI, Uvicorn, HTML5, Tailwind CSS, Vanilla JavaScript |
| **Data & Queue Processing** | Pandas, OpenPyXL, CSV, JSON, Heuristic Classification & Regex |
| **Daemon & OS Integration** | macOS `launchd`, LaunchAgent Plist, AppleScript (`osascript`) Desktop Banners |
| **Verification & Tests** | Python `unittest`, Pytest, Playwright (Headless Visual Regression & Telemetry Verification) |

---

## Repository Guide

```text
Job-Outreach-Platform/
├── config.json                     # Outreach configuration (accounts, caps, delays)
├── daily_outreach_daemon.py        # Master autonomous daemon script
├── server.py                       # FastAPI backend for dashboard and preview
├── build_prioritized_queue.py      # Multi-tier queue builder and deduplication logic
├── manage_daemon.sh                # Management CLI (status, run-now, logs, install)
├── dashboard.sh                    # Web control center startup script
├── com.rajatmurhe.outreach.plist   # macOS launchd service definition
├── todays_outreach_queue.csv       # Active lead pool with personalized hooks
├── emails_sent.csv                 # Master tracking and deduplication history
├── resumes/                        # Directory for your role-specific resume PDFs
│   └── README.md                   # Guide for configuring specialized resumes
├── static/                         # Dashboard UI assets (HTML, CSS, JS)
└── docs/screenshots/               # Interface walkthrough captures
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- macOS Sonoma or Sequoia
- Python 3.11+
- Brave Browser installed

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone git@github.com:rajatmurhe/Job-Outreach-Platform.git
cd Job-Outreach-Platform

pip install -r requirements.txt # or: pip install fastapi uvicorn pandas websockets openpyxl
```

### 3. Add Your Resumes
Drop your resume PDFs into the `resumes/` folder:
```bash
resumes/
├── resume_agentic_ai.pdf
├── resume_computer_vision.pdf
├── resume_voice_conversational.pdf
├── resume_rag_nlp.pdf
├── resume_ml_systems.pdf
└── resume_general_swe.pdf
```
*(See [`resumes/README.md`](resumes/README.md) for full role matching details).*

### 4. Launching Brave with Remote Debugging
Open Brave with CDP remote debugging active on port 9222:
```bash
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9222 &
```
*(Ensure you are logged into your sending accounts in your browser profiles)*.

### 5. Running the Web Dashboard
Start the visual control center:
```bash
./dashboard.sh
```
Open [http://localhost:5050](http://localhost:5050) in your browser.

### 6. Running Outreach
- **Manual Single Batch:**
  ```bash
  ./manage_daemon.sh run-now
  ```
- **Install Scheduled Weekday Morning Daemon (09:30 AM):**
  ```bash
  ./manage_daemon.sh install
  ```
- **Inspect Live Activity Logs:**
  ```bash
  ./manage_daemon.sh logs
  ```

---

## Safeguards & Production Boundaries

1. **Strictly 1-to-1 Delivery:** Does not use BCC or CC batching. Each email is composed and delivered individually.
2. **Account Health Preservation:** Enforces a hard stop at 25 emails per account per day. Even if the queue contains 1,800 leads, daily quota ceilings cannot be breached without explicit manual config changes.
3. **Failsafe Attachment Verification:** If a resume PDF is missing or fails to upload to the compose modal within 12 seconds, the email dispatch aborts immediately and discards the draft rather than sending an empty application.
4. **Data Isolation:** All personal application logs and recruiter records remain local to your machine. No external servers or telemetry tracking are used.
