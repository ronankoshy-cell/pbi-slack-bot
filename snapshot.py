import os
import sys
import requests
import time
from slack_sdk import WebClient

# 1. Setup - Mapping to your Secrets
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') 
target_id = os.environ.get('SLACK_CHANNEL_ID')      
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Binary-Strict Relay ---")
        
        # 24-hour search window
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 2. Iterate through messages & filter out the HTML "Trap"
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue
            
            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")
                
                if not url: continue

                # HARD EXCLUSION: Ignore anything that is HTML or Email text
                is_html = "html" in mimetype or "email" in mimetype or fname.endswith(".html")
                is_image = "image/png" in mimetype or fname.endswith(".png")

                if is_image and not is_html:
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ REAL PNG ATTACHMENT MATCHED: {key} ({fname})")

        # 3. Download and Post binary PNG data
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key} PNG...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_file = f"final_{key.lower()}.png"
                with open(temp_file, "wb") as f: f.write(img_data)

                # Post as binary file to ensure it renders as a picture
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} snapshot posted.")
            else:
                print(f"SKIP: {key} PNG not found (only HTML was detected).")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
