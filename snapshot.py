import os
import sys
import requests
import re
import time
from slack_sdk import WebClient

# Configuration
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print("--- Precision Image Relay Started ---")
        
        # 1. Get today's messages (24h window)
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=relay_id, limit=20)
        messages = res.get("messages", [])
        
        # 2. Define our targets
        reports = {
            "Overall": {"kw": "overall", "msg": "Hi Team, Sharing the Overall Ramadan Funnel View Snapshot", "url": None},
            "iOS": {"kw": "ios", "msg": "Hi Team, Sharing the iOS Ramadan Funnel View Snapshot", "url": None},
            "Android": {"kw": "android", "msg": "Hi Team, Sharing the Android Ramadan Funnel View Snapshot", "url": None}
        }

        # 3. Scan messages for HIDDEN image links
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue

            # Search the entire message body (HTML) for Slack-hosted image URLs
            text_content = str(msg)
            # This regex finds the actual image hosting link inside the HTML source
            found_urls = re.findall(r'https://[^\s"\'<>]*files-origin\.slack\.com/[^\s"\'<>]+', text_content)
            
            for raw_url in found_urls:
                url = raw_url.replace('\\', '') # Clean up escape characters
                # Match URL to the correct category based on the message's context or filename
                for key, data in reports.items():
                    if data["kw"] in text_content.lower() and not data["url"]:
                        data["url"] = url
                        print(f"Matched Image for: {key}")

        # 4. Download and Re-Upload as clean PNGs
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Downloading {key} PNG...")
                img_data = requests.get(data["url"], headers=headers).content
                
                with open("temp.png", "wb") as f:
                    f.write(img_data)

                # Post to target channel
                client.files_upload_v2(
                    channel=target_id, 
                    file="temp.png", 
                    title=f"Ramadan Funnel - {key}",
                    initial_comment=data["message"]
                )
                print(f"SUCCESS: {key} posted.")
            else:
                print(f"SKIP: No today's snapshot found for {key}.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
