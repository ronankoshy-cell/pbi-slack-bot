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
        print(f"--- App Funnel v3.0 Universal Attachment Search ---")
        
        # 1. 24-hour window
        cutoff = time.time() - (24 * 60 * 60)
        
        # 2. List ALL files (no type filter) to find the hidden PNGs
        res = client.files_list(channel=source_id, ts_from=cutoff)
        files = res.get("files", [])
        
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Precision matching by Extension and Keyword
        for f in files:
            fname = f.get("name", "").lower()
            url = f.get("url_private_download")
            
            if not url: continue
            
            # This logs every file the bot sees to help us debug
            print(f"Inspecting: {fname}")

            # Identify snapshots by '.png' and keyword
            if fname.endswith(".png"):
                for key in reports:
                    if reports[key]["kw"] in fname and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"✅ MATCH FOUND: {key} snapshot ({fname})")

        # 4. Download and Relay
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
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
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: {key} PNG not found. (Check if the subscription has been sent today)")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
