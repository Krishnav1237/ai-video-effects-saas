# Deployment Guide

This guide covers deploying VideoFX AI to production using Fly.io (backend) and static hosting (frontend).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Backend Deployment (Fly.io)](#backend-deployment-flyio)
- [Frontend Deployment](#frontend-deployment)
- [Environment Variables](#environment-variables)
- [Persistent Volume](#persistent-volume)
- [Multi-Instance Routing](#multi-instance-routing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) installed and authenticated
- Node.js 18+ and npm (for frontend build)
- A Fly.io account (free tier works for testing)

---

## Backend Deployment (Fly.io)

### 1. Initialize Fly App

```bash
cd video-fx-api
flyctl launch --name your-app-name --no-deploy
```

This creates a `fly.toml` configuration file. The included `Dockerfile` handles the build.

### 2. Create Persistent Volume

The backend stores uploaded and processed videos on disk. Create a volume for persistence:

```bash
flyctl volumes create app_data --size 1 --region sin
```

> Use `--region sin` (Singapore) for lowest latency to India. Other options: `maa` (Chennai), `bom` (Mumbai) if available.

### 3. Configure fly.toml

Ensure your `fly.toml` includes the volume mount:

```toml
[build]

[env]
  UPLOAD_DIR = "/data/video-fx-uploads"
  OUTPUT_DIR = "/data/video-fx-outputs"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[mounts]
  source = "app_data"
  destination = "/data"

[[vm]]
  size = "shared-cpu-1x"
  memory = "256mb"
```

### 4. Set Secrets

```bash
# Required for AI-enhanced effects (optional - falls back to curated presets)
flyctl secrets set GEMINI_API_KEY=your-gemini-key
flyctl secrets set CLAUDE_API_KEY=your-claude-key

# Required for real IPFS storage (optional - uses demo mode)
flyctl secrets set PINATA_JWT=your-pinata-jwt

# Required for live payments (optional - uses demo mode)
flyctl secrets set STRIPE_SECRET_KEY=your-stripe-secret-key
```

### 5. Deploy

```bash
flyctl deploy
```

### 6. Verify

```bash
# Check app status
flyctl status

# View logs
flyctl logs

# Test health endpoint
curl https://your-app-name.fly.dev/healthz
```

---

## Frontend Deployment

The frontend is a static Vite build that can be deployed to any static hosting provider.

### Build

```bash
cd video-fx-app

# Set the backend URL
echo "VITE_API_URL=https://your-app-name.fly.dev" > .env

# Build
npm install
npm run build
```

The `dist/` folder contains the static site.

### Deploy Options

**Vercel:**
```bash
npx vercel --prod
```

**Netlify:**
```bash
npx netlify deploy --prod --dir=dist
```

**Fly.io Static (via Dockerfile):**
Create a simple nginx Dockerfile and deploy alongside the backend.

**Any static host:**
Upload the `dist/` folder contents to your preferred CDN or static hosting.

---

## Environment Variables

### Backend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | No | - | Google Gemini 2.0 Flash API key |
| `CLAUDE_API_KEY` | No | - | Anthropic Claude Sonnet API key |
| `PINATA_JWT` | No | - | Pinata JWT for IPFS pinning |
| `STRIPE_SECRET_KEY` | No | - | Stripe secret key for payments |
| `UPLOAD_DIR` | No | `/tmp/video-fx-uploads` | Video upload directory |
| `OUTPUT_DIR` | No | `/tmp/video-fx-outputs` | Processed video output directory |

> **Note:** On Fly.io, set `UPLOAD_DIR=/data/video-fx-uploads` and `OUTPUT_DIR=/data/video-fx-outputs` to use the persistent volume.

### Frontend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | - | Full URL of the backend API |

---

## Persistent Volume

Fly.io machines are ephemeral. Without a persistent volume, uploaded videos are lost on restart.

### Volume Details

- Mount point: `/data`
- Recommended size: 1GB for testing, 10GB+ for production
- Contains: uploaded videos, processed outputs, metadata JSON stores

### Scaling Note

Each Fly.io machine gets its own volume. If you scale to 2+ machines:
- Each machine has an independent volume with independent data
- The `FlyReplayMiddleware` handles routing requests to the correct machine
- A 404 on machine A automatically retries on machine B

For true multi-instance scaling, consider migrating to an external object store (S3, R2, etc.).

---

## Multi-Instance Routing

Fly.io may run multiple machines for availability. The backend includes `FlyReplayMiddleware` that automatically handles cross-machine routing:

1. Request hits machine A
2. If the requested video isn't on machine A, it returns a 404
3. The middleware adds `fly-replay: elsewhere=true` header
4. Fly.io's proxy retries the request on machine B
5. The `fly-replay-src` header prevents infinite loops

This works transparently for all video/job endpoints without any client-side changes.

---

## Monitoring

### Health Check

```bash
curl https://your-app-name.fly.dev/healthz
# {"status":"ok"}
```

### Logs

```bash
# Live log stream
flyctl logs

# Or via the Fly.io dashboard
```

### Key Metrics to Watch

- **Memory usage:** FFmpeg processing can spike RAM. The encoding settings are tuned for 256MB machines (`-preset ultrafast -threads 1`).
- **Disk usage:** Monitor volume usage with `flyctl volumes list`. Videos accumulate quickly.
- **Processing time:** Color grading takes ~2.5s; stabilization (two-pass) takes longer.

---

## Troubleshooting

### FFmpeg Not Found

The backend bundles FFmpeg via `imageio-ffmpeg`. If you see "ffmpeg not found" errors:
1. Ensure `imageio-ffmpeg` is in `pyproject.toml` dependencies
2. The code uses `imageio_ffmpeg.get_ffmpeg_exe()` to locate the binary
3. System FFmpeg is not required

### Out of Memory (OOM)

If FFmpeg processes get killed:
1. Ensure encoding settings use `-preset ultrafast -threads 1`
2. Add `-bufsize 2M -maxrate 2M` to limit memory
3. Consider scaling to a larger VM: `flyctl scale vm shared-cpu-2x`

### Videos Not Found After Deploy

Fly.io creates new machines on deploy. Ensure:
1. A persistent volume is mounted at `/data`
2. `UPLOAD_DIR` and `OUTPUT_DIR` point to `/data/...`
3. The volume is in the same region as your machines

### CORS Errors

The backend allows all origins by default. If you see CORS errors:
1. Check that the backend URL in the frontend `.env` doesn't have a trailing slash
2. Verify the backend is actually running and accessible
3. Check browser console for the actual blocked origin

### Stripe Webhook Issues

For production Stripe:
1. Set up webhook endpoint at `https://your-app.fly.dev/api/payments/webhook`
2. Configure Stripe webhook signing secret
3. Verify webhook signatures in production
