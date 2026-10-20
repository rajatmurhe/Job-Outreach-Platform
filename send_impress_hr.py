import asyncio
import os
import csv
import datetime
from daily_outreach_daemon import send_single_email

async def main():
    recipient_email = "hr.india@impress.ai"
    name = "India HR Team"
    company = "impress.ai"
    role = "AI Engineering Intern (Dialogue & NLP)"
    subject = f"Application: {role} Opportunities at {company} - Rajat Murhe"

    body = f"""Hi {name},

I'm Rajat Murhe, a final year CS student (AI and ML) at VIT Chennai, based in Pune. I'm writing to apply for internship or entry level opportunities at {company}, especially for the {role} role.

I've been following {company}'s conversational assessment platform, which connects to my experience developing multi-agent conversational systems with LangGraph and semantic search validation pipelines.

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

    resume_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Rajat_Murhe_Resume.pdf")
    account_email = "murherajat1@gmail.com"
    user_index = 7

    print(f"Sending application to {name} <{recipient_email}> from {account_email} (u/{user_index})...")
    success, reason = await send_single_email(
        recipient_email=recipient_email,
        name=name,
        company=company,
        subject=subject,
        body=body,
        resume_path=resume_path,
        user_index=user_index,
        account_email=account_email,
        port=9222
    )

    print(f"Result: success={success}, reason={reason}")

    if success:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = "emails_sent.csv"
        with open(log_file, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([ts, recipient_email, name, company, "Success", subject, account_email])
        print("Logged success in emails_sent.csv")

if __name__ == "__main__":
    asyncio.run(main())
