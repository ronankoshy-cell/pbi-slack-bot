import os
import sys
import requests
from slack_sdk import WebClient

# 1. Config from GitHub Secrets
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
RELAY_ID = os.environ.get('RELAY_CHANNEL_ID')
TARGET_ID = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=SLACK_TOKEN)

def run_relay():
    try:
        print(f"--- Diagnostic Check ---")
        print(f"Relay Channel: {RELAY_ID} | Target Channel: {TARGET_ID}")

        # 2. Search for the image
        # Using types="images" to find the PNG from your screenshot
        result = client.files_list(channel=RELAY_ID, types="images", count=5)
        
        files = result.get("files", [])
        print(f"Files found in relay channel: {len(files)}")

        if not files:
            print("ERROR: No images found. Did you /invite the bot to the relay channel?")
            return

        # 3. Download the newest file
        latest_file = files[0]
        print(f"Downloading: {latest_file['name']}")
        
        res = requests.get(
            latest_file["url_private_download"], 
            headers={'Authorization': f'Bearer {SLACK_TOKEN}'}
        )
        
        if res.status_code == 200:
            with open("report.png", "wb") as f:
                f.write(res.content)
        else:
            print(f"Download failed: {res.status_code}")
            return

        # 4. Final Upload
        print("Uploading to final destination...")
        client.files_upload_v2(
            channel=TARGET_ID,
            file="report.png",
            title="Daily Power BI Snapshot",
            initial_comment="📊 *Daily Power BI Update* relayed from subscription."
        )
        print("SUCCESS: Report relayed!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
