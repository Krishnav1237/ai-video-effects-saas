# Architecture & System Design

## High-Level Overview

VideoFX AI is a full-stack video effects SaaS with a React frontend and FastAPI backend. Videos are uploaded to the server, processed with real FFmpeg filter chains (parameterized by AI models or curated presets), and served back to the client for preview and download.

```
                            +------------------+
                            |   React Frontend |
                            |  (Vite + TS)     |
                            +--------+---------+
                                     |
                              HTTPS / REST
                                     |
                            +--------v---------+
                            |  FastAPI Backend  |
                            |  (Fly.io x2)     |
                            +--------+---------+
                                     |
                   +-----------------+------------------+
                   |                 |                  |
           +-------v------+  +------v-------+  +------v-------+
           | FFmpeg Engine |  | AI Orchestrator|  | Pinata IPFS |
           | (imageio-ffmpeg)|  | Gemini/Claude |  | (optional)  |
           +--------------+  +--------------+  +--------------+
```

---

## Request Flow

### Upload -> Process -> Download

```
1. Client uploads video via POST /api/upload
   - File saved to UPLOAD_DIR (chunked 1MB reads, max 500MB)
   - Metadata extracted via `ffmpeg -i` stderr parsing
   - VideoMetadata stored in file-backed JSON store

2. Client applies effect via POST /api/effects/apply
   - AI Orchestrator generates FFmpeg parameters:
     a. Try primary AI model (Gemini or Claude based on effect type)
     b. Fallback to secondary model if primary fails
     c. Fallback to curated production presets if no API keys
   - Job created in file-backed job queue
   - Background task starts FFmpeg processing

3. Client polls job via GET /api/jobs/{job_id}
   - Returns status (queued -> analyzing -> processing -> encoding -> completed)
   - Progress percentage (5% -> 15% -> 25% -> 85% -> 100%)
   - Result includes output_video_id on completion

4. Client streams/downloads via GET /api/videos/{output_id}/stream
   - FileResponse with Accept-Ranges for browser video player
   - Processed video includes watermark overlay on free tier
```

---

## Backend Architecture

### Module Responsibilities

```
app/
├── main.py                    # FastAPI app, middleware stack, directory config
│
├── models/
│   └── schemas.py             # Pydantic models: VideoMetadata, EffectRequest,
│                              # PricingPlan, TimelineTrack, etc.
│
├── routers/
│   ├── videos.py              # CRUD + streaming for video files
│   ├── effects.py             # Effect application + job management
│   ├── storage.py             # IPFS pinning via Pinata
│   └── payments.py            # Stripe checkout + subscriptions
│
└── services/
    ├── video_processor.py     # FFmpeg filter chain builders + process_video()
    ├── ai_orchestrator.py     # Gemini/Claude API calls + curated presets
    ├── job_queue.py           # File-backed async job queue
    ├── video_store.py         # File-backed video metadata store
    ├── stripe_service.py      # Stripe plan definitions + checkout
    └── pinata_service.py      # Pinata IPFS pin/unpin
```

### Middleware Stack (order matters)

1. **FlyReplayMiddleware** - Intercepts 404 responses and adds `fly-replay: elsewhere=true` header. This tells Fly.io's proxy to retry the request on another machine, solving the multi-instance state split problem.
2. **CORSMiddleware** - Allows all origins for frontend-backend communication.

### Video Processing Pipeline

The `video_processor.py` module builds FFmpeg filter chains for each effect type:

| Effect | Video Filter | Audio Filter | Notes |
|--------|-------------|-------------|-------|
| Color Grading | `eq` + `colorbalance` + `hue` + `vignette` + `unsharp` | - | 6 curated presets with intensity scaling |
| Upscaling | `scale=W:H:flags=lanczos` + `unsharp` | - | Target resolution calculated from scale factor |
| Style Transfer | `curves` + `eq` + `hue` + `colorbalance` + `vignette` | - | 8 style presets |
| Slow Motion | `setpts=N*PTS` | `atempo` (chained for >2x) | Maintains audio sync |
| Stabilization | `vidstabdetect` (pass 1) + `vidstabtransform` + `unsharp` (pass 2) | - | Two-pass for quality |
| Background Blur | `split` + `boxblur` + `overlay` | - | Simulated depth-of-field |
| Motion Graphics | `fade` + `drawbox` | - | Title and lower-third overlays |
| Auto Captions | `drawbox` | - | Positioned caption bar |
| Watermark | `drawbox` (bottom-right) | - | Semi-transparent branding box |

### Encoding Settings

Optimized for Fly.io's 256MB RAM machines:

```
-c:v libx264 -preset ultrafast -crf 23 -tune fastdecode
-bufsize 2M -maxrate 2M -threads 1
-c:a aac -b:a 128k -movflags +faststart
```

---

## Frontend Architecture

### Page Structure

```
App.tsx (React Router)
├── / ............... Dashboard.tsx     # Video library, stats, quick actions
├── /editor ......... Editor.tsx        # Main editing workspace
│   ├── VideoPreview                    # HTML5 video player
│   ├── EffectsPanel                    # Effect cards, presets, intensity
│   ├── StoragePanel                    # IPFS pinning
│   └── Timeline                        # Drag-and-drop tracks (@dnd-kit)
├── /upload ......... UploadPage.tsx    # Dropzone upload
└── /pricing ........ PricingPage.tsx   # INR plan comparison
```

### State Management

The frontend uses local React state (no Redux/Zustand) since the app is server-driven:
- Video metadata comes from `GET /api/videos`
- Effect processing is tracked via job polling (`GET /api/jobs/{id}`)
- The API client (`services/api.ts`) manages all backend communication

### Effect Application Flow (Frontend)

```
1. User selects effect card in EffectsPanel
2. Frontend sends POST /api/effects/apply with:
   - video_id, effect_type, preset, intensity, ai_model
3. UI shows "Processing" state with progress bar
4. Frontend polls GET /api/jobs/{job_id} every 2 seconds
5. On completion, UI shows:
   - "Effect Applied" badge
   - Processing time and model used
   - Download button for output video
   - Before/after toggle capability
```

---

## AI Orchestration

### Model Selection

```python
EFFECT_MODEL_MAP = {
    MOTION_GRAPHICS:     Claude,   # Creative text/graphics
    AUTO_CAPTION:        Claude,   # Creative text generation
    UPSCALING:           Gemini,   # Technical image processing
    STYLE_TRANSFER:      Gemini,   # Technical color manipulation
    COLOR_GRADING:       Gemini,   # Technical color science
    STABILIZATION:       Gemini,   # Technical motion analysis
    SLOW_MOTION:         Gemini,   # Technical temporal processing
    BACKGROUND_REMOVAL:  Gemini,   # Technical segmentation
}
```

### Fallback Chain

```
1. Primary model (based on effect type or user selection)
   ↓ (if API key missing or API error)
2. Secondary model (the other AI)
   ↓ (if also unavailable)
3. Curated production presets (always available, no API key needed)
```

The curated presets are professionally tuned and produce high-quality output even without any AI API keys.

---

## Data Persistence

### File-Backed Stores

Both `VideoStore` and `JobQueue` use JSON files for persistence:

```
{STORE_DIR}/
├── .video_store.json    # Array of VideoMetadata objects
└── .jobs_store.json     # Array of Job objects
```

Each store:
- Uses `threading.Lock()` for thread-safe concurrent access
- Re-reads from disk on every `get()` call for cross-instance consistency
- Writes to disk after every mutation (`add`, `update`, `delete`)
- Handles corrupt/missing files gracefully

### Directory Layout on Deployment

```
/data/                          # Fly.io persistent volume
├── video-fx-uploads/           # Uploaded video files
│   ├── {uuid}.mp4
│   ├── .video_store.json       # Video metadata
│   └── .jobs_store.json        # Job state
└── video-fx-outputs/           # Processed video files
    ├── {uuid}.mp4              # Output videos
    └── thumb_{uuid}.jpg        # Thumbnails
```

---

## Fly.io Multi-Instance Routing

Fly.io runs 2 machines by default. Since each machine has its own volume, an upload on machine A won't be visible on machine B.

**Solution: `fly-replay` header middleware**

```python
class FlyReplayMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if response.status_code == 404 and not request.headers.get("fly-replay-src"):
            response.headers["fly-replay"] = "elsewhere=true"
        return response
```

When a request returns 404 (e.g., video not found on this machine), the middleware adds `fly-replay: elsewhere=true`. Fly.io's proxy automatically retries the request on the other machine. The `fly-replay-src` check prevents infinite loops.

---

## Security Considerations

- No API keys or secrets in source code; all loaded from environment variables
- File uploads validated by extension and size (max 500MB)
- CORS configured for cross-origin frontend access
- Stripe webhook signatures should be verified in production
- IPFS pins are public by nature; ensure users understand this
