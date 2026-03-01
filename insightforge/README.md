# InsightForge AI - Automated Industry Intelligence Platform

InsightForge AI is a production-ready MVP SaaS for generating structured, citation-backed industry intelligence reports.

## Features
- Single-user dashboard (no auth required in MVP)
- Report input form:
  - Industry
  - Geography
  - Time horizon
  - Depth (`Basic`, `Professional`, `Investor-grade`)
  - Include Financial Forecast
  - Include Competitive Landscape
- Async report generation pipeline:
  - Local mode: FastAPI BackgroundTasks (no Celery worker required)
  - Docker/production mode: Celery + Redis
- Multi-agent orchestration (Research, Scraper, Analysis, Cross-Validation, Financial Model, Report Composer)
- Structured outputs:
  - Executive Summary
  - Market Overview
  - TAM/SAM/SOM
  - CAGR Forecast
  - Drivers / Restraints / Trends
  - Regulatory Landscape
  - Competitive Landscape
  - Company Profiles
  - 5-year Financial Forecast Table
  - Risks & Sensitivity
  - Numbered citation list with hyperlinks
- PDF export via WeasyPrint
- Progress states: `Queued`, `Running`, `Complete`, `Failed`
- Source cap: max 20 links per report
- Mock research mode when API keys are missing

## Project Structure

```text
/insightforge
  /backend
  /frontend
  docker-compose.yml
  README.md
```

## Tech Stack
- Backend: FastAPI, SQLAlchemy, SQLite/PostgreSQL, Celery (optional in local mode), Redis, OpenAI SDK, Anthropic SDK, Requests, BeautifulSoup, WeasyPrint
- Frontend: Next.js, Tailwind CSS, Axios
- Infra: Docker Compose

## Environment Variables
Copy `.env.example` to `.env`.

Required:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `PARALLEL_API_KEY`
- `DATABASE_URL`

Also used:
- `REDIS_URL`
- `REPORTS_DIR`
- `SYNC_TASKS`
- `STRICT_NO_KEY_RESEARCH`
- `NEXT_PUBLIC_API_BASE_URL`

If `PARALLEL_API_KEY` is empty, the platform uses mock research sources.
If `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` are empty, deterministic local extraction/composition fallbacks are used.

## Local Setup (Without Docker)
Local mode defaults:
- `DATABASE_URL=sqlite:///./insightforge.db`
- `SYNC_TASKS=true` (no Celery worker needed)
- Python 3.14 compatible install path (Postgres/PDF native deps are optional in local mode)
- `STRICT_NO_KEY_RESEARCH=true` (authority-only sourcing when API keys are missing)

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

App URL: `http://localhost:3000`

## Docker Run Instructions

```bash
cp .env.example .env
docker compose up --build
```

Docker mode sets `SYNC_TASKS=false` and runs Celery worker + Redis.

Services:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## API Endpoints
- `POST /api/reports` - Create report and enqueue generation
- `GET /api/reports` - List reports
- `GET /api/reports/{id}` - Report details
- `GET /api/reports/{id}/status` - Status message
- `GET /api/reports/{id}/pdf` - Download PDF
- `POST /api/reports/{id}/regenerate-section` - Re-run generation for selected section request

## Financial Model Logic
- Formula: `Future Value = Present × (1 + CAGR)^Years`
- If market size or CAGR is missing:
  - Market base fallback is used
  - Peer average CAGR (`7.5%`) is used
  - Forecast is marked as `Estimated`

## Citation Format
- Inline citation style: `[1]`, `[2]`
- Citation section includes numbered links for each source URL.

## Test Data / Mock Mode
- Sample report markdown:
  - `backend/sample_data/sample_report.md`
- Mock research mode automatically activates when `PARALLEL_API_KEY` is not set.

## GitHub Push Instructions

```bash
cd /Users/vibhor/Documents/New\ project
git checkout -b codex/insightforge-mvp
git add insightforge
git commit -m "Build InsightForge AI MVP SaaS platform"
git remote add origin <your-repo-url>
git push -u origin codex/insightforge-mvp
```

## Deployment Notes

## Quick Public Deploy

### Render (Recommended)
1. Open this one-click Blueprint import:
   - `https://render.com/deploy?repo=https://github.com/vibhorkumar1209/Industry-Report-V1`
2. In the Render Blueprint screen, set root directory to `insightforge` if prompted.
3. Confirm services from [`render.yaml`](./render.yaml).
4. Set secrets:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `PARALLEL_API_KEY`
5. Deploy. Public URL will be the frontend Render URL (for example `https://insightforge-frontend.onrender.com`).

### Railway
1. Go to [Railway](https://railway.app/new) and choose **Deploy from GitHub Repo**.
2. Select `vibhorkumar1209/Industry-Report-V1`.
3. Create 5 services:
   - `backend` (root dir: `insightforge/backend`)
   - `worker` (root dir: `insightforge/backend`, start command: `celery -A app.celery_app.celery_app worker --loglevel=info`)
   - `frontend` (root dir: `insightforge/frontend`)
   - PostgreSQL
   - Redis
4. Set env vars for backend/worker/frontend according to `.env.example`.
5. Public URL will be the Railway frontend domain generated after deploy.

### Railway
1. Create a new project from GitHub repo.
2. Add services for `backend`, `worker`, `frontend`, `postgres`, and `redis`.
3. Set shared env vars from `.env.example`.
4. Backend start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Worker start command: `celery -A app.celery_app.celery_app worker --loglevel=info`
6. Frontend build/start: default Next.js (`npm run build`, `npm run start`).

### Render
1. Create Web Service for backend and frontend, and Background Worker for Celery.
2. Provision Render Postgres and Redis instances.
3. Link env vars (`DATABASE_URL`, `REDIS_URL`, keys).
4. Expose backend URL to frontend as `NEXT_PUBLIC_API_BASE_URL`.

### Fly.io
1. Create separate Fly apps for backend, worker, and frontend.
2. Provision managed Postgres + Redis.
3. Set secrets with `fly secrets set`.
4. Deploy each app with corresponding Docker context (`backend` / `frontend`).

### Supabase (Database)
1. Create Supabase project and Postgres database.
2. Replace `DATABASE_URL` with Supabase connection string.
3. Keep compute apps on Railway/Render/Fly and point backend to Supabase Postgres.

## Notes
- This MVP intentionally avoids user auth to stay single-user and minimal.
- Regenerate section currently re-runs the full pipeline while preserving requested section intent in status messaging.
