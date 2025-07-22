
"""
1) Generate a signed GCS URL for a private video  
2) Verify the URL is reachable  
3) Create an IG Reels container pointing at that URL  
4) Poll until processing is FINISHED  
5) Publish the Reel to your Business Instagram feed
"""

import requests
import time
import yaml
import sys
from google.cloud import storage
from datetime import timedelta

API_VERSION = "v19.0"
BASE_URL    = f"https://graph.facebook.com/{API_VERSION}"

def load_credentials():
    with open("credentials.yml", "r") as f:
        creds = yaml.safe_load(f)
    return (
        creds["instagram_id"],            # Your IG Business Account ID
        creds["page_access_token"],       # Long‑lived Page access token
        creds["service_account_file"]     # Path to your GCS service account JSON
    )

def load_business_config():
    with open("business_config.yaml", "r") as f:
        cfg = yaml.safe_load(f)["instagram_post"]
    return (
        cfg["gcs_bucket_name"],           # e.g. "my-private-bucket"
        cfg["gcs_object_name"],           # e.g. "videos/my_reel.mp4"
        cfg["caption"]                    # Your reel caption; generated via a RAG pipeline
    )

def generate_signed_url(keyfile, bucket, obj, expiration_minutes=15):
    client = storage.Client.from_service_account_json(keyfile)
    blob   = client.bucket(bucket).blob(obj)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
        query_parameters={"alt": "media"}  # ensure raw bytes
    )

def verify_url(url):
    print("→ Verifying signed URL…")
    resp = requests.head(url)
    resp.raise_for_status()
    ct = resp.headers.get("Content-Type", "")
    print(f"✅ URL reachable (status {resp.status_code}, content-type {ct})\n")

def create_media_container(ig_id, token, video_url, caption):
    print("→ Creating IG media container…")
    resp = requests.post(
        f"{BASE_URL}/{ig_id}/media",
        data={
            "media_type":   "REELS",
            "video_url":    video_url,
            "caption":      caption,
            "share_to_feed":"true",
            "access_token": token
        }
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print("✅ Container ID:", container_id, "\n")
    return container_id

def wait_until_finished(container_id, token, interval=5):
    print("→ Polling for processing status…")
    while True:
        resp = requests.get(
            f"{BASE_URL}/{container_id}",
            params={
                "fields":       "status_code",
                "access_token": token
            }
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        print("   status_code =", status)
        if status == "FINISHED":
            print("✅ Video processing complete.\n")
            return
        if status == "ERROR":
            raise RuntimeError("Processing failed: " + str(resp.json()))
        time.sleep(interval)

def publish_media(ig_id, token, creation_id):
    print("→ Publishing media container…")
    resp = requests.post(
        f"{BASE_URL}/{ig_id}/media_publish",
        data={
            "creation_id":  creation_id,
            "access_token": token
        }
    )
    resp.raise_for_status()
    media_id = resp.json()["id"]
    print("✅ Successfully published! Media ID:", media_id)
    return media_id

def main():
    ig_id, access_token, keyfile = load_credentials()
    bucket, obj, caption         = load_business_config()

    signed_url   = generate_signed_url(keyfile, bucket, obj, expiration_minutes=15)
    print("🔗 Signed URL:\n", signed_url, "\n")
    verify_url(signed_url)

    container_id = create_media_container(ig_id, access_token, signed_url, caption)
    wait_until_finished(container_id, access_token)
    publish_media(ig_id, access_token, container_id)

if __name__ == "__main__":
    main()
