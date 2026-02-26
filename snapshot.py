import os
import sys
import requests
from slack_sdk import WebClient

# 1. Setup from GitHub Secrets
token = os.environ.get('SLACK_TOKEN')
relay_channel = os.environ.get('RELAY_CHANNEL_ID') # Private channel ID
target_channel = os.environ.get('SLACK_CHANNEL_ID') # Public/Team channel ID
client = WebClient(token=token)

try:
    # 2. Find the latest file in the relay channel
    print(f"Searching relay channel ({relay_channel}) for reports...")
    # types="images" ensures we only grab the PNG/JPG
    result = client.files_list(channel=relay_channel, types="images", count=1)
    
    if not result.get("files"):
        print("No images found in the relay channel. Check your Outlook forwarder!")
        sys.exit(0)

    latest_file = result["files"][0]
    file_url = latest_file["url_private_download"]
    file_name = latest_file["name"]

    # 3. Download the image using the Bot Token for auth
    print(f"Downloading {file_name}...")
    response = requests.get(file_url, headers={'Authorization': f'Bearer {token}'})
    
    if response.status_code == 200:
        with open("report.png", "wb") as f:
            f.write(response.content)
    else:
        print(f"Download failed with status: {response.status_code}")
        sys.exit(1)

    # 4. Upload to the final target channel
    print(f"Relaying report to final channel ({target_channel})...")
    client.files_upload_v2(
        channel=target_channel,
        file="report.png",
        title="Daily Power BI Snapshot",
        initial_comment="📊 *Daily Power BI Update*\nHere is the latest snapshot from the automated subscription."
    )
    print("Success! Relay complete.")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
