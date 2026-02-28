"""File-backed video store for managing video metadata.

Persists state to a JSON file so it survives across Fly.io instances and restarts.
"""

import json
import os
import threading
from app.models.schemas import VideoMetadata, VideoStatus

STORE_DIR = os.getenv("STORE_DIR", "/tmp/video-fx-uploads")
STORE_FILE = os.path.join(STORE_DIR, ".video_store.json")


class VideoStore:
    """File-backed store for video metadata."""

    def __init__(self) -> None:
        self._videos: dict[str, VideoMetadata] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        """Load state from disk."""
        if not os.path.exists(STORE_FILE):
            return
        try:
            with open(STORE_FILE, "r") as f:
                data = json.load(f)
            for vid_data in data:
                video = VideoMetadata(**vid_data)
                self._videos[video.id] = video
        except (json.JSONDecodeError, Exception):
            pass

    def _save(self) -> None:
        """Persist state to disk."""
        os.makedirs(os.path.dirname(STORE_FILE), exist_ok=True)
        try:
            data = [v.model_dump() for v in self._videos.values()]
            with open(STORE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def add(self, video: VideoMetadata) -> VideoMetadata:
        with self._lock:
            self._videos[video.id] = video
            self._save()
        return video

    def get(self, video_id: str) -> VideoMetadata | None:
        with self._lock:
            self._load()
            return self._videos.get(video_id)

    def list_all(self) -> list[VideoMetadata]:
        with self._lock:
            self._load()
            return sorted(self._videos.values(), key=lambda v: v.created_at, reverse=True)

    def update_status(self, video_id: str, status: VideoStatus) -> VideoMetadata | None:
        with self._lock:
            self._load()
            video = self._videos.get(video_id)
            if video:
                video.status = status
                self._save()
            return video

    def update(self, video_id: str, **kwargs: object) -> VideoMetadata | None:
        with self._lock:
            self._load()
            video = self._videos.get(video_id)
            if video:
                for key, value in kwargs.items():
                    if hasattr(video, key):
                        setattr(video, key, value)
                self._save()
            return video

    def delete(self, video_id: str) -> bool:
        with self._lock:
            self._load()
            if video_id in self._videos:
                del self._videos[video_id]
                self._save()
                return True
            return False


# Singleton instance
video_store = VideoStore()
