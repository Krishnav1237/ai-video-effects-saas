# VideoFX AI — Backend API

FastAPI backend for the VideoFX AI video effects platform. Handles video upload, real FFmpeg-based effect processing, AI model orchestration (Gemini/Claude), IPFS storage via Pinata, and Stripe payments.

---

## Quick Start

```bash
# Install dependencies
poetry install

# (Optional) Configure API keys
cp .env.example .env

# Start dev server with auto-reload
poetry run fastapi dev app/main.py
```

- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Requirements

- Python 3.12+
- [Poetry](https://python-poetry.org/) package manager
- FFmpeg (optional locally — bundled via `imageio-ffmpeg`)

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi[standard]` | Web framework + Uvicorn server |
| `python-multipart` | File upload handling |
| `ffmpeg-python` | FFmpeg filter chain builder |
| `imageio-ffmpeg` | Bundled FFmpeg binary (no system install needed) |
| `httpx` | Async HTTP client for AI API calls |
| `aiohttp` | Async HTTP for Pinata uploads |
| `aiofiles` | Async file I/O |
| `stripe` | Payment processing |
| `pinatapy-vourhey` | Pinata IPFS SDK |
| `python-dotenv` | Environment variable loading |

---

## Environment Variables

Create a `.env` file in this directory:

```env
# AI Models (optional — falls back to curated presets)
GEMINI_API_KEY=your-google-gemini-key
CLAUDE_API_KEY=your-anthropic-claude-key

# IPFS Storage (optional — uses demo mode)
PINATA_JWT=your-pinata-jwt-token

# Payments (optional — uses demo mode)
STRIPE_SECRET_KEY=your-stripe-secret-key

# File Storage (defaults shown)
UPLOAD_DIR=/tmp/video-fx-uploads
OUTPUT_DIR=/tmp/video-fx-outputs
```

> The app is fully functional without any API keys. AI effects fall back to curated professional presets, IPFS returns demo CIDs, and Stripe returns demo checkout URLs.

---

## Project Structure

```
app/
├── main.py                     # FastAPI app, middleware, startup config
│
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic models and enums
│       ├── EffectType           # 8 effect types
│       ├── AIModel              # gemini / claude / auto
│       ├── VideoStatus          # uploaded / processing / completed / failed
│       ├── PlanTier             # free / pro / enterprise
│       ├── VideoMetadata        # Video file + metadata
│       ├── EffectRequest        # Apply effect request body
│       └── PricingPlan          # Subscription plan definition
│
├── routers/
│   ├── videos.py               # Upload, list, stream, download, delete
│   ├── effects.py              # Apply effects, preview, job tracking
│   ├── storage.py              # IPFS pin/unpin via Pinata
│   └── payments.py             # Stripe checkout, plans, subscriptions
│
└── services/
    ├── video_processor.py      # FFmpeg filter chain builders
    │   ├── process_video()     # Main processing pipeline
    │   ├── _build_*_filters()  # Per-effect filter chain builders
    │   └── _add_watermark()    # Free tier watermark overlay
    │
    ├── ai_orchestrator.py      # AI model orchestration
    │   ├── generate_effect_params()   # Main entry point
    │   ├── _call_gemini()      # Gemini API call + JSON parsing
    │   ├── _call_claude()      # Claude API call + JSON parsing
    │   ├── COLOR_GRADING_PRESETS      # 6 curated looks
    │   └── STYLE_TRANSFER_PRESETS     # 8 cinematic styles
    │
    ├── job_queue.py            # File-backed async job queue
    │   ├── JobQueue class      # Thread-safe JSON persistence
    │   └── Job states          # queued -> analyzing -> processing -> encoding -> completed
    │
    ├── video_store.py          # File-backed video metadata store
    │   └── VideoStore class    # Thread-safe CRUD with JSON persistence
    │
    ├── stripe_service.py       # Stripe plan definitions + checkout
    └── pinata_service.py       # IPFS pin/unpin operations
```

---

## API Endpoints

See [docs/API.md](../docs/API.md) for the full API reference.

### Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/healthz` | Health check |
| `GET` | `/api/info` | App metadata |
| `POST` | `/api/upload` | Upload video |
| `GET` | `/api/videos` | List videos |
| `GET` | `/api/videos/{id}` | Get video details |
| `GET` | `/api/videos/{id}/stream` | Stream video |
| `GET` | `/api/videos/{id}/download` | Download video |
| `GET` | `/api/videos/{id}/thumbnail` | Get thumbnail |
| `DELETE` | `/api/videos/{id}` | Delete video |
| `GET` | `/api/effects` | List available effects |
| `POST` | `/api/effects/apply` | Apply effect (async) |
| `POST` | `/api/effects/preview` | Preview effect params |
| `GET` | `/api/jobs/{id}` | Get job status |
| `GET` | `/api/jobs` | List jobs |
| `POST` | `/api/storage/pin` | Pin to IPFS |
| `GET` | `/api/storage/{cid}` | Get pin info |
| `DELETE` | `/api/storage/{cid}` | Unpin from IPFS |
| `GET` | `/api/payments/plans` | List pricing plans |
| `POST` | `/api/payments/create-checkout` | Create Stripe session |

---

## Video Processing

All effects use real FFmpeg processing via `imageio-ffmpeg`. The processing pipeline:

1. **Metadata extraction:** Parse `ffmpeg -i` stderr for resolution, FPS, codec, duration
2. **AI parameter generation:** Call Gemini/Claude or use curated presets
3. **Filter chain construction:** Build FFmpeg `-vf` and `-af` filter strings
4. **Encoding:** Run FFmpeg with memory-efficient settings (`ultrafast`, 1 thread, 2M buffer)
5. **Watermarking:** Overlay branding box on free-tier exports
6. **Output registration:** Store output video metadata in the video store

### Encoding Settings (Production)

```
-c:v libx264 -preset ultrafast -crf 23 -tune fastdecode
-bufsize 2M -maxrate 2M -threads 1
-c:a aac -b:a 128k -movflags +faststart
```

These settings are tuned for Fly.io's 256MB shared-CPU machines.

---

## Deployment

See [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for the full deployment guide.

```bash
# Quick deploy to Fly.io
flyctl launch --name your-app-name
flyctl volumes create app_data --size 1
flyctl secrets set GEMINI_API_KEY=... CLAUDE_API_KEY=...
flyctl deploy
```

---

## Docker

```bash
# Build
docker build -t videofx-api .

# Run
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -v $(pwd)/data:/data \
  videofx-api
```
