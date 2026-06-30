import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# Target URLs
LOGIN_URL = "https://myblocks.in/login"
QA_APP_URL = "https://myblocks.in/businessuserhome"

# Credentials
USERNAME = "test11"
PASSWORD = "test11"

def main():
    # Setup Chrome options
    options = Options()
    # You can set headless to False if you want to see the browser UI
    options.add_argument("--start-maximized")
    
    # Initialize WebDriver
    print("Launching browser...")
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to login page
        print(f"Navigating to {LOGIN_URL}...")
        driver.get(LOGIN_URL)
        
        # Wait for elements and perform login
        wait = WebDriverWait(driver, 10)
        
        # Enter Username
        print("Entering username...")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        username_field.clear()
        username_field.send_keys(USERNAME)
        
        # Enter Password
        print("Entering password...")
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_field.clear()
        password_field.send_keys(PASSWORD)
        
        # Select User Type
        print("Selecting user type...")
        usertype_dropdown = wait.until(EC.presence_of_element_located((By.ID, "userType")))
        Select(usertype_dropdown).select_by_value("BUSINESSAPP")
        
        # Click Login
        print("Clicking login button...")
        login_button = wait.until(EC.presence_of_element_located((By.ID, "login-button")))
        login_button.click()
        
        # Wait for login to process
        print("Waiting for login process...")
        time.sleep(5)
        
        # Open the QA App URL
        print(f"Opening QA App URL: {QA_APP_URL}...")
        driver.get(QA_APP_URL)
        
        # Keep it open for 10 seconds to verify success
        print("Successfully opened the QA App URL. Keeping browser open for 10 seconds...")
        time.sleep(10)
        
    finally:
        print("Closing browser.")
        driver.quit()

if __name__ == "__main__":
    main()
