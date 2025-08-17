from sqlalchemy import create_engine, Column, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/youtube_cache")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Channel(Base):
    __tablename__ = "channels"
    name = Column(String, primary_key=True)
    channel_id = Column(String, nullable=False)

class Video(Base):
    __tablename__ = "videos"
    video_id = Column(String, primary_key=True)
    channel_id = Column(String, ForeignKey("channels.channel_id"), nullable=False)
    title = Column(String, nullable=False)

class Transcript(Base):
    __tablename__ = "transcripts"
    video_id = Column(String, ForeignKey("videos.video_id"), primary_key=True)
    title = Column(String, nullable=False)
    text = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)
