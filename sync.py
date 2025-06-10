import os
import time
import requests
import json

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

DROPBOX_LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
DROPBOX_CONTINUE_URL = "https://api.dropboxapi.com/2/files/list_folder/continue"
DROPBOX_TEMP_LINK_URL = "https://api.dropboxapi.com/2/files/get_temporary_link"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"


def get_temp_dropbox_link(path):
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(DROPBOX_TEMP_LINK_URL, headers=headers, json={"path": path})
    if response.status_code == 200:
        return response.json().get("link")
    else:
        print("⚠️ Failed to get temporary link:", response.text)
        return None


def record_exists(file_path):
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    }
    params = {
        "filterByFormula": f"{{Dropbox Path}} = '{file_path}'"
    }
    response = requests.get(AIRTABLE_URL, headers=headers, params=params)
    if response.status_code != 200:
        print("⚠️ Airtable check failed:", response.text)
        return False
    return len(response.json().get("records", [])) > 0


def upload_to_airtable(file_entry, category):
    file_name = file_entry["name"]
    file_path = file_entry["path_display"]
    file_type = file_name.split(".")[-1].lower()
    created_at = file_entry.get("client_modified", None)

    if record_exists(file_path):
        print(f"⏭️ Skipping already-synced file: {file_name}")
        return

    preview_url = get_temp_dropbox_link(file_entry["path_lower"])

    record = {
        "fields": {
            "File Name": file_name,
            "Dropbox Path": file_path,
            "File Type": file_type,
            "Category": category,
        }
    }

    if created_at:
        record["fields"]["Date Created"] = created_at

    if preview_url:
        record["fields"]["Media Preview"] = [{"url": preview_url}]
        record["fields"]["Media Download"] = [{"url": preview_url}]
        record["fields"]["Media URL (optional)"] = preview_url

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"📤 Uploading {file_name} to Airtable...")
    response = requests.post(AIRTABLE_URL, headers=headers, json=record)

    if response.status_code == 429:
        print("⏳ Rate limited. Retrying...")
        time.sleep(1)
        upload_to_airtable(file_entry, category)
    elif not response.ok:
        print("❌ Airtable error:", response.text)
    else:
        print(f"✅ Uploaded: {file_name}")
        time.sleep(0.2)  # prevent rapid-fire uploads


def list_dropbox_entries(path="", recursive=False):
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "path": path,
        "recursive": recursive,
        "include_media_info": True
    }
    entries = []
    print(f"🔍 Listing Dropbox path: '{path or '/'}'...")
    response = requests.post(DROPBOX_LIST_FOLDER_URL, headers=headers, json=payload)
    if not response.ok:
        print("❌ Dropbox error:", response.text)
        response.raise_for_status()
    data = response.json()
    entries.extend(data.get("entries", []))
    while data.get("has_more"):
        cursor = data["cursor"]
        response = requests.post(DROPBOX_CONTINUE_URL, headers=headers, json={"cursor": cursor})
        if not response.ok:
            print("❌ Pagination error:", response.text)
            break
        data = response.json()
        entries.extend(data.get("entries", []))
    return entries


def main():
    top_level = list_dropbox_entries(path="", recursive=False)
    folders = [f for f in top_level if f[".tag"] == "folder"]
    print(f"📁 Found {len(folders)} folders.")
    for folder in folders:
        folder_path = folder["path_display"]
        folder_name = folder["name"]
        print(f"\n📂 Scanning '{folder_name}'...")
        all_entries = list_dropbox_entries(path=folder_path, recursive=True)
        files = [f for f in all_entries if f[".tag"] == "file"]
        print(f"📦 Found {len(files)} files in '{folder_name}'")
        for file in files:
            upload_to_airtable(file, category=folder_name)


if __name__ == "__main__":
    main()
