# VideoFX AI - AI-Powered Video Effects SaaS

Production-grade video effects platform for Indian creators. Upload videos, apply professional AI-powered effects (color grading, upscaling, style transfer, slow motion, and more), and export with real FFmpeg processing.

**Live Demo:** [Frontend](https://ai-video-editor-app-i7vzlo4k.devinapps.com) | [API](https://app-zkatyczs.fly.dev/docs)

---

## Features

### 8 AI Video Effects
| Effect | Description | Model |
|--------|-------------|-------|
| Color Grading | 6 curated looks: cinematic warm/cool, vibrant, moody, golden hour, film emulation | Gemini |
| AI Upscaling | Lanczos scaling up to 4K with unsharp mask sharpening | Gemini |
| Style Transfer | 8 cinematic styles: noir, vintage, anime, sunset, bleach, warm, cool | Gemini |
| Slow Motion | 1.5x to 8x with pitch-corrected audio via `atempo` | Gemini |
| Stabilization | Two-pass `vidstabdetect` + `vidstabtransform` | Gemini |
| Background Blur | Depth-of-field bokeh via split/boxblur overlay | Gemini |
| Motion Graphics | Fade-in/out, lower-third bar overlays | Claude |
| Auto Captions | Styled caption bar overlays with position control | Claude |

### Multi-Model AI Orchestration
- **Gemini 2.0 Flash** for technical effects (color, upscaling, stabilization)
- **Claude Sonnet** for creative effects (motion graphics, captions)
- **Auto mode** selects the best model per effect type
- Falls back to curated professional presets when API keys are not configured

### Profitability
- Watermarked exports on free tier
- 3-tier INR pricing: Free / Rs 499 Pro / Rs 1,999 Studio
- Stripe checkout integration
- Usage metering and export limits

### Infrastructure
- Real FFmpeg video processing (not mock/demo)
- Async job queue with real-time progress tracking
- File-backed state persistence with thread-safe locking
- IPFS decentralized storage via Pinata
- Fly.io `fly-replay` header for multi-instance routing
- Memory-efficient encoding for cloud VMs

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| UI Components | shadcn/ui + Lucide icons + Recharts |
| Drag & Drop | @dnd-kit (timeline tracks) |
| Backend | FastAPI (Python 3.12) + Uvicorn |
| Video Processing | FFmpeg via `imageio-ffmpeg` + `ffmpeg-python` |
| AI Models | Google Gemini 2.0 Flash + Anthropic Claude Sonnet |
| Storage | IPFS via Pinata |
| Payments | Stripe (INR) |
| Deployment | Fly.io (backend) + Static hosting (frontend) |

---

## Project Structure

```
ai-video-effects-saas/
├── video-fx-api/            # FastAPI backend
│   ├── app/
│   │   ├── main.py          # App entry, middleware, directory config
│   │   ├── models/
│   │   │   └── schemas.py   # Pydantic models & enums
│   │   ├── routers/
│   │   │   ├── videos.py    # Upload, stream, download, delete
│   │   │   ├── effects.py   # Apply effects, job tracking
│   │   │   ├── storage.py   # IPFS/Pinata pinning
│   │   │   └── payments.py  # Stripe checkout & subscriptions
│   │   └── services/
│   │       ├── video_processor.py  # FFmpeg filter chains
│   │       ├── ai_orchestrator.py  # Gemini/Claude API + presets
│   │       ├── job_queue.py        # Async job queue (file-backed)
│   │       ├── video_store.py      # Video metadata store (file-backed)
│   │       ├── stripe_service.py   # Stripe integration
│   │       └── pinata_service.py   # IPFS pinning
│   ├── Dockerfile
│   └── pyproject.toml
├── video-fx-app/            # React frontend
│   ├── src/
│   │   ├── App.tsx          # Router setup
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx    # Video library & stats
│   │   │   ├── Editor.tsx       # Main editor (preview + effects + timeline)
│   │   │   ├── UploadPage.tsx   # Drag-and-drop upload
│   │   │   └── PricingPage.tsx  # INR subscription plans
│   │   ├── components/
│   │   │   ├── VideoPreview.tsx   # HTML5 video player with controls
│   │   │   ├── EffectsPanel.tsx   # Effect cards + preset selector
│   │   │   ├── Timeline.tsx       # Drag-and-drop timeline
│   │   │   ├── VideoUploader.tsx  # Upload dropzone
│   │   │   ├── StoragePanel.tsx   # IPFS pinning UI
│   │   │   └── Navbar.tsx         # Navigation bar
│   │   ├── services/
│   │   │   └── api.ts       # Axios API client
│   │   └── types/
│   │       └── index.ts     # TypeScript interfaces
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md      # System design & data flow
│   ├── API.md               # API reference
│   └── DEPLOYMENT.md        # Deployment guide
└── CONTRIBUTING.md           # Contribution guidelines
```

---

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+ and [Poetry](https://python-poetry.org/)
- FFmpeg (optional locally; bundled via `imageio-ffmpeg` on deployment)

### Backend

```bash
cd video-fx-api
poetry install

# Optional: configure API keys for AI-enhanced processing
cp .env.example .env
# Edit .env with your GEMINI_API_KEY, CLAUDE_API_KEY, etc.

poetry run fastapi dev app/main.py
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend

```bash
cd video-fx-app
npm install

# Point to local backend
echo "VITE_API_URL=http://localhost:8000" > .env

npm run dev
# App running at http://localhost:5173
```

---

## Environment Variables

### Backend (`video-fx-api/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No | Google Gemini API key for AI-enhanced effects |
| `CLAUDE_API_KEY` | No | Anthropic Claude API key for creative effects |
| `PINATA_JWT` | No | Pinata JWT for real IPFS pinning |
| `STRIPE_SECRET_KEY` | No | Stripe secret key for live payments |
| `UPLOAD_DIR` | No | Upload directory (default: `/tmp/video-fx-uploads`) |
| `OUTPUT_DIR` | No | Output directory (default: `/tmp/video-fx-outputs`) |

> Without API keys, the app uses curated professional presets that produce high-quality output.

### Frontend (`video-fx-app/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL (e.g., `http://localhost:8000`) |

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full deployment instructions.

**Quick deploy:**

```bash
# Backend (Fly.io with persistent volume)
cd video-fx-api
flyctl launch --name your-app-name
flyctl volumes create app_data --size 1
flyctl deploy

# Frontend (any static host)
cd video-fx-app
echo "VITE_API_URL=https://your-backend.fly.dev" > .env
npm run build
# Deploy the dist/ folder
```

---

## Documentation

- [Architecture & System Design](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing](CONTRIBUTING.md)
- [Backend README](video-fx-api/README.md)
- [Frontend README](video-fx-app/README.md)

---

## License

MIT
