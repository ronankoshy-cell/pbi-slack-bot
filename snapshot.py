import os
import sys
import requests
import time
from slack_sdk import WebClient

# 1. Setup
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') # funnel-snapshot-automations
target_id = os.environ.get('SLACK_CHANNEL_ID')      # Target Team Channel
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Deep-Dive Relay ---")
        
        # Look back 24 hours to find today's subscriptions
        cutoff = time.time() - (24 * 60 * 60)
        
        # Use history to find attachments nested inside emails
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        print(f"DEBUG: Scanning {len(messages)} messages for hidden attachments...")

        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 2. Iterate through messages and their internal files
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue
            
            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")

                if not url: continue

                # Logic: Skip the 'text/html' email body; grab the actual image
                if "image" in mimetype or fname.endswith(".png"):
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ ATTACHMENT FOUND: {key} ({fname})")

        # 3. Download and Relay binary PNG data
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Processing {key} snapshot...")
                img_data = requests.get(data["url"], headers=headers).content
                temp_file = f"final_{key.lower()}.png"
                with open(temp_file, "wb") as f: f.write(img_data)

                # Post to target channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: No PNG attachment found for {key} in the last 24h.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
