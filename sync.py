import os
import requests

DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]
AIRTABLE_TOKEN = os.environ["AIRTABLE_TOKEN"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]
TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]

DROPBOX_FOLDER = "/"  # e.g. "/Shoots" or "/" for root

def list_dropbox_files():
    res = requests.post(
        "https://api.dropboxapi.com/2/files/list_folder",
        headers={"Authorization": f"Bearer {DROPBOX_TOKEN}",
                 "Content-Type": "application/json"},
        json={"path": DROPBOX_FOLDER, "recursive": False}
    )
    return res.json().get("entries", [])

def get_share_link(path):
    res = requests.post(
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        headers={"Authorization": f"Bearer {DROPBOX_TOKEN}",
                 "Content-Type": "application/json"},
        json={"path": path, "settings": {"requested_visibility": "public"}}
    )
    link = res.json().get("url", "")
    return link.replace("?dl=0", "?raw=1")

def detect_file_type(name):
    ext = name.lower().split(".")[-1]
    return "Image" if ext in ["jpg", "jpeg", "png", "gif"] else "Video" if ext in ["mp4", "mov"] else "Other"

def push_to_airtable(name, url, file_type, created_time):
    data = {
        "fields": {
            "File Name": name,
            "Dropbox Share Link": url,
            "File Type": file_type,
            "Date Created": created_time,
            "Category": "Auto-sync"
        }
    }
    r = requests.post(
        f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}",
        headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}",
                 "Content-Type": "application/json"},
        json=data
    )
    print(r.status_code, r.text)

def main():
    for file in list_dropbox_files():
        if file[".tag"] != "file":
            continue
        name = file["name"]
        path = file["path_lower"]
        date = file["client_modified"]
        url = get_share_link(path)
        file_type = detect_file_type(name)
        push_to_airtable(name, url, file_type, date)

if __name__ == "__main__":
    main()
