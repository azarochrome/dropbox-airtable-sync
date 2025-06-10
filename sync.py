import os
import requests
import json

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

DROPBOX_API_URL = "https://api.dropboxapi.com/2/files/list_folder"


def list_dropbox_files():
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "path": "",
        "recursive": True,
        "include_media_info": True
    }

    print("🔍 Requesting Dropbox file list...")
    response = requests.post(DROPBOX_API_URL, headers=headers, json=payload)

    print("📦 Dropbox Response Status Code:", response.status_code)

    if not response.ok:
        print("❌ Dropbox returned error response:")
        print(response.text)
        response.raise_for_status()

    try:
        json_data = response.json()
        print(f"✅ Successfully parsed JSON. Found {len(json_data.get('entries', []))} files.")
        return json_data.get("entries", [])
    except json.JSONDecodeError:
        print("❌ Failed to decode JSON from Dropbox response:")
        print(response.text)
        raise


def upload_to_airtable(file_entry):
    airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    file_name = file_entry["name"]
    file_path = file_entry["path_display"]
    file_type = file_name.split(".")[-1]

    record = {
        "fields": {
            "File Name": file_name,
            "Dropbox Path": file_path,
            "File Type": file_type,
        }
    }

    print(f"📤 Uploading {file_name} to Airtable...")
    response = requests.post(airtable_url, headers=headers, json=record)
    print("📡 Airtable Response Status:", response.status_code)

    if not response.ok:
        print("❌ Airtable upload failed:", response.text)
        response.raise_for_status()
    else:
        print(f"✅ Uploaded: {file_name}")


def main():
    files = list_dropbox_files()
    print(f"🔁 Uploading {len(files)} files to Airtable...")
    for file in files:
        upload_to_airtable(file)


if __name__ == "__main__":
    main()
