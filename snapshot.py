import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from slack_sdk import WebClient

# Cloud setup for Chrome (Headless mode)
options = Options()
options.add_argument("--headless") 
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # 1. Open the Report (Uses the Secret URL)
    driver.get(os.environ['POWERBI_URL'])
    time.sleep(20) # Wait for visuals to load
    
    # 2. Capture the Snapshot
    driver.save_screenshot("table.png")

    # 3. Upload to Slack
    client = WebClient(token=os.environ['SLACK_TOKEN'])
    client.files_upload_v2(channel=os.environ['SLACK_CHANNEL_ID'], file="table.png", title="Daily Snapshot")
    
finally:
    driver.quit()
