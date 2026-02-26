import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from slack_sdk import WebClient

# 1. Pull Environment Variables
pbi_url = os.environ.get('POWERBI_URL')
username = os.environ.get('PBI_USERNAME')
password = os.environ.get('PBI_PASSWORD')
slack_token = os.environ.get('SLACK_TOKEN')
channel_id = os.environ.get('SLACK_CHANNEL_ID')

# Setup Headless Chrome with a Real User-Agent to avoid bot detection
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 30)

try:
    print(f"Navigating to {pbi_url}...")
    driver.get(pbi_url)

    # --- STEP 1: POWER BI INITIAL EMAIL SCREEN (from your screenshot) ---
    print("Handling Power BI initial email box...")
    # The input in your screenshot is a standard email type
    pbi_email_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    pbi_email_box.send_keys(username)
    
    # Click the 'Submit' button seen in your screenshot
    submit_btn = driver.find_element(By.ID, "submitBtn") # or By.XPATH, "//button[contains(text(),'Submit')]"
    submit_btn.click()
    
    # --- STEP 2: MICROSOFT PASSWORD SCREEN ---
    print("Waiting for Microsoft Password field...")
    # This often takes a moment to redirect
    time.sleep(5) 
    
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
    print("Entering Password...")
    password_field.send_keys(password)
    password_field.send_keys(Keys.ENTER)
    
    # --- STEP 3: STAY SIGNED IN ---
    print("Handling 'Stay Signed In' prompt...")
    time.sleep(3)
    try:
        stay_signed_in_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
        stay_signed_in_btn.click()
    except:
        print("Stay Signed In button not found, continuing...")
    
    # --- STEP 4: RENDER & SNAPSHOT ---
    print("Waiting 45s for report visuals to render...")
    time.sleep(45) 
    
    print("Taking snapshot...")
    driver.save_screenshot("snapshot.png")

    print("Uploading to Slack...")
    client = WebClient(token=slack_token)
    client.files_upload_v2(
        channel=channel_id, 
        file="snapshot.png", 
        title="Daily Power BI Update"
    )
    print("Process Complete!")
    
except Exception as e:
    print(f"FAILED: {e}")
    driver.save_screenshot("error_view.png")
    # Send the error screenshot so you can see where it stopped
    try:
        client = WebClient(token=slack_token)
        client.files_upload_v2(channel=channel_id, file="error_view.png", title="Debug: Failed Login State")
    except:
        pass
    sys.exit(1)
finally:
    driver.quit()
