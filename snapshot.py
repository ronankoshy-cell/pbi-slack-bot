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
        print(f"--- App Funnel v3.0 Deep-Discovery Relay ---")
        
        # 1. 24-hour window
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        reports = {
            "Overall": {"kw": "overall", "url": None},
            "iOS": {"kw": "ios", "url": None},
            "Android": {"kw": "android", "url": None}
        }

        # 2. Look in 'files' AND 'attachments' (where the "1 attachment" is hidden)
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue
            
            # Combine all possible file locations
            items = msg.get("files", []) + msg.get("attachments", [])
            
            for item in items:
                fname = (item.get("name") or item.get("title") or item.get("fallback") or "").lower()
                url = item.get("url_private_download") or item.get("image_url")
                mimetype = str(item.get("mimetype", "")).lower()

                if not url: continue
                
                # Logic: Skip the HTML body; target the hidden Image
                is_html = "html" in mimetype or "email" in mimetype or fname.endswith(".html")
                is_image = "image" in mimetype or fname.endswith(".png") or "snapshot" in fname

                if is_image and not is_html:
                    for key in reports:
                        if reports[key]["kw"] in fname and not reports[key]["url"]:
                            reports[key]["url"] = url
                            print(f"✅ FOUND HIDDEN ATTACHMENT: {key} ({fname})")

        # 3. Relay binary data
        headers = {'Authorization': f'Bearer {token}'}
        for key in reports:
            if reports[key]["url"]:
                img_data = requests.get(reports[key]["url"], headers=headers).content
                temp_file = f"v3_{key.lower()}.png"
                with open(temp_file, "wb") as f: f.write(img_data)

                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_file, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=f"Hi Team, Sharing the {key} App Funnel Snapshot"
                )
                os.remove(temp_file)
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: No {key} PNG found. (Bot only saw the email HTML wrapper)")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
