import os
import sys
import requests
from slack_sdk import WebClient

# Configuration from GitHub Secrets
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- Deep Scan Diagnostic ---")
        
        # 1. Pull the last 10 messages from the relay channel
        print(f"Scanning history of {relay_id}...")
        res = client.conversations_history(channel=relay_id, limit=10)
        messages = res.get("messages", [])
        print(f"Total messages found: {len(messages)}")
        
        target_file_url = None

        # 2. Iterate through messages to find the embedded email image
        for msg in messages:
            # Check standard files first
            if "files" in msg:
                for f in msg["files"]:
                    print(f"Found file: {f.get('name')} (Type: {f.get('filetype')})")
                    if "png" in f.get('filetype', '').lower() or "png" in f.get('name', '').lower():
                        target_file_url = f.get("url_private_download")
                        break
            
            # Check 'attachments' (Email apps often use this structure)
            if not target_file_url and "attachments" in msg:
                for att in msg["attachments"]:
                    # Email apps sometimes use image_url or a link within fallback text
                    if "image_url" in att:
                        target_file_url = att.get("image_url")
                        print("Found target via attachment image_url.")
                        break

            if target_file_url:
                break

        if not target_file_url:
            print("ERROR: No PNG found in the last 10 messages.")
            return

        # 3. Download the image
        print(f"Target found. Downloading...")
        headers = {'Authorization': f'Bearer {token}'}
        img_res = requests.get(target_file_url, headers=headers)
        
        if img_res.status_code == 200:
            with open("report.png", "wb") as f:
                f.write(img_res.content)
            
            # 4. Upload to target channel
            print(f"Uploading to final channel: {target_id}...")
            client.files_upload_v2(
                channel=target_id, 
                file="report.png", 
                title="Power BI Daily Report",
                initial_comment="📊 *Daily Snapshot Relayed*"
            )
            print("SUCCESS: Relay complete!")
        else:
            print(f"Download failed with status: {img_res.status_code}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
