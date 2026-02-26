import os
import sys
import requests
from slack_sdk import WebClient

# 1. Configuration from GitHub Secrets
token = os.environ.get('SLACK_TOKEN')
relay_channel = os.environ.get('RELAY_CHANNEL_ID') # Private relay channel
target_channel = os.environ.get('SLACK_CHANNEL_ID') # Final public/team channel
client = WebClient(token=token)

def run_relay():
    try:
        # 2. Find the latest PNG in the relay channel
        print("Searching relay channel for the latest report...")
        result = client.files_list(channel=relay_channel, types="images", count=1)
        
        if not result.get("files"):
            print("No files found in the relay channel yet. Check your Outlook forwarder!")
            return

        latest_file = result["files"][0]
        file_url = latest_file["url_private_download"]
        file_name = latest_file["name"]

        # 3. Download the file from Slack's server using the Bot Token
        print(f"Downloading {file_name} from relay...")
        response = requests.get(file_url, headers={'Authorization': f'Bearer {token}'})
        
        if response.status_code == 200:
            with open("report.png", "wb") as f:
                f.write(response.content)
        else:
            print(f"Failed to download file: {response.status_code}")
            return

        # 4. Upload to the final target channel
        print(f"Relaying report to {target_channel}...")
        client.files_upload_v2(
            channel=target_channel,
            file="report.png",
            title="Daily Power BI Snapshot",
            initial_comment="📊 *Daily Power BI Update*\nHere is the latest snapshot relayed from the report subscription."
        )
        print("Success! Report has been relayed.")

    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_relay()
