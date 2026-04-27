import asyncio
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

# ----------------------------
# Config
# ----------------------------
URLS = [
    "https://www.nike.com/ro/t/mind-002-shoes-Ivli88gE/HQ4308-001"
]

TARGET_SIZES = ["42.5"]
CHECK_INTERVAL = 180

# Email config
EMAIL_FROM = ""
EMAIL_PASS = ""
EMAIL_TO = ""

# Timezone (EEST / Bucharest)
TIMEZONE = ZoneInfo("Europe/Bucharest")

# ----------------------------
# Logger
# ----------------------------
def log(msg):
    now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} {msg}", flush=True)

# ----------------------------
# Email sender
# ----------------------------
def send_email(message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = "Nike Bot Alert"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.send_message(msg)

        log("📧 Email sent!")

    except Exception as e:
        log(f"❌ Email error: {e}")

# ----------------------------
# Accept cookies
# ----------------------------
async def accept_cookies(page):
    try:
        await page.locator("button:has-text('Accept All')").click(timeout=3000)
        log("✅ Accepted cookies")
        await page.wait_for_timeout(2000)
    except:
        pass

# ----------------------------
# Check Nike
# ----------------------------
async def check_nike(page, url):
    log(f"🔍 Checking: {url}")

    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        await accept_cookies(page)
    except Exception as e:
        log(f"❌ Load error: {e}")
        return []

    found = []

    items = await page.locator(
        '[data-testid="pdp-grid-selector-item"], '
        '[data-testid="pdp-grid-selector-item-selected"]'
    ).all()

    if not items:
        log("🔴 OUT OF STOCK (no sizes)")
        return []

    for item in items:
        try:
            label = await item.locator("label").text_content()

            if not label or not label.startswith("EU"):
                continue

            size = label.replace("EU ", "").strip()

            if size not in TARGET_SIZES:
                continue

            input_el = item.locator("input")
            aria_disabled = await input_el.get_attribute("aria-disabled")

            is_available = aria_disabled != "true"

            log(f"DEBUG → {size} | available={is_available}")

            if is_available:
                found.append(size)

        except:
            continue

    if found:
        log(f"🟢 IN STOCK {found}")
    else:
        log(f"🔴 OUT OF STOCK {TARGET_SIZES}")

    return found

# ----------------------------
# Monitor loop (ALWAYS ALERT)
# ----------------------------
async def monitor():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="/app/profile",
            headless=False
        )

        page = await context.new_page()

        while True:
            try:
                for url in URLS:
                    sizes = await check_nike(page, url)

                    # 🔥 Always alert
                    for size in sizes:
                        msg = f"[{datetime.now(TIMEZONE).strftime('%H:%M:%S')}] Size {size} available!\n{url}"
                        log(f"🚨 ALERT: {msg}")
                        send_email(msg)

                log(f"⏳ Sleeping {CHECK_INTERVAL}s")
                await asyncio.sleep(CHECK_INTERVAL)

            except Exception as e:
                log(f"🔥 Loop error: {e}")
                await asyncio.sleep(10)

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    log("🚀 Starting Nike bot (EEST + ALWAYS ALERT)")
    asyncio.run(monitor())