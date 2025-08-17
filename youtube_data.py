import time
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.proxies import GenericProxyConfig
from googleapiclient.discovery import build
from db import SessionLocal, Channel, Video, Transcript
import os
from datetime import datetime
from proxy_randomizer import RegisteredProviders

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
RATE_LIMIT_SECONDS = 1  # Configurable
RP = RegisteredProviders()
RP.parse_providers()

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_youtube_client():
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

def get_channel_id_by_name(youtube, name):
    session = SessionLocal()
    channel = session.query(Channel).filter(Channel.name == name).first()
    if channel:
        log(f"[CACHE HIT] Channel {name} → {channel.channel_id}")
        session.close()
        return channel.channel_id

    log(f"[CACHE MISS] Fetching channelId for {name}")
    response = youtube.search().list(
        q=name,
        type="channel",
        part="id",
        maxResults=1
    ).execute()
    items = response.get("items", [])
    if not items:
        session.close()
        raise ValueError(f"No channel found for {name}")
    channel_id = items[0]["id"]["channelId"]
    session.add(Channel(name=name, channel_id=channel_id))
    session.commit()
    session.close()
    return channel_id

def get_all_video_ids(youtube, channel_id):
    session = SessionLocal()
    videos = session.query(Video).filter(Video.channel_id == channel_id).all()
    if videos:
        log(f"[CACHE HIT] Videos for channel {channel_id}")
        session.close()
        return [(v.video_id, v.title) for v in videos]

    log(f"[CACHE MISS] Fetching videos for channel {channel_id}")
    all_videos = []
    next_page_token = None
    while True:
        response = youtube.search().list(
            channelId=channel_id,
            part="snippet",
            order="date",
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        items = response.get("items", [])
        for item in items:
            vid_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            all_videos.append((vid_id, title))
            session.add(Video(video_id=vid_id, channel_id=channel_id, title=title))
        session.commit()
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(RATE_LIMIT_SECONDS)
    session.close()
    return all_videos

def get_transcript_text(video_id, title=None):
    session = SessionLocal()
    transcript = session.query(Transcript).filter(Transcript.video_id == video_id).first()
    if transcript:
        log(f"[CACHE HIT] Transcript for {video_id}")
        session.close()
        return transcript.text

    log(f"[CACHE MISS] Fetching transcript for {video_id}")
    text = None
    wait = RATE_LIMIT_SECONDS

    proxy = RP.get_random_proxy().get_proxy()
    api = YouTubeTranscriptApi(
        proxy_config=GenericProxyConfig(
            http_url=proxy
        )
    )
    for attempt in range(5):
        try:
            data = api.fetch(video_id)
            text = " ".join([x["text"] for x in data])
            break
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            log(f"[WARN] No transcript for {video_id}: {e}")
            break
        except Exception as e:
            log(f"[ERROR] Attempt {attempt+1} failed for {video_id}: {e}")
            time.sleep(wait)
            wait *= 2

    session.add(Transcript(video_id=video_id, text=text))
    session.commit()
    session.close()
    return text
