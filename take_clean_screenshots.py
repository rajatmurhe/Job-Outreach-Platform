import os
import time
from playwright.sync_api import sync_playwright

DOCS_DIR = os.path.abspath("docs/screenshots")
os.makedirs(DOCS_DIR, exist_ok=True)
BRAVE_BIN = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=BRAVE_BIN,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 920},
            device_scale_factor=2
        )
        page = context.new_page()
        
        print("Navigating to http://localhost:5050...")
        page.goto("http://localhost:5050", wait_until="networkidle")
        time.sleep(2)

        # 1. Dashboard Overview
        print("Capturing dashboard-overview.png...")
        page.screenshot(path=os.path.join(DOCS_DIR, "dashboard-overview.png"))
        print("✅ Captured dashboard-overview.png")

        # 2. Scroll to Leads Table
        print("Capturing leads-priority-queue.png...")
        page.evaluate("window.scrollTo(0, 420);")
        time.sleep(1)
        page.screenshot(path=os.path.join(DOCS_DIR, "leads-priority-queue.png"))
        print("✅ Captured leads-priority-queue.png")

        # 3. Open Preview Modal for first lead (SirionLabs)
        print("Opening Email Preview modal via table button...")
        btn = page.locator("button[onclick*='previewEmail']").first
        if btn.count() > 0:
            btn.click()
            time.sleep(2.0)
            print("Capturing email-preview-modal.png...")
            page.screenshot(path=os.path.join(DOCS_DIR, "email-preview-modal.png"))
            print("✅ Captured email-preview-modal.png")
            
            # Close modal
            page.evaluate("closeEmailPreview();")
            time.sleep(0.8)

        # 4. Scroll to Resume Live Management Tab
        print("Switching to Resumes management section...")
        page.evaluate("window.scrollTo(0, 0);")
        time.sleep(1.0)
        page.screenshot(path=os.path.join(DOCS_DIR, "system-telemetry.png"))
        print("✅ Captured system-telemetry.png")

        browser.close()
        print("🎉 All screenshots captured successfully!")

if __name__ == "__main__":
    capture()
