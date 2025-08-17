-- channels table
CREATE TABLE channels (
    name TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL
);

-- videos table
CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES channels(channel_id),
    title TEXT NOT NULL
);

-- transcripts table
CREATE TABLE transcripts (
    video_id TEXT PRIMARY KEY REFERENCES videos(video_id),
    title TEXT NOT NULL,
    text TEXT
);

