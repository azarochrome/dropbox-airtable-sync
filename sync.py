import os
import time
import requests
import json
import sys
from datetime import datetime

# Environment variable validation
def validate_env_vars():
    """Validate that all required environment variables are set."""
    required_vars = {
        "DROPBOX_TOKEN": os.getenv("DROPBOX_TOKEN"),
        "AIRTABLE_TOKEN": os.getenv("AIRTABLE_TOKEN"),
        "AIRTABLE_BASE_ID": os.getenv("AIRTABLE_BASE_ID"),
        "AIRTABLE_TABLE_NAME": os.getenv("AIRTABLE_TABLE_NAME")
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please ensure all secrets are properly configured in GitHub Actions.")
        sys.exit(1)
    
    print("✅ All environment variables are set")
    return required_vars

# Initialize environment variables
env_vars = validate_env_vars()
DROPBOX_ACCESS_TOKEN = env_vars["DROPBOX_TOKEN"]
AIRTABLE_API_KEY = env_vars["AIRTABLE_TOKEN"]
AIRTABLE_BASE_ID = env_vars["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = env_vars["AIRTABLE_TABLE_NAME"]

DROPBOX_LIST_FOLDER_URL = "https://api.dropboxapi.com/2/files/list_folder"
DROPBOX_CONTINUE_URL = "https://api.dropboxapi.com/2/files/list_folder/continue"
DROPBOX_TEMP_LINK_URL = "https://api.dropboxapi.com/2/files/get_temporary_link"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

def log(message, level="INFO"):
    """Log messages with timestamp for better debugging."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def get_temp_dropbox_link(path, max_retries=3):
    """Get temporary Dropbox link with retry logic."""
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(DROPBOX_TEMP_LINK_URL, headers=headers, json={"path": path}, timeout=30)
            if response.status_code == 200:
                return response.json().get("link")
            elif response.status_code == 429:
                wait_time = 2 ** attempt
                log(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
            else:
                log(f"Failed to get temporary link (attempt {attempt + 1}): {response.status_code} - {response.text}", "ERROR")
                if attempt == max_retries - 1:
                    return None
        except requests.exceptions.RequestException as e:
            log(f"Request error (attempt {attempt + 1}): {str(e)}", "ERROR")
            if attempt == max_retries - 1:
                return None
            time.sleep(1)
    
    return None

def record_exists(file_path):
    """Check if a record already exists in Airtable."""
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    }
    params = {
        "filterByFormula": f"{{Dropbox Path}} = '{file_path}'"
    }
    
    try:
        response = requests.get(AIRTABLE_URL, headers=headers, params=params, timeout=30)
        if response.status_code != 200:
            log(f"Airtable check failed: {response.status_code} - {response.text}", "ERROR")
            return False
        return len(response.json().get("records", [])) > 0
    except requests.exceptions.RequestException as e:
        log(f"Request error checking record existence: {str(e)}", "ERROR")
        return False

def upload_to_airtable(file_entry, category, max_retries=3):
    """Upload file entry to Airtable with improved retry logic."""
    file_name = file_entry["name"]
    file_path = file_entry["path_display"]
    file_type = file_name.split(".")[-1].lower() if "." in file_name else "unknown"
    created_at = file_entry.get("client_modified", None)

    if record_exists(file_path):
        log(f"Skipping already-synced file: {file_name}")
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

    for attempt in range(max_retries):
        try:
            log(f"Uploading {file_name} to Airtable (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(AIRTABLE_URL, headers=headers, json=record, timeout=30)

            if response.status_code == 429:
                wait_time = 2 ** attempt
                log(f"Rate limited, waiting {wait_time}s before retry")
                time.sleep(wait_time)
                continue
            elif response.status_code == 200:
                log(f"Successfully uploaded: {file_name}")
                time.sleep(0.2)  # prevent rapid-fire uploads
                return
            else:
                log(f"Airtable error (attempt {attempt + 1}): {response.status_code} - {response.text}", "ERROR")
                if attempt == max_retries - 1:
                    log(f"Failed to upload {file_name} after {max_retries} attempts", "ERROR")
                    return
                time.sleep(1)
                
        except requests.exceptions.RequestException as e:
            log(f"Request error uploading {file_name} (attempt {attempt + 1}): {str(e)}", "ERROR")
            if attempt == max_retries - 1:
                log(f"Failed to upload {file_name} after {max_retries} attempts", "ERROR")
                return
            time.sleep(1)

def list_dropbox_entries(path="", recursive=False, max_retries=3):
    """List Dropbox entries with improved error handling."""
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
    
    log(f"Listing Dropbox path: '{path or '/'}'...")
    
    for attempt in range(max_retries):
        try:
            response = requests.post(DROPBOX_LIST_FOLDER_URL, headers=headers, json=payload, timeout=30)
            if not response.ok:
                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    log(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    log(f"Dropbox error: {response.status_code} - {response.text}", "ERROR")
                    if attempt == max_retries - 1:
                        response.raise_for_status()
                    time.sleep(1)
                    continue
            
            data = response.json()
            entries.extend(data.get("entries", []))
            
            # Handle pagination
            while data.get("has_more"):
                cursor = data["cursor"]
                pagination_response = requests.post(DROPBOX_CONTINUE_URL, headers=headers, json={"cursor": cursor}, timeout=30)
                if not pagination_response.ok:
                    log(f"Pagination error: {pagination_response.status_code} - {pagination_response.text}", "ERROR")
                    break
                data = pagination_response.json()
                entries.extend(data.get("entries", []))
            
            return entries
            
        except requests.exceptions.RequestException as e:
            log(f"Request error listing entries (attempt {attempt + 1}): {str(e)}", "ERROR")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)
    
    return entries

def main():
    """Main function with improved error handling."""
    try:
        log("Starting Dropbox to Airtable sync...")
        
        # Test API connections
        log("Testing Dropbox API connection...")
        test_entries = list_dropbox_entries(path="", recursive=False)
        log(f"Dropbox API test successful, found {len(test_entries)} top-level items")
        
        log("Testing Airtable API connection...")
        headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
        test_response = requests.get(AIRTABLE_URL, headers=headers, params={"maxRecords": 1}, timeout=30)
        if test_response.status_code == 200:
            log("Airtable API test successful")
        else:
            log(f"Airtable API test failed: {test_response.status_code} - {test_response.text}", "ERROR")
            sys.exit(1)
        
        # Main sync logic
        top_level = list_dropbox_entries(path="", recursive=False)
        folders = [f for f in top_level if f[".tag"] == "folder"]
        log(f"Found {len(folders)} folders to process")
        
        total_files = 0
        processed_files = 0
        
        for folder in folders:
            folder_path = folder["path_display"]
            folder_name = folder["name"]
            log(f"Scanning folder: '{folder_name}'...")
            
            try:
                all_entries = list_dropbox_entries(path=folder_path, recursive=True)
                files = [f for f in all_entries if f[".tag"] == "file"]
                log(f"Found {len(files)} files in '{folder_name}'")
                total_files += len(files)
                
                for file in files:
                    try:
                        upload_to_airtable(file, category=folder_name)
                        processed_files += 1
                    except Exception as e:
                        log(f"Error processing file {file.get('name', 'unknown')}: {str(e)}", "ERROR")
                        
            except Exception as e:
                log(f"Error processing folder '{folder_name}': {str(e)}", "ERROR")
        
        log(f"Sync completed! Processed {processed_files}/{total_files} files")
        
    except Exception as e:
        log(f"Fatal error during sync: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
