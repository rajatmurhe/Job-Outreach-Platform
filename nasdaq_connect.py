#!/usr/bin/env python3
"""
LinkedIn Connection Automation for Nasdaq Campus Program - 2027 (R0027122)
Connects to Brave Browser via Chrome DevTools Protocol (CDP) on port 9222.
Dispatches personalized connection notes to Talent Acquisition, Campus Recruiters, and Engineers at Nasdaq.
"""

import csv
import datetime
import os
import random
import sys
import time
from playwright.sync_api import sync_playwright

LOG_FILE = "nasdaq_connections_sent.csv"

# Target recruiters, campus managers, VIT alumni, and engineers at Nasdaq
TARGETS = [
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=campus%20recruiter%20india",
        "name_match": "Syed",
        "name": "Syed Shabuddin",
        "title": "Manager : Talent Acquisition and Campus at Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=talent%20acquisition%20bengaluru",
        "name_match": "Tharun",
        "name": "Tharun S",
        "title": "Talent Acquisition Partner - Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=talent%20acquisition%20bengaluru",
        "name_match": "Chaitra",
        "name": "Chaitra P V",
        "title": "Talent Acquisition Specialist @ NASDAQ"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=talent%20acquisition%20bengaluru",
        "name_match": "Lhakpa",
        "name": "Lhakpa Bhuchung",
        "title": "HR Business Partner @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=vit",
        "name_match": "Ritesh",
        "name": "Ritesh Pokarne",
        "title": "Senior Software Developer (AI) @ Nasdaq Fintech (VIT Alumni)"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=vit",
        "name_match": "Ankit",
        "name": "Ankit Gupta",
        "title": "Cloud Operations Intern @ Nasdaq (VIT)"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=campus%20bengaluru",
        "name_match": "Raunak",
        "name": "Raunak Sarada",
        "title": "Engineering @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=university",
        "name_match": "Creflo",
        "name": "Creflo Coelho",
        "title": "Engineering @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=software%20engineer%20bengaluru",
        "name_match": "Sneha",
        "name": "Sneha Trivedi",
        "title": "Software Developer at Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=software%20engineer%20bengaluru",
        "name_match": "Sourav",
        "name": "Sourav Sinha",
        "title": "Software Engineering @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=recruiter%20india",
        "name_match": "Suhas",
        "name": "Suhas Ramamurthy",
        "title": "Director - Quality Assurance at Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=intern%20bengaluru",
        "name_match": "Vignesh",
        "name": "Vignesh Madan",
        "title": "Analyst - Software Engineering @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=intern%20bengaluru",
        "name_match": "Devangana",
        "name": "Devangana Nair",
        "title": "Data Engineering at Nasdaq | AI/ML Graduate"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=intern%20bengaluru",
        "name_match": "Shruti",
        "name": "Shruti Singhal",
        "title": "Senior Analyst | Nasdaq | Market Operations"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=intern%20bengaluru",
        "name_match": "Subhankit",
        "name": "Subhankit Prusti",
        "title": "Cloud Engineer @ Nasdaq | AWS Certified | ML/DL"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=intern%20bengaluru",
        "name_match": "Aniket",
        "name": "Aniket Arya",
        "title": "Data Science Intern @ NASDAQ | Generative AI · NLP"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=chennai",
        "name_match": "Goutham",
        "name": "Goutham M",
        "title": "Axiom Analyst @ Nasdaq Chennai"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=chennai",
        "name_match": "Dhilip",
        "name": "Dhilip Kumar Murali",
        "title": "DevOps Application Support Engineer at Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=recruiter%20india",
        "name_match": "BHOGI",
        "name": "BHOGI ROHIT",
        "title": "Data Analyst @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=software%20bengaluru",
        "name_match": "Gowrish",
        "name": "Gowrish Kotari",
        "title": "Senior Software Developer @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=software%20bengaluru",
        "name_match": "Mitesh",
        "name": "Mitesh Sah",
        "title": "Sr. Platform Engineer (DevSecOps) @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=software%20bengaluru",
        "name_match": "Ankur",
        "name": "Ankur Yaduvanshi",
        "title": "Senior UI Engineer @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=university",
        "name_match": "Farukh",
        "name": "Farukh Shaikh",
        "title": "Java & Calypso Developer @ Nasdaq"
    },
    {
        "search_url": "https://www.linkedin.com/company/nasdaq/people/?keywords=university",
        "name_match": "AKSHAY",
        "name": "Akshay Shilawane",
        "title": "Java & SpringBoot Developer @ Nasdaq"
    }
]


def log(msg, level="INFO"):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def get_personalized_note(first_name):
    # If name is all caps or formatted, clean it
    fn = first_name.title()
    if fn.upper() == "BHOGI":
        fn = "Rohit"
    note = (
        f"Hi {fn}, I’m a final year CSE student at VIT Chennai, interested in "
        f"Nasdaq Campus Program - 2027 - R0027122 . I’d love to connect and hear any "
        f"advice you may have regarding the opportunity"
    )
    return note.strip()


def send_invite_for_target(page, target):
    first_name = target["name"].split()[0]
    note = get_personalized_note(first_name)

    log(f"--- Processing Target: {target['name']} ({target['title']}) ---")
    
    # Dismiss any leftover dialogs
    try:
        dismiss = page.locator("div.send-invite button[aria-label='Dismiss'], button[aria-label='Dismiss']").first
        if dismiss.count() > 0 and dismiss.is_visible():
            dismiss.click()
            time.sleep(1)
    except Exception:
        pass

    page.goto(target["search_url"], wait_until="domcontentloaded", timeout=45000)
    time.sleep(3)
    page.evaluate("window.scrollBy(0, 600)")
    time.sleep(1.5)

    cards = page.locator("li.org-people-profiles-module__profile-item, div.org-people-profile-card, .artdeco-card")
    matched_card = None

    for i in range(cards.count()):
        c = cards.nth(i)
        t = c.locator(".org-people-profile-card__profile-title, .artdeco-entity-lockup__title, [class*='profile-title']").first
        if t.count() > 0 and target["name_match"].lower() in t.inner_text().lower():
            matched_card = c
            break

    if not matched_card:
        log(f"❌ Could not find card for {target['name']} on page.", level="WARNING")
        return False, "Profile card not found"

    connect_btn = matched_card.locator("button:has-text('Connect'), button[aria-label*='Invite'][aria-label*='to connect'], button[aria-label^='Connect with']").first
    if connect_btn.count() == 0 or not connect_btn.is_visible():
        log(f"❌ No visible Connect button for {target['name']}.", level="WARNING")
        return False, "No direct Connect button"

    try:
        matched_card.scroll_into_view_if_needed()
        time.sleep(1)
        connect_btn.click()
        log(f"Clicked 'Connect' for {target['name']}.")
        time.sleep(1.5)

        modal = page.locator("div.send-invite, div[aria-labelledby='send-invite-modal'], .artdeco-modal:not(.msg-convo-wrapper)").first
        modal.wait_for(state="visible", timeout=8000)
        time.sleep(1)
        modal_text = modal.inner_text().lower()

        if "weekly invitation limit" in modal_text or "reached the limit" in modal_text:
            log("🚨 LinkedIn invitation limit reached!", level="ERROR")
            dismiss = modal.locator("button[aria-label='Dismiss'], button:has-text('Got it')").first
            if dismiss.count() > 0:
                dismiss.click()
            return False, "LIMIT_REACHED"

        if "how do you know" in modal_text:
            log("Prompted with 'How do you know this person?'. Dismissing.")
            dismiss = modal.locator("button[aria-label='Dismiss'], button:has-text('Cancel')").first
            if dismiss.count() > 0:
                dismiss.click()
            return False, "Verification required"

        add_note_btn = modal.locator("button:has-text('Add a note'), button[aria-label='Add a note']").first
        if add_note_btn.count() > 0 and add_note_btn.is_visible():
            add_note_btn.click()
            time.sleep(1)

        textarea = modal.locator("textarea#custom-message, textarea[name='message'], textarea").first
        try:
            textarea.wait_for(state="visible", timeout=3000)
        except Exception:
            pass
        if textarea.count() == 0 or not textarea.is_visible():
            log("Textarea for note not visible.")
            dismiss = modal.locator("button[aria-label='Dismiss'], button:has-text('Cancel')").first
            if dismiss.count() > 0:
                dismiss.click()
            return False, "Textarea missing"

        max_len = 300
        attr_max = textarea.get_attribute("maxlength")
        if attr_max and attr_max.isdigit():
            max_len = int(attr_max)

        final_note = note if len(note) <= max_len else note[:max_len]

        log(f"Entering note ({len(final_note)} chars): '{final_note}'")
        textarea.fill(final_note)
        time.sleep(1)

        send_btn = modal.locator("button[aria-label='Send invitation'], button:has-text('Send'), button[aria-label='Send now']").first
        if send_btn.count() == 0 or not send_btn.is_visible():
            log("Send button disabled or not visible.")
            dismiss = modal.locator("button[aria-label='Dismiss'], button:has-text('Cancel')").first
            if dismiss.count() > 0:
                dismiss.click()
            return False, "Send button disabled"

        send_btn.click()
        time.sleep(2)
        log(f"✅ Successfully sent connection invitation to {target['name']} with custom note!")
        return True, "Delivered"

    except Exception as e:
        log(f"Error connecting with {target['name']}: {e}", level="ERROR")
        try:
            dismiss = page.locator("div.send-invite button[aria-label='Dismiss'], button[aria-label='Dismiss'], button:has-text('Cancel')").first
            if dismiss.count() > 0 and dismiss.is_visible():
                dismiss.click()
        except Exception:
            pass
        return False, str(e)


def main():
    print("=" * 65)
    print("🚀 Nasdaq Campus Program - 2027 (R0027122) - LinkedIn Outreach")
    print(f"Targets: {len(TARGETS)} verified campus recruiters, talent partners & engineers")
    print("=" * 65)

    already_sent = set()
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r, None)
            for row in r:
                if len(row) > 2 and row[2] == "Success":
                    already_sent.add(row[1].strip())

    csv_file = open(LOG_FILE, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if not os.path.isfile(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        csv_writer.writerow(["Timestamp", "Name", "Status", "Details", "Note"])

    successful = 0

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = next((pg for pg in context.pages if "linkedin.com" in pg.url), None)
        if not page:
            page = context.new_page()

        for target in TARGETS:
            if target["name"] in already_sent:
                log(f"Skipping {target['name']} (already sent previously).")
                continue

            success, reason = send_invite_for_target(page, target)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            first_name = target["name"].split()[0]
            note = get_personalized_note(first_name)
            csv_writer.writerow([ts, target["name"], "Success" if success else "Failed", reason, note])
            csv_file.flush()

            if reason == "LIMIT_REACHED":
                log("Halting run due to LinkedIn limit.", level="WARNING")
                break

            if success:
                successful += 1
                already_sent.add(target["name"])
                delay = random.uniform(22, 35)
                log(f"Progress: {successful} sent. Sleeping for {delay:.1f}s to protect account...")
                time.sleep(delay)

    csv_file.close()
    print("=" * 65)
    print(f"🎉 Nasdaq outreach complete! Successfully sent: {successful} invitations.")
    print(f"Logged to '{LOG_FILE}'.")
    print("=" * 65)


if __name__ == "__main__":
    main()
