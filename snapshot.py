import os
import sys
import requests
import time
from slack_sdk import WebClient

# Setup
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') 
target_id = os.environ.get('SLACK_CHANNEL_ID')      
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Success Relay ---")
        # 1. 24-hour window to ignore old Ramadan reports
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=30)
        messages = res.get("messages", [])
        
        # Keywords for App Funnel Version 3.0
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 2. Scan specifically for PNG ATTACHMENTS
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue
            
            for f in msg.get("files", []):
                fname = f.get("name", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")
                
                # STRICT FILTER: Target only image PNGs
                if url and ("image" in mimetype or fname.endswith(".png")):
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ Found PNG Attachment: {key}")

        # 3. Download and Relay binary PNG data
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                img_data = requests.get(data["url"], headers=headers).content
                temp_file = f"{key.lower()}.png"
                with open(temp_file, "wb") as f: f.write(img_data)

                # Post binary PNG to ensure no code blocks appear
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} snapshot posted.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
