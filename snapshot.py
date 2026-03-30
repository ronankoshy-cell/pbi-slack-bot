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
        print(f"--- App Funnel v3.0 Precision Relay ---")
        
        # 2. Increase window to 25 hours to ensure no time-zone misses
        cutoff = time.time() - (25 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=30)
        messages = res.get("messages", [])
        
        # Exact keywords for Version 3.0
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Scan for PNG Attachments ONLY
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts < cutoff: continue

            # Get files from the message
            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                ftype = f.get("filetype", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")

                # STRICT FILTER: Skip anything that isn't a PNG image
                # This stops the script from grabbing the HTML code block!
                if not url or ("png" not in ftype and "png" not in mimetype):
                    continue

                for key in reports:
                    if reports[key]["kw"] in fname and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"✅ Found Today's PNG Attachment: {key} ({fname})")

        # 4. Download and Relay binary data
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key} PNG...")
                img_res = requests.get(data["url"], headers=headers)
                
                if img_res.status_code == 200:
                    temp_file = f"today_{key.lower()}.png"
                    with open(temp_file, "wb") as f:
                        f.write(img_res.content)
                    
                    # Upload the binary file to ensure it's an image, not code
                    client.files_upload_v2(
                        channel=target_id, 
                        file=temp_file, 
                        title=f"App Funnel v3.0 - {key}",
                        initial_comment=data["text"]
                    )
                    os.remove(temp_file)
                    print(f"SUCCESS: {key} snapshot posted.")
            else:
                print(f"SKIP: {key} not found in last 24h. Check filenames!")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
