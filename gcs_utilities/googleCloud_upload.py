#!/usr/bin/env python3
"""
Uploads a local file to a private Google Cloud Storage bucket.
This script will create the bucket if it does not exist and is designed
to keep all assets private and secure. It also prevents accidental overwrites.
"""

import os
import sys
import yaml
from pathlib import Path
from google.cloud import storage
from google.cloud.exceptions import PreconditionFailed
from google.oauth2 import service_account

# --- Configuration Loading ---

def load_credentials():
    """Loads service account key path from credentials.yml."""
    print("→ Loading credentials...")
    try:
        with open('credentials.yml', 'r') as file:
            creds = yaml.safe_load(file)
            key_path = creds['gcs_service_account_key_file']
            if not Path(key_path).is_file():
                print(f"❌ Service account JSON not found at path specified in credentials.yml: {key_path}")
                sys.exit(1)
            print("✅ Credentials loaded.")
            return key_path
    except (FileNotFoundError, KeyError) as e:
        print(f"❌ Error loading credentials.yml: {e}. Make sure the file exists and contains 'gcs_service_account_key_file'.")
        sys.exit(1)

def load_business_config():
    """Loads GCS upload settings from the existing business_config.yaml structure."""
    print("→ Loading business configuration...")
    try:
        with open('business_config.yaml', 'r') as file:
            config = yaml.safe_load(file)

            # Get values from the user's existing config structure
            local_file_str = config['instagram_local_media_path']
            bucket_name_str = config['instagram_post']['gcs_bucket_name']
            blob_name_str = config['instagram_post']['gcs_object_name']

            local_path = Path(local_file_str)
            if not local_path.is_file():
                print(f"❌ Local file to upload not found at path specified in business_config.yaml: {local_path}")
                sys.exit(1)

            print("✅ Business configuration loaded.")
            return {
                "bucket_name": bucket_name_str,
                "bucket_location": config.get('bucket_location', 'us-central1'), # Keep this for flexibility
                "local_file_path": local_path,
                "destination_blob_name": blob_name_str
            }
    except (FileNotFoundError, KeyError) as e:
        print(f"❌ Error loading business_config.yaml: {e}. Make sure it contains 'instagram_local_media_path' and the 'instagram_post' section with 'gcs_bucket_name' and 'gcs_object_name'.")
        sys.exit(1)

def main():
    """
    Main function to handle authentication, bucket management, and file upload.
    """
    service_account_json = load_credentials()
    config = load_business_config()

    # 1) Authenticate
    print("→ Authenticating with Google Cloud...")
    creds = service_account.Credentials.from_service_account_file(service_account_json)
    client = storage.Client(credentials=creds, project=creds.project_id)
    print("✅ Authentication successful.")

    # 2) Get or Create Bucket (as a private bucket)
    try:
        bucket = client.get_bucket(config['bucket_name'])
        print(f"ℹ️  Bucket '{config['bucket_name']}' already exists.")
    except Exception:
        print(f" Bucket '{config['bucket_name']}' not found. Creating it in {config['bucket_location']}…")
        bucket = client.create_bucket(config['bucket_name'], location=config['bucket_location'])
        # By default, new buckets are private with uniform access. No public changes needed.
        print(f"✅ Bucket '{config['bucket_name']}' created successfully.")

    # 3) Upload the file with overwrite protection
    blob = bucket.blob(config['destination_blob_name'])
    local_file = config['local_file_path']

    print(f"→ Uploading '{local_file.name}' to 'gs://{config['bucket_name']}/{config['destination_blob_name']}'...")
    try:
        # if_generation_match=0 is a precondition that makes the upload fail
        # if an object with that name already exists. This prevents overwrites.
        blob.upload_from_filename(str(local_file), if_generation_match=0)
        print("✅ Upload successful. The file remains private.")
        print("\n---")
        print("Object Details:")
        print(f"  Bucket: {config['bucket_name']}")
        print(f"  Object: {config['destination_blob_name']}")
        print(f"  GCS Path: gs://{config['bucket_name']}/{config['destination_blob_name']}")
        print("---")

    except PreconditionFailed:
        print(f"❌ UPLOAD FAILED: A file named '{config['destination_blob_name']}' already exists in this bucket.")
        print("   Please rename the local file, change 'destination_blob_name' in your config, or delete the existing object.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during upload: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
