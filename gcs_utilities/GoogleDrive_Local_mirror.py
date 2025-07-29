import io
import yaml
import argparse
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def load_business_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_args():
    p = argparse.ArgumentParser(
        description="Download the latest Drive subfolder into local_media_root"
    )
    p.add_argument(
        "--config", "-c", required=True,
        help="Path to your business_config.yaml"
    )
    return p.parse_args()

def main():
    args = get_args()
    cfg = load_business_config(args.config)

    DRIVE_ROOT_ID     = cfg["google_drive_folder_id"]
    SERVICE_ACCOUNT   = cfg["service_account_file"]
    LOCAL_MEDIA_ROOT  = Path(cfg["local_media_root"])
    LOCAL_MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

    # Auth (readonly)
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    creds  = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT, scopes=SCOPES
    )
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    # 1) Grab the single most-recent folder under your root:
    resp = drive.files().list(
        q=(
            f"'{DRIVE_ROOT_ID}' in parents "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        ),
        orderBy="createdTime desc",
        pageSize=1,
        fields="files(id,name,createdTime)"
    ).execute()

    folders = resp.get("files", [])
    if not folders:
        raise FileNotFoundError("No sub-folders found under Drive root.")
    latest = folders[0]
    drive_folder_id   = latest["id"]
    drive_folder_name = latest["name"]
    print(f"🕒 Latest Drive folder: {drive_folder_name} (created {latest['createdTime']})")

    # 2) Prepare local target <local_media_root>/<folder_name>
    local_target = LOCAL_MEDIA_ROOT / drive_folder_name
    local_target.mkdir(parents=True, exist_ok=True)

    # 3) List and download new files
    resp = drive.files().list(
        q=f"'{drive_folder_id}' in parents and trashed=false",
        fields="files(id,name)"
    ).execute()

    existing = {p.name for p in local_target.iterdir() if p.is_file()}
    for f in resp.get("files", []):
        name = f["name"]
        if name in existing:
            continue
        request = drive.files().get_media(fileId=f["id"])
        dest = local_target / name
        with io.FileIO(dest, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        print(f"Downloaded ▼ {name}")

if __name__ == "__main__":
    main()
