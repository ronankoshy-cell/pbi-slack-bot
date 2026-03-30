import os
import sys
import requests
import time
from slack_sdk import WebClient

# 1. Setup
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') 
target_id = os.environ.get('SLACK_CHANNEL_ID')      
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Deep-Scan Relay ---")
        
        # 2. Window: 48 hours for this test to ensure we find the latest ones
        cutoff = time.time() - (48 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Aggressive Search: Look in 'files', 'attachments', and 'blocks'
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue
            
            # Combine all potential data sources where Slack hides images
            potential_files = msg.get("files", []) + msg.get("attachments", [])
            
            for f in potential_files:
                # Check filename, title, or image_url
                fname = (f.get("name") or f.get("title") or f.get("fallback") or "").lower()
                url = f.get("url_private_download") or f.get("image_url")
                mimetype = str(f.get("mimetype", "")).lower()

                if not url: continue
                
                # Logic: If it's a PNG or an Image type, check keywords
                if "image" in mimetype or ".png" in fname or "snapshot" in fname:
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ FOUND HIDDEN IMAGE: {key} ({fname})")

        # 4. Download and Relay
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                temp_file = f"final_{key.lower()}.png"
                with open(temp_file, "wb") as f: f.write(img_data)

                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: No hidden PNG found for {key} snapshot.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
