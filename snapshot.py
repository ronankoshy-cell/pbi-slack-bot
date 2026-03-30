import os
import sys
import requests
import time
from slack_sdk import WebClient

# 1. Configuration
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') # funnel-snapshot-automations
target_id = os.environ.get('SLACK_CHANNEL_ID')      # Target Team Channel
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Precision Relay Started ---")
        
        # 2. Today's Window (Last 24 hours)
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=30)
        messages = res.get("messages", [])
        
        # Updated naming and messages for Version 3.0
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Strictly Filter for PNG Attachments
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue

            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                ftype = f.get("filetype", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")

                # CRITICAL: Skip the HTML/Email body; target only the PNG image
                if not url or ("png" not in ftype and "png" not in mimetype):
                    continue

                for key in reports:
                    # Match filenames like "App Funnel Version 3.0 -(Android Snapshot).png"
                    if reports[key]["kw"] in fname and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"✅ Found Today's PNG: {key} ({fname})")

        # 4. Download and Relay
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                img_data = requests.get(data["url"], headers=headers).content
                temp_file = f"v3_{key.lower()}.png"
                with open(temp_file, "wb") as f:
                    f.write(img_data)

                # Post as binary PNG to prevent HTML output
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: No today's {key} PNG found. Check source channel.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
