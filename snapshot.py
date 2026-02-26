import os
import sys
import requests
from slack_sdk import WebClient

# 1. Configuration from GitHub Secrets
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
RELAY_CHANNEL = os.environ.get('RELAY_CHANNEL_ID') # Private channel where email arrives
TARGET_CHANNEL = os.environ.get('SLACK_CHANNEL_ID') # Final team destination channel
client = WebClient(token=SLACK_TOKEN)

def run_relay():
    try:
        print(f"--- Diagnostic Check ---")
        print(f"Searching Relay Channel ID: {RELAY_CHANNEL}")
        print(f"Targeting Final Channel ID: {TARGET_CHANNEL}")

        # 2. Find the latest image in the relay channel
        # 'types="images"' ensures we only pick up the PNG/JPG report
        result = client.files_list(channel=RELAY_CHANNEL, types="images", count=1)
        
        if not result.get("files"):
            print("ERROR: No images found in the relay channel. Check your Outlook forwarder!")
            return

        latest_file = result["files"][0]
        file_url = latest_file["url_private_download"]
        file_name = latest_file["name"]
        print(f"Found latest report: {file_name}")

        # 3. Download the file using the Bot Token for Authorization
        print(f"Downloading file from Slack servers...")
        response = requests.get(file_url, headers={'Authorization': f'Bearer {SLACK_TOKEN}'})
        
        if response.status_code == 200:
            with open("report.png", "wb") as f:
                f.write(response.content)
            print("Download successful.")
        else:
            print(f"ERROR: Download failed with status code {response.status_code}")
            return

        # 4. Upload to the final target channel
        print(f"Uploading report to final destination...")
        upload = client.files_upload_v2(
            channel=TARGET_CHANNEL,
            file="report.png",
            title="Daily Power BI Snapshot",
            initial_comment="📊 *Daily Power BI Update*\nHere is the latest snapshot from the automated subscription."
        )
        
        if upload.get("ok"):
            print("SUCCESS: Report has been relayed to the target channel!")
        else:
            print(f"ERROR: Upload failed: {upload.get('error')}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
