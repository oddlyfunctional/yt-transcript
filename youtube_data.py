from googleapiclient.discovery import build
import logging, time, json

def get_all_video_ids(channel_name, api_key, cache):
    if channel_name in cache.get("videoIds", {}):
        logging.info(f"Cache hit: videoIds for {channel_name}")
        return cache["videoIds"][channel_name]

    logging.info(f"Cache miss: videoIds for {channel_name}")

    youtube = build("youtube", "v3", developerKey=api_key)

    if channel_name in cache.get("channelIds", {}):
        channel_id = cache["channelIds"][channel_name]
        logging.info(f"Cache hit: channelId for {channel_name}")
    else:
        request = youtube.channels().list(part="id", forUsername=channel_name)
        response = request.execute()
        items = response.get("items", [])
        if not items:
            raise ValueError(f"Channel {channel_name} not found")
        channel_id = items[0]["id"]
        cache["channelIds"][channel_name] = channel_id
        with open("cache.json", "w") as f:
            json.dump(cache, f, indent=2)

    videos = []
    next_page_token = None
    while True:
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            maxResults=50,
            order="date",
            pageToken=next_page_token,
            type="video"
        )
        response = request.execute()
        for item in response.get("items", []):
            vid = item["id"]["videoId"]
            title = item["snippet"]["title"]
            videos.append({"id": vid, "title": title})

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    cache["videoIds"][channel_name] = videos
    with open("cache.json", "w") as f:
        json.dump(cache, f, indent=2)

    logging.info(f"Fetched {len(videos)} videos for channel {channel_name}")
    return videos
