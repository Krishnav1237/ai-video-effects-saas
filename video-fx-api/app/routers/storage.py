"""IPFS/Pinata storage routes for decentralized video storage."""

import os
from fastapi import APIRouter, HTTPException

from app.models.schemas import PinRequest, PinResponse
from app.services.pinata_service import pin_file, get_pin_info, unpin_file, test_connection
from app.services.video_store import video_store

router = APIRouter(tags=["storage"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/video-fx-uploads")


@router.post("/storage/pin")
async def pin_video(request: PinRequest):
    """Pin a video to IPFS via Pinata for decentralized storage."""
    video = video_store.get(request.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = os.path.join(UPLOAD_DIR, video.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    pin_name = request.name or video.original_name
    result = await pin_file(file_path, pin_name)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Pin failed"))

    ipfs_cid = result.get("IpfsHash", "")
    ipfs_url = result.get("ipfs_url", "")

    video_store.update(
        request.video_id,
        ipfs_cid=ipfs_cid,
        ipfs_url=ipfs_url,
    )

    return {
        "status": "pinned",
        "video_id": request.video_id,
        "ipfs_cid": ipfs_cid,
        "ipfs_url": ipfs_url,
        "pin_size": result.get("PinSize", 0),
        "is_demo": result.get("status") == "demo_mode",
    }


@router.get("/storage/{cid}")
async def get_storage_info(cid: str):
    """Get information about a pinned file on IPFS."""
    result = await get_pin_info(cid)
    if result.get("pin_status") == "not_found":
        raise HTTPException(status_code=404, detail="CID not found on IPFS")
    return result


@router.delete("/storage/{cid}")
async def unpin_video(cid: str):
    """Unpin a video from IPFS."""
    result = await unpin_file(cid)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Unpin failed"))
    return result


@router.get("/storage/health/check")
async def storage_health():
    """Check Pinata/IPFS connection status."""
    result = await test_connection()
    return result
