# Ivy

AI-powered manuscript analysis tool. Upload a PDF, get structured chapter data, a global story timeline, and a list of detected plot holes.

---

## What it does

Ivy runs a three-stage agent pipeline on your manuscript:

1. **Ingestion** — parses the PDF chapter by chapter, extracts summaries, key events, characters, and temporal markers
2. **Timeline** — merges chapter-local events into a single globally ordered story chronology with causality links
3. **Plot Hole Detection** — cross-references the finished story state and flags high-confidence contradictions (timeline paradoxes, location conflicts, dead-character reappearances, unresolved setups)

Results are available through a web UI showing chapter cards, a visual timeline rail, and a list of findings with severity and confidence scores.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11+, LangGraph (functional API) |
| LLM | OpenAI (`gpt-4o-mini` by default, configurable) |
| Database | PostgreSQL via [Neon](https://neon.tech) |
| Job state | Redis via [Upstash](https://upstash.com) |
| File storage | S3-compatible via [Cloudflare R2](https://developers.cloudflare.com/r2/) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for Python dependency management
- Node.js 20+
- A Neon PostgreSQL database
- An Upstash Redis instance
- A Cloudflare R2 bucket
- An OpenAI API key

---

## Local setup

### 1. Environment

Copy the example env file and fill in values:

```bash
cp server/.env.example .env
```

Required variables:

```env
# PostgreSQL (Neon)
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require

# Redis (Upstash)
REDIS_URL=rediss://default:token@host.upstash.io:6379

# Cloudflare R2
S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET=ivy-pdfs
S3_REGION=auto

# OpenAI
OPENAI_API_KEY=sk-...
```

### 2. Database

Run the schema against your Neon database:

```bash
psql $DATABASE_URL -f server/schema.sql
```

### 3. Backend

```bash
cd server
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend

```bash
cd client
npm install
npm run dev
```

Vite proxies `/api/*` to `http://localhost:8000` — no additional config needed.

Open `http://localhost:5173`.

---

## How the pipeline works

```
Upload PDF → POST /api/upload/presign → PUT to R2
                ↓
           POST /api/jobs
                ↓
     ┌──────────────────────┐
     │   Ingestion Agent    │  parallel LLM calls per chapter
     └──────────┬───────────┘
                ↓
     ┌──────────────────────┐
     │   Timeline Agent     │  local extraction → batch merge → global order
     └──────────┬───────────┘
                ↓
     ┌──────────────────────┐
     │  Plot Hole Agent     │  single LLM call over full story state
     └──────────┬───────────┘
                ↓
           Results UI
```

Job status is written to both PostgreSQL (durable) and Redis (live polling). The frontend polls `GET /api/jobs/:id` every 3 seconds until a terminal state is reached.

---

## API reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload/presign` | Generate a presigned R2 PUT URL |
| `POST` | `/api/jobs` | Create a job and start the pipeline |
| `GET` | `/api/jobs/:id` | Get current job status |
| `GET` | `/api/jobs/:id/chapters` | Get extracted chapter data |
| `GET` | `/api/jobs/:id/timeline` | Get ordered timeline events |
| `GET` | `/api/jobs/:id/plot-holes` | Get detected plot holes |

---

## Configuration

Model and pipeline behavior can be tuned via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required. OpenAI API key |
| `DATABASE_URL` | — | Required. PostgreSQL connection string |
| `REDIS_URL` | — | Required. Redis connection string |
| `S3_ENDPOINT` | — | Required. R2/S3 endpoint URL |
| `S3_ACCESS_KEY` | — | Required. R2/S3 access key |
| `S3_SECRET_KEY` | — | Required. R2/S3 secret key |
| `S3_BUCKET` | `ivy-pdfs` | Bucket name |
| `S3_REGION` | `auto` | Bucket region |

To swap models, edit `MODEL` in `server/utils/client.py`.

---

## Project structure

```
ivy/
├── server/                 # FastAPI backend
│   ├── agents/             # LangGraph pipeline agents
│   │   ├── ingestion_agent.py
│   │   ├── timeline_agent.py
│   │   └── plot_hole_agent.py
│   ├── api/routes/         # REST endpoints
│   ├── db/                 # DB pool, Redis, repositories
│   ├── services/           # PDF parsing
│   ├── utils/              # LLM client, storage, job state
│   ├── schema.sql          # Full database schema
│   └── main.py
└── client/                 # React frontend
    └── src/
        ├── api/            # Fetch wrappers
        ├── components/     # UI components
        ├── hooks/          # useJobPolling, useJobResults
        └── pages/          # Home, graph status, results
```

---

## License

MIT
