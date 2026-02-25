import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from slack_sdk import WebClient

pbi_url = os.environ.get('POWERBI_URL')
slack_token = os.environ.get('SLACK_TOKEN')
channel_id = os.environ.get('SLACK_CHANNEL_ID')

# Check if any are missing before starting
if not all([pbi_url, slack_token, channel_id]):
    print(f"ERROR: Missing one or more secrets!")
    print(f"POWERBI_URL present: {bool(pbi_url)}")
    print(f"SLACK_TOKEN present: {bool(slack_token)}")
    print(f"SLACK_CHANNEL_ID present: {bool(channel_id)}")
    sys.exit(1)

# 2. Setup Headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    print("Navigating to Power BI...")
    driver.get(pbi_url)
    time.sleep(20) # Give it time to load visuals
    
    print("Taking snapshot...")
    driver.save_screenshot("snapshot.png")

    print("Uploading to Slack...")
    client = WebClient(token=slack_token)
    client.files_upload_v2(
        channel=channel_id, 
        file="snapshot.png", 
        title="Daily Power BI Update"
    )
    print("Done!")
    
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
    
finally:
    driver.quit()
