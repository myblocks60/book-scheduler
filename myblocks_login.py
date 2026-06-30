import asyncio
import logging
from playwright.async_api import async_playwright, Page

# Target URLs
LOGIN_URL = "https://myblocks.in/login"
QA_APP_URL = "https://myblocks.in/businessuserhome"

# Credentials
USERNAME = "test11"
PASSWORD = "test11"

async def login_to_myblocks(page: Page, username=USERNAME, password=PASSWORD):
    """
    Performs the login flow on the given Playwright Page.
    """
    logging.info(f"Navigating to {LOGIN_URL}...")
    await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    
    # Enter Username
    logging.info("Entering username...")
    await page.wait_for_selector("#username", state="visible", timeout=15000)
    await page.fill("#username", username)
    
    # Enter Password
    logging.info("Entering password...")
    await page.wait_for_selector("#password", state="visible", timeout=15000)
    await page.fill("#password", password)
    
    # Select User Type
    logging.info("Selecting user type...")
    await page.wait_for_selector("#userType", state="visible", timeout=15000)
    await page.select_option("#userType", value="BUSINESSAPP")
    
    # Click Login
    logging.info("Clicking login button...")
    await page.wait_for_selector("#login-button", state="visible", timeout=15000)
    await page.click("#login-button")
    
    # Wait for login to process (usually redirects to QA_APP_URL)
    logging.info("Waiting for login redirect...")
    try:
        await page.wait_for_url("**/businessuserhome", timeout=30000)
        logging.info("Redirected to business user home successfully.")
    except Exception as e:
        logging.warning(f"Did not detect redirect to businessuserhome, checking current URL: {page.url}")

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await login_to_myblocks(page)
            print(f"Opening QA App URL: {QA_APP_URL}...")
            await page.goto(QA_APP_URL, wait_until="domcontentloaded")
            print("Successfully opened the QA App URL. Keeping browser open for 10 seconds...")
            await page.wait_for_timeout(10000)
        finally:
            print("Closing browser.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
