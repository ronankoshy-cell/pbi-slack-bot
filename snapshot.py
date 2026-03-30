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
        print(f"--- App Funnel v3.0 Precision Relay: {source_id} -> {target_id} ---")
        
        # 2. Window: Last 24 hours
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=30)
        messages = res.get("messages", [])
        
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Scan for files based on Extension and Keywords
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts < cutoff: continue

            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                url = f.get("url_private_download")

                if not url: continue
                
                # Debug: Show everything the bot sees in the logs
                print(f"Checking file: {fname}")

                # RELAXED FILTER: Look for .png in the name and the keyword
                # This avoids the "HTML code" block because that doesn't end in .png
                if ".png" in fname:
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"MATCHED: Found PNG for {key}")

        # 4. Download and Relay
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Downloading {key} snapshot...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_file = f"v3_{key.lower()}.png"
                with open(temp_file, "wb") as f:
                    f.write(img_data)

                # Post to target channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted to team channel.")
            else:
                print(f"SKIP: {key} snapshot not found in history.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
