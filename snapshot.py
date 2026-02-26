import os
import sys
import requests
import time
from slack_sdk import WebClient

# Configuration from GitHub Secrets
token = os.environ.get('SLACK_TOKEN')
relay_id = os.environ.get('RELAY_CHANNEL_ID')
target_id = os.environ.get('SLACK_CHANNEL_ID')
client = WebClient(token=token)

def run_relay():
    try:
        print("--- Today's Targeted Multi-Report Relay ---")
        
        # 1. Define 'Today' (Messages from the last 24 hours only)
        day_in_seconds = 24 * 60 * 60
        cutoff_time = time.time() - day_in_seconds

        # 2. Fetch history from the private relay channel
        res = client.conversations_history(channel=relay_id, limit=20)
        messages = res.get("messages", [])
        
        # Define our mapping for keywords, specific messages, and found URLs
        reports = {
            "Overall": {
                "keyword": "overall",
                "message": "Hi Team, Sharing the Overall Ramadan Funnel View Snapshot",
                "url": None
            },
            "iOS": {
                "keyword": "ios",
                "message": "Hi Team, Sharing the iOS Ramadan Funnel View Snapshot",
                "url": None
            },
            "Android": {
                "keyword": "android",
                "message": "Hi Team, Sharing the Android Ramadan Funnel View Snapshot",
                "url": None
            }
        }

        # 3. Scan messages for today's snapshots
        for msg in messages:
            msg_ts = float(msg.get("ts", 0))
            if msg_ts < cutoff_time:
                continue # Ignore old reports from previous days

            # Email integrations often wrap PNGs in 'files' or 'attachments'
            items = msg.get("files", []) + msg.get("attachments", [])
            for item in items:
                search_text = str(item).lower()
                # Get the secure download URL
                url = item.get("url_private_download") or item.get("image_url")
                
                if not url: continue

                # Match found URL to the correct category based on keywords
                for key in reports:
                    if reports[key]["keyword"] in search_text and not reports[key]["url"]:
                        reports[key]["url"] = url
                        print(f"Matched Today's {key} Report.")

        # 4. Download and Relay with specific messages
        headers = {'Authorization': f'Bearer {token}'}
        found_any = False

        for key, data in reports.items():
            if data["url"]:
                print(f"Relaying {key}...")
                img_data = requests.get(data["url"], headers=headers).content
                filename = f"{key.lower()}.png"
                
                with open(filename, "wb") as f:
                    f.write(img_data)

                # Post to final channel with your specific requested message
                client.files_upload_v2(
                    channel=target_id, 
                    file=filename, 
                    title=f"Ramadan Funnel - {key}",
                    initial_comment=data["message"]
                )
                found_any = True
            else:
                print(f"Note: No fresh {key} report found for today.")

        if found_any:
            print("SUCCESS: Today's snapshots relayed.")
        else:
            print("FINISH: No new snapshots found in the 24-hour window.")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
