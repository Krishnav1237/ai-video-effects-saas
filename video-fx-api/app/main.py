from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os
import shutil
from dotenv import load_dotenv

load_dotenv()


def _ensure_ffmpeg() -> None:
    """Ensure ffmpeg is available on PATH via imageio-ffmpeg fallback."""
    if shutil.which("ffmpeg"):
        return

    try:
        import imageio_ffmpeg
        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.exists(bundled):
            link = "/usr/local/bin/ffmpeg"
            try:
                os.symlink(bundled, link)
                print(f"Linked bundled ffmpeg: {bundled} -> {link}")
            except OSError:
                # If symlink fails (e.g. permissions), add to PATH
                os.environ["PATH"] = os.path.dirname(bundled) + ":" + os.environ.get("PATH", "")
                print(f"Added bundled ffmpeg to PATH: {os.path.dirname(bundled)}")
    except ImportError:
        print("Warning: imageio-ffmpeg not installed, FFmpeg unavailable")


_ensure_ffmpeg()

app = FastAPI(title="VideoFX AI - Video Effects SaaS API")


class FlyReplayMiddleware(BaseHTTPMiddleware):
    """Route 404s to the other Fly.io machine for multi-instance consistency.

    When Fly.io runs 2 machines, uploads land on one machine but subsequent
    requests may hit the other.  Returning ``fly-replay: elsewhere=true``
    tells Fly's proxy to transparently retry on another instance.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.status_code == 404 and not request.headers.get("fly-replay-src"):
            response.headers["fly-replay"] = "elsewhere=true"
        return response


app.add_middleware(FlyReplayMiddleware)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Ensure directories exist — use /data on Fly.io (persistent volume)
_data_root = "/data" if os.path.isdir("/data") else "/tmp"
UPLOAD_DIR = os.getenv("UPLOAD_DIR", f"{_data_root}/video-fx-uploads")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", f"{_data_root}/video-fx-outputs")
os.environ.setdefault("UPLOAD_DIR", UPLOAD_DIR)
os.environ.setdefault("OUTPUT_DIR", OUTPUT_DIR)
os.environ.setdefault("STORE_DIR", UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Import routers AFTER ffmpeg install so HAS_FFMPEG detects it
from app.routers import videos, effects, storage, payments

app.include_router(videos.router, prefix="/api")
app.include_router(effects.router, prefix="/api")
app.include_router(storage.router, prefix="/api")
app.include_router(payments.router, prefix="/api")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/info")
async def info():
    return {
        "name": "VideoFX AI",
        "version": "1.0.0",
        "description": "AI-powered video effects SaaS for Indian creators",
        "features": [
            "Multi-model AI effects (Gemini + Claude)",
            "Decentralized IPFS storage via Pinata",
            "1080p video support up to 500MB",
            "Stripe payments in INR",
        ],
    }
