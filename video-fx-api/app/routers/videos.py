"""Video upload, management, and streaming routes."""

import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.models.schemas import VideoMetadata, VideoStatus
from app.services.video_store import video_store
from app.services.video_processor import get_video_info, generate_thumbnail

router = APIRouter(tags=["videos"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/video-fx-uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/video-fx-outputs")
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file (max 500MB, common video formats).

    Automatically extracts metadata via ffprobe after upload.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    video_id = str(uuid.uuid4())
    safe_filename = f"{video_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    total_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks for low-latency streaming

    async with aiofiles.open(file_path, "wb") as out_file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                os.remove(file_path)
                raise HTTPException(
                    status_code=413, detail="File too large. Maximum size is 500MB."
                )
            await out_file.write(chunk)

    # Extract real video metadata via ffprobe
    info = get_video_info(file_path)

    video = VideoMetadata(
        id=video_id,
        filename=safe_filename,
        original_name=file.filename,
        size_bytes=total_size,
        duration_seconds=info.get("duration_seconds"),
        width=info.get("width"),
        height=info.get("height"),
        format=ext.lstrip("."),
        status=VideoStatus.UPLOADED,
    )
    video_store.add(video)

    # Generate thumbnail in background
    thumb_path = await generate_thumbnail(file_path)

    return {
        "status": "success",
        "video": video.model_dump(),
        "metadata": {
            "duration_seconds": info.get("duration_seconds"),
            "resolution": f"{info.get('width', '?')}x{info.get('height', '?')}",
            "fps": info.get("fps"),
            "codec": info.get("codec"),
            "bit_rate": info.get("bit_rate"),
            "has_audio": "audio" in info,
        },
        "thumbnail_available": thumb_path is not None,
        "message": f"Video uploaded ({total_size / (1024*1024):.1f}MB, {info.get('width', '?')}x{info.get('height', '?')}, {info.get('duration_seconds', 0):.1f}s)",
    }


@router.get("/videos")
async def list_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List all uploaded videos with pagination."""
    all_videos = video_store.list_all()
    start = (page - 1) * limit
    end = start + limit
    paginated = all_videos[start:end]

    total_size = sum(v.size_bytes for v in all_videos)
    total_with_effects = sum(1 for v in all_videos if v.effects_applied)
    total_ipfs = sum(1 for v in all_videos if v.ipfs_cid)

    return {
        "videos": [v.model_dump() for v in paginated],
        "total": len(all_videos),
        "page": page,
        "limit": limit,
        "has_more": end < len(all_videos),
        "stats": {
            "total_videos": len(all_videos),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 1),
            "videos_with_effects": total_with_effects,
            "videos_on_ipfs": total_ipfs,
        },
    }


@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    """Get video details by ID."""
    video = video_store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Check if file exists on disk
    file_path = _find_video_file(video)
    file_exists = file_path is not None and os.path.exists(file_path)

    return {
        "video": video.model_dump(),
        "file_available": file_exists,
        "stream_url": f"/api/videos/{video_id}/stream" if file_exists else None,
        "download_url": f"/api/videos/{video_id}/download" if file_exists else None,
    }


@router.get("/videos/{video_id}/stream")
async def stream_video(video_id: str):
    """Stream a video file for playback in the browser."""
    video = video_store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = _find_video_file(video)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        file_path,
        media_type="video/mp4",
        filename=video.original_name,
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/videos/{video_id}/download")
async def download_video(video_id: str):
    """Download a processed video file."""
    video = video_store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = _find_video_file(video)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=video.original_name,
    )


@router.get("/videos/{video_id}/thumbnail")
async def get_thumbnail(video_id: str):
    """Get a video thumbnail."""
    video = video_store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Look for existing thumbnail
    for thumb_dir in [OUTPUT_DIR, UPLOAD_DIR]:
        for fname in os.listdir(thumb_dir) if os.path.isdir(thumb_dir) else []:
            if fname.startswith(f"thumb_") and fname.endswith(".jpg"):
                thumb_path = os.path.join(thumb_dir, fname)
                if os.path.exists(thumb_path):
                    return FileResponse(thumb_path, media_type="image/jpeg")

    # Generate one on the fly
    file_path = _find_video_file(video)
    if file_path and os.path.exists(file_path):
        thumb_path = await generate_thumbnail(file_path)
        if thumb_path:
            return FileResponse(thumb_path, media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Thumbnail not available")


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and its output files."""
    video = video_store.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Remove from upload dir
    file_path = os.path.join(UPLOAD_DIR, video.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove from output dir
    output_path = os.path.join(OUTPUT_DIR, video.filename)
    if os.path.exists(output_path):
        os.remove(output_path)

    video_store.delete(video_id)
    return {"status": "deleted", "video_id": video_id}


def _find_video_file(video: VideoMetadata) -> str | None:
    """Find the video file on disk (check upload and output directories)."""
    # Check upload dir first
    upload_path = os.path.join(UPLOAD_DIR, video.filename)
    if os.path.exists(upload_path):
        return upload_path

    # Check output dir (for processed videos)
    output_path = os.path.join(OUTPUT_DIR, video.filename)
    if os.path.exists(output_path):
        return output_path

    return None
