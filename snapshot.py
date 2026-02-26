import os
import sys
import requests
import re
from slack_sdk import WebClient

# 1. Config from GitHub Secrets
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print("--- Universal Scraper Started ---")
        
        # 2. Get message history (uses your groups:history scope)
        print(f"Scanning {relay_id} for the Power BI email content...")
        res = client.conversations_history(channel=relay_id, limit=5)
        messages = res.get("messages", [])
        
        target_image_url = None

        for msg in messages:
            # Look for standard files first
            if "files" in msg:
                for f in msg["files"]:
                    if "png" in f.get('filetype', '').lower():
                        target_image_url = f.get("url_private_download")
                        print(f"Found standard file: {f.get('name')}")
                        break
            
            # If no standard file, scan the HTML/Text for the Slack-hosted image link
            if not target_image_url:
                text_to_scan = str(msg)
                # This regex finds the Slack-origin URL found in your HTML snippet
                match = re.search(r'https://[^\s"\'<>]*files-origin\.slack\.com/[^\s"\'<>]+', text_to_scan)
                if match:
                    target_image_url = match.group(0).replace('\\', '')
                    print(f"Found hosted image link in HTML: {target_image_url}")
                    break

        if not target_image_url:
            print("ERROR: Could not find any PNG or hosted image link in the messages.")
            return

        # 3. Download using Bot Token
        print("Downloading image...")
        headers = {'Authorization': f'Bearer {token}'}
        img_res = requests.get(target_image_url, headers=headers)
        
        if img_res.status_code == 200:
            with open("report.png", "wb") as f:
                f.write(img_res.content)
            
            # 4. Final Upload to the team channel
            print(f"Relaying report to {target_id}...")
            client.files_upload_v2(
                channel=target_id, 
                file="report.png", 
                title="Power BI Report Snapshot",
                initial_comment="📊 *Daily Power BI Update* relayed from subscription."
            )
            print("SUCCESS: Relay complete!")
        else:
            print(f"Download failed: {img_res.status_code}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
