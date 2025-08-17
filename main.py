import os
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import GenericProxyConfig
import time, random, logging, json, os
from youtube_data import get_all_video_ids
from proxy_randomizer import RegisteredProviders

API_KEY = os.environ.get("YOUTUBE_API_KEY")
CACHE_FILE = "cache.json"
RATE_LIMIT_SECONDS = 1.0
RP = RegisteredProviders()
RP.parse_providers()

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {"channelIds": {}, "videoIds": {}, "transcripts": {}}

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def log_cache_hit_or_miss(name, hit):
    logging.info(f"{'Cache hit' if hit else 'Cache miss'}: {name}")

def get_transcript(video_id):
    if video_id in cache["transcripts"]:
        log_cache_hit_or_miss(f"transcript for {video_id}", True)
        return cache["transcripts"][video_id]

    log_cache_hit_or_miss(f"transcript for {video_id}", False)
    proxy = RP.get_random_proxy().get_proxy()
    api = YouTubeTranscriptApi(
        proxy_config=GenericProxyConfig(
            http_url=proxy
        )
    )

    for attempt in range(5):
        try:
            transcript = api.fetch(video_id)
            text = " ".join([t["text"] for t in transcript])
            cache["transcripts"][video_id] = {"text": text}
            save_cache()
            time.sleep(RATE_LIMIT_SECONDS)
            return cache["transcripts"][video_id]
        except (TranscriptsDisabled, NoTranscriptFound):
            logging.warning(f"No transcript available for {video_id}")
            cache["transcripts"][video_id] = {"text": ""}
            save_cache()
            return cache["transcripts"][video_id]
        except Exception as e:
            wait = 2 ** attempt
            logging.warning(f"Error fetching transcript for {video_id}, retrying in {wait}s: {e}")
            time.sleep(wait)
    return {"text": ""}

app = Flask(__name__)

@app.route("/transcripts", methods=["GET"])
def transcripts():
    channel_name = request.args.get("channel")
    if not channel_name:
        return jsonify({"error": "Missing 'channel' parameter"}), 400

    try:
        videos = get_all_video_ids(channel_name, API_KEY, cache)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    results = []
    for vid in videos:
        transcript_entry = get_transcript(vid["id"])
        results.append({
            "video_id": vid["id"],
            "title": vid["title"],
            "transcript": transcript_entry["text"]
        })

    return jsonify({"channel": channel_name, "videos": results})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
