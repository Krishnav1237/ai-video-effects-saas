"""AI effects routes with real FFmpeg video processing."""

import asyncio
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import EffectRequest, EffectType, AIModel, VideoMetadata, VideoStatus
from app.services.ai_orchestrator import generate_effect_params
from app.services.video_processor import get_video_info, process_video
from app.services.job_queue import job_queue, Job, JobStatus
from app.services.video_store import video_store

router = APIRouter(tags=["effects"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/video-fx-uploads")

EFFECT_CATALOG = [
    {
        "type": EffectType.MOTION_GRAPHICS,
        "name": "Motion Graphics",
        "description": "AI-generated titles, lower-thirds, and animated text overlays",
        "icon": "sparkles",
        "recommended_model": "claude",
        "category": "creative",
        "produces_output": True,
    },
    {
        "type": EffectType.UPSCALING,
        "name": "AI Upscaling",
        "description": "Enhance resolution up to 4K with Lanczos scaling and AI sharpening",
        "icon": "maximize",
        "recommended_model": "gemini",
        "category": "enhancement",
        "produces_output": True,
    },
    {
        "type": EffectType.STYLE_TRANSFER,
        "name": "Style Transfer",
        "description": "8 cinematic styles: noir, vintage, anime, sunset, bleach, warm, cool",
        "icon": "palette",
        "recommended_model": "gemini",
        "category": "creative",
        "produces_output": True,
    },
    {
        "type": EffectType.COLOR_GRADING,
        "name": "Color Grading",
        "description": "Professional color correction: 6 curated looks with fine-tuning controls",
        "icon": "sun",
        "recommended_model": "gemini",
        "category": "enhancement",
        "produces_output": True,
    },
    {
        "type": EffectType.BACKGROUND_REMOVAL,
        "name": "Background Blur",
        "description": "Depth-of-field background blur for a cinematic bokeh look",
        "icon": "scissors",
        "recommended_model": "gemini",
        "category": "editing",
        "produces_output": True,
    },
    {
        "type": EffectType.SLOW_MOTION,
        "name": "Slow Motion",
        "description": "Smooth slow-motion from 1.5x to 8x with pitch-corrected audio",
        "icon": "clock",
        "recommended_model": "gemini",
        "category": "editing",
        "produces_output": True,
    },
    {
        "type": EffectType.STABILIZATION,
        "name": "Stabilization",
        "description": "Two-pass video stabilization for shaky handheld footage",
        "icon": "anchor",
        "recommended_model": "gemini",
        "category": "enhancement",
        "produces_output": True,
    },
    {
        "type": EffectType.AUTO_CAPTION,
        "name": "Auto Captions",
        "description": "Styled text overlay captions with customizable position and appearance",
        "icon": "message-square",
        "recommended_model": "claude",
        "category": "creative",
        "produces_output": True,
    },
]


@router.get("/effects")
async def list_effects():
    """List all available AI effects with capabilities."""
    return {
        "effects": EFFECT_CATALOG,
        "models": [
            {
                "id": "gemini",
                "name": "Gemini 2.0 Flash",
                "provider": "Google",
                "best_for": ["upscaling", "style_transfer", "color_grading", "stabilization"],
                "description": "Fast technical processing and enhancement",
            },
            {
                "id": "claude",
                "name": "Claude Sonnet",
                "provider": "Anthropic",
                "best_for": ["motion_graphics", "auto_caption"],
                "description": "Creative effects and text generation",
            },
        ],
        "presets": {
            "color_grading": [
                "cinematic_warm", "cinematic_cool", "vibrant",
                "moody", "golden_hour", "film_emulation",
            ],
            "style_transfer": [
                "cinematic", "vintage", "noir", "warm",
                "cool", "anime", "bleach", "sunset",
            ],
        },
    }


@router.post("/effects/apply")
async def apply_video_effect(request: EffectRequest):
    """Apply an AI effect to a video — real FFmpeg processing.

    Returns a job ID for tracking progress. The processed video
    is available via /api/videos/{output_id}/stream once complete.
    """
    video = video_store.get(request.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = os.path.join(UPLOAD_DIR, video.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    # Create a processing job
    job = Job(
        video_id=request.video_id,
        effect_type=request.effect_type.value,
        params=request.parameters,
        ai_model=request.ai_model.value,
        intensity=request.intensity,
        add_watermark=True,
    )
    job_queue.submit(job)

    # Process in background
    asyncio.create_task(
        _process_effect(job, file_path, request.effect_type, request.ai_model, request.intensity, request.parameters)
    )

    return {
        "status": "processing",
        "job_id": job.id,
        "message": f"Processing '{request.effect_type.value}' effect — track progress via /api/jobs/{job.id}",
    }


async def _process_effect(
    job: Job,
    file_path: str,
    effect_type: EffectType,
    ai_model: AIModel,
    intensity: float,
    user_params: dict,
) -> None:
    """Background task: AI parameter generation then FFmpeg processing."""
    try:
        # Step 1: Analyze video
        job_queue.update_job(job.id, status=JobStatus.ANALYZING, progress=5.0, message="Analyzing video...")
        video_info = get_video_info(file_path)

        # Step 2: Generate parameters via AI or curated presets
        job_queue.update_job(job.id, progress=15.0, message="Generating effect parameters...")
        ai_result = await generate_effect_params(
            effect_type=effect_type,
            ai_model=ai_model,
            video_info=video_info,
            intensity=intensity,
            user_params=user_params,
        )

        # Step 3: Process video with FFmpeg
        job_queue.update_job(
            job.id,
            status=JobStatus.PROCESSING,
            progress=25.0,
            message=f"Applying {effect_type.value} effect (model: {ai_result['model_used']})...",
        )

        result = await process_video(
            input_path=file_path,
            effect_type=effect_type.value,
            params=ai_result["params"],
            add_watermark=job.add_watermark,
        )

        if result["status"] == "failed":
            job_queue.update_job(
                job.id,
                status=JobStatus.FAILED,
                progress=0.0,
                message=result.get("error", "Processing failed"),
                error=result.get("error"),
            )
            return

        # Step 4: Register output video
        job_queue.update_job(job.id, status=JobStatus.ENCODING, progress=85.0, message="Finalizing output...")

        source = video_store.get(job.video_id)
        source_name = source.original_name if source else "output"
        output_video = VideoMetadata(
            id=result["output_id"],
            filename=result["output_filename"],
            original_name=f"{effect_type.value}_{source_name}",
            size_bytes=result["output_info"].get("size_bytes", 0),
            duration_seconds=result["output_info"].get("duration_seconds"),
            width=result["output_info"].get("width"),
            height=result["output_info"].get("height"),
            format="mp4",
            status=VideoStatus.COMPLETED,
        )
        video_store.add(output_video)

        # Update source video metadata
        if source:
            video_store.update(
                job.video_id,
                effects_applied=[*source.effects_applied, effect_type.value],
            )

        # Complete
        job_queue.update_job(
            job.id,
            status=JobStatus.COMPLETED,
            progress=100.0,
            message="Processing complete",
            result={
                "output_video_id": result["output_id"],
                "processing_time_seconds": result["processing_time_seconds"],
                "model_used": ai_result["model_used"],
                "ai_enhanced": ai_result["ai_enhanced"],
                "effect_params": ai_result["params"],
                "input_info": result["input_info"],
                "output_info": result["output_info"],
            },
        )

    except Exception as e:
        job_queue.update_job(
            job.id,
            status=JobStatus.FAILED,
            error=str(e),
            message=f"Error: {str(e)[:200]}",
        )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status and progress of a processing job."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job.to_dict()}


@router.get("/jobs")
async def list_jobs(video_id: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=200)):
    """List processing jobs, optionally filtered by video ID."""
    if video_id:
        jobs = job_queue.get_jobs_for_video(video_id)
    else:
        jobs = job_queue.list_jobs(limit=limit)
    return {"jobs": [j.to_dict() for j in jobs]}


@router.post("/effects/preview")
async def preview_effect(request: EffectRequest):
    """Preview effect parameters without processing (instant response)."""
    video = video_store.get(request.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = os.path.join(UPLOAD_DIR, video.filename)
    video_info = get_video_info(file_path) if os.path.exists(file_path) else {}

    ai_result = await generate_effect_params(
        effect_type=request.effect_type,
        ai_model=request.ai_model,
        video_info=video_info,
        intensity=request.intensity,
        user_params=request.parameters,
    )

    return {
        "status": "preview",
        "effect_type": request.effect_type.value,
        "model_used": ai_result["model_used"],
        "ai_enhanced": ai_result["ai_enhanced"],
        "params": ai_result["params"],
        "message": "Preview parameters generated. Use /effects/apply to process the video.",
    }
