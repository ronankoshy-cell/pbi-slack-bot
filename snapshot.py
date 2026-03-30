import os
import sys
import requests
import time
from slack_sdk import WebClient

# Setup - Mapping to your specific Secret names
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') # funnel-snapshot-automations
target_id = os.environ.get('SLACK_CHANNEL_ID')      # Target Team Channel
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Success Relay ---")
        
        # 1. Look back 24 hours
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        # Reports to find for App Funnel Version 3.0
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 2. Iterate through messages & find the hidden PNG attachments
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue
            
            # Reach into the 'files' array for the specific message
            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")
                
                if not url: continue

                # Logic: Skip the HTML body; target only the Image/PNG
                is_html = "html" in mimetype or "email" in mimetype or fname.endswith(".html")
                is_image = "image" in mimetype or fname.endswith(".png")

                if is_image and not is_html:
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ ATTACHMENT FOUND: {key} ({fname})")

        # 3. Download and Post binary PNG data
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key} PNG...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_file = f"v3_{key.lower()}.png"
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
                print(f"SKIP: No PNG attachment found for {key} snapshot today.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
