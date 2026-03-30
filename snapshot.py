import os
import sys
import requests
import re
import time
from slack_sdk import WebClient

# 1. Setup - Using your current secrets
token = os.environ.get('SLACK_TOKEN')
source_id = os.environ.get('AUTOMATION_CHANNEL_ID') 
target_id = os.environ.get('SLACK_CHANNEL_ID')      
client = WebClient(token=token)

def run_relay():
    try:
        print("--- App Funnel v3.0 Regex Scraper Relay ---")
        
        # 2. Get today's messages (24h window)
        cutoff = time.time() - (24 * 60 * 60)
        res = client.conversations_history(channel=source_id, limit=40)
        messages = res.get("messages", [])
        
        # 3. Targets for App Funnel Version 3.0
        reports = {
            "Overall": {"kw": "overall", "text": "Hi Team, Sharing the Overall App Funnel Snapshot", "url": None},
            "iOS": {"kw": "ios", "text": "Hi Team, Sharing the iOS App Funnel Snapshot", "url": None},
            "Android": {"kw": "android", "text": "Hi Team, Sharing the Android App Funnel Snapshot", "url": None}
        }

        # 4. Scrape the raw message string for hosted image links (Your working method!)
        for msg in messages:
            if float(msg.get("ts", 0)) < cutoff: continue

            text_content = str(msg).lower()
            
            # Find URLs pointing to the Slack origin servers where the PNGs are stored
            found_urls = re.findall(r'https://[^\s"\'<>]*files-origin\.slack\.com/[^\s"\'<>]+', str(msg))
            
            for raw_url in found_urls:
                url = raw_url.replace('\\', '')
                
                # Match the URL to the correct report based on the keywords in the email
                for key, data in reports.items():
                    if data["kw"] in text_content and not data["url"]:
                        data["url"] = url
                        print(f"✅ Regex Matched Image Link for: {key}")

        # 5. Download and Re-Upload
        headers = {'Authorization': f'Bearer {token}'}
        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                
                temp_filename = f"today_{key.lower()}.png"
                with open(temp_filename, "wb") as f:
                    f.write(img_data)

                # Post clean binary to target channel
                client.files_upload_v2(
                    channel=target_id, 
                    file=temp_filename, 
                    title=f"App Funnel v3.0 - {key}",
                    initial_comment=data["text"]
                )
                print(f"SUCCESS: {key} relayed.")
                os.remove(temp_filename)
            else:
                print(f"SKIP: No today's snapshot found for {key}.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
