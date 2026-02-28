# API Reference

**Base URL:** `https://app-zkatyczs.fly.dev` (production) or `http://localhost:8000` (development)

**Interactive Docs:** `{BASE_URL}/docs` (Swagger UI) | `{BASE_URL}/redoc` (ReDoc)

---

## Table of Contents

- [Health](#health)
- [Videos](#videos)
  - [Upload Video](#upload-video)
  - [List Videos](#list-videos)
  - [Get Video](#get-video)
  - [Stream Video](#stream-video)
  - [Download Video](#download-video)
  - [Get Thumbnail](#get-thumbnail)
  - [Delete Video](#delete-video)
- [Effects](#effects)
  - [List Effects](#list-effects)
  - [Apply Effect](#apply-effect)
  - [Preview Effect](#preview-effect)
- [Jobs](#jobs)
  - [Get Job Status](#get-job-status)
  - [List Jobs](#list-jobs)
- [Storage (IPFS)](#storage-ipfs)
  - [Pin Video](#pin-video)
  - [Get Pin Info](#get-pin-info)
  - [Unpin Video](#unpin-video)
  - [Storage Health](#storage-health)
- [Payments](#payments)
  - [List Plans](#list-plans)
  - [Create Checkout](#create-checkout)
  - [Get Subscription](#get-subscription)
  - [Upgrade Plan](#upgrade-plan)

---

## Health

### `GET /healthz`

Health check endpoint.

**Response:**
```json
{ "status": "ok" }
```

### `GET /api/info`

Application metadata.

**Response:**
```json
{
  "name": "VideoFX AI",
  "version": "1.0.0",
  "description": "AI-powered video effects SaaS for Indian creators",
  "features": [
    "Multi-model AI effects (Gemini + Claude)",
    "Decentralized IPFS storage via Pinata",
    "1080p video support up to 500MB",
    "Stripe payments in INR"
  ]
}
```

---

## Videos

### Upload Video

`POST /api/upload`

Upload a video file for processing. Supports MP4, MOV, AVI, MKV, WebM, M4V up to 500MB.

**Request:** `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| `file` | File | Video file (required) |

**Response:** `200 OK`
```json
{
  "status": "success",
  "video": {
    "id": "8ba97b96-567c-452a-9650-76835ca2916e",
    "filename": "8ba97b96-567c-452a-9650-76835ca2916e.mp4",
    "original_name": "my_video.mp4",
    "size_bytes": 183459,
    "duration_seconds": 5.0,
    "width": 640,
    "height": 360,
    "format": "mp4",
    "status": "uploaded",
    "ipfs_cid": null,
    "ipfs_url": null,
    "created_at": 1772280733.09,
    "effects_applied": []
  },
  "metadata": {
    "duration_seconds": 5.0,
    "resolution": "640x360",
    "fps": 30.0,
    "codec": "h264",
    "bit_rate": 293000,
    "has_audio": true
  },
  "thumbnail_available": true,
  "message": "Video uploaded (0.2MB, 640x360, 5.0s)"
}
```

**Errors:**
- `400` - No filename or unsupported format
- `413` - File exceeds 500MB limit

---

### List Videos

`GET /api/videos?page=1&limit=20`

List all uploaded videos with pagination and statistics.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (>= 1) |
| `limit` | int | 20 | Items per page (1-100) |

**Response:** `200 OK`
```json
{
  "videos": [ ... ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "has_more": false,
  "stats": {
    "total_videos": 5,
    "total_size_bytes": 917295,
    "total_size_mb": 0.9,
    "videos_with_effects": 2,
    "videos_on_ipfs": 0
  }
}
```

---

### Get Video

`GET /api/videos/{video_id}`

**Response:** `200 OK`
```json
{
  "video": { ... },
  "file_available": true,
  "stream_url": "/api/videos/{video_id}/stream",
  "download_url": "/api/videos/{video_id}/download"
}
```

---

### Stream Video

`GET /api/videos/{video_id}/stream`

Stream video for browser playback. Returns `video/mp4` with `Accept-Ranges` header for seeking.

**Response:** `200 OK` (video/mp4 binary stream)

---

### Download Video

`GET /api/videos/{video_id}/download`

Download video as a file attachment.

**Response:** `200 OK` (application/octet-stream)

---

### Get Thumbnail

`GET /api/videos/{video_id}/thumbnail`

Get a JPEG thumbnail frame from the video (auto-generated at 1s offset).

**Response:** `200 OK` (image/jpeg)

---

### Delete Video

`DELETE /api/videos/{video_id}`

Delete a video and its associated files from disk.

**Response:** `200 OK`
```json
{ "status": "deleted", "video_id": "..." }
```

---

## Effects

### List Effects

`GET /api/effects`

Get the full effect catalog with available presets and AI models.

**Response:** `200 OK`
```json
{
  "effects": [
    {
      "type": "color_grading",
      "name": "Color Grading",
      "description": "Professional color correction: 6 curated looks with fine-tuning controls",
      "icon": "sun",
      "recommended_model": "gemini",
      "category": "enhancement",
      "produces_output": true
    }
  ],
  "models": [
    { "id": "gemini", "name": "Gemini 2.0 Flash", "provider": "Google", "best_for": [...] },
    { "id": "claude", "name": "Claude Sonnet", "provider": "Anthropic", "best_for": [...] }
  ],
  "presets": {
    "color_grading": ["cinematic_warm", "cinematic_cool", "vibrant", "moody", "golden_hour", "film_emulation"],
    "style_transfer": ["cinematic", "vintage", "noir", "warm", "cool", "anime", "bleach", "sunset"]
  }
}
```

---

### Apply Effect

`POST /api/effects/apply`

Apply an AI effect to a video. Starts asynchronous processing and returns a job ID.

**Request Body:**
```json
{
  "video_id": "8ba97b96-567c-452a-9650-76835ca2916e",
  "effect_type": "color_grading",
  "ai_model": "auto",
  "parameters": {
    "look": "cinematic_warm"
  },
  "intensity": 0.8
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `video_id` | string | required | ID of uploaded video |
| `effect_type` | enum | required | One of: `color_grading`, `upscaling`, `style_transfer`, `slow_motion`, `stabilization`, `background_removal`, `motion_graphics`, `auto_caption` |
| `ai_model` | enum | `"auto"` | `"auto"`, `"gemini"`, or `"claude"` |
| `parameters` | object | `{}` | Effect-specific parameters (see below) |
| `intensity` | float | `0.5` | Effect strength (0.0 to 1.0) |

**Effect Parameters:**

| Effect | Key Parameters |
|--------|---------------|
| `color_grading` | `look`: preset name (e.g., `cinematic_warm`) |
| `upscaling` | `width`, `height`: target resolution |
| `style_transfer` | `style`: style name (e.g., `noir`, `vintage`) |
| `slow_motion` | `factor`: slowdown multiplier (1.5 - 8.0) |
| `stabilization` | `shakiness` (1-10), `smoothing` (1-30) |
| `background_removal` | `blur_background` (bool), `blur_strength` (5-40) |
| `motion_graphics` | `type` (`title`/`lower_third`/`fade`), `title`, `name` |
| `auto_caption` | `text`, `position` (`bottom`/`top`/`center`), `bg_opacity` |

**Response:** `200 OK`
```json
{
  "status": "processing",
  "job_id": "d852befc-db2e-4c14-a609-4d4cb5bd79f5",
  "message": "Processing 'color_grading' effect -- track progress via /api/jobs/{job_id}"
}
```

---

### Preview Effect

`POST /api/effects/preview`

Generate effect parameters without processing (instant response). Same request body as Apply Effect.

**Response:** `200 OK`
```json
{
  "status": "preview",
  "effect_type": "color_grading",
  "model_used": "curated_preset",
  "ai_enhanced": false,
  "params": { "brightness": 0.02, "contrast": 1.15, ... },
  "message": "Preview parameters generated. Use /effects/apply to process the video."
}
```

---

## Jobs

### Get Job Status

`GET /api/jobs/{job_id}`

Poll for processing progress and results.

**Response:** `200 OK`
```json
{
  "job": {
    "id": "d852befc-db2e-4c14-a609-4d4cb5bd79f5",
    "video_id": "8ba97b96-567c-452a-9650-76835ca2916e",
    "effect_type": "color_grading",
    "ai_model": "auto",
    "intensity": 0.8,
    "status": "completed",
    "progress": 100.0,
    "message": "Processing complete",
    "result": {
      "output_video_id": "2968ac81-fa93-42c5-8d89-6ce691b8121b",
      "processing_time_seconds": 2.48,
      "model_used": "curated_preset",
      "ai_enhanced": false,
      "effect_params": { ... },
      "input_info": { "width": 640, "height": 360, ... },
      "output_info": { "width": 640, "height": 360, ... }
    },
    "error": null,
    "created_at": 1772280733.89,
    "started_at": 1772280733.90,
    "completed_at": 1772280736.38,
    "processing_time_seconds": 2.48
  }
}
```

**Job Status Values:**
| Status | Description |
|--------|-------------|
| `queued` | Job created, waiting to start |
| `analyzing` | Extracting video metadata |
| `processing` | Applying FFmpeg effect |
| `encoding` | Finalizing output file |
| `completed` | Done; result contains output_video_id |
| `failed` | Error occurred; check error field |

---

### List Jobs

`GET /api/jobs?video_id={id}&limit=50`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_id` | string | null | Filter by video ID |
| `limit` | int | 50 | Max results (1-200) |

**Response:** `200 OK`
```json
{ "jobs": [ ... ] }
```

---

## Storage (IPFS)

### Pin Video

`POST /api/storage/pin`

Pin a video to IPFS via Pinata for decentralized storage.

**Request Body:**
```json
{
  "video_id": "8ba97b96-567c-452a-9650-76835ca2916e",
  "name": "My Video"
}
```

**Response:** `200 OK`
```json
{
  "status": "pinned",
  "video_id": "...",
  "ipfs_cid": "QmXyz...",
  "ipfs_url": "https://gateway.pinata.cloud/ipfs/QmXyz...",
  "pin_size": 183459,
  "is_demo": true
}
```

> `is_demo: true` when `PINATA_JWT` is not configured.

---

### Get Pin Info

`GET /api/storage/{cid}`

Get information about a pinned file by CID.

---

### Unpin Video

`DELETE /api/storage/{cid}`

Remove a pin from IPFS.

---

### Storage Health

`GET /api/storage/health/check`

Check Pinata/IPFS connection status.

---

## Payments

### List Plans

`GET /api/payments/plans`

Get all pricing plans in INR.

**Response:** `200 OK`
```json
{
  "plans": [
    {
      "tier": "free",
      "name": "Starter",
      "price_inr": 0,
      "price_display": "Free",
      "features": ["5 video exports/month", "720p max", "Basic AI effects", "500MB storage", "Watermarked exports"],
      "max_video_size_mb": 100,
      "max_monthly_exports": 5,
      "ai_models_available": ["gemini"]
    },
    {
      "tier": "pro",
      "name": "Pro Creator",
      "price_inr": 499,
      "price_display": "Rs 499/month",
      "features": ["50 exports/month", "1080p", "All AI effects", "5GB IPFS", "No watermark", "Priority processing"],
      "max_video_size_mb": 500,
      "max_monthly_exports": 50,
      "ai_models_available": ["gemini", "claude"]
    },
    {
      "tier": "enterprise",
      "name": "Studio",
      "price_inr": 1999,
      "price_display": "Rs 1999/month",
      "features": ["Unlimited exports", "4K", "All AI + custom models", "50GB IPFS", "No watermark", "Priority", "API access", "Team collaboration"],
      "max_video_size_mb": 500,
      "max_monthly_exports": -1,
      "ai_models_available": ["gemini", "claude"]
    }
  ]
}
```

---

### Create Checkout

`POST /api/payments/create-checkout`

Create a Stripe checkout session for subscription.

**Request Body:**
```json
{
  "plan": "pro",
  "success_url": "https://your-app.com/success",
  "cancel_url": "https://your-app.com/pricing"
}
```

**Response:** `200 OK`
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_..."
}
```

> Returns demo checkout URL when `STRIPE_SECRET_KEY` is not configured.

---

### Get Subscription

`GET /api/user/subscription`

Get current user's subscription status.

**Response:** `200 OK`
```json
{
  "subscription": {
    "tier": "free",
    "active": true,
    "exports_used": 2,
    "exports_limit": 5,
    "storage_used_mb": 0.9,
    "storage_limit_mb": 500.0
  }
}
```

---

### Upgrade Plan

`POST /api/user/subscription/upgrade?tier=pro`

Upgrade subscription tier (demo mode).

**Response:** `200 OK`
```json
{
  "status": "upgraded",
  "subscription": { ... },
  "message": "Upgraded to Pro Creator"
}
```
