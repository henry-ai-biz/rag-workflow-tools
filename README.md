# 🤖 AI-Powered Workflow Utilities

A collection of practical automation scripts developed using gemini cli as the coding assistant. This repository showcases the "sub-task" part of a RAG pipeline.

► Overview
This repository is a showcase of my journey in building practical, AI-assisted tools. The scripts here are designed to integrate with the output of Retrieval-Augmented Generation (RAG) systems, which I use to create relevant and timely social media content for the small businesses I partner with.

While the core RAG and content generation scripts remain in a private repo for now, this public repository contains the operational tools that bring that content to life—automating tasks like:

Video & Image Processing: Creating video reels from still images and open-source audio.

Cloud Integration: Uploading and managing media assets on Google Cloud Services.

Social Media Automation: Posting generated content directly to platforms like Instagram via their APIs.

My goal is to demonstrate a hands-on ability to build, iterate, and solve problems using the latest generation of AI developer tools.

► A Note on Methodology
You might notice that for tasks like posting to Instagram, I am interacting directly with the Graph API instead of using higher-level abstractions or third-party libraries or even MCP. This was a deliberate choice.

Why? My focus for these initial versions was to gain a deep, foundational understanding of the entire workflow, especially the complexities of authentication, app permissions, and token management. By avoiding abstractions, I was able to effectively debug and iterate on the core mechanics, ensuring a robust and reliable connection. This hands-on approach was important for me at this stage to make sure any automation was dependable.

► Project Structure
The repository is organized by function to maintain clarity and scalability.

.
├── gcs_utilities/       # Scripts for Google Cloud Storage tasks
├── instagram_automation/  # Tools for posting and managing Instagram content
├── video_processing/      # Scripts for creating and editing video files
└── ...                    # Additional utility folders

► Tech Stack
Primary Language: Python

AI Development: Google Gemini CLI & API

APIs & Services:

Instagram Graph API

Google Cloud Storage API

Freesound API (for open-source audio)

Core Libraries: requests, google-cloud-storage, Pillow, moviepy

This repository represents an active and ongoing effort. Thank you for visiting.
