import os
import re
import asyncio
import pandas as pd
import logging
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError
from datetime import datetime


# --- CONFIGURATION ---
CSV_FILE = "careers_12000_clean.csv"
PROMPT_FILE = "C index book prompt.txt"
DOWNLOAD_DIR = Path("downloads")
PROGRESS_FILE = "processed_tracker.txt"
LOG_FILE = "automation_status.log"

RAG_CONNECTED = False

# URLs
CINDEX_URL = "http://192.168.1.57:5635/"
RAG_URL = "https://myblocks.in/ragnew"

# Setup Directories and Logging
DOWNLOAD_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# --- UTILS ---
def get_safe_filename(name):
    """Removes invalid characters for file saving."""
    return re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip() + ".pdf"

def load_processed_careers():
    """Reads the tracker file so we don't repeat work."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def mark_done(career):
    """Saves the completed career to the tracker."""
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{career}\n")


# --- SELECTOR HELPER ---
async def fill_with_fallback(page, selectors, value, timeout=5000):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            await locator.first.wait_for(state="visible", timeout=timeout)
            await locator.first.fill(value)
            return
        except Exception:
            continue
    raise Exception(f"All selectors failed for value: {value}")

async def click_with_fallback(page, selectors, timeout=5000):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            await locator.first.wait_for(state="visible", timeout=timeout)
            await locator.first.click()
            return
        except Exception:
            continue
    raise Exception(f"All click selectors failed: {selectors}")


async def wait_for_generation_complete(page):
    tasks = [
        # 1. Button becomes enabled again
        page.wait_for_selector(
            "button.primary-button:not([disabled])",
            timeout=180000
        ),

        # 2. Success message appears
        page.wait_for_selector(
            ".success-box",
            timeout=180000
        ),

        # 3. Download button appears
        page.wait_for_selector(
            "text=Download",
            timeout=180000
        )
    ]

    done, pending = await asyncio.wait(
        [asyncio.create_task(t) for t in tasks],
        return_when=asyncio.FIRST_COMPLETED
    )

    # Cancel remaining tasks
    for task in pending:
        task.cancel()

    return done

# --- CORE LOGIC ---
async def process_career(context, career, base_prompt, connect_rag=False):
    # Each career gets a fresh page to prevent memory issues
    page = await context.new_page()
    # Increase patience: 90 seconds for all actions
    page.set_default_timeout(90000) 
    
    try:
        # 1. PREPARE DATA
        topic = f"Inside the Real Life & Career Success Path of a {career}"
        subtopic = "Daily Responsibilities, Work Environment, Career Entry Path, Job Landing Strategy, Challenges, Lifestyle & Industry Reality"
        final_prompt = base_prompt.replace("{{career_name}}", career)

        # 2. GENERATE PDF
        logging.info(f"Step 1: Generating PDF for {career}")
        # Use 'domcontentloaded' to avoid waiting for slow external ads/trackers
        await page.goto(CINDEX_URL, wait_until="domcontentloaded", timeout=90000)
        
          # Topic (INPUT)
        await fill_with_fallback(
            page,
            [
                'input[placeholder="e.g. Hospitality, IT, Healthcare"]',
                'xpath=//*[@id="root"]/div/div/div[2]/div[1]/input',
                'xpath=/html/body/div/div/div/div[2]/div[1]/input'
            ],
            subtopic
        )

        # Subtopic (Textarea 1)
        await fill_with_fallback(
            page,
            [
                'input[placeholder="e.g. Customer Service Excellence"]',
                'xpath=//*[@id="root"]/div/div/div[2]/div[2]/input',
                'xpath=/html/body/div/div/div/div[2]/div[2]/input'
            ],
            topic
        )

        # Final Prompt (Textarea 2)
        await fill_with_fallback(
            page,
            [
                'textarea[placeholder="Describe what the book should focus on..."]',
                'xpath=//*[@id="root"]/div/div/div[2]/div[3]/div/textarea',
                'xpath=/html/body/div/div/div/div[2]/div[3]/div/textarea'
            ],
            final_prompt
        )
        await click_with_fallback(
            page,
            [
                "role=button[name='Generate Book']",
                "text=Generate Book",
                "button.primary-button",
                "xpath=//button[contains(., 'Generate Book')]",
                'xpath=//*[@id="root"]/div/div/div[3]/button[2]',
                "xpath=/html/body/div/div/div/div[3]/button[2]"
            ]
        )

        await wait_for_generation_complete(page)

        # Detect final state
        if await page.locator("text=Download").is_visible():
            logging.info("Download ready")

        elif await page.locator(".success-box").is_visible():
            logging.info("Success message detected — waiting for download button")
            # Sometimes UI shows success first, then download
            await page.wait_for_selector("text=Download", timeout=60000)

        elif await page.locator("button.primary-button:not([disabled])").is_visible():
            raise Exception("Generation likely failed — button reset without success/download")

        else:
            raise Exception("Unknown state after generation")

        

        if connect_rag:

            await page.wait_for_selector("text=Connect to RAG Server", timeout=60000)

            # Click it
            await click_with_fallback(
                page,
                [
                    "role=button[name='Connect to RAG Server']",
                    "text=Connect to RAG Server",
                    "button.rag-button",
                    "xpath=//button[contains(., 'Connect to RAG Server')]"
                ]
            )

            await page.wait_for_timeout(1000)


            logging.info("Clicked Connect to RAG Server")

            # Wait for modal input to appear FIRST
            await page.wait_for_selector(
                'input[placeholder="e.g. 1559"]',
                state="visible",
                timeout=15000
            )

            

            await fill_with_fallback(
                page,
                [
                    'input[placeholder="e.g. 1559"]',
                    'xpath=//input[@placeholder="e.g. 1559"]'
                ],
                "1559"
            )

            await click_with_fallback(
                page,
                [
                    "role=button[name='Connect']",
                    "text=Connect",
                    "button:has-text('Connect')",
                    "xpath=//button[.//text()[contains(., 'Connect')]]"
                ]
            )

            await page.wait_for_function("""
                () => !document.querySelector('input[placeholder="e.g. 1559"]')
            """, timeout=20000)

        

        # Wait for select to exist AND be stable
        select_locator = page.locator('xpath=//*[@id="root"]/div/div/div[3]/div/select')

        await select_locator.wait_for(state="attached", timeout=20000)
        await select_locator.wait_for(state="visible", timeout=20000)
                # Ensure options are actually loaded (important)
        # CRITICAL: wait for options to be populated (not just present)
        await page.wait_for_function("""
        () => {
            const sel = document.querySelector("select");
            if (!sel) return false;

            // ensure real options exist (not placeholder)
            return sel.options.length > 1 &&
                Array.from(sel.options).some(o => o.text.includes("Career"));
        }
        """, timeout=30000)

        await page.select_option("select", label="Health Care")
        logging.info("Selected Health Care category")

        await click_with_fallback(
            page,
            [
                "role=button[name='📚 Add to RAG']",
                "text=Add to RAG",
                "button:has-text('Add to RAG')",
                "xpath=//button[contains(., 'Add to RAG')]"
            ]
        )

        logging.info("Clicked Add to RAG")

        # STEP 1: Wait for loading state (button becomes disabled or shows spinner)
        await page.wait_for_function("""
        () => {
            const btn = Array.from(document.querySelectorAll("button"))
                .find(b => b.innerText.includes("Adding") || b.disabled);
            return !!btn;
        }
        """, timeout=10000)

        logging.info("Add to RAG started (loading detected)")

        # STEP 2: Wait for loading to finish
        await page.wait_for_function("""
        () => {
            const btn = Array.from(document.querySelectorAll("button"))
                .find(b => b.innerText.includes("Adding"));

            // Done when:
            // - no "Adding..." button exists OR
            // - button is no longer disabled
            return !btn || !btn.disabled;
        }
        """, timeout=120000)

        logging.info("Add to RAG completed")


       
        
        # Brief wait to ensure indexing starts before closing page
        # await asyncio.sleep(30)
        
        # mark_done(career)
        logging.info(f"SUCCESS: {career} indexed.")

    except Exception as e:
        logging.error(f"FAILURE on {career}: {str(e)}")
        raise   
    finally:
        await page.close()

async def main():
    # Load Data
    if not os.path.exists(CSV_FILE):
        logging.error(f"Missing {CSV_FILE}!")
        return

    df = pd.read_csv(CSV_FILE)

    # Ensure columns exist
    if 'processed' not in df.columns:
        df['processed'] = 'NO'

    if 'processed_date' not in df.columns:
        df['processed_date'] = ''

    
    

    # Ensure processed column exists
    if 'processed' not in df.columns:
        df['processed'] = 'NO'

    # Normalize values
    df['processed'] = df['processed'].fillna('NO').str.upper()
    df['processed_date'] = df['processed_date'].fillna('')

    df['career_name'] = df['career_name'].str.strip()

    # DAILY LIMIT
    DAILY_LIMIT = 50

    # Select only pending rows
    pending_df = df[df['processed'] != 'YES'].head(DAILY_LIMIT)

    logging.info(f"Total rows: {len(df)}")
    logging.info(f"Today will process: {len(pending_df)} rows")



    
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        base_prompt = f.read()

    
    

    async with async_playwright() as p:
        # headless=False lets you watch the work. Change to True for speed.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)

        rag_connected = False

        for idx, row in pending_df.iterrows():
            career = row['career_name']
            category = row.get('category', '')

            try:
                # 🔥 STEP 1: MARK IN_PROGRESS (ADD HERE)
                df.at[idx, 'processed'] = 'IN_PROGRESS'
                df.at[idx, 'processed_date'] = datetime.now().isoformat()
                df.to_csv(CSV_FILE, index=False)

                # 🔥 STEP 2: ACTUAL PROCESS
                await process_career(
                    context,
                    career,
                    base_prompt,
                    connect_rag=not rag_connected
                )

                # 🔥 STEP 3: MARK SUCCESS
                df.at[idx, 'processed'] = 'YES'
                df.at[idx, 'processed_date'] = datetime.now().isoformat()
                df.to_csv(CSV_FILE, index=False)

                logging.info(f"SUCCESS + SAVED: {career}")

                if not rag_connected:
                    rag_connected = True

            except Exception as e:
                logging.error(f"FAILED: {career} -> {str(e)}")

                # 🔥 STEP 4: MARK FAILED
                df.at[idx, 'processed'] = 'FAILED'
                df.at[idx, 'processed_date'] = datetime.now().isoformat()
                df.to_csv(CSV_FILE, index=False)

            await asyncio.sleep(2)
           
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")