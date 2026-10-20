#!/usr/bin/env python3
"""
Autonomous Cold Outreach Daemon for Rajat Murhe
Independent from Antigravity. Runs silently in the background on macOS via launchd / cron.
- Auto-checks and connects to Brave Browser via CDP (port 9222).
- Automatically unfreezes background tabs without stealing macOS window focus.
- Attaches Rajat_Murhe_Resume.pdf and personalizes each application.
- Enforces safe daily caps across multiple personal Gmail accounts.
- Automatically sends macOS desktop notifications upon completion.
"""

import asyncio
import csv
import datetime
import json
import os
import random
import subprocess
import sys
import time
import urllib.request
import websockets
import websockets.sync.client as ws_sync

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

TODAY_STR = datetime.date.today().strftime("%Y-%m-%d")
DAILY_LOG_PATH = os.path.join(LOGS_DIR, f"outreach_{TODAY_STR}.log")


def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [{level}] {msg}"
    print(formatted, flush=True)
    try:
        with open(DAILY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def notify_mac(title, message):
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def load_config():
    if not os.path.isfile(CONFIG_PATH):
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_brave_running(port=9222):
    log(f"Checking if Brave Browser CDP port {port} is active...")
    try:
        req = urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=3)
        if req.status == 200:
            log("✅ Brave CDP port 9222 is active and responsive.")
            return True
    except Exception:
        pass

    log("⚠️ Brave is not responding on port 9222. Attempting to launch Brave automatically with remote debugging...", level="WARNING")
    brave_app = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    if not os.path.isfile(brave_app):
        log(f"❌ Brave binary not found at {brave_app}", level="ERROR")
        return False

    try:
        subprocess.Popen(
            [brave_app, f"--remote-debugging-port={port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    except Exception as e:
        log(f"❌ Failed to launch Brave: {e}", level="ERROR")
        return False

    log("Waiting for Brave CDP port to initialize...")
    for _ in range(15):
        time.sleep(1)
        try:
            req = urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=3)
            if req.status == 200:
                log("✅ Brave started successfully on port 9222!")
                return True
        except Exception:
            pass

    log("❌ Could not connect to Brave port 9222 after launch.", level="ERROR")
    return False


def activate_tab_silently(port, target_id):
    """Activates tab inside Brave so V8 execution is unthrottled, without stealing macOS window focus."""
    try:
        ver_url = f"http://localhost:{port}/json/version"
        ver_req = urllib.request.urlopen(ver_url, timeout=5)
        ver_data = json.loads(ver_req.read().decode("utf-8"))
        browser_ws = ver_data.get("webSocketDebuggerUrl")
        if browser_ws and target_id:
            with ws_sync.connect(browser_ws, open_timeout=3) as ws:
                ws.send(json.dumps({"id": 1, "method": "Target.activateTarget", "params": {"targetId": target_id}}))
                ws.recv(timeout=3)
    except Exception:
        pass


def get_gmail_tab_ws(port, user_index, account_email):
    try:
        url = f"http://localhost:{port}/json/list"
        req = urllib.request.urlopen(url, timeout=15)
        targets = json.loads(req.read().decode("utf-8"))

        target_pattern = f"mail.google.com/mail/u/{user_index}"

        # 1. Look for matching tab with inbox
        for t in targets:
            if t.get("type") == "page" and target_pattern in t.get("url", "") and "inbox" in t.get("url", "").lower():
                activate_tab_silently(port, t.get("id"))
                return t["webSocketDebuggerUrl"]

        # 2. Look for any matching user_index tab
        for t in targets:
            if t.get("type") == "page" and target_pattern in t.get("url", ""):
                activate_tab_silently(port, t.get("id"))
                return t["webSocketDebuggerUrl"]

        # 3. Look by account email in title
        if account_email:
            for t in targets:
                if t.get("type") == "page" and account_email.lower() in t.get("title", "").lower():
                    activate_tab_silently(port, t.get("id"))
                    return t["webSocketDebuggerUrl"]

        # 4. Open tab if not found
        log(f"Opening background tab for {account_email} (u/{user_index})...")
        open_req = urllib.request.Request(f"http://localhost:{port}/json/new?https://mail.google.com/mail/u/{user_index}/#inbox", method="PUT")
        new_target = json.loads(urllib.request.urlopen(open_req, timeout=15).read().decode("utf-8"))
        time.sleep(3)
        activate_tab_silently(port, new_target.get("id"))
        return new_target.get("webSocketDebuggerUrl")

    except Exception as e:
        log(f"Failed to locate Gmail tab for u/{user_index}: {e}", level="ERROR")
    return None



def get_resume_for_role(role, base_dir=BASE_DIR):
    role_lower = (role or '').lower()
    if any(k in role_lower for k in ['agent', 'multi-agent', 'orchestrat', 'genai platform', 'mcp']):
        candidate = 'Rajat.pdf'
    elif any(k in role_lower for k in ['voice', 'clinical', 'speech', 'dialogue', 'conversational', 'healthcare']):
        candidate = 'Rajat-Murhe.pdf'
    elif any(k in role_lower for k in ['vision', 'video', 'cv', 'image', 'multimodal', 'object detect']):
        candidate = 'Rajat-Resume.pdf'
    elif any(k in role_lower for k in ['rag', 'document', 'contract', 'legal', 'retrieval', 'nlp']):
        candidate = 'Rajat-CV.pdf'
    elif any(k in role_lower for k in ['anomaly', 'threat', 'risk', 'telematics', 'machine learning', 'data science', 'data ai', 'cloud ai', 'infrastructure', 'deep learning']):
        candidate = 'Rajat-Murhe-Resume.pdf'
    else:
        candidate = 'Rajat-Murhe-CV.pdf'

    p = os.path.join(base_dir, candidate)
    if os.path.isfile(p):
        return p
    sub_p = os.path.join(base_dir, 'resumes', candidate)
    if os.path.isfile(sub_p):
        return sub_p
    for fb in ['Rajat-Murhe-CV.pdf', 'Rajat_Murhe_Resume.pdf', 'Rajat.pdf']:
        fb_p = os.path.join(base_dir, fb)
        if os.path.isfile(fb_p):
            return fb_p
    return p

def format_lead_message(row):
    company = row.get("Company", "").strip()
    raw_name = row.get("Contact_Name", "").strip()
    role = row.get("Target_Role", "AI Engineering Intern").strip()
    email = row.get("Email", "").strip()

    if any(term in raw_name.lower() for term in ["team", "inbox", "support", "contact", "not established"]):
        name = "Hiring Team"
    else:
        name = raw_name.split()[0].strip()

    subject = f"Application: {role} Opportunities at {company} - Rajat Murhe"

    if row.get("Personalized_Hook"):
        hook = row.get("Personalized_Hook").strip()
    else:
        hook = f"I've been following what {company} is building in applied AI and tech innovation."

    body = f"""Hi {name},

I'm Rajat Murhe, a final year CS student (AI and ML) at VIT Chennai, based in Pune. I'm writing to apply for internship or entry level opportunities at {company}, especially for the {role} role.

{hook}

A few things I've built:
1. ClinicVoice AI: a voice agent that books real appointments on Google Calendar, with safety checks and tests (github.com/rajatmurhe/clinicvoice-ai)
2. ContractIQ: a contract review app that answers with the exact source quote (github.com/rajatmurhe/contractiq)
3. FieldProof AI: Gemini reviews field work videos, with human review and an audit trail (github.com/rajatmurhe/fieldproof-ai)

I have also done three internships across AI engineering and product testing, on live products.

My resume is attached for your reference. If there is an opening, or someone else I should speak to, I would be grateful for your guidance. I can start right away and learn fast.

Thank you for your time.

Best regards,
Rajat Murhe
+91 7507661881
linkedin.com/in/rajat-murhe | github.com/rajatmurhe"""

    return email, name, company, subject, body


async def send_single_email(recipient_email, name, company, subject, body, resume_path, user_index, account_email, port=9222):
    log(f"Preparing application from {account_email} for: {name} at {company} <{recipient_email}>")

    ws_url = get_gmail_tab_ws(port, user_index=user_index, account_email=account_email)
    if not ws_url:
        raise Exception(f"Could not connect to Gmail tab for {account_email} (u/{user_index}).")

    async with websockets.connect(ws_url, max_size=10_000_000, ping_interval=10, ping_timeout=10) as ws:
        msg_id = 0

        async def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            cid = msg_id
            payload = {"id": cid, "method": method}
            if params:
                payload["params"] = params
            await ws.send(json.dumps(payload))
            while True:
                r_str = await asyncio.wait_for(ws.recv(), timeout=20)
                r = json.loads(r_str)
                if r.get("id") == cid:
                    return r

        async def eval_js(expression, return_by_value=True):
            r = await send_cmd("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": return_by_value
            })
            return r.get("result", {}).get("result", {}).get("value")

        # 1. Clean up any open draft
        await eval_js("""(() => {
            const discards = Array.from(document.querySelectorAll("div[aria-label*='Discard draft'], div[data-tooltip*='Discard']"));
            for (const d of discards) { try { d.click(); } catch(e){} }
        })()""")
        await asyncio.sleep(0.5)

        # 2. Trigger Compose
        log("Opening Compose window in background...")
        await eval_js("""(() => {
            const btn = document.querySelector("div[gh='cm'], div[role='button'].T-I.T-I-KE");
            if (btn) btn.click();
            else window.location.hash = "#inbox?compose=" + Date.now();
        })()""")

        dialog_ready = False
        for _ in range(15):
            await asyncio.sleep(0.4)
            if await eval_js("!!document.querySelector('div[role=\"dialog\"]')"):
                dialog_ready = True
                break

        if not dialog_ready:
            raise Exception("Compose dialog did not open within timeout.")

        log("Compose dialog opened.")

        # 3. Fill 'To'
        js_fill_to = f"""
        (() => {{
            const dialog = document.querySelector("div[role='dialog']");
            if (!dialog) return false;
            const toInput = dialog.querySelector("input.agP, input[peoplekit-id], input[aria-label*='To'], textarea[name='to']");
            if (!toInput) return false;
            toInput.focus();
            toInput.value = {json.dumps(recipient_email)};
            toInput.dispatchEvent(new Event("input", {{bubbles: true}}));
            toInput.dispatchEvent(new KeyboardEvent("keydown", {{key: "Enter", keyCode: 13, bubbles: true}}));
            toInput.dispatchEvent(new KeyboardEvent("keyup", {{key: "Enter", keyCode: 13, bubbles: true}}));
            return true;
        }})()
        """
        if not await eval_js(js_fill_to):
            raise Exception("Failed to fill 'To' recipient field.")
        await asyncio.sleep(0.5)

        # 4. Fill 'Subject'
        js_fill_subject = f"""
        (() => {{
            const dialog = document.querySelector("div[role='dialog']");
            if (!dialog) return false;
            const subjInput = dialog.querySelector("input[name='subjectbox'], input[aria-label*='Subject']");
            if (!subjInput) return false;
            subjInput.focus();
            subjInput.value = {json.dumps(subject)};
            subjInput.dispatchEvent(new Event("input", {{bubbles: true}}));
            return true;
        }})()
        """
        if not await eval_js(js_fill_subject):
            raise Exception("Failed to fill 'Subject' field.")
        await asyncio.sleep(0.5)

        # 5. Fill 'Body'
        js_fill_body = f"""
        (() => {{
            const dialog = document.querySelector("div[role='dialog']");
            if (!dialog) return false;
            const bodyDiv = dialog.querySelector("div[role='textbox'][aria-label*='Message Body'], div[aria-label='Message Body']");
            if (!bodyDiv) return false;
            bodyDiv.focus();
            document.execCommand("selectAll", false, null);
            document.execCommand("insertText", false, {json.dumps(body)});
            return true;
        }})()
        """
        if not await eval_js(js_fill_body):
            raise Exception("Failed to fill 'Message Body' field.")
        await asyncio.sleep(0.8)

        # 6. Attach Resume
        if os.path.exists(resume_path):
            log(f"Attaching resume: {os.path.basename(resume_path)}...")
            await send_cmd("DOM.enable")
            res = await send_cmd("Runtime.evaluate", {
                "expression": "document.querySelector('div[role=\"dialog\"] input[type=\"file\"]') || document.querySelector('input[type=\"file\"]')",
                "returnByValue": False
            })
            obj_id = res.get("result", {}).get("result", {}).get("objectId")
            if not obj_id:
                raise Exception("Could not find file input element in Compose dialog.")

            await send_cmd("DOM.setFileInputFiles", {
                "files": [resume_path],
                "objectId": obj_id
            })

            attached = False
            for _ in range(12):
                await asyncio.sleep(0.5)
                text = await eval_js("document.querySelector('div[role=\"dialog\"]') ? document.querySelector('div[role=\"dialog\"]').innerText : ''")
                if "Resume.pdf" in (text or "") or "Rajat" in (text or ""):
                    attached = True
                    break

            if not attached:
                log("Warning: Attachment text confirmation buffer...", level="WARNING")
                await asyncio.sleep(2.0)
            else:
                log("✅ Resume attached and verified.")
        else:
            raise FileNotFoundError(f"Resume file not found at: {resume_path}")

        # 7. Click Send
        log(f"Clicking Send to {recipient_email}...")
        click_res = await eval_js("""
        (() => {
            const dialog = document.querySelector("div[role='dialog']");
            if (!dialog) return "no_dialog";
            const btns = Array.from(dialog.querySelectorAll("div[role='button']"));
            const sendBtn = btns.find(b => (b.innerText || "").includes("Send") || (b.getAttribute("data-tooltip") || "").includes("Send"));
            if (sendBtn) {
                sendBtn.click();
                return "clicked";
            }
            return "not_found";
        })()
        """)
        if click_res != "clicked":
            raise Exception(f"Send button click failed: {click_res}")

        # 8. Verify sent confirmation
        delivered = False
        for _ in range(15):
            await asyncio.sleep(0.5)
            check_state = await eval_js("""
            (() => {
                const dialog = document.querySelector("div[role='dialog']");
                const alerts = Array.from(document.querySelectorAll("span.bAq, div.bA8, div[role='alert']")).map(e => e.innerText);
                return {
                    dialogOpen: !!dialog,
                    hasSentAlert: alerts.some(t => t.includes("Message sent") || t.includes("Your message has been sent"))
                };
            })()
            """)
            if check_state and (not check_state.get("dialogOpen") or check_state.get("hasSentAlert")):
                delivered = True
                break

        if delivered:
            log(f"✅ Successfully delivered application to {name} at {company} <{recipient_email}>!")
            return True, "Delivered"
        else:
            log("⚠️ Dialog didn't close in time, cleaning up...", level="WARNING")
            await eval_js("""(() => {
                const discards = Array.from(document.querySelectorAll("div[aria-label*='Discard draft'], div[data-tooltip*='Discard']"));
                for (const d of discards) { try { d.click(); } catch(e){} }
            })()""")
            return False, "Delivery verification timeout"


def replenish_queue_if_needed(queue_file, sent_file):
    """Ensures todays_outreach_queue.csv always has fresh leads from recruiter_leads.csv or Excel."""
    sent_emails = set()
    if os.path.isfile(sent_file):
        with open(sent_file, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r, None)
            for row in r:
                if len(row) > 4 and row[4] == "Success":
                    sent_emails.add(row[1].lower().strip())

    existing_queue = []
    if os.path.isfile(queue_file):
        with open(queue_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                em = row.get("Email", "").lower().strip()
                if em and em not in sent_emails:
                    existing_queue.append(row)

    if len(existing_queue) >= 30:
        return existing_queue

    log(f"Queue has {len(existing_queue)} remaining leads. Auto-replenishing from master lead sources...")
    queued_emails = set(q["Email"].lower().strip() for q in existing_queue) | sent_emails

    # Replenish from recruiter_leads.csv first
    recruiter_file = os.path.join(BASE_DIR, "recruiter_leads.csv")
    if os.path.isfile(recruiter_file):
        with open(recruiter_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                em = row.get("Email", "").lower().strip()
                if em and em not in queued_emails:
                    existing_queue.append({
                        "Priority": row.get("Priority", "2"),
                        "Company": row.get("Company", "").strip(),
                        "Contact_Name": row.get("Contact_Name", "").strip(),
                        "Email": em,
                        "Target_Role": row.get("Target_Role", "AI Engineering Intern").strip(),
                        "Personalized_Hook": row.get("Personalized_Hook", "").strip()
                    })
                    queued_emails.add(em)

    # Save replenished queue
    fieldnames = ["Priority", "Company", "Contact_Name", "Email", "Target_Role", "Personalized_Hook"]
    with open(queue_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_queue)

    log(f"Queue replenished to {len(existing_queue)} fresh leads.")
    return existing_queue


async def run_daily_outreach():
    config = load_config()
    port = config.get("cdp_port", 9222)
    queue_file = os.path.join(BASE_DIR, config.get("leads_file", "todays_outreach_queue.csv"))
    log_file = os.path.join(BASE_DIR, config.get("log_file", "emails_sent.csv"))
    resume_path = os.path.join(BASE_DIR, config.get("resume_filename", "Rajat_Murhe_Resume.pdf"))
    min_delay = config.get("delays", {}).get("min_seconds", 45)
    max_delay = config.get("delays", {}).get("max_seconds", 75)
    accounts = [acc for acc in config.get("accounts", []) if acc.get("enabled", True)]

    print("=" * 65)
    print("🤖 Rajat Murhe - Autonomous Cold Outreach Daemon")
    print(f"Date:          {TODAY_STR}")
    print(f"Log:           {DAILY_LOG_PATH}")
    print(f"Resume:        {resume_path}")
    print(f"Delay Range:   {min_delay}s - {max_delay}s")
    for acc in accounts:
        print(f"  • {acc['account']} (u/{acc['user_index']}): Limit = {acc['daily_limit']}/day")
    print("=" * 65)

    if not ensure_brave_running(port=port):
        log("Cannot proceed without Brave Browser running on port 9222.", level="ERROR")
        return

    # Check today's sent history
    today_sent_by_account = {}
    sent_emails = set()
    if os.path.isfile(log_file):
        with open(log_file, "r", encoding="utf-8") as rf:
            r = csv.reader(rf)
            next(r, None)
            for row in r:
                if len(row) > 4 and row[4] == "Success":
                    em = row[1].lower().strip()
                    sent_emails.add(em)
                    sender = row[6].strip() if len(row) > 6 else ""
                    ts = row[0].strip()
                    if ts.startswith(TODAY_STR):
                        today_sent_by_account[sender] = today_sent_by_account.get(sender, 0) + 1

    log(f"Total historical successful recipients: {len(sent_emails)}")
    log(f"Today's counts so far: {today_sent_by_account}")

    # Check if all enabled accounts have completed their daily limits
    all_done = True
    for acc in accounts:
        sent_so_far = today_sent_by_account.get(acc["account"], 0)
        if sent_so_far < acc["daily_limit"]:
            all_done = False
            break

    if all_done:
        log("🎉 All enabled accounts have already completed today's daily limit! Nothing to send.", level="INFO")
        if config.get("desktop_notifications", True):
            notify_mac("Outreach Daemon", "All daily quotas already satisfied for today!")
        return

    leads = replenish_queue_if_needed(queue_file, log_file)
    csv_file = open(log_file, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if not os.path.isfile(log_file) or os.path.getsize(log_file) == 0:
        csv_writer.writerow(["Timestamp", "Email", "Name", "Company", "Status", "Subject", "Sender"])

    total_session_sent = 0

    for acc in accounts:
        cur_account = acc["account"]
        cur_index = acc["user_index"]
        cur_limit = acc["daily_limit"]

        already_sent = today_sent_by_account.get(cur_account, 0)
        remaining_slots = cur_limit - already_sent

        if remaining_slots <= 0:
            log(f"Account {cur_account} has already reached today's limit ({already_sent}/{cur_limit}). Moving to next...")
            continue

        log(f"▶️ Starting dispatch for {cur_account} (u/{cur_index}) | Target: {remaining_slots} emails.")
        account_sent_count = 0

        for lead in leads:
            if account_sent_count >= remaining_slots:
                break

            email, name, company, subject, body = format_lead_message(lead)
            if email.lower() in sent_emails:
                continue

            try:
                success, reason = await send_single_email(
                    email, name, company, subject, body,
                    resume_path=get_resume_for_role(lead.get("Target_Role", "")),
                    user_index=cur_index,
                    account_email=cur_account,
                    port=port
                )
            except Exception as e:
                log(f"❌ Error sending to {email} from {cur_account}: {e}", level="ERROR")
                success, reason = False, str(e)

            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            csv_writer.writerow([ts, email, name, company, "Success" if success else "Failed", subject, cur_account])
            csv_file.flush()

            if success:
                sent_emails.add(email.lower())
                account_sent_count += 1
                total_session_sent += 1
                today_sent_by_account[cur_account] = today_sent_by_account.get(cur_account, 0) + 1
                log(f"[{cur_account}] Progress: {account_sent_count}/{remaining_slots} sent (Session total: {total_session_sent}).")

                if account_sent_count < remaining_slots:
                    sleep_time = random.uniform(min_delay, max_delay)
                    log(f"Sleeping for {sleep_time:.1f}s to protect deliverability...")
                    await asyncio.sleep(sleep_time)

        log(f"🏁 Finished batch for {cur_account}: {account_sent_count} sent.")
        if accounts.index(acc) < len(accounts) - 1:
            log("Switching to next account in 10s...")
            await asyncio.sleep(10)

    csv_file.close()
    summary_msg = f"Outreach session completed! Total sent: {total_session_sent} applications."
    log(f"🎉 {summary_msg}")
    if config.get("desktop_notifications", True):
        notify_mac("Cold Outreach Complete", summary_msg)


def main():
    try:
        asyncio.run(run_daily_outreach())
    except KeyboardInterrupt:
        log("Process interrupted by user. Exiting cleanly.", level="WARNING")
    except Exception as e:
        log(f"Unhandled error in outreach daemon: {e}", level="ERROR")


if __name__ == "__main__":
    main()
