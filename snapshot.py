import os
import sys
import requests
import time
from slack_sdk import WebClient

# 1. Config: Mapping to your specific Secret names
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') # funnel-snapshot-automations
target_id = os.environ.get('SLACK_CHANNEL_ID')      # Target Team Channel
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Relay: {source_id} -> {target_id} ---")
        
        # 2. Time Filter: Last 24 hours only
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=20)
        messages = res.get("messages", [])
        
        # Exact keyword mapping for App Funnel Version 3.0
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Scan for PNG Attachments
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue

            for f in msg.get("files", []):
                fname = f.get("name", "").lower()
                ftype = f.get("filetype", "").lower()
                url = f.get("url_private_download")

                # Skip HTML/Email body; target PNG files only
                if not url or ftype != "png": continue

                for key in reports:
                    if reports[key]["kw"] in fname and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"Found Today's {key} Snapshot.")

        # 4. Download and Relay
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                img_data = requests.get(data["url"], headers=headers).content
                temp_file = f"{key.lower()}.png"
                with open(temp_file, "wb") as f:
                    f.write(img_data)

                # Post to target channel with your specific greeting
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} relayed.")
            else:
                print(f"SKIP: {key} not found in last 24h.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
