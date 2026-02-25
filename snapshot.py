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

# Setup Headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

try:
    print("Navigating to Power BI...")
    driver.get(pbi_url)

    # --- LOGIN FLOW ---
    print("Entering Email...")
    email_field = wait.until(EC.presence_of_element_located((By.NAME, "loginfmt")))
    email_field.send_keys(username)
    email_field.send_keys(Keys.ENTER)
    
    # Wait for password field to appear
    time.sleep(3)

    print("Entering Password...")
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
    password_field.send_keys(password)
    password_field.send_keys(Keys.ENTER)
    
    # Click 'Yes' to 'Stay signed in?' prompt
    print("Confirming 'Stay Signed In'...")
    stay_signed_in_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
    stay_signed_in_btn.click() 
    
    # 2. Wait for visuals to load (30s to be safe)
    print("Waiting for report visuals to render...")
    time.sleep(30) 
    
    # 3. Capture & Upload
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
    print(f"An error occurred: {e}")
    # Take a screenshot of the error page to see what went wrong (e.g. MFA prompt)
    driver.save_screenshot("error_state.png")
    sys.exit(1)
finally:
    driver.quit()
