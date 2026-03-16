# Ivy

Ivy is an Azure-backed story-analysis app that ingests a PDF manuscript, extracts chapter summaries and entities, merges a global timeline, and surfaces plot holes through a React frontend and a FastAPI backend.

## Architecture Summary

Ivy uses a simple two-tier architecture that works well for a hackathon demo and still reads as production-aware. The React + Vite frontend runs as a static app, the FastAPI backend runs as a single Azure Container App, uploaded PDFs are stored in Azure Blob Storage, job and analysis state live in Azure Cosmos DB, and narrative extraction plus reasoning calls go through Azure AI Foundry's OpenAI-compatible endpoints. The backend keeps the pipeline in-process so a single upload can create a job, run ingestion, merge the timeline, and write plot-hole findings without introducing a queue or worker layer.

## Repo Layout

- `backend` - FastAPI API, agents, Azure integrations, tests
- `ivy-client` - React + Vite frontend
- `docs/azure-deployment.md` - Azure deployment and production-readiness guide

## Local Setup

### Backend

1. Install Python 3.11+ and `uv`.
2. Copy [`backend/.env.example`](backend/.env.example) to `backend/.env`.
3. Fill in the required Azure values:
   - `PROJECT_KEY`
   - `OPENAI_ENDPOINT` or `PROJECT_ENDPOINT`
   - Cosmos DB settings
   - Blob Storage settings
4. Install dependencies and run the API:

```bash
cd backend
uv sync
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The backend serves routes under `/api/*`, including:
- `/api/health`
- `/api/health/live`
- `/api/health/ready`

### Frontend

1. Install Node.js 20+.
2. Install dependencies and start Vite:

```bash
cd ivy-client
npm install
npm run dev
```

The Vite dev server is already aligned with the backend `/api/*` route shape from Batch 2.

## Azure AI Foundry Setup

Deploy at least:
- `gpt-4o-mini` for ingestion, local timeline extraction, and fallbacks
- `gpt-4.1` for timeline merge if you want to keep the current defaults

The backend supports two config patterns:

1. Shared Foundry/OpenAI-compatible client:
   - `PROJECT_KEY`
   - `OPENAI_ENDPOINT=https://<resource>.cognitiveservices.azure.com/`
   - or `PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>`

2. Optional per-model override for timeline merge:
   - `TIMELINE_MERGE_ENDPOINT`
   - `TIMELINE_MERGE_KEY`
   - optionally `TIMELINE_MERGE_FALLBACK_ENDPOINT`
   - optionally `TIMELINE_MERGE_FALLBACK_KEY`

Use the deployment Target URI when you set `TIMELINE_MERGE_ENDPOINT`. For structured outputs, the API version on that URI should be `2024-08-01-preview` or later.

## Azure Deployment Steps

1. Create Azure resources:
   - Azure Container Registry
   - Azure Container Apps Environment
   - Azure Container App for `backend`
   - Azure Static Web App Standard for `ivy-client`
   - Azure Blob Storage account and container
   - Azure Cosmos DB account, database, and container
   - Azure AI Foundry project and model deployments
2. Configure backend settings in Container Apps using the values documented in [`backend/.env.example`](backend/.env.example).
3. Deploy the backend image with the repo's Container Apps workflow.
4. Deploy the frontend with the Static Web Apps workflow.
5. Link the Static Web App to the Container App so frontend `/api/...` calls are proxied to the backend.
6. Configure health probes to use:
   - liveness: `/api/health/live`
   - readiness: `/api/health/ready`

Detailed steps live in [`docs/azure-deployment.md`](docs/azure-deployment.md).

## Where Azure Is Used

- Azure AI Foundry provides the OpenAI-compatible model access for ingestion, timeline extraction, timeline merge, and plot-hole analysis.
- Azure Blob Storage stores uploaded PDFs.
- Azure Cosmos DB stores jobs, chapters, timeline events, entities, and plot-hole documents.
- Azure Container Apps hosts the FastAPI backend and background pipeline execution.
- Azure Static Web Apps hosts the frontend and proxies `/api/*` to the backend.
- Azure Container Registry stores the backend image used by Container Apps.

## Where Azure Can Be Used Next

- Azure AI Search can add semantic retrieval over chapters, entities, and timeline events so later agents reason over retrieved evidence instead of only the current prompt payload.
- Microsoft Agent Framework can formalize orchestration between ingestion, timeline, and plot-hole agents if the project graduates from the current in-process pipeline.
- Azure MCP tooling can improve developer and demo workflows for prompt inspection, environment debugging, and Azure-aware automations.
- Azure Key Vault plus Managed Identity can centralize secrets and reduce direct secret sprawl in Container Apps.
- Azure Monitor plus Log Analytics can turn the current logs into dashboards, saved queries, and alerts for demo reliability.

## Submission-Ready Summary

Ivy is a story-intelligence pipeline built on Azure. A user uploads a manuscript PDF, the FastAPI backend stores it in Blob Storage, tracks pipeline state in Cosmos DB, and uses Azure AI Foundry models to extract chapter-level structure, merge a global narrative timeline, and identify plot holes. The app is deployed as a React frontend on Static Web Apps and a Python backend on Azure Container Apps, which makes the project easy to demo while still showing a credible path to production hardening through Key Vault, managed identity, health probes, and Azure Monitor.
