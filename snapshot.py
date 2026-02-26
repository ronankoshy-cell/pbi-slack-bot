import os
import sys
import requests
from slack_sdk import WebClient

# 1. Config
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- Aggressive Search ---")
        
        # Search Method A: Look for files directly
        print(f"Searching for files in {relay_id}...")
        res_files = client.files_list(channel=relay_id, count=10)
        files = res_files.get("files", [])
        
        # Search Method B: Look for messages (in case it's an email integration)
        print(f"Searching message history in {relay_id}...")
        res_hist = client.conversations_history(channel=relay_id, limit=5)
        messages = res_hist.get("messages", [])

        target_file_url = None

        # Try to find file in file list
        for f in files:
            if "png" in f.get('name', '').lower() or "png" in f.get('filetype', ''):
                target_file_url = f.get("url_private_download")
                print(f"Found via Files API: {f['name']}")
                break
        
        # If not found, try to find file inside messages (Email integration style)
        if not target_file_url:
            for m in messages:
                if "files" in m:
                    for f in m["files"]:
                        if "png" in f.get('name', '').lower():
                            target_file_url = f.get("url_private_download")
                            print(f"Found via History API: {f['name']}")
                            break
                if target_file_url: break

        if not target_file_url:
            print("ERROR: Still cannot find a PNG. Is the bot definitely in the relay channel?")
            return

        # 3. Download & Upload
        print("Downloading image...")
        img_data = requests.get(target_file_url, headers={'Authorization': f'Bearer {token}'}).content
        with open("report.png", "wb") as f:
            f.write(img_data)

        print(f"Uploading to {target_id}...")
        client.files_upload_v2(channel=target_id, file="report.png", title="Power BI Report")
        print("SUCCESS!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
