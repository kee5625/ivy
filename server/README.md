# Ivy Server

FastAPI + LangGraph backend for manuscript analysis with Ingestion, Timeline, and Plot-Hole detection agents.

## Architecture

```
Client (React/Vite)
       |
       v
FastAPI + LangGraph (Single Container)
  - Upload API
  - Jobs API
  - WebSocket (progress)
  - Agent Graph Execution
       |
       v
  +-----------+   +-----------+   +-----------+
  | PostgreSQL|   | S3/MinIO  |   | Anthropic |
  | (jobs,    |   | (PDFs)    |   | Claude    |
  | chapters, |   +-----------+   +-----------+
  | timeline) |
  +-----------+
```

## Tech Stack

| Component | Choice |
|-----------|--------|
| API Framework | FastAPI |
| Agent Framework | LangGraph |
| Primary DB | PostgreSQL |
| PDF Storage | S3 / MinIO |
| Cache/Queue | Redis |
| LLM Provider | Anthropic Claude |
| Character Graph | NetworkX (in-memory) |

## Overview

Moving from Azure (Cosmos DB, Blob Storage) to a vendor-neutral stack:
- PostgreSQL for job tracking and structured data
- S3-compatible storage for PDFs
- NetworkX for character relationship mapping

## Database Schema

```sql
-- Job tracking
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL, -- pending | ingesting | timeline | plot_hole | complete | failed
    pdf_filename TEXT,
    pdf_key TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Chapter data (JSONB for flexible metadata)
CREATE TABLE chapters (
    chapter_id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id),
    chapter_num INTEGER,
    title TEXT,
    summary JSONB,
    key_events JSONB,
    characters TEXT[],
    temporal_markers TEXT[],
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_chapters_job ON chapters(job_id);

-- Timeline events
CREATE TABLE timeline_events (
    event_id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id),
    description TEXT,
    chapter_num INTEGER,
    event_order INTEGER,
    characters_present TEXT[],
    location TEXT,
    causes TEXT[],
    caused_by TEXT[],
    time_reference TEXT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_timeline_job ON timeline_events(job_id);
CREATE INDEX idx_timeline_order ON timeline_events(event_order);

-- Character interactions (for NetworkX graph export)
CREATE TABLE character_interactions (
    job_id TEXT,
    char_a TEXT,
    char_b TEXT,
    chapter_num INTEGER,
    interaction_type TEXT,
    PRIMARY KEY (job_id, char_a, char_b, chapter_num)
);

-- Plot holes
CREATE TABLE plot_holes (
    hole_id TEXT PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id),
    hole_type TEXT,
    severity TEXT,
    description TEXT,
    chapters_involved INTEGER[],
    characters_involved TEXT[],
    events_involved TEXT[],
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT now()
);
CREATE INDEX idx_plotholes_job ON plot_holes(job_id);
```

## Local Development

```bash
# Start infrastructure
docker compose up postgres redis minio -d

# Install dependencies
uv sync

# Run server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ivy_dev

# Redis
REDIS_URL=redis://localhost:6379

# S3-compatible storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=ivy-pdfs

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# LangGraph
LANGGRAPH_CHECKPOINT_POSTGRES_URI=${DATABASE_URL}
```
