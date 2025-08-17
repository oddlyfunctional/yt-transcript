import os
from flask import Flask, request, jsonify
from db import init_db
from youtube_data import get_youtube_client, get_channel_id_by_name, get_all_video_ids, get_transcript_text

app = Flask(__name__)
init_db()
youtube = get_youtube_client()

@app.route("/fetch_transcripts")
def transcripts():
    channel_name = request.args.get("channel")
    if not channel_name:
        return jsonify({"error": "Missing channel parameter"}), 400

    try:
        channel_id = get_channel_id_by_name(youtube, channel_name)
        videos = get_all_video_ids(youtube, channel_id)
        results = {}
        for vid_id, title in videos:
            text = get_transcript_text(vid_id, title)
            results[vid_id] = {"title": title, "transcript": text}
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/transcripts")
def cached_title_transcripts():
    from db import SessionLocal, Transcript, Video

    channel_name = request.args.get("channel")
    if not channel_name:
        return jsonify({"error": "Missing channel parameter"}), 400

    session = SessionLocal()
    try:
        # Get channel ID
        from db import Channel
        channel = session.query(Channel).filter(Channel.name == channel_name).first()
        if not channel:
            return jsonify({"error": f"No cached channel named {channel_name}"}), 404

        # Join videos and transcripts
        results = {}
        videos = session.query(Video).filter(Video.channel_id == channel.channel_id).all()
        for video in videos:
            transcript = session.query(Transcript).filter(Transcript.video_id == video.video_id).first()
            if transcript and transcript.text:
                results[video.title] = transcript.text

        session.close()
        return jsonify(results)
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
