#push local media files to Google Drive

import io
import yaml
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Load config
with open("business_config.yaml") as f:
    cfg = yaml.safe_load(f)

DRIVE_ROOT_ID       = cfg["google_drive_folder_id"]
SERVICE_ACCOUNT_KEY = cfg["service_account_file"]
LOCAL_ROOT          = Path(cfg["local_media_folder"])

# sanity check
if not LOCAL_ROOT.is_dir():
    raise FileNotFoundError(f"{LOCAL_ROOT} not found or not a directory")

# 2. Authenticate Drive API
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds  = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_KEY, scopes=SCOPES
)
drive = build("drive", "v3", credentials=creds, cache_discovery=False)

def find_or_create_folder(name, parent_id):
    """Returns folder ID for name under parent, creating it if needed."""
    resp = drive.files().list(
        q=f"'{parent_id}' in parents and name='{name}' "
          "and mimeType='application/vnd.google-apps.folder' "
          "and trashed=false",
        fields="files(id)"
    ).execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    return drive.files().create(body=meta, fields="id").execute()["id"]

def upload_new_files(local_folder: Path, drive_folder_id: str):
    """Upload any files in local_folder that don't already exist in Drive."""
    # list existing file names in that Drive folder
    resp = drive.files().list(
        q=f"'{drive_folder_id}' in parents and trashed=false",
        fields="files(name)"
    ).execute()
    existing = {f["name"] for f in resp.get("files", [])}

    for file in local_folder.iterdir():
        if file.is_file() and file.name not in existing:
            media = MediaFileUpload(str(file), resumable=True)
            drive.files().create(
                body={"name": file.name, "parents": [drive_folder_id]},
                media_body=media
            ).execute()
            print(f"Uploaded ▶ {file.name}")

if __name__ == "__main__":
    # create/find a folder named like your local one (e.g. "pics194")
    folder_name   = LOCAL_ROOT.name
    drive_folder  = find_or_create_folder(folder_name, DRIVE_ROOT_ID)
    # push everything in /.../pics194 up into Drive/.../pics194
    upload_new_files(LOCAL_ROOT, drive_folder)
