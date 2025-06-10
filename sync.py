import os
import requests
import json

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_TOKEN")  # 👈 matches your secret
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")     # 👈 matches your secret
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

DROPBOX_LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"


def list_dropbox_entries(path=""):
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "path": path,
        "recursive": False,
        "include_media_info": True
    }

    print(f"🔍 Listing Dropbox path: '{path or '/'}'")
    response = requests.post(DROPBOX_LIST_FOLDER_URL, headers=headers, json=payload)
    print("📦 Status Code:", response.status_code)

    if not response.ok:
        print("❌ Dropbox Error:", response.text)
        response.raise_for_status()

    try:
        return response.json().get("entries", [])
    except json.JSONDecodeError:
        print("❌ JSON Decode Error from Dropbox:")
        print(response.text)
        raise


def upload_to_airtable(file_entry, parent_folder):
    airtable_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    file_name = file_entry["name"]
    file_path = file_entry["path_display"]
    file_type = file_name.split(".")[-1].lower()

    record = {
        "fields": {
            "File Name": file_name,
            "Dropbox Path": file_path,
            "File Type": file_type,
            "Category": parent_folder,  # Category from folder name
        }
    }

    print(f"📤 Uploading {file_name} from '{parent_folder}' to Airtable...")
    response = requests.post(airtable_url, headers=headers, json=record)

    if not response.ok:
        print("❌ Airtable Error:", response.text)
        response.raise_for_status()
    else:
        print(f"✅ Uploaded: {file_name}")


def main():
    top_level_entries = list_dropbox_entries()

    folders = [entry for entry in top_level_entries if entry[".tag"] == "folder"]

    print(f"📁 Found {len(folders)} top-level folders.")

    for folder in folders:
        folder_path = folder["path_display"]
        folder_name = folder["name"]

        files = list_dropbox_entries(path=folder_path)
        files = [f for f in files if f[".tag"] == "file"]

        print(f"📂 Syncing {len(files)} files from folder '{folder_name}'...")

        for file in files:
            upload_to_airtable(file, parent_folder=folder_name)


if __name__ == "__main__":
    main()
