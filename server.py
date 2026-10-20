#!/usr/bin/env python3
import sys
"""
FastAPI Backend for Rajat Murhe's Cold Outreach Control Center.
Powers the market-grade SaaS Web Dashboard.
"""

import csv
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from typing import Dict, Any, List, Optional
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOG_FILE = os.path.join(BASE_DIR, "emails_sent.csv")
QUEUE_FILE = os.path.join(BASE_DIR, "todays_outreach_queue.csv")
RESUME_FILE = os.path.join(BASE_DIR, "Rajat_Murhe_Resume.pdf")
PLIST_NAME = "com.rajatmurhe.outreach.plist"

app = FastAPI(title="Autonomous Outreach API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_config() -> Dict[str, Any]:
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "accounts": [
            {"account": "murherajat27@gmail.com", "user_index": 5, "daily_limit": 25, "enabled": True},
            {"account": "murherajat1@gmail.com", "user_index": 7, "daily_limit": 25, "enabled": True},
            {"account": "rajatmurhe1@gmail.com", "user_index": 1, "daily_limit": 25, "enabled": False}
        ],
        "cdp_port": 9222,
        "delays": {"min_seconds": 45, "max_seconds": 75},
        "desktop_notifications": True
    }


def save_config(cfg: Dict[str, Any]):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_sent_emails() -> set:
    sent = set()
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r, None)
            for row in r:
                if len(row) > 4 and row[4] == "Success":
                    sent.add(row[1].lower().strip())
    return sent


def is_brave_active(port=9222) -> bool:
    try:
        req = urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=2)
        return req.status == 200
    except Exception:
        return False


def is_daemon_scheduled() -> bool:
    try:
        res = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
        return "com.rajatmurhe.outreach" in res.stdout
    except Exception:
        return False


def is_outreach_running() -> bool:
    try:
        res = subprocess.run(["pgrep", "-fl", "daily_outreach_daemon.py"], capture_output=True, text=True)
        return bool(res.stdout.strip())
    except Exception:
        return False


# ==============================================================================
# API ROUTES
# ==============================================================================

@app.get("/api/status")
def get_status():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    cfg = load_config()
    all_sent = get_sent_emails()

    today_sent = 0
    today_by_account = {}
    recent_sends = []

    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r, None)
            rows = list(r)
            for row in rows:
                if len(row) > 4:
                    ts = row[0]
                    email = row[1]
                    name = row[2] if len(row) > 2 else ""
                    comp = row[3] if len(row) > 3 else ""
                    status = row[4]
                    subj = row[5] if len(row) > 5 else ""
                    sender = row[6].strip() if len(row) > 6 else "unknown"

                    if status == "Success" and ts.startswith(today_str):
                        today_sent += 1
                        today_by_account[sender] = today_by_account.get(sender, 0) + 1

                    recent_sends.append({
                        "timestamp": ts,
                        "email": email,
                        "name": name,
                        "company": comp,
                        "status": status,
                        "subject": subj,
                        "sender": sender
                    })

    # Account metrics
    accounts_info = []
    for acc in cfg.get("accounts", []):
        email_addr = acc["account"]
        sent_today = today_by_account.get(email_addr, 0)
        limit = acc.get("daily_limit", 25)
        accounts_info.append({
            "account": email_addr,
            "user_index": acc.get("user_index", 5),
            "daily_limit": limit,
            "enabled": acc.get("enabled", True),
            "sent_today": sent_today,
            "percent_today": min(round((sent_today / limit) * 100, 1) if limit > 0 else 0, 100.0)
        })

    # Queue metrics
    queue_total = 0
    queue_unsent = 0
    if os.path.isfile(QUEUE_FILE):
        try:
            q_df = pd.read_csv(QUEUE_FILE)
            queue_total = len(q_df)
            if not q_df.empty and "Email" in q_df.columns:
                queue_unsent = len(q_df[~q_df["Email"].str.lower().str.strip().isin(all_sent)])
        except Exception:
            pass

    return {
        "today_str": today_str,
        "today_sent": today_sent,
        "all_time_sent": len(all_sent),
        "queue_total": queue_total,
        "queue_unsent": queue_unsent,
        "accounts": accounts_info,
        "daemon_scheduled": is_daemon_scheduled(),
        "outreach_running": is_outreach_running(),
        "brave_cdp_active": is_brave_active(cfg.get("cdp_port", 9222)),
        "recent_sends": recent_sends[-50:][::-1]
    }


@app.get("/api/leads")
def get_leads(limit: int = 100, search: str = ""):
    all_sent = get_sent_emails()
    leads = []
    if os.path.isfile(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    em = row.get("Email", "").strip().lower()
                    is_sent = em in all_sent
                    if search:
                        q = search.lower()
                        if not any(q in str(val).lower() for val in row.values()):
                            continue
                    leads.append({
                        "priority": row.get("Priority", "2"),
                        "company": row.get("Company", ""),
                        "contact_name": row.get("Contact_Name", "Hiring Team"),
                        "email": row.get("Email", ""),
                        "target_role": row.get("Target_Role", "AI Engineering Intern"),
                        "personalized_hook": row.get("Personalized_Hook", ""),
                        "is_sent": is_sent
                    })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"leads": leads[:limit], "total_count": len(leads)}


class ManualLead(BaseModel):
    company: str
    contact_name: Optional[str] = "Hiring Team"
    email: str
    target_role: Optional[str] = "AI Engineering Intern"
    personalized_hook: Optional[str] = ""


@app.post("/api/leads/add")
def add_lead(lead: ManualLead):
    em = lead.email.strip().lower()
    if "@" not in em or "." not in em.split("@")[1]:
        raise HTTPException(status_code=400, detail="Invalid email address.")

    sent_emails = get_sent_emails()
    if em in sent_emails:
        raise HTTPException(status_code=400, detail="Recruiter already contacted in previous campaigns!")

    hook = lead.personalized_hook.strip() if lead.personalized_hook else f"I've been following what {lead.company} is building in applied AI and software innovation."

    row = {
        "Priority": "1 - Manual",
        "Company": lead.company.strip(),
        "Contact_Name": lead.contact_name.strip() if lead.contact_name else "Hiring Team",
        "Email": em,
        "Target_Role": lead.target_role.strip() if lead.target_role else "AI Engineering Intern",
        "Personalized_Hook": hook
    }

    file_exists = os.path.isfile(QUEUE_FILE) and os.path.getsize(QUEUE_FILE) > 0
    with open(QUEUE_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Priority", "Company", "Contact_Name", "Email", "Target_Role", "Personalized_Hook"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return {"status": "success", "message": f"Added {lead.company} ({em}) to queue."}


@app.post("/api/leads/upload")
async def upload_leads_file(file: UploadFile = File(...)):
    filename = file.filename.lower()
    if not (filename.endswith(".xlsx") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx and .csv files are supported.")

    temp_path = os.path.join(BASE_DIR, f"temp_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if filename.endswith(".xlsx"):
            df = pd.read_excel(temp_path)
            # If headers are in row 1 or 2
            if "Email" not in df.columns:
                for h in range(1, 4):
                    test_df = pd.read_excel(temp_path, header=h)
                    if any("email" in str(c).lower() for c in test_df.columns):
                        df = test_df
                        break
        else:
            df = pd.read_csv(temp_path)

        # Detect columns
        email_col = next((c for c in df.columns if "email" in str(c).lower() or "mail" in str(c).lower()), None)
        name_col = next((c for c in df.columns if "name" in str(c).lower() or "contact" in str(c).lower() or "person" in str(c).lower()), None)
        comp_col = next((c for c in df.columns if "company" in str(c).lower() or "firm" in str(c).lower() or "org" in str(c).lower()), None)
        role_col = next((c for c in df.columns if "role" in str(c).lower() or "title" in str(c).lower() or "position" in str(c).lower()), None)

        if not email_col:
            raise HTTPException(status_code=400, detail="Could not auto-detect an Email column in your spreadsheet.")

        sent_emails = get_sent_emails()
        existing_queued = set()
        if os.path.isfile(QUEUE_FILE):
            try:
                q_df = pd.read_csv(QUEUE_FILE)
                if "Email" in q_df.columns:
                    existing_queued = set(q_df["Email"].str.lower().str.strip())
            except Exception:
                pass

        new_rows = []
        dup_count = 0

        for _, r in df.iterrows():
            raw_email = str(r.get(email_col, "")).strip().lower()
            if "@" in raw_email and "." in raw_email.split("@")[1]:
                if raw_email in sent_emails or raw_email in existing_queued:
                    dup_count += 1
                    continue

                comp = str(r.get(comp_col, "")).strip() if comp_col else "your company"
                if comp == "nan": comp = "your company"
                comp = comp.rstrip(",")

                name = str(r.get(name_col, "")).strip() if name_col else "Hiring Team"
                if name == "nan" or not name: name = "Hiring Team"

                role = str(r.get(role_col, "")).strip() if role_col else "AI Engineering Intern"
                if role == "nan" or not role: role = "AI Engineering Intern"

                new_rows.append({
                    "Priority": "Imported",
                    "Company": comp,
                    "Contact_Name": name,
                    "Email": raw_email,
                    "Target_Role": role,
                    "Personalized_Hook": f"I've been following what {comp} is building in applied AI and software innovation."
                })
                existing_queued.add(raw_email)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            file_exists = os.path.isfile(QUEUE_FILE) and os.path.getsize(QUEUE_FILE) > 0
            new_df.to_csv(QUEUE_FILE, mode="a", index=False, header=not file_exists)

        return {
            "status": "success",
            "added_count": len(new_rows),
            "duplicates_filtered": dup_count,
            "filename": file.filename
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)



# EXACT PROJECTS AS PRINTED IN EACH SPECIFIC RESUME PDF
RESUME_PROJECTS = {
    "Rajat.pdf": [
        "ClinicVoice AI: voice receptionist for clinics booking appointments on Google Calendar with LangGraph, MCP tools, 4 safety layers and red-team CI evals (github.com/rajatmurhe/clinicvoice-ai)",
        "Atlas: commercial analytics workbench with a LangGraph SQL agent, PostgreSQL star schema over 24k+ records, reaching 1.25% forecast MAPE (github.com/rajatmurhe/atlas-commercial-intelligence)",
        "FieldProof AI: multi-tenant platform where Gemini checks technician job videos with human review & async PostgreSQL queue (github.com/rajatmurhe/fieldproof-ai)",
        "AI Job Assistant: resume-to-job matching tool with evidence, n8n automation, and multi-provider LLM API schema validation (github.com/rajatmurhe/ai-job-assistant)"
    ],
    "Rajat-Murhe.pdf": [
        "ClinicVoice AI: multilingual voice receptionist for clinics (Hindi, English, Marathi) with Whisper, LangGraph, MCP, XTTS v2, booking real Google Calendar appointments & 48ms semantic caching (github.com/rajatmurhe/clinicvoice-ai)",
        "NeuroAI: explainable clinical diagnostic platform predicting Alzheimer's stages using Random Forest/XGBoost (85.23% accuracy) and fine-tuned BERT (81.82%) with SHAP explanations (github.com/rajatmurhe/NeuroAI-Diagnostic-Platform | neuroai-diagnostic-platform.onrender.com)",
        "Atlas: commercial analytics workbench with a LangGraph SQL agent over 24k+ PostgreSQL records, reaching 1.25% forecast MAPE (github.com/rajatmurhe/atlas-commercial-intelligence)",
        "FieldProof AI: multi-tenant platform where Gemini audits technician job videos with human-in-the-loop review and audit trails (github.com/rajatmurhe/fieldproof-ai)"
    ],
    "Rajat-Resume.pdf": [
        "FieldProof AI: multi-tenant platform where Gemini video understanding audits technician job videos with human review and an async PostgreSQL queue with retries (github.com/rajatmurhe/fieldproof-ai)",
        "NeuroAI: explainable clinical diagnostic platform predicting Alzheimer's stages with Random Forest/XGBoost (85.23% accuracy) and SHAP feature attributions (github.com/rajatmurhe/NeuroAI-Diagnostic-Platform | neuroai-diagnostic-platform.onrender.com)",
        "SentinelAI: adaptive insider threat detection using Isolation Forest and One-Class SVM with Tree SHAP explanations (github.com/rajatmurhe/Sentinel-AI | sentinel-ai-czmu.onrender.com)",
        "CreditX: credit risk classifier evaluated on 31,711 rows reaching 78.62% accuracy and 74.26% Macro F1 (github.com/rajatmurhe/CrediX-Explainable-Credit-Intelligence | credix.streamlit.app)"
    ],
    "Rajat-CV.pdf": [
        "ContractIQ: AI contract review assistant where you upload contracts, ask questions in plain language, and see the exact verbatim source quote behind each answer (github.com/rajatmurhe/contractiq | contractiq-frontend-2e3u.onrender.com)",
        "AI Job Assistant: resume and job match tool showing skill fit with evidence, automated n8n workflows, and multi-provider LLM schema validation (github.com/rajatmurhe/ai-job-assistant)",
        "Atlas: commercial analytics workbench with a LangGraph SQL agent over 24k+ PostgreSQL records, achieving 1.25% forecast MAPE (github.com/rajatmurhe/atlas-commercial-intelligence)",
        "ClinicVoice AI: voice receptionist with LangGraph and MCP tools that answers patient queries, books real appointments & enforces safety guardrails (github.com/rajatmurhe/clinicvoice-ai)"
    ],
    "Rajat-Murhe-Resume.pdf": [
        "SentinelAI: insider threat detection using Isolation Forest and One-Class SVM with Tree SHAP to explain every flag, tested with attack simulations (github.com/rajatmurhe/Sentinel-AI | sentinel-ai-czmu.onrender.com)",
        "NeuroAI: clinical diagnostic platform predicting Alzheimer's stages using Random Forest/XGBoost (85.23% accuracy) and fine-tuned BERT with SHAP explanations (github.com/rajatmurhe/NeuroAI-Diagnostic-Platform | neuroai-diagnostic-platform.onrender.com)",
        "CreditX: credit risk classification model evaluated on 31,711 rows reaching 78.62% accuracy and 74.26% Macro F1 (github.com/rajatmurhe/CrediX-Explainable-Credit-Intelligence | credix.streamlit.app)",
        "FieldProof AI: multi-tenant platform where Gemini audits technician job videos with human review and an async PostgreSQL job queue with retries (github.com/rajatmurhe/fieldproof-ai)"
    ],
    "Rajat-Murhe-CV.pdf": [
        "ClinicVoice AI: voice receptionist for clinics booking appointments on Google Calendar with LangGraph, MCP tools, 4 safety layers and red-team CI evals (github.com/rajatmurhe/clinicvoice-ai)",
        "ContractIQ: AI contract review web app where users ask questions and see the exact verbatim source quote behind each answer (github.com/rajatmurhe/contractiq | contractiq-frontend-2e3u.onrender.com)",
        "AI Job Assistant: resume and job match tool showing skill fit with evidence, drafting materials, and automating with n8n workflows (github.com/rajatmurhe/ai-job-assistant)",
        "FieldProof AI: multi-tenant platform where Gemini checks technician job videos against checklists with human review & async PostgreSQL queue (github.com/rajatmurhe/fieldproof-ai)"
    ]
}



def get_resume_for_role(role, base_dir=BASE_DIR):
    filename = get_resume_filename_for_role(role)
    candidates = [
        os.path.join(base_dir, filename),
        os.path.join(base_dir, "resumes", filename),
        os.path.join(base_dir, "Rajat_Murhe_Resume.pdf")
    ]
    for c in candidates:
        if os.path.isfile(c):
            return os.path.basename(c)
    return "Rajat_Murhe_Resume.pdf"


@app.post("/api/leads/preview")
def preview_lead_email(lead: Dict[str, Any]):
    comp = lead.get("company", "Company")
    raw_name = lead.get("contact_name", "Hiring Team").strip()
    role = lead.get("target_role", "AI Engineering Intern").strip()
    em = lead.get("email", "").strip()
    hook = lead.get("personalized_hook", "").strip()

    if any(term in raw_name.lower() for term in ["team", "inbox", "support", "contact", "not established"]):
        name = "Hiring Team"
    else:
        name = raw_name.split()[0].strip() if raw_name else "Hiring Team"

    subject = f"Application: {role} Opportunities at {comp} - Rajat Murhe"

    if not hook:
        hook = f"I've been following what {comp} is building in applied AI and tech innovation."

    resume_name = get_resume_filename_for_role(role)
    projects = RESUME_PROJECTS.get(resume_name, RESUME_PROJECTS["Rajat-Murhe-CV.pdf"])
    projects_formatted = "\n".join(f"{i+1}. {p}" for i, p in enumerate(projects[:3]))

    body = f"""Hi {name},

I'm Rajat Murhe, a final year CS student (AI and ML) at VIT Chennai, based in Pune. I'm writing to apply for internship or entry level opportunities at {comp}, especially for the {role} role.

{hook}

A few projects from my resume:
{projects_formatted}

I have also completed three internships across AI engineering, multimodal workflows, and platform development on live products.

My resume ({resume_name}) is attached for your reference. If there is an opening, or someone else I should speak to, I would be grateful for your guidance. I can start right away and learn fast.

Thank you for your time.

Best regards,
Rajat Murhe
+91 7507661881
linkedin.com/in/rajat-murhe | github.com/rajatmurhe"""

    return {
        "subject": subject,
        "recipient": em,
        "name": name,
        "body": body,
        "attachment": resume_name
    }


@app.delete("/api/leads/{email}")
def delete_lead(email: str):
    em = email.strip().lower()
    if not os.path.isfile(QUEUE_FILE):
        raise HTTPException(status_code=404, detail="Queue file not found.")

    try:
        df = pd.read_csv(QUEUE_FILE)
        initial_len = len(df)
        df = df[df["Email"].str.lower().str.strip() != em]
        if len(df) == initial_len:
            raise HTTPException(status_code=404, detail="Lead not found in queue.")
        df.to_csv(QUEUE_FILE, index=False)
        return {"status": "success", "message": f"Lead {em} removed from queue."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resume")
def get_resume_info():
    if not os.path.isfile(RESUME_FILE):
        return {"exists": False}

    size_kb = os.path.getsize(RESUME_FILE) / 1024
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(RESUME_FILE)).strftime("%Y-%m-%d %H:%M:%S")
    with open(RESUME_FILE, "rb") as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()

    return {
        "exists": True,
        "filename": os.path.basename(RESUME_FILE),
        "size_kb": round(size_kb, 1),
        "last_modified": mtime,
        "md5": md5_hash
    }


@app.get("/api/resume/view")
def view_resume():
    if not os.path.isfile(RESUME_FILE):
        raise HTTPException(status_code=404, detail="Resume PDF file missing.")
    return FileResponse(RESUME_FILE, media_type="application/pdf")


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted for resume.")

    # Create backup of current resume
    if os.path.isfile(RESUME_FILE):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(BASE_DIR, f"Rajat_Murhe_Resume_backup_{ts}.pdf")
        shutil.copyfile(RESUME_FILE, backup)

    with open(RESUME_FILE, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return get_resume_info()


@app.get("/api/config")
def get_config_endpoint():
    return load_config()


@app.post("/api/config")
def update_config_endpoint(cfg: Dict[str, Any]):
    save_config(cfg)
    return {"status": "success", "config": cfg}


@app.post("/api/outreach/start")
def start_outreach():
    if is_outreach_running():
        return {"status": "already_running", "message": "Outreach process is already executing!"}

    script_path = os.path.join(BASE_DIR, "daily_outreach_daemon.py")
    python_bin = sys.executable or "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"

    proc = subprocess.Popen(
        [python_bin, script_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    return {"status": "started", "pid": proc.pid}


@app.post("/api/outreach/stop")
def stop_outreach():
    subprocess.run(["pkill", "-f", "daily_outreach_daemon.py"], capture_output=True)
    return {"status": "stopped", "message": "Outreach daemon terminated."}


@app.get("/api/logs")
def get_logs():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(LOGS_DIR, f"outreach_{today_str}.log")
    lines = []
    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    return {"lines": [l.strip() for l in lines[-150:]], "date": today_str}


@app.post("/api/daemon/toggle")
def toggle_daemon(action: str = Form(...)):
    user_plist = os.path.expanduser(f"~/Library/LaunchAgents/{PLIST_NAME}")
    src_plist = os.path.join(BASE_DIR, PLIST_NAME)

    if action == "install":
        os.makedirs(os.path.expanduser("~/Library/LaunchAgents"), exist_ok=True)
        shutil.copyfile(src_plist, user_plist)
        subprocess.run(["launchctl", "unload", user_plist], capture_output=True)
        subprocess.run(["launchctl", "load", user_plist], capture_output=True)
        return {"status": "active", "scheduled": True}
    else:
        subprocess.run(["launchctl", "unload", user_plist], capture_output=True)
        if os.path.exists(user_plist):
            os.remove(user_plist)
        return {"status": "inactive", "scheduled": False}


# Mount Static Files at Root
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


def main():
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=5050, reload=False, log_level="info")


if __name__ == "__main__":
    main()
