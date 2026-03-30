import os
import sys
import requests
import time
from slack_sdk import WebClient

# Setup - Using your specific Secret names
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') # funnel-snapshot-automations
target_id = os.environ.get('SLACK_CHANNEL_ID')      # Target Team Channel
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Deep-Dive Attachment Search ---")
        
        # 1. 24-hour window
        cutoff = time.time() - (24 * 60 * 60)
        
        # 2. Get message history to find files attached to those emails
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Look inside messages for image attachments
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts < cutoff: continue
            
            # Check files attached to this specific message
            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")
                
                if not url: continue
                
                # Identify if it is an actual image (skips the email wrapper)
                if "image" in mimetype or fname.endswith(".png"):
                    print(f"Inspecting Image: {fname}")
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ MATCH FOUND: {key} snapshot")

        # 4. Download and Relay
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_file = f"v3_{key.lower()}.png"
                with open(temp_file, "wb") as f:
                    f.write(img_data)

                # Post binary PNG to the team channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: {key} PNG not found in today's messages.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
