# VideoFX AI — Frontend

React + TypeScript + Vite frontend for the VideoFX AI video effects platform. Features a drag-and-drop timeline editor, real-time effect preview, IPFS storage panel, and INR pricing page.

---

## Quick Start

```bash
# Install dependencies
npm install

# Set backend URL
echo "VITE_API_URL=http://localhost:8000" > .env

# Start dev server
npm run dev
```

- **App:** http://localhost:5173
- **HMR** enabled for instant feedback

---

## Requirements

- Node.js 18+
- npm 9+

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `react` + `react-dom` | UI framework |
| `react-router-dom` | Client-side routing |
| `axios` | HTTP client for API calls |
| `@dnd-kit/core` + `@dnd-kit/sortable` | Drag-and-drop timeline |
| `lucide-react` | Icon library |
| `recharts` | Dashboard charts |
| `tailwindcss` + `tailwindcss-animate` | Utility-first CSS |
| `class-variance-authority` + `clsx` + `tailwind-merge` | Conditional class utilities |

---

## Environment Variables

Create a `.env` file in this directory:

```env
# Backend API URL (required)
VITE_API_URL=http://localhost:8000
```

For production builds, point to your deployed backend:

```env
VITE_API_URL=https://your-backend.fly.dev
```

---

## Project Structure

```
src/
├── App.tsx                    # React Router setup
├── main.tsx                   # Entry point
├── index.css                  # Tailwind base + custom styles
│
├── pages/
│   ├── Dashboard.tsx          # Video library with stats and quick actions
│   ├── Editor.tsx             # Main editing workspace
│   ├── UploadPage.tsx         # Drag-and-drop video upload
│   └── PricingPage.tsx        # INR subscription plans
│
├── components/
│   ├── Navbar.tsx             # Top navigation bar
│   ├── VideoPreview.tsx       # HTML5 video player with controls
│   ├── EffectsPanel.tsx       # Effect cards, presets, intensity slider
│   ├── Timeline.tsx           # Drag-and-drop timeline tracks (@dnd-kit)
│   ├── VideoUploader.tsx      # Upload dropzone component
│   └── StoragePanel.tsx       # IPFS pinning UI
│
├── services/
│   └── api.ts                 # Axios API client (all backend calls)
│
└── types/
    └── index.ts               # TypeScript interfaces and types
```

---

## Pages

### Dashboard (`/`)
- Lists all uploaded videos with thumbnails
- Shows aggregate stats (total videos, storage used, effects applied)
- Quick action buttons for upload and edit

### Editor (`/editor?video={id}`)
- **VideoPreview:** HTML5 video player with play/pause, seeking, and fullscreen
- **EffectsPanel:** 8 AI effects with preset dropdowns, intensity slider, and model selector (Gemini/Claude/Auto)
- **Timeline:** Drag-and-drop tracks for arranging effects (via @dnd-kit)
- **StoragePanel:** Pin processed videos to IPFS via Pinata
- Real-time job progress tracking with polling

### Upload (`/upload`)
- Drag-and-drop zone for video files
- Supports MP4, MOV, AVI, MKV, WebM, M4V up to 500MB
- Shows upload progress and redirects to editor on success

### Pricing (`/pricing`)
- Three-tier INR pricing: Free / Rs 499 Pro / Rs 1,999 Studio
- Feature comparison table
- Stripe checkout integration

---

## API Client

All backend communication goes through `services/api.ts`:

```typescript
import api from '../services/api';

// Upload a video
const response = await api.uploadVideo(file);

// Apply an effect
const job = await api.applyEffect(videoId, 'color_grading', {
  look: 'cinematic_warm',
  intensity: 0.8,
  ai_model: 'auto'
});

// Poll job status
const status = await api.getJobStatus(jobId);

// Stream video
const streamUrl = api.getStreamUrl(videoId);
```

---

## Building for Production

```bash
# Build optimized bundle
npm run build

# Preview production build locally
npm run preview
```

The `dist/` folder contains the static site ready for deployment to any CDN or static host.

---

## Styling

The app uses **Tailwind CSS** with the following conventions:

- Utility-first classes throughout (no CSS modules)
- `cn()` helper (clsx + tailwind-merge) for conditional classes
- Dark gradient backgrounds (`from-gray-900 via-gray-800 to-gray-900`)
- Purple/blue accent colors for interactive elements
- `tailwindcss-animate` for transition utilities

---

## Deployment

See [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for full instructions.

```bash
# Build with production backend URL
echo "VITE_API_URL=https://your-backend.fly.dev" > .env
npm run build

# Deploy dist/ to any static host (Vercel, Netlify, etc.)
```
