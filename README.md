# YouTube Transcripts API

## Description
This project provides a REST API to fetch all transcripts of a YouTube channel using caching, proxies, and rate-limiting.

## Setup

1. Clone the repo
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Set your YouTube API key:
```
export YOUTUBE_API_KEY="YOUR_KEY"
```
4. Run the app:
5. Access the API:
```
GET http://localhost:5000/transcripts?channel=Drawfee
```


## Notes
- Uses `youtube_transcript_api` with optional proxies to avoid IP blocks.
- Caches channel IDs, video IDs, and transcripts locally in `cache.json`.
- Supports free deployment on Render or any Python web host.
