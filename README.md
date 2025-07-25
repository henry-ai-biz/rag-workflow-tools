# 🤖 AI‑Powered Workflow Utilities

A collection of practical automation scripts developed using the Google Gemini CLI as the main coding assistant (with VSCode Copilot as a fallback). My goal is to build, iterate, and solve real‑world problems using the latest AI developer tools.

---

## 🚀 Overview

This repository showcases my journey in building practical, AI‑assisted tools and the “sub‑task” parts of a Retrieval‑Augmented Generation (RAG) pipeline. The scripts here take RAG output and turn it into runnable automations:

- **Video & Image Processing**  
  Creating video reels from still images and open‑source audio.

- **Cloud Integration**  
  Uploading and managing media assets on Google Cloud Storage.

- **Social Media Automation**  
  Posting generated content directly to platforms like Instagram via their APIs.

My goal is to demonstrate a hands‑on ability to build, iterate, and solve problems using the latest generation of AI developer tools.

---

## 🔍 A Note on Methodology

> For tasks like posting to Instagram, I interact *directly* with the Graph API instead of using higher‑level wrappers or third‑party libraries (e.g., MCP).

**Why?**  

1. Deeply understand authentication, permissions, and token management
2. Debug and iterate on the core mechanics  
3. Ensure a robust, reliable connection

---

## 🗂 Project Structure

\`\`\`
├── gcs_utilities/          # Scripts for Google Cloud Storage tasks  
├── instagram_automation/   # Tools for posting & managing Instagram content  
├── video_processing/       # Scripts for creating and editing video files  
└── ...                     # Additional utility folders
\`\`\`

---

## 🛠 Tech Stack

- **Primary Language:** Python  
- **AI Development:** Google Gemini CLI, Claude Code & API's  

**APIs & Services:**  

- Instagram Graph API  
- Google Cloud Storage API  
- Freesound API (for open‑source audio)  

**Core Libraries:**  

- requests
- google-cloud-storage  
- Pillow  
- moviepy

---

> This repository represents an active, ongoing effort. Thank you for visiting!
