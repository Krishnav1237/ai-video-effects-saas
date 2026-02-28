# Contributing to VideoFX AI

Thank you for your interest in contributing! This guide covers the development workflow and conventions used in this project.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Architecture Notes](#architecture-notes)

---

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-video-effects-saas.git
   cd ai-video-effects-saas
   ```
3. Set up the development environment (see below)
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Backend

```bash
cd video-fx-api

# Install Python 3.12+ and Poetry
pip install poetry

# Install dependencies
poetry install

# Create environment file
cp .env.example .env
# Edit .env with your API keys (optional — app works without them)

# Start development server
poetry run fastapi dev app/main.py
```

The API runs at `http://localhost:8000` with auto-reload enabled. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd video-fx-app

# Install dependencies
npm install

# Set backend URL
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

The app runs at `http://localhost:5173` with hot module replacement.

### Running Both Together

Open two terminal tabs:

```bash
# Tab 1: Backend
cd video-fx-api && poetry run fastapi dev app/main.py

# Tab 2: Frontend
cd video-fx-app && npm run dev
```

---

## Project Structure

```
video-fx-api/           # FastAPI backend
├── app/
│   ├── main.py         # App setup, middleware, config
│   ├── models/         # Pydantic schemas and enums
│   ├── routers/        # API endpoint handlers
│   └── services/       # Business logic (video processing, AI, payments)
├── Dockerfile          # Production container
└── pyproject.toml      # Python dependencies

video-fx-app/           # React frontend
├── src/
│   ├── App.tsx         # Router and layout
│   ├── pages/          # Page components
│   ├── components/     # Reusable UI components
│   ├── services/       # API client
│   └── types/          # TypeScript type definitions
└── package.json        # Node dependencies
```

---

## Code Style

### Backend (Python)

- **Type hints** on all function signatures
- **Pydantic models** for request/response schemas (not raw dicts)
- **Async functions** for all route handlers and I/O operations
- **Docstrings** on public functions and classes
- Follow PEP 8; use `ruff` for linting if available
- Keep services stateless where possible; use the file-backed stores for persistence

### Frontend (TypeScript)

- **TypeScript strict mode** — no `any` types
- **Functional components** with hooks (no class components)
- **Tailwind CSS** for styling (no inline styles or CSS modules)
- **Lucide React** for icons (consistent with existing UI)
- Use the `api.ts` service for all backend calls (not raw `fetch`)
- Component naming: PascalCase files matching component names

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new video effect
fix: handle FFmpeg timeout on large files
docs: update API reference for storage endpoints
refactor: extract color grading into separate module
chore: update dependencies
```

---

## Making Changes

### Adding a New Effect

1. **Backend:**
   - Add the effect type to `EffectType` enum in `models/schemas.py`
   - Add FFmpeg filter chain builder in `services/video_processor.py`
   - Add curated presets in `services/ai_orchestrator.py`
   - Add effect metadata to the catalog in `routers/effects.py`

2. **Frontend:**
   - Add the effect type to the TypeScript types in `types/index.ts`
   - The `EffectsPanel` component will auto-discover effects from the API catalog

### Adding an API Endpoint

1. Create or modify the appropriate router in `routers/`
2. Define request/response models in `models/schemas.py`
3. Implement business logic in the appropriate service under `services/`
4. Update `docs/API.md` with the new endpoint documentation

### Modifying the UI

1. Check existing components in `components/` for reusable patterns
2. Use shadcn/ui component patterns and Tailwind utility classes
3. Use the `cn()` utility from `lib/utils` for conditional class merging
4. All API calls should go through `services/api.ts`

---

## Pull Request Process

1. Ensure your code follows the style guidelines above
2. Update documentation if you've changed APIs or added features
3. Test locally:
   - Backend: Verify the endpoint works via Swagger UI at `/docs`
   - Frontend: Verify the UI renders correctly and interacts with the API
4. Create a pull request with a clear description of:
   - What changed and why
   - How to test the changes
   - Any breaking changes or migration steps
5. Wait for review and address any feedback

### PR Checklist

- [ ] Code follows project conventions
- [ ] New endpoints are documented in `docs/API.md`
- [ ] TypeScript types are updated if API contracts changed
- [ ] No secrets or API keys in committed code
- [ ] Tested locally with both frontend and backend running

---

## Architecture Notes

Before making significant changes, read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand:

- The AI orchestration flow (Gemini -> Claude -> curated presets)
- The file-backed persistence model (no database)
- The Fly.io multi-instance routing via `fly-replay` headers
- The FFmpeg encoding settings tuned for low-memory VMs

### Key Design Decisions

1. **File-backed stores over a database:** Simplifies deployment (no Postgres setup) and works well with Fly.io volumes. Trade-off: no cross-machine queries.

2. **Curated presets as fallback:** The app must work without any API keys. Professional presets ensure good output even without AI models.

3. **Bundled FFmpeg (`imageio-ffmpeg`):** Avoids system dependency issues on different platforms and container images.

4. **Watermark on free tier:** Revenue model depends on watermarked free exports driving upgrades to paid plans.

---

## Questions?

Open an issue on GitHub or reach out to the maintainers. We're happy to help you get started!
