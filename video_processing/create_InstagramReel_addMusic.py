import os
import re
import random
import requests
import shutil
import yaml
from moviepy.editor import (ImageClip, concatenate_videoclips, AudioFileClip, 
                            CompositeVideoClip, ColorClip)
from moviepy.video.fx import all as vfx 

# --- Configuration ---

# Freesound API Key
try:
    with open('credentials.yml', 'r') as file:
        FREESOUND_API_KEY = yaml.safe_load(file)['freesound']
except FileNotFoundError:
    print("Error: `credentials.yml` not found. Please create it with your Freesound API key.")
    exit()
except KeyError:
    print("Error: 'freesound' key not found in `credentials.yml`.")
    exit()

# List of queries for background music suitable for showcasing masonry
MUSIC_QUERIES = [
    "corporate",
    "inspirational",
    "uplifting",
    "cinematic",
    "motivational",
    "powerful"
]

# --- Functions ---

def get_freesound_music(query, duration_range=(30, 300)):
    """
    Searches Freesound for music, downloads a random selection, and returns its path.
    """
    url = "https://freesound.org/apiv2/search/text/"
    headers = {"Authorization": f"Token {FREESOUND_API_KEY}"}
    params = {
        "query": query,
        "filter": f"duration:[{duration_range[0]} TO {duration_range[1]}] tag:music license:\"Creative Commons 0\"",
        "fields": "id,name,previews,duration"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Freesound: {e}")
        return None

    results = response.json().get("results", [])
    if not results:
        print(f"No results found for query: '{query}'")
        return None

    selected_sound = random.choice(results)
    music_url = selected_sound['previews']['preview-hq-mp3']
    
    # Sanitize filename to prevent path issues
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", selected_sound['name'])
    music_path = f"/tmp/{safe_filename}.mp3"

    try:
        with requests.get(music_url, stream=True) as r:
            r.raise_for_status()
            with open(music_path, "wb") as music_file:
                shutil.copyfileobj(r.raw, music_file)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading music file: {e}")
        return None

    print(f"Selected music: {selected_sound['name']} (Duration: {selected_sound['duration']:.2f}s)")
    return music_path

def natural_sort_key(s):
    """
    Provides a key for natural sorting of filenames (e.g., 'image1', 'image2', 'image10').
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def cleanup_temp_file(file_path):
    """
    Removes a temporary file if it exists.
    """
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        print(f"Cleaned up temporary file: {file_path}")

def create_video_with_music(image_paths, output_video_path, fps=24, duration_per_image=2, volume=0.5):
    """
    Creates a 16:9 video from images, adds background music, and handles cleanup.
    Prioritizes output quality.
    """
    if not image_paths:
        print("No images found to create a video.")
        return

    # --- Create Video Clips ---
    target_size = (1920, 1080)  # Standard 16:9 aspect ratio
    clips = []
    for img_path in image_paths:
        # Create a black background clip
        bg_clip = ColorClip(size=target_size, color=(0, 0, 0), duration=duration_per_image)
        
        # Create an image clip and set its duration
        img_clip = ImageClip(img_path).set_duration(duration_per_image)

        # --- New Resizing Logic to Preserve Quality ---
        # Don't upscale images smaller than the target frame.
        if img_clip.size[0] > target_size[0] or img_clip.size[1] > target_size[1]:
            # Resize only if the image is larger than the frame, maintaining aspect ratio.
            img_clip = img_clip.resize(height=target_size[1])
            if img_clip.size[0] > target_size[0]:
                img_clip = img_clip.resize(width=target_size[0])

        # Center the (potentially resized) image on the black background
        final_image_clip = CompositeVideoClip([bg_clip, img_clip.set_position("center")])
        clips.append(final_image_clip)
        
    final_clip = concatenate_videoclips(clips, method="compose")

    # --- Add Audio ---
    music_path = None
    random.shuffle(MUSIC_QUERIES) # Try different queries
    for query in MUSIC_QUERIES:
        music_path = get_freesound_music(query=query)
        if music_path:
            break # Stop once we find a suitable track
    
    try:
        if music_path:
            music = AudioFileClip(music_path).volumex(volume)
            if music.duration < final_clip.duration:
                music = music.fx(vfx.loop, duration=final_clip.duration)
            else:
                music = music.subclip(0, final_clip.duration)
            
            final_clip = final_clip.set_audio(music)
        else:
            print("Could not find suitable music. Video will have no audio.")

        # --- Write Video File with High-Quality Settings ---
        final_clip.write_videofile(
            output_video_path,
            codec='libx264',
            bitrate='8000k',       # Set a high bitrate for better quality
            preset='slow',         # Use a slower preset for better compression
            fps=fps,
            audio_codec="aac"
        )
        print(f"\n✅ Video saved successfully to: {output_video_path}")

    finally:
        # --- Cleanup ---
        cleanup_temp_file(music_path)