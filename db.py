# db.py
import os
from sqlalchemy import create_engine, Column, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Read the DATABASE_URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")  # fallback to local SQLite

# Create engine and session
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ---- Models ----
class Channel(Base):
    __tablename__ = "channels"
    channel_id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    videos = relationship("Video", back_populates="channel")

class Video(Base):
    __tablename__ = "videos"
    video_id = Column(String, primary_key=True, index=True)
    channel_id = Column(String, ForeignKey("channels.channel_id"))
    title = Column(String)
    channel = relationship("Channel", back_populates="videos")
    transcript = relationship("Transcript", back_populates="video", uselist=False)

class Transcript(Base):
    __tablename__ = "transcripts"
    video_id = Column(String, ForeignKey("videos.video_id"), primary_key=True)
    text = Column(Text)
    video = relationship("Video", back_populates="transcript")

# ---- Initialize DB ----
def init_db():
    """Creates all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
    print("[INFO] Database tables ensured.")