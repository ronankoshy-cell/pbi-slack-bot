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
        print(f"--- Nested Email Search ---")
        
        # 2. Get history
        res = client.conversations_history(channel=relay_id, limit=5)
        messages = res.get("messages", [])
        
        target_file_url = None

        for msg in messages:
            if "files" in msg:
                for f in msg["files"]:
                    print(f"Inspecting: {f.get('name')} | Mode: {f.get('mode')}")
                    
                    # Method A: Direct PNG
                    if "png" in f.get('filetype', '').lower():
                        target_file_url = f.get("url_private_download")
                        break
                    
                    # Method B: Nested Image in Email Object
                    # Slack often puts the thumbnail of the email here
                    if f.get('filetype') == 'email' and 'thumb_pdf' not in f:
                        # Try to grab the largest preview image Slack generated
                        target_file_url = f.get("url_private_download") or f.get("thumb_1024") or f.get("thumb_720")
                        if target_file_url:
                            print(f"Found image inside email object: {f.get('name')}")
                            break
            if target_file_url: break

        if not target_file_url:
            print("ERROR: Could not find image URL inside the email objects.")
            return

        # 3. Download & Upload
        print("Downloading...")
        headers = {'Authorization': f'Bearer {token}'}
        img_data = requests.get(target_file_url, headers=headers).content
        
        with open("report.png", "wb") as f:
            f.write(img_data)

        print(f"Uploading to {target_id}...")
        client.files_upload_v2(
            channel=target_id, 
            file="report.png", 
            title="Power BI Report"
        )
        print("SUCCESS!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
