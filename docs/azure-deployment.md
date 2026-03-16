# Azure Deployment Guide

This repo is deployed as:

- Frontend: Azure Static Web Apps Standard
- Backend: Azure Container Apps
- AI: Azure AI Foundry OpenAI-compatible endpoints
- Storage: Azure Blob Storage
- Operational data: Azure Cosmos DB

## 1. Provision the Azure resources

Create or confirm:

- Azure AI Foundry project
- Azure Container Registry
- Azure Container Apps Environment
- Azure Container App for the backend
- Azure Static Web App on the Standard plan
- Azure Blob Storage account and container
- Azure Cosmos DB account, database, and container
- Optional: Azure Key Vault
- Optional but recommended: Log Analytics workspace / Azure Monitor integration

## 2. Deploy the Azure AI Foundry models

You should deploy at least:

- `gpt-4o-mini` for ingestion, timeline-local extraction, and fallback flows
- `gpt-4.1` for timeline merge if you want to keep the current default merge model

If you do not want to deploy `gpt-4.1`, point `TIMELINE_MERGE_MODEL` at a deployment you do have, such as `gpt-4o-mini`.

### Recommended deployment names

- `gpt-4o-mini`
- `gpt-4.1`

If you choose different deployment names, update:

- `OPENAI_MODEL`
- `TIMELINE_LOCAL_MODEL`
- `TIMELINE_MERGE_MODEL`
- `TIMELINE_MERGE_FALLBACK_MODEL`
- `PLOT_HOLE_MODEL`
- `PLOT_HOLE_FALLBACK_MODEL`

## 3. Understand the backend config shape

The backend supports two Azure AI config patterns.

### Shared client config

Use this for the normal OpenAI-compatible path:

- `PROJECT_KEY`
- `OPENAI_ENDPOINT=https://<resource>.cognitiveservices.azure.com/`

or:

- `PROJECT_KEY`
- `PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>`

### Optional per-model timeline merge override

Use this when the timeline merge step needs a different deployment Target URI or key:

- `TIMELINE_MERGE_ENDPOINT`
- `TIMELINE_MERGE_KEY`
- `TIMELINE_MERGE_FALLBACK_ENDPOINT`
- `TIMELINE_MERGE_FALLBACK_KEY`

The merge override expects the deployment Target URI shape:

```text
https://<resource>.cognitiveservices.azure.com/openai/deployments/<deployment>/chat/completions?api-version=2024-08-01-preview
```

Use `2024-08-01-preview` or later on this override URI because the timeline merge agent uses structured outputs.

## 4. Backend environment variables for Azure Container Apps

Set these values on the Container App.

### Required

- `PORT=8000`
- `PROJECT_KEY`
- `OPENAI_ENDPOINT` or `PROJECT_ENDPOINT`
- `OPENAI_MODEL`
- `OPENAI_TIMEOUT_SECONDS`
- `TIMELINE_LOCAL_MODEL`
- `TIMELINE_MERGE_MODEL`
- `TIMELINE_MERGE_FALLBACK_MODEL`
- `TIMELINE_CHAPTER_CONCURRENCY`
- `TIMELINE_LOCAL_TIMEOUT_SECONDS`
- `TIMELINE_MERGE_TIMEOUT_SECONDS`
- `TIMELINE_MERGE_BATCH_EVENT_LIMIT`
- `TIMELINE_MAX_EVENTS_PER_CHAPTER`
- `PLOT_HOLE_MODEL`
- `PLOT_HOLE_FALLBACK_MODEL`
- `PLOT_HOLE_TIMEOUT_SECONDS`
- `PLOT_HOLE_MAX_RETRIES`
- `PLOT_HOLE_RETRY_BASE_DELAY_SECONDS`
- `PLOT_HOLE_MAX_FINDINGS`
- `PLOT_HOLE_CONFIDENCE_THRESHOLD`
- `COSMOS_ACCOUNT_URL`
- `COSMOS_DATABASE`
- `COSMOS_CONTAINER`
- `AZURE_BLOB_CONTAINER`
- `FRONTEND_ORIGIN`

### Required unless you use managed identity or another Azure identity path already supported by the SDK

- `COSMOS_KEY`
- `AZURE_STORAGE_CONNECTION_STRING` or `AZURE_STORAGE_ACCOUNT_URL`

### Optional

- `TIMELINE_MERGE_ENDPOINT`
- `TIMELINE_MERGE_KEY`
- `TIMELINE_MERGE_FALLBACK_ENDPOINT`
- `TIMELINE_MERGE_FALLBACK_KEY`
- `GREMLIN_ENDPOINT`
- `GREMLIN_KEY`
- `GREMLIN_DATABASE`
- `GREMLIN_GRAPH`

`FRONTEND_ORIGIN` should match your Static Web App URL if you want direct browser-to-backend access outside the linked `/api` proxy.

## 5. Create the backend Container App

Recommended starting settings:

- Ingress: enabled
- Ingress type: external
- Target port: `8000`
- Min replicas: `1`
- Max replicas: `1`

Keep one replica for now. The current architecture intentionally runs the manuscript pipeline as an in-process background task after upload, so horizontal scaling would introduce duplicate-work risk.

## 6. Configure health checks for Azure Container Apps

Batch 4 adds better app-level probe endpoints:

- Liveness: `/api/health` or `/api/health/live`
- Readiness: `/api/health/ready`

Readiness now reports the state of:

- Azure AI Foundry/OpenAI client
- Azure Blob Storage
- Azure Cosmos DB
- Gremlin, as an optional dependency

Recommended probe mapping for Container Apps:

- startup probe: `/api/health`
- liveness probe: `/api/health/live`
- readiness probe: `/api/health/ready`

This is especially helpful on Container Apps because the platform can add default probes when HTTP ingress is enabled, but explicit probe paths make failures easier to reason about and document. See Microsoft Learn for Container Apps health probes and troubleshooting: [Health probes](https://learn.microsoft.com/en-ca/azure/container-apps/health-probes), [Troubleshooting](https://learn.microsoft.com/en-us/azure/container-apps/troubleshooting).

## 7. Link the Static Web App to the Container App

This repo already uses `/api/*`, which is the right route shape for a linked Static Web App backend.

Portal steps:

1. Open the Static Web App.
2. Go to `APIs`.
3. Choose `Link`.
4. Select backend resource type `Container App`.
5. Pick your backend Container App.
6. Complete the link.

After linking, frontend requests to `/api/...` are proxied to the Container App.

## 8. GitHub Actions setup

### Required GitHub secrets

- `AZURE_CREDENTIALS`
- `AZURE_STATIC_WEB_APPS_API_TOKEN`

### Required GitHub repository variables

- `AZURE_RESOURCE_GROUP`
- `AZURE_CONTAINER_REGISTRY_NAME`
- `AZURE_CONTAINER_APP_NAME`

### Workflow files

- `.github/workflows/deploy-backend-aca.yml`
- `.github/workflows/deploy-frontend-swa.yml`

## 9. Key Vault + managed identity guidance

For a stronger production story, use Azure Key Vault and managed identity instead of storing raw secrets directly in Container Apps.

### Recommended approach

1. Enable a system-assigned or user-assigned managed identity on the Container App.
2. Grant that identity the `Key Vault Secrets User` role on the vault.
3. Store sensitive values like:
   - `PROJECT_KEY`
   - `TIMELINE_MERGE_KEY`
   - `TIMELINE_MERGE_FALLBACK_KEY`
   - `COSMOS_KEY`
   - `AZURE_STORAGE_CONNECTION_STRING`
4. Reference those secrets from the Container App rather than pasting values into app settings.

Container Apps supports Key Vault-backed secret references for app secrets. Microsoft Learn documents the `keyvaultref:` pattern and the managed identity requirement here: [Manage secrets in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets).

### What the current app already supports

- Cosmos DB can already fall back to `DefaultAzureCredential()` when `COSMOS_KEY` is omitted.
- Blob Storage can already use `DefaultAzureCredential()` when `AZURE_STORAGE_ACCOUNT_URL` is set instead of a connection string.
- The shared Azure AI Foundry/OpenAI client is still key-based today, so the practical production move is to keep `PROJECT_KEY` in Key Vault and inject it via Container Apps secrets.

## 10. Azure Monitor / Log Analytics guidance

Azure Container Apps integrates with Log Analytics through Azure Monitor, which is the fastest way to make the hackathon deployment feel production-aware.

Recommended setup:

1. Attach the Container Apps environment to a Log Analytics workspace.
2. Keep application logs going to stdout/stderr so they land in Container Apps console logs.
3. Save a few Kusto queries for demo operations:
   - console logs by app / revision
   - system logs for crashes or probe failures
   - error lines from `agents.timeline_agent`, `agents.ingestion_agent`, and `agents.plot_hole_agent`
4. Add alerts for:
   - repeated readiness failures
   - exception spikes
   - frequent revision restarts

Useful references:

- [Monitor logs in Azure Container Apps with Log Analytics](https://learn.microsoft.com/en-us/azure/container-apps/log-monitoring)
- [Log storage and monitoring options in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/log-options)
- [View log streams in Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/log-streaming)

## 11. Runtime notes

- The backend Docker image is built from `backend/Dockerfile`.
- The frontend includes `staticwebapp.config.json` for SPA fallback behavior.
- Azure Static Web Apps linked backends require the API prefix to remain `/api`.
- Azure Static Web Apps bring-your-own API support requires the Standard plan.

## 12. Azure expansion ideas for the submission

- Azure AI Search for semantic retrieval over chapters, entities, and timeline events
- Microsoft Agent Framework for more formal multi-agent orchestration
- Azure MCP tooling for developer and demo workflows
- Key Vault + Managed Identity + Azure Monitor as production credibility boosters

## 13. Reusable architecture summary

Ivy is a manuscript-analysis application deployed on Azure. The frontend runs on Azure Static Web Apps, the FastAPI backend runs on Azure Container Apps, uploaded PDFs are stored in Azure Blob Storage, and job plus analysis state are stored in Azure Cosmos DB. Azure AI Foundry powers chapter extraction, timeline merging, and plot-hole analysis through OpenAI-compatible model endpoints. The system keeps a deliberately simple single-container background-task architecture for demo velocity, while still showing a clear production path through explicit health probes, Key Vault-backed secrets, managed identity, and Azure Monitor observability.
