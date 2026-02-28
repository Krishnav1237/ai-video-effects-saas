"""File-backed job queue for video processing with progress tracking.

Persists state to a JSON file so it survives across Fly.io instances and restarts.
"""

import json
import os
import time
import threading
import uuid
from enum import Enum
from typing import Optional

STORE_DIR = os.getenv("STORE_DIR", "/tmp/video-fx-uploads")
JOBS_FILE = os.path.join(STORE_DIR, ".jobs_store.json")


class JobStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    ENCODING = "encoding"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Represents a video processing job."""

    def __init__(
        self,
        video_id: str,
        effect_type: str,
        params: dict,
        ai_model: str = "auto",
        intensity: float = 0.5,
        add_watermark: bool = True,
        id: Optional[str] = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.video_id = video_id
        self.effect_type = effect_type
        self.params = params
        self.ai_model = ai_model
        self.intensity = intensity
        self.add_watermark = add_watermark
        self.status = JobStatus.QUEUED
        self.progress: float = 0.0
        self.message: str = "Queued for processing"
        self.result: Optional[dict] = None
        self.error: Optional[str] = None
        self.created_at: float = time.time()
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "video_id": self.video_id,
            "effect_type": self.effect_type,
            "ai_model": self.ai_model,
            "intensity": self.intensity,
            "status": self.status.value,
            "progress": round(self.progress, 1),
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "processing_time_seconds": (
                round(self.completed_at - self.started_at, 2)
                if self.started_at and self.completed_at
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Reconstruct a Job from a dict."""
        job = cls(
            video_id=data["video_id"],
            effect_type=data["effect_type"],
            params=data.get("params", {}),
            ai_model=data.get("ai_model", "auto"),
            intensity=data.get("intensity", 0.5),
            add_watermark=data.get("add_watermark", True),
            id=data["id"],
        )
        job.status = JobStatus(data.get("status", "queued"))
        job.progress = data.get("progress", 0.0)
        job.message = data.get("message", "")
        job.result = data.get("result")
        job.error = data.get("error")
        job.created_at = data.get("created_at", time.time())
        job.started_at = data.get("started_at")
        job.completed_at = data.get("completed_at")
        return job


class JobQueue:
    """File-backed job queue with progress tracking."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        """Load state from disk."""
        if not os.path.exists(JOBS_FILE):
            return
        try:
            with open(JOBS_FILE, "r") as f:
                data = json.load(f)
            for job_data in data:
                job = Job.from_dict(job_data)
                self._jobs[job.id] = job
        except (json.JSONDecodeError, Exception):
            pass

    def _save(self) -> None:
        """Persist state to disk."""
        os.makedirs(os.path.dirname(JOBS_FILE), exist_ok=True)
        try:
            data = [j.to_dict() for j in self._jobs.values()]
            with open(JOBS_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def submit(self, job: Job) -> str:
        """Submit a job to the queue. Returns job ID."""
        with self._lock:
            self._jobs[job.id] = job
            self._save()
        return job.id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        with self._lock:
            self._load()
            return self._jobs.get(job_id)

    def get_jobs_for_video(self, video_id: str) -> list[Job]:
        """Get all jobs for a video, sorted by creation time."""
        with self._lock:
            self._load()
            jobs = [j for j in self._jobs.values() if j.video_id == video_id]
            return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def list_jobs(self, limit: int = 50) -> list[Job]:
        """List recent jobs."""
        with self._lock:
            self._load()
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
            return jobs[:limit]

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update a job's status and persist to disk."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            if status is not None:
                job.status = status
                if status == JobStatus.PROCESSING and job.started_at is None:
                    job.started_at = time.time()
                if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    job.completed_at = time.time()
            if progress is not None:
                job.progress = progress
            if message is not None:
                job.message = message
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            self._save()


# Singleton instance
job_queue = JobQueue()
