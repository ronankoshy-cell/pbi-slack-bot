import os
import sys
import requests
import re
import time
from slack_sdk import WebClient

# 1. Setup
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print("--- Precision Image Relay: Landmark Edition ---")
        
        # 2. Get today's messages (24h window)
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=relay_id, limit=20)
        messages = res.get("messages", [])
        
        # 3. Define our targets with the correct keys
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall Ramadan Funnel View Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS Ramadan Funnel View Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android Ramadan Funnel View Snapshot", "url": None}
        }

        # 4. Scrape the HTML for hosted image links
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue

            text_content = str(msg)
            # Find URLs pointing to the Slack origin servers
            found_urls = re.findall(r'https://[^\s"\'<>]*files-origin\.slack\.com/[^\s"\'<>]+', text_content)
            
            for raw_url in found_urls:
                url = raw_url.replace('\\', '')
                for key, data in reports.items():
                    if data["kw"] in text_content.lower() and not data["url"]:
                        data["url"] = url
                        print(f"Matched Image for: {key}")

        # 5. Download and Re-Upload
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_filename = f"today_{key.lower()}.png"
                with open(temp_filename, "wb") as f:
                    f.write(img_data)

                # Post to target channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_filename, 
                    title=f"Ramadan Funnel - {key}",
                    initial_comment=data["text"] # Fixed the key name here
                )
                print(f"SUCCESS: {key} relayed.")
                os.remove(temp_filename) # Cleanup
            else:
                print(f"SKIP: No today's snapshot found for {key}.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
