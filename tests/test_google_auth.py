#!/usr/bin/env python3
"""
Quick script to verify Google Drive & Sheets access via your newly created OAuth Client.
"""

from harness.google_auth import get_google_access_token
import urllib.request
import json

def test_drive():
    print("Testing Google Drive / Sheets connection...")
    token = get_google_access_token()
    if not token:
        print("❌ Could not get access token.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # List files in Google Drive
    req = urllib.request.Request(
        "https://www.googleapis.com/drive/v3/files?pageSize=5&fields=files(id,name,mimeType)",
        headers=headers
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("🎉 SUCCESS! Connected to your Google Drive & Sheets account.")
            print(f"Found {len(data.get('files', []))} files in Drive:")
            for f in data.get("files", []):
                print(f"  • {f['name']} ({f['mimeType']})")
    except Exception as err:
        print(f"❌ Error connecting to Google Drive API: {err}")

if __name__ == "__main__":
    test_drive()
