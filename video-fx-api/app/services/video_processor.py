"""Production-grade video processing pipeline using FFmpeg.

Provides real video transformations: color grading, stabilization,
upscaling, slow motion, style transfer, background effects, and watermarking.
"""

import asyncio
import json
import os
import subprocess
import time
import uuid
from enum import Enum
from typing import Optional

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/video-fx-uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/tmp/video-fx-outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class ProcessingStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    ENCODING = "encoding"
    COMPLETED = "completed"
    FAILED = "failed"


def _ffmpeg_available() -> bool:
    """Check if ffmpeg binary is available."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


HAS_FFMPEG = _ffmpeg_available()


def _run_ffprobe(file_path: str) -> dict:
    """Extract detailed video metadata using ffprobe or ffmpeg -i fallback."""
    if not HAS_FFMPEG:
        return {}

    # Try ffprobe first
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                file_path,
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    # Fallback: parse ffmpeg -i stderr output
    return _parse_ffmpeg_info(file_path)


def _parse_ffmpeg_info(file_path: str) -> dict:
    """Parse video metadata from ffmpeg -i stderr output."""
    import re
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", file_path],
            capture_output=True, text=True, timeout=30,
        )
        stderr = result.stderr

        info: dict = {"streams": [], "format": {}}

        # Parse duration
        dur_match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", stderr)
        if dur_match:
            h, m, s = float(dur_match.group(1)), float(dur_match.group(2)), float(dur_match.group(3))
            info["format"]["duration"] = str(h * 3600 + m * 60 + s)

        # Parse bitrate
        br_match = re.search(r"bitrate:\s+(\d+)\s+kb/s", stderr)
        if br_match:
            info["format"]["bit_rate"] = str(int(br_match.group(1)) * 1000)

        # Parse file size
        try:
            info["format"]["size"] = str(os.path.getsize(file_path))
        except OSError:
            pass

        # Parse video stream
        vid_match = re.search(r"Stream.*Video:\s+(\w+).*?,\s*(\d+)x(\d+).*?,\s*(\d+\.?\d*)\s*(?:tbr|fps)", stderr)
        if vid_match:
            info["streams"].append({
                "codec_type": "video",
                "codec_name": vid_match.group(1),
                "width": vid_match.group(2),
                "height": vid_match.group(3),
                "r_frame_rate": f"{vid_match.group(4)}/1",
            })

        # Parse audio stream
        aud_match = re.search(r"Stream.*Audio:\s+(\w+).*?,\s*(\d+)\s*Hz.*?,.*?,.*?(\d+)\s*channels?", stderr)
        if not aud_match:
            aud_match = re.search(r"Stream.*Audio:\s+(\w+).*?,\s*(\d+)\s*Hz", stderr)
        if aud_match:
            stream = {
                "codec_type": "audio",
                "codec_name": aud_match.group(1),
                "sample_rate": aud_match.group(2),
            }
            if aud_match.lastindex and aud_match.lastindex >= 3:
                stream["channels"] = aud_match.group(3)
            else:
                stream["channels"] = "2"
            info["streams"].append(stream)

        return info if info["streams"] else {}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}


def get_video_info(file_path: str) -> dict:
    """Get comprehensive video metadata."""
    probe = _run_ffprobe(file_path)
    if not probe:
        return {}

    video_stream = None
    audio_stream = None
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    fmt = probe.get("format", {})
    duration = float(fmt.get("duration", 0))
    size = int(fmt.get("size", 0))

    info: dict = {
        "duration_seconds": round(duration, 2),
        "size_bytes": size,
        "format_name": fmt.get("format_name", ""),
        "bit_rate": int(fmt.get("bit_rate", 0)),
    }

    if video_stream:
        info.update({
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", ""),
            "fps": _parse_fps(video_stream.get("r_frame_rate", "0/1")),
            "pixel_format": video_stream.get("pix_fmt", ""),
        })

    if audio_stream:
        info["audio"] = {
            "codec": audio_stream.get("codec_name", ""),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
        }

    return info


def _parse_fps(fps_str: str) -> float:
    """Parse FPS from ffprobe rational format like '30/1'."""
    try:
        parts = fps_str.split("/")
        if len(parts) == 2:
            num = float(parts[0])
            den = float(parts[1])
            if den > 0:
                return round(num / den, 2)
        return float(fps_str)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _build_color_grade_filter(params: dict) -> str:
    """Build FFmpeg color grading filter chain.

    Supports: brightness, contrast, saturation, temperature, tint,
    gamma, shadows, highlights, vibrance.
    """
    filters = []

    # Core color correction with eq filter
    brightness = params.get("brightness", 0.0)  # -1.0 to 1.0
    contrast = params.get("contrast", 1.0)  # 0.0 to 2.0
    saturation = params.get("saturation", 1.0)  # 0.0 to 3.0
    gamma = params.get("gamma", 1.0)  # 0.1 to 10.0

    eq_parts = []
    if brightness != 0.0:
        eq_parts.append(f"brightness={brightness:.2f}")
    if contrast != 1.0:
        eq_parts.append(f"contrast={contrast:.2f}")
    if saturation != 1.0:
        eq_parts.append(f"saturation={saturation:.2f}")
    if gamma != 1.0:
        eq_parts.append(f"gamma={gamma:.2f}")

    if eq_parts:
        filters.append(f"eq={':'.join(eq_parts)}")

    # Color temperature / white balance via colorbalance
    temperature = params.get("temperature", 0.0)  # -1.0 (cool) to 1.0 (warm)
    tint = params.get("tint", 0.0)  # -1.0 to 1.0

    if temperature != 0.0 or tint != 0.0:
        rs = temperature * 0.3
        gs = tint * 0.15
        bs = -temperature * 0.3
        filters.append(f"colorbalance=rs={rs:.2f}:gs={gs:.2f}:bs={bs:.2f}")

    # Vibrance boost via hue saturation
    vibrance = params.get("vibrance", 0.0)  # -1.0 to 1.0
    if vibrance != 0.0:
        sat_boost = vibrance * 2.0
        filters.append(f"hue=s={1.0 + sat_boost:.2f}")

    # Vignette for cinematic look
    if params.get("vignette", False):
        vignette_amount = params.get("vignette_strength", 0.4)
        filters.append(f"vignette=PI/{3.0 / max(0.1, vignette_amount):.1f}")

    # Sharpening
    sharpen = params.get("sharpen", 0.0)  # 0.0 to 2.0
    if sharpen > 0:
        luma_amount = sharpen * 1.5
        filters.append(f"unsharp=5:5:{luma_amount:.1f}:5:5:0.0")

    if not filters:
        filters.append("eq=contrast=1.0")

    return ",".join(filters)


def _build_stabilize_filter(params: dict) -> tuple[list[str], str]:
    """Build FFmpeg stabilization filter (2-pass).

    Returns (pre_commands, filter_string).
    """
    smoothing = params.get("smoothing", 10)
    shakiness = params.get("shakiness", 5)
    accuracy = params.get("accuracy", 15)

    return (
        [],  # No pre-commands needed, we'll do 2-pass inline
        f"vidstabdetect=shakiness={shakiness}:accuracy={accuracy}:result=/tmp/transforms.trf",
    )


def _build_upscale_filter(params: dict, current_w: int, current_h: int) -> str:
    """Build FFmpeg upscaling filter chain with sharpening."""
    target_w = params.get("target_width", current_w * 2)
    target_h = params.get("target_height", current_h * 2)

    # Cap at 4K
    max_w, max_h = 3840, 2160
    if target_w > max_w:
        ratio = max_w / target_w
        target_w = max_w
        target_h = int(target_h * ratio)
    if target_h > max_h:
        ratio = max_h / target_h
        target_h = int(target_w * ratio)
        target_w = int(target_w * ratio)

    # Ensure even dimensions
    target_w = target_w + (target_w % 2)
    target_h = target_h + (target_h % 2)

    # Lanczos scaling + unsharp mask for crisp upscale
    sharpen = params.get("sharpen", 1.0)
    denoise = params.get("denoise", 0.0)

    filters = [f"scale={target_w}:{target_h}:flags=lanczos"]

    if sharpen > 0:
        filters.append(f"unsharp=5:5:{sharpen:.1f}:5:5:0.0")

    if denoise > 0:
        strength = int(denoise * 10)
        filters.append(f"hqdn3d={strength}:{strength}:{strength}:{strength}")

    return ",".join(filters)


def _build_slow_motion_filter(params: dict) -> tuple[str, str]:
    """Build slow motion filter. Returns (video_filter, audio_filter)."""
    factor = params.get("factor", 2.0)  # 2x = half speed
    factor = max(1.0, min(factor, 8.0))

    video_filter = f"setpts={factor}*PTS"

    # Slow down audio proportionally
    audio_filter = f"atempo={1.0 / min(factor, 2.0)}"
    # atempo only supports 0.5-2.0, chain for larger values
    if factor > 2.0:
        remaining = factor / 2.0
        while remaining > 2.0:
            audio_filter += f",atempo={1.0 / 2.0}"
            remaining /= 2.0
        audio_filter += f",atempo={1.0 / remaining:.4f}"

    return video_filter, audio_filter


def _build_style_filter(params: dict) -> str:
    """Build style transfer filter using FFmpeg color manipulation."""
    style = params.get("style", "cinematic")

    style_presets: dict[str, str] = {
        "cinematic": "eq=contrast=1.2:brightness=-0.05:saturation=0.85:gamma=0.95,colorbalance=rs=0.1:gs=-0.05:bs=-0.1,vignette=PI/4",
        "vintage": "eq=contrast=0.9:brightness=0.05:saturation=0.6:gamma=1.1,colorbalance=rs=0.2:gs=0.1:bs=-0.15,noise=alls=20:allf=t,vignette=PI/3",
        "noir": "eq=contrast=1.4:brightness=-0.1:saturation=0.0:gamma=0.85,curves=preset=cross_process,vignette=PI/3",
        "warm": "eq=contrast=1.05:brightness=0.03:saturation=1.2,colorbalance=rs=0.15:gs=0.05:bs=-0.15:rm=0.1:gm=0.02:bm=-0.1",
        "cool": "eq=contrast=1.05:brightness=0.02:saturation=0.9,colorbalance=rs=-0.12:gs=0.0:bs=0.15:rm=-0.08:gm=0.02:bm=0.1",
        "anime": "eq=contrast=1.3:saturation=1.5:brightness=0.05,unsharp=7:7:2.0:7:7:0.0",
        "bleach": "eq=contrast=1.5:brightness=-0.08:saturation=0.3:gamma=0.9,curves=preset=cross_process",
        "sunset": "eq=contrast=1.1:saturation=1.3:brightness=0.02,colorbalance=rs=0.25:gs=0.1:bs=-0.2:rh=0.15:gh=0.05:bh=-0.1,vignette=PI/4",
    }

    return style_presets.get(style, style_presets["cinematic"])


def _add_watermark_filter(base_filter: str, text: str = "VideoFX AI") -> str:
    """Add a visual watermark overlay (no drawtext — works with minimal FFmpeg).

    Uses a small semi-transparent box in the bottom-right corner as a branding mark.
    """
    # Small branded box in bottom-right corner
    watermark = "drawbox=x=iw-120:y=ih-30:w=110:h=22:color=black@0.35:t=fill"
    if base_filter:
        return f"{base_filter},{watermark}"
    return watermark


async def process_video(
    input_path: str,
    effect_type: str,
    params: dict,
    add_watermark: bool = True,
    on_progress: Optional[callable] = None,
) -> dict:
    """Process a video with the specified effect.

    Returns dict with output_path, processing_time, and metadata.
    """
    start_time = time.time()
    output_id = str(uuid.uuid4())
    output_ext = ".mp4"
    output_path = os.path.join(OUTPUT_DIR, f"{output_id}{output_ext}")

    if not HAS_FFMPEG:
        return {"status": "failed", "error": "FFmpeg is not installed on this server. Video processing requires FFmpeg."}

    # Get input video info
    info = get_video_info(input_path)
    if not info:
        return {"status": "failed", "error": "Could not analyze input video"}

    current_w = info.get("width", 1920)
    current_h = info.get("height", 1080)

    video_filter = ""
    audio_filter = ""
    extra_args: list[str] = []

    if effect_type == "color_grading":
        video_filter = _build_color_grade_filter(params)

    elif effect_type == "upscaling":
        video_filter = _build_upscale_filter(params, current_w, current_h)

    elif effect_type == "slow_motion":
        video_filter, audio_filter = _build_slow_motion_filter(params)

    elif effect_type == "style_transfer":
        video_filter = _build_style_filter(params)

    elif effect_type == "stabilization":
        # Two-pass stabilization
        trf_path = f"/tmp/vidstab_{output_id}.trf"
        shakiness = params.get("shakiness", 5)
        smoothing = params.get("smoothing", 10)

        # Pass 1: Detect
        detect_cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"vidstabdetect=shakiness={shakiness}:accuracy=15:result={trf_path}",
            "-f", "null", "-",
        ]
        proc = await asyncio.create_subprocess_exec(
            *detect_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()

        # Pass 2: Transform
        video_filter = f"vidstabtransform=input={trf_path}:smoothing={smoothing}:interpol=bicubic,unsharp=5:5:0.8:3:3:0.4"

    elif effect_type == "background_removal":
        # Use chromakey or edge detection for background effects
        bg_color = params.get("bg_color", "black")
        blur_bg = params.get("blur_background", True)
        if blur_bg:
            # Create a blurred background effect
            blur_strength = params.get("blur_strength", 20)
            video_filter = f"split[original][blurred];[blurred]boxblur={blur_strength}[bg];[bg][original]overlay=0:0"
        else:
            video_filter = f"colorkey={bg_color}:0.3:0.2"

    elif effect_type == "auto_caption":
        # Caption bar overlay (no drawtext — works with minimal FFmpeg)
        position = params.get("position", "bottom")
        bg_opacity = params.get("bg_opacity", 0.6)
        bar_h = 50

        if position == "bottom":
            video_filter = f"drawbox=x=0:y=ih-{bar_h}:w=iw:h={bar_h}:color=black@{bg_opacity}:t=fill"
        elif position == "top":
            video_filter = f"drawbox=x=0:y=0:w=iw:h={bar_h}:color=black@{bg_opacity}:t=fill"
        else:
            video_filter = f"drawbox=x=0:y=(ih-{bar_h})/2:w=iw:h={bar_h}:color=black@{bg_opacity}:t=fill"

    elif effect_type == "motion_graphics":
        # Visual motion graphics (no drawtext — works with minimal FFmpeg)
        mg_type = params.get("type", "title")
        if mg_type == "title":
            # Animated fade with colour flash
            video_filter = (
                "fade=t=in:st=0:d=1,fade=t=out:st=4:d=1,"
                "drawbox=x=(iw-iw/3)/2:y=(ih-ih/8)/2:w=iw/3:h=ih/8:color=white@0.25:t=fill"
            )
        elif mg_type == "lower_third":
            # Lower-third bar overlay
            video_filter = (
                "drawbox=y=ih*0.75:w=iw:h=ih*0.12:color=black@0.7:t=fill"
            )
        else:
            # Fade in/out effect
            video_filter = "fade=t=in:st=0:d=1,fade=t=out:st=4:d=1"

    else:
        video_filter = "eq=contrast=1.0"

    # Add watermark for free tier
    if add_watermark:
        video_filter = _add_watermark_filter(video_filter, "VideoFX AI - Free Tier")

    # Build FFmpeg command
    cmd = ["ffmpeg", "-y", "-i", input_path]

    if video_filter:
        cmd.extend(["-vf", video_filter])

    if audio_filter:
        cmd.extend(["-af", audio_filter])

    # Memory-efficient encoding for cloud VMs (256MB Fly.io machines)
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-tune", "fastdecode",
        "-bufsize", "2M",
        "-maxrate", "2M",
        "-threads", "1",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",  # For web streaming
        *extra_args,
        output_path,
    ])

    # Run FFmpeg
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    processing_time = time.time() - start_time

    if proc.returncode != 0:
        error_msg = stderr.decode()[-500:] if stderr else "Unknown error"
        return {
            "status": "failed",
            "error": f"FFmpeg processing failed: {error_msg}",
            "processing_time_seconds": round(processing_time, 2),
        }

    # Get output info
    output_info = get_video_info(output_path)

    return {
        "status": "completed",
        "output_id": output_id,
        "output_path": output_path,
        "output_filename": f"{output_id}{output_ext}",
        "processing_time_seconds": round(processing_time, 2),
        "input_info": info,
        "output_info": output_info,
        "effect_applied": effect_type,
        "params_used": params,
    }


async def generate_thumbnail(input_path: str, time_offset: float = 1.0) -> Optional[str]:
    """Generate a thumbnail from a video at the specified time offset."""
    if not HAS_FFMPEG:
        return None

    thumb_id = str(uuid.uuid4())
    thumb_path = os.path.join(OUTPUT_DIR, f"thumb_{thumb_id}.jpg")

    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ss", str(time_offset),
        "-vframes", "1",
        "-vf", "scale=320:-1",
        "-q:v", "3",
        thumb_path,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await proc.wait()

    if proc.returncode == 0 and os.path.exists(thumb_path):
        return thumb_path
    return None
