import os
import sys
import requests
import time
from slack_sdk import WebClient

# Setup
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') # funnel-snapshot-automations
target_id = os.environ.get('SLACK_CHANNEL_ID')      # Target Team Channel
client = WebClient(token=token)

def run_relay():
    try:
        print(f"--- App Funnel v3.0 Universal File Search ---")
        
        # 1. 24-hour window
        cutoff = time.time() - (24 * 60 * 60)
        
        # 2. List ALL files in the channel (bypasses message history limits)
        res = client.files_list(channel=source_id, ts_from=cutoff)
        all_files = res.get("files", [])
        
        print(f"DEBUG: Slack found {len(all_files)} total files in the last 24h.")

        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 3. Match the actual PNG attachments
        for f in all_files:
            fname = f.get("name", "").lower()
            url = f.get("url_private_download")
            mimetype = f.get("mimetype", "").lower()

            if not url: continue
            
            # Print every file found to the log for verification
            print(f"Inspecting: {fname} ({mimetype})")

            # Logic: If it contains our keyword and is an image, grab it
            if "image" in mimetype or fname.endswith(".png"):
                for key in reports:
                    if reports[key]["kw"] in fname and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"✅ MATCHED PNG: {key}")

        # 4. Download and Relay binary PNG data
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_file = f"relay_{key.lower()}.png"
                with open(temp_file, "wb") as f:
                    f.write(img_data)

                # Post as a clean binary file to the team channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: {key} PNG attachment not found.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
