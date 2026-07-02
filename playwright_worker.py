import os
import argparse
import asyncio
import logging
import mysql.connector
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError
from datetime import datetime
from myblocks_login import login_to_myblocks


def add_db_columns():
    import mysql.connector
    conn = mysql.connector.connect(host='88.150.227.117', user='nrktrn_web_admin', password='GOeg&*$*657', database='nrkindex_trn', port=3306)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE aia_job_roles ADD COLUMN processed VARCHAR(20) DEFAULT 'NO'")
    except Exception as e:
        print("processed column already exists or error:", str(e))
    try:
        cur.execute("ALTER TABLE aia_job_roles ADD COLUMN processed_date DATETIME")
    except Exception as e:
        print("processed_date column already exists or error:", str(e))
    conn.commit()
    # Verify columns
    cur.execute("DESCRIBE aia_job_roles")
    print("\nCurrent table columns:")
    for col in cur.fetchall():
        print("  -", col[0])
    cur.close()
    conn.close()
    print("\nDone checking/adding columns!")

# Uncomment to verify/run
# add_db_columns()

# --- PARSE INCOMING ARGUMENTS ---
parser = argparse.ArgumentParser()
parser.add_argument('--prompt', required=True)
parser.add_argument('--query', required=True)
parser.add_argument('--table', required=True)
parser.add_argument('--topic', required=True)
parser.add_argument('--subtopic', required=True)
parser.add_argument('--rag_category', required=True)
parser.add_argument('--rag_userid', required=True)
parser.add_argument('--login_username', required=True)
parser.add_argument('--login_password', required=True)
parser.add_argument('--llm_provider', required=True)
parser.add_argument('--llm_model', required=True)
parser.add_argument('--userid', default='919')
parser.add_argument('--firmid', default='5')
args = parser.parse_args()

CUSTOM_PROMPT = args.prompt
CUSTOM_QUERY = args.query
CUSTOM_TABLE = args.table
CUSTOM_TOPIC = args.topic
CUSTOM_SUBTOPIC = args.subtopic
CUSTOM_RAG_CATEGORY = args.rag_category
CUSTOM_RAG_USERID = args.rag_userid
CUSTOM_LOGIN_USERNAME = args.login_username
CUSTOM_LOGIN_PASSWORD = args.login_password
CUSTOM_LLM_PROVIDER = args.llm_provider
CUSTOM_LLM_MODEL = args.llm_model
CUSTOM_USERID = args.userid
CUSTOM_FIRMID = args.firmid

# --- CONFIGURATION ---
DOWNLOAD_DIR = Path("downloads")
DATA_DIR = Path("data")
os.makedirs("logs", exist_ok=True)
LOG_FILE = f"logs/automation_status_worker_{CUSTOM_USERID}_{CUSTOM_FIRMID}.log"
PROCESSED_FILE = DATA_DIR / f"processed_roles_{CUSTOM_USERID}_{CUSTOM_FIRMID}.txt"

# URLs
CINDEX_URL = "https://myblocks.in/book-gen/"
RAG_URL = "https://myblocks.in/ragnew"

# DB Configuration - UPDATE THESE WITH YOUR ACTUAL CREDENTIALS
DB_CONFIG = {
    'host': '88.150.227.117',
    'user': 'nrktrn_web_admin',
    'password': 'GOeg&*$*657', # Add your password here
    'database': 'nrkindex_trn' # Add your DB name here


}

# Check environment
import socket
HOSTNAME = socket.gethostname().upper()
DEV_KEYWORDS = ['MSI', 'I3ADMIN-PRECISION-TOWER-5810', 'DESKTOP-KAL0REJ']
IS_LOCAL = any(kw in HOSTNAME for kw in DEV_KEYWORDS)

screenshot_counter = 0

async def capture_screenshot(page, action_name):
    global screenshot_counter
    if not IS_LOCAL:
        return
    screenshot_counter += 1
    screenshot_dir = os.path.join("screenshots", "steps")
    os.makedirs(screenshot_dir, exist_ok=True)
    # Sanitise name for file system
    clean_action_name = "".join(c for c in action_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{screenshot_counter:03d}_{clean_action_name.replace(' ', '_')}.png"
    filepath = os.path.join(screenshot_dir, filename)
    try:
        await page.screenshot(path=filepath)
        logging.info(f"Step screenshot saved to {filepath}")
    except Exception as e:
        logging.warning(f"Failed to capture screenshot for '{action_name}': {e}")

# Setup
DOWNLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logging.info(f"Worker process started. Provider: {CUSTOM_LLM_PROVIDER}, Model: {CUSTOM_LLM_MODEL}")

# Load processed roles from file
def load_processed_roles():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

# Save processed role to file
def mark_role_processed(role_id):
    with open(PROCESSED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{role_id}\n")

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

async def fill_with_fallback(page, selectors, value, timeout=5000):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            await locator.first.wait_for(state="visible", timeout=timeout)
            await locator.first.fill(value)
            await capture_screenshot(page, f"filled_{value[:20]}")
            return
        except Exception:
            continue
    raise Exception(f"All selectors failed for value: {value}")

async def click_with_fallback(page, selectors, timeout=5000):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            await locator.first.wait_for(state="visible", timeout=timeout)
            # Use JS click to bypass pointer interception
            await locator.first.evaluate("node => node.click()")
            await capture_screenshot(page, f"clicked_{sel[:20]}")
            return
        except Exception:
            continue
    raise Exception(f"All click selectors failed: {selectors}")

async def select_with_fallback(page, selectors, value, timeout=5000):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            await locator.first.wait_for(state="visible", timeout=timeout)
            await locator.first.select_option(value)
            await capture_screenshot(page, f"selected_{value[:20]}")
            return
        except Exception:
            continue
    raise Exception(f"All select selectors failed for value: {value} with selectors: {selectors}")

async def wait_for_fallback(page, selectors, timeout=5000):
    for sel in selectors:
        try:
            locator = page.locator(sel)
            await locator.first.wait_for(state="visible", timeout=timeout)
            return locator.first
        except Exception:
            continue
    raise Exception(f"All wait selectors failed: {selectors}")

async def wait_for_generation_complete(page):
    tasks = [
        page.wait_for_selector("button:has-text('Generate Book'):not([disabled])", timeout=400000),
        page.wait_for_selector(".success-box", timeout=400000),
        page.wait_for_selector("button:has-text('Download')", timeout=400000)
    ]
    done, pending = await asyncio.wait(
        [asyncio.create_task(t) for t in tasks],
        return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    return done


async def process_career(context, career, base_prompt, connect_rag=False):
    page = await context.new_page()
    page.set_default_timeout(90000)

    try:
        topic = CUSTOM_TOPIC.replace("{{career_name}}", career)
        subtopic = CUSTOM_SUBTOPIC.replace("{{career_name}}", career)
        final_prompt = base_prompt.replace("{{career_name}}", career)

        logging.info("=" * 80)
        logging.info(f"STARTING BOOK GENERATION FOR: {career}")
        logging.info(f"SUBTOPIC: {subtopic}")
        logging.info(f"TOPIC: {topic}")
        logging.info(f"PROMPT PREVIEW: {final_prompt[:300]}...")
        logging.info("=" * 80)

        # ----------------------------------------------------
        # OPEN CINDEX
        # ----------------------------------------------------
        logging.info("Opening CIndex...")
        await page.goto(
            CINDEX_URL,
            wait_until="domcontentloaded",
            timeout=90000
        )

        # ----------------------------------------------------
        # SUBTOPIC
        # ----------------------------------------------------
        logging.info(f"Entering Subtopic: {subtopic}")

        await fill_with_fallback(
            page,
            [
                'input[placeholder="e.g. Hospitality, IT, Healthcare"]',
                'xpath=//*[@id="root"]/div/div/div[2]/div[1]/input'
            ],
            subtopic
        )

        logging.info("Subtopic entered successfully")

        # ----------------------------------------------------
        # TOPIC
        # ----------------------------------------------------
        logging.info(f"Entering Topic: {topic}")

        await fill_with_fallback(
            page,
            [
                'input[placeholder="e.g. Customer Service Excellence"]',
                'xpath=//*[@id="root"]/div/div/div[2]/div[2]/input'
            ],
            topic
        )

        logging.info("Topic entered successfully")

        # ----------------------------------------------------
        # PROMPT
        # ----------------------------------------------------
        logging.info(
            f"Entering Prompt ({len(final_prompt)} chars)"
        )

        await fill_with_fallback(
            page,
            [
                'textarea[placeholder="Describe what the book should focus on..."]',
                'xpath=//*[@id="root"]/div/div/div[2]/div[3]/div/textarea'
            ],
            final_prompt
        )

        logging.info("Prompt entered successfully")

        # ----------------------------------------------------
        # SELECT LLM PROVIDER & MODEL
        # ----------------------------------------------------
        logging.info(f"Selecting LLM Provider: {CUSTOM_LLM_PROVIDER}")
        try:
            await select_with_fallback(
                page,
                [
                    'xpath=//*[@id="root"]/div/div/div[2]/div[5]/select',
                    'xpath=/html/body/div/div/div/div[2]/div[5]/select',
                    'select:has(option[value="GROQ"])',
                    'select:has(option[value="MYBLOCKS_SERVERS 1"])'
                ],
                CUSTOM_LLM_PROVIDER
            )
            logging.info("LLM Provider selected successfully")
        except Exception as e:
            logging.warning(f"Could not select LLM Provider: {e}")

        # Wait for the target model option to populate in the dropdown DOM
        logging.info(f"Waiting for LLM Model option '{CUSTOM_LLM_MODEL}' to populate...")
        try:
            await page.wait_for_selector(
                f'xpath=//select[option[@value="{CUSTOM_LLM_MODEL}"]] | xpath=//select[option[text()="{CUSTOM_LLM_MODEL}"]] | xpath=//*[@id="root"]/div/div/div[2]/div[6]/select/option[@value="{CUSTOM_LLM_MODEL}"]', 
                timeout=15000
            )
            logging.info(f"Target model option '{CUSTOM_LLM_MODEL}' is available in DOM.")
        except Exception as e:
            logging.warning(f"Timeout waiting for model option: {e}. Attempting selection anyway...")

        logging.info(f"Selecting LLM Model: {CUSTOM_LLM_MODEL}")
        try:
            await select_with_fallback(
                page,
                [
                    'xpath=//*[@id="root"]/div/div/div[2]/div[6]/select',
                    'xpath=/html/body/div/div/div/div[2]/div[6]/select',
                    f'select:has(option[value="{CUSTOM_LLM_MODEL}"])',
                    f'select:has(option:has-text("{CUSTOM_LLM_MODEL}"))',
                    'select:nth-of-type(2)'
                ],
                CUSTOM_LLM_MODEL
            )
            logging.info("LLM Model selected successfully")
        except Exception as e:
            logging.warning(f"Could not select LLM Model: {e}")


        # ----------------------------------------------------
        # GENERATE BOOK & DOWNLOAD
        # ----------------------------------------------------
        logging.info("Searching for Generate Book button...")

        try:
            async with page.expect_download(timeout=400000) as download_info:
                await click_with_fallback(
                    page,
                    [
                        "button:has-text('Generate Book')",
                        "text=🚀 Generate Book",
                        "text=Generate Book"
                    ]
                )

                logging.info("Generate Book button clicked")
                logging.info("Waiting for generation to complete and download to start...")

                await wait_for_generation_complete(page)
                await capture_screenshot(page, "generation_completed_screen")
            
            download = await download_info.value
            target_dir = DOWNLOAD_DIR / CUSTOM_FIRMID / CUSTOM_USERID
            target_dir.mkdir(parents=True, exist_ok=True)
            save_path = target_dir / f"{career.replace(' ', '_')}.pdf"
            await download.save_as(save_path)
            logging.info(f"PDF Downloaded Successfully: {save_path}")

        except Exception as e:
            logging.error(f"Generation or download failed: {e}")
            raise e

        logging.info(
            "Generation completion signal received."
        )

        # ----------------------------------------------------
        # CONNECT RAG
        # ----------------------------------------------------
        if connect_rag:

            logging.info(
                "Looking for Connect to RAG Server button..."
            )

            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )

            try:

                await page.wait_for_selector(
                    "button:has-text('Connect to RAG Server')",
                    timeout=20000
                )

                logging.info(
                    "Connect to RAG Server button found"
                )

                await click_with_fallback(
                    page,
                    [
                        "button:has-text('Connect to RAG Server')",
                        "text=Connect to RAG Server",
                        ".rag-button"
                    ]
                )

                logging.info(
                    "Connect to RAG button clicked"
                )

                await page.wait_for_selector(
                    'input[placeholder="e.g. 1559"]',
                    state="visible",
                    timeout=15000
                )

                logging.info(
                    "User ID input found"
                )

                # CHANGED TO DYNAMIC USER ID
                await fill_with_fallback(
                    page,
                    ['input[placeholder="e.g. 1559"]'],
                    CUSTOM_RAG_USERID
                )

                logging.info(
                    f"Entered RAG User ID: {CUSTOM_RAG_USERID}"
                )

                await click_with_fallback(
                    page,
                    [
                        "role=button[name='Connect']",
                        "text=Connect"
                    ]
                )

                logging.info(
                    "Clicked Connect"
                )

                await page.wait_for_timeout(3000)

                logging.info(
                    "RAG connection completed"
                )

            except Exception as rag_error:
                logging.warning(
                    f"RAG Connection button not found or already connected: {rag_error}. Proceeding to upload..."
                )

        # ----------------------------------------------------
        # RAG CATEGORY DROPDOWN
        # ----------------------------------------------------
        logging.info("Looking for RAG category dropdown...")

        all_selects = page.locator("select")

        # Wait for at least one select to appear to be safe
        try:
            await page.wait_for_selector("select", state="attached", timeout=15000)
        except:
            logging.warning("No select found within 15 seconds, attempting anyway")

        select_count = await all_selects.count()

        logging.info(
            f"Total dropdowns found: {select_count}"
        )

        rag_dropdown = None
        rag_options = []

        for i in range(select_count):

            try:

                current_dropdown = all_selects.nth(i)

                current_options = await current_dropdown.locator(
                    "option"
                ).all_text_contents()

                logging.info(
                    f"Dropdown #{i+1}: {current_options}"
                )
                
                # Automatically select General, Intelligence, or Supervised if present
                for opt in current_options:
                    lower_opt = opt.strip().lower()
                    if lower_opt in ["general", "intelligence", "supervised"]:
                        logging.info(f"Found required RAG option '{opt}' in dropdown #{i+1}, selecting it.")
                        try:
                            await current_dropdown.select_option(label=opt)
                            await current_dropdown.evaluate(
                                '''(node, val) => {
                                    const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value')?.set;
                                    if (setter) { setter.call(node, val); } else { node.value = val; }
                                    node.dispatchEvent(new Event('change', { bubbles: true }));
                                }''', opt
                            )
                        except Exception as sel_err:
                            logging.warning(f"Failed to auto-select '{opt}': {sel_err}")

                if CUSTOM_RAG_CATEGORY in current_options:

                    rag_dropdown = current_dropdown
                    rag_options = current_options

                    logging.info(
                        f"Found RAG category dropdown at position #{i+1}"
                    )
                    # Removed break to ensure we check all dropdowns for other required options
                    
            except Exception as ex:

                logging.warning(
                    f"Could not inspect dropdown #{i+1}: {ex}"
                )

        if rag_dropdown is None:

            raise Exception(
                f"Could not locate dropdown containing '{CUSTOM_RAG_CATEGORY}'"
            )

        logging.info(
            f"RAG Dropdown Options: {rag_options}"
        )

        try:

            logging.info(
                f"Selecting '{CUSTOM_RAG_CATEGORY}' from RAG dropdown..."
            )

            # 1. Use Playwright's native select
            await rag_dropdown.select_option(
                label=CUSTOM_RAG_CATEGORY
            )

            # 2. Force React to recognize the change by bypassing its synthetic event tracker
            await rag_dropdown.evaluate(
                '''(node, val) => {
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
                    if (setter) {
                        setter.call(node, val);
                    } else {
                        node.value = val;
                    }
                    node.dispatchEvent(new Event('change', { bubbles: true }));
                }''',
                CUSTOM_RAG_CATEGORY
            )

            logging.info(
                f"Successfully selected '{CUSTOM_RAG_CATEGORY}' and forced React state update"
            )

        except Exception as e:

            logging.error(
                f"Failed to select {CUSTOM_RAG_CATEGORY}: {e}"
            )

            raise

        # ----------------------------------------------------
        # ADD TO RAG
        # ----------------------------------------------------
        logging.info(
            "Looking for Add to RAG button..."
        )

        await click_with_fallback(
            page,
            [
                "text=Add to RAG",
                "button:has-text('Add to RAG')",
                "role=button[name='📚 Add to RAG']"
            ]
        )

        logging.info(
            "Add to RAG button clicked"
        )

        try:
            # STEP 1: Wait for loading state (button becomes disabled or shows spinner)
            await page.wait_for_function("""
            () => {
                const btn = Array.from(document.querySelectorAll("button"))
                    .find(b => b.innerText.includes("Adding") || b.disabled);
                return !!btn;
            }
            """, timeout=15000)

            logging.info("Add to RAG started (loading detected)")

            # STEP 2: Wait for loading to finish
            await page.wait_for_function("""
            () => {
                const btn = Array.from(document.querySelectorAll("button"))
                    .find(b => b.innerText.includes("Adding"));

                // Done when no "Adding" button exists OR it's no longer disabled
                return !btn || !btn.disabled;
            }
            """, timeout=120000)
            logging.info("Add to RAG completed successfully based on UI state")
            await capture_screenshot(page, "add_to_rag_completed")
            print(f"✅ SUCCESS: Book '{career}' was successfully added to RAG '{CUSTOM_RAG_CATEGORY}'", flush=True)
        except Exception as wait_err:
            logging.warning(f"Wait for 'Adding' UI state timed out or failed: {wait_err}. Assuming completed based on fallback wait.")
            await page.wait_for_timeout(15000)
            await capture_screenshot(page, "add_to_rag_after_fallback_wait")

        logging.info(
            f"BOOK SUCCESSFULLY PROCESSED: {career}"
        )

    except Exception as e:

        logging.exception(
            f"FAILURE ON {career}"
        )

        raise

    finally:
        await page.close()
async def main():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
    except Exception as e:
        logging.error(f"Failed to connect to DB: {e}")
        import sys
        sys.exit(1)

    try:
        logging.info(f"Executing UI Query: {CUSTOM_QUERY}")
        cursor.execute(CUSTOM_QUERY)
        pending_rows = cursor.fetchall()
    except Exception as e:
        logging.error(f"Failed to fetch with custom query: {e}")
        import sys
        sys.exit(1)

    # Load already processed roles
    processed_roles = load_processed_roles()
    # Filter out already processed roles
    filtered_rows = []
    for row in pending_rows:
        row_id = row.get('id') or row.get('job_role_id')
        if str(row_id) not in processed_roles:
            filtered_rows.append(row)
    
    logging.info(f"Will process: {len(filtered_rows)} new rows (total {len(pending_rows)} in query)")

    if not filtered_rows:
        logging.info("No new roles to process.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Check if running locally/localhost
        import socket
        hostname = socket.gethostname().upper()
        dev_keywords = ['MSI', 'I3ADMIN-PRECISION-TOWER-5810', 'DESKTOP-KAL0REJ']
        is_local = any(kw in hostname for kw in dev_keywords)
        
        context_args = {"accept_downloads": True}
        if is_local:
            video_dir = os.path.join("downloads", "videos")
            os.makedirs(video_dir, exist_ok=True)
            context_args["record_video_dir"] = video_dir
            context_args["record_video_size"] = {"width": 1280, "height": 720}
            logging.info(f"Local/localhost detected. Playwright video recording enabled: {video_dir}")
        else:
            logging.info("Production mode detected. Playwright video recording disabled.")
            
        context = await browser.new_context(**context_args)

        # Perform login once so session is authenticated for all pages
        logging.info("Performing MyBlocks login session setup...")
        login_page = await context.new_page()
        try:
            await login_to_myblocks(login_page, username=CUSTOM_LOGIN_USERNAME, password=CUSTOM_LOGIN_PASSWORD)
        except Exception as login_err:
            logging.error(f"MyBlocks session login failed: {login_err}")
        finally:
            await login_page.close()

        rag_connected = False

        for row in filtered_rows:
            # Handle different possible column names for ID
            row_id = row.get('id') or row.get('job_role_id')
            career = row.get('career_name') or row.get('role_name')

            if not row_id or not career:
                logging.error(f"Row missing required data: {row}")
                continue

            try:
                # ACTUAL PROCESS
                await process_career(context, career, CUSTOM_PROMPT, connect_rag=not rag_connected)

                # Mark role as processed in local file
                mark_role_processed(str(row_id))
                logging.info(f"SUCCESS + SAVED: {career}")
                rag_connected = True

            except Exception as e:
                logging.error(f"FAILED: {career} -> {str(e)}")

            await asyncio.sleep(2)
           
        await context.close()
        await browser.close()
    
    logging.info(f"✅ BATCH COMPLETED. Processed {len(filtered_rows)} roles.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
