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
        print(f"--- App Funnel v3.0 Debug Relay ---")
        
        # 1. Expand search to 48 hours for this test
        cutoff = time.time() - (48 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=50)
        messages = res.get("messages", [])
        
        print(f"DEBUG: Found {len(messages)} total messages in source channel.")

        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 2. Iterate through messages
        for msg in messages:
            ts = float(msg.get("ts", 0))
            if ts < cutoff: continue # Skip if older than 48 hours
            
            files = msg.get("files", [])
            for f in files:
                fname = f.get("name", "").lower()
                mimetype = f.get("mimetype", "").lower()
                url = f.get("url_private_download")
                
                # DEBUG: Print EVERY file the bot sees
                print(f"DEBUG: Found File -> Name: {fname} | Mimetype: {mimetype}")

                # Logic: Accept if it's an image or ends in .png
                if url and ("image" in mimetype or fname.endswith(".png")):
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ MATCH CONFIRMED: {key}")

        # 3. Relay the matches
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key} binary...")
                img_data = requests.get(data["url"], headers=headers).content
                temp_file = f"{key.lower()}.png"
                with open(temp_file, "wb") as f: f.write(img_data)

                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} snapshot posted to team channel.")
            else:
                print(f"NOTICE: {key} snapshot was not found in the search window.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
