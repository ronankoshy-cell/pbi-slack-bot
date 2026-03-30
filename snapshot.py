import os
import sys
import requests
import time
from slack_sdk import WebClient

# 1. Setup from GitHub Secrets
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print("--- App Funnel v3.0 Precision Attachment Relay ---")
        
        # 2. Today's Window (Last 24 hours only)
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=relay_id, limit=20)
        messages = res.get("messages", [])
        
        # Mapping the new filenames to your specific team messages
        reports = {
            "Overall": {
                "kw": "overall", 
                "text": "Hi Team, Sharing the Overall App Funnel Snapshot", 
                "url": None
            },
            "iOS": {
                "kw": "ios", 
                "text": "Hi Team, Sharing the iOS App Funnel Snapshot", 
                "url": None
            },
            "Android": {
                "kw": "android", 
                "text": "Hi Team, Sharing the Android App Funnel Snapshot", 
                "url": None
            }
        }

        # 3. Identify ONLY PNG Attachments from Today
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts < cutoff: 
                continue # Skip historical messages from previous days

            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                ftype = f.get("filetype", "").lower()
                url = f.get("url_private_download")

                # CRITICAL: Ignore the HTML/Email body; only target PNG files
                if not url or ftype != "png": 
                    continue

                # Match the PNG to the correct category using your new naming
                for key in reports:
                    if reports[key]["kw"] in fname and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"Matched Today's PNG: {key} snapshot found.")

        # 4. Download and Relay with Custom Messages
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_file = f"{key.lower()}.png"
                with open(temp_file, "wb") as f:
                    f.write(img_data)

                # Post as a proper image file to the team channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file) # Keep the runner environment clean
                print(f"SUCCESS: {key} snapshot posted to team channel.")
            else:
                print(f"SKIP: No fresh {key} PNG found in the last 24 hours.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
