#!/usr/bin/env python3
"""
Post a Reel to Instagram using a short-lived, signed GCS URL for the video.
"""

import requests
import time
import yaml
import sys
from google.cloud import storage
from datetime import timedelta

# === CONFIGURATION ===
API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

# === LOAD CREDENTIALS & CONFIG ===
def load_credentials():
    """Loads all necessary secrets from the credentials file."""
    print("→ Loading credentials...")
    try:
        with open('credentials.yml', 'r') as file:
            creds = yaml.safe_load(file)
            print("✅ Credentials loaded.")
            return {
                "instagram_id": creds['instagram_id'],
                "page_access_token": creds['page_access_token'],
                "gcs_service_account_key_file": creds['service_account_file']
            }
    except (FileNotFoundError, KeyError) as e:
        print(f"❌ Error loading credentials.yml: {e}. Make sure the file exists and contains all required keys.")
        sys.exit(1)

def load_business_config():
    """Loads all necessary business settings from the config file."""
    print("→ Loading business configuration...")
    try:
        with open('business_config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            print("✅ Business configuration loaded.")
            return {
                "gcs_bucket_name": config['instagram_post']['gcs_bucket_name'],
                "gcs_object_name": config['instagram_post']['gcs_object_name'],
                "caption": config['instagram_post']['caption']
            }
    except (FileNotFoundError, KeyError) as e:
        print(f"❌ Error loading business_config.yaml: {e}. Make sure the file exists and contains the required structure.")
        sys.exit(1)

def generate_signed_url(service_account_key_file, bucket_name, object_name, expiration_minutes=15):
    """
    Generates a short-lived, signed URL for a private GCS object.
    """
    print(f"→ Generating signed URL for gs://{bucket_name}/{object_name}...")
    try:
        storage_client = storage.Client.from_service_account_json(service_account_key_file)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )
        print(f"✅ Signed URL created. Valid for {expiration_minutes} minutes.")
        return signed_url
    except Exception as e:
        print(f"❌ Failed to generate signed URL: {e}")
        sys.exit(1)

def create_media_container(ig_account_id, access_token, video_url, caption):
    """
    Step 1: Create the IG media container pointing at your signed video_url.
    """
    print("→ Creating media container…")
    resp = requests.post(
        f"{BASE_URL}/{ig_account_id}/media",
        params={
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption,
            "access_token": access_token
        }
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print(f"✅ Container ID: {container_id}")

    # Poll until ready
    while True:
        status_resp = requests.get(
            f"{BASE_URL}/{container_id}",
            params={
                "fields":       "status_code",
                "access_token": access_token
            }
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")

        print(f"   Processing status: {status}")
        if status == "FINISHED":
            print("✅ Video processing complete.")
            return container_id
        if status == "ERROR":
            print(f"❌ Video processing failed. Full error response: {status_resp.text}")
            sys.exit(1)
        time.sleep(5)

def publish_media(ig_account_id, access_token, creation_id):
    """
    Step 2: Publish the finished container.
    """
    print("→ Publishing media container…")
    resp = requests.post(
        f"{BASE_URL}/{ig_account_id}/media_publish",
        params={
            "creation_id":  creation_id,
            "access_token": access_token
        }
    )
    resp.raise_for_status()
    media_id = resp.json()["id"]
    print(f"✅ Successfully posted! Media ID: {media_id}")
    return media_id

if __name__ == "__main__":
    credentials = load_credentials()
    config = load_business_config()

    # Generate the temporary URL for the private GCS video
    signed_video_url = generate_signed_url(
        service_account_key_file=credentials['gcs_service_account_key_file'],
        bucket_name=config['gcs_bucket_name'],
        object_name=config['gcs_object_name']
    )

    # Run the upload + publish flow
    container_id = create_media_container(
        credentials['instagram_id'],
        credentials['page_access_token'],
        signed_video_url,
        config['caption']
    )
    publish_media(
        credentials['instagram_id'],
        credentials['page_access_token'],
        container_id
    )
