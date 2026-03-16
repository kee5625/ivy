# Azure Deployment Guide

This project is set up for:

- Frontend: Azure Static Web Apps Standard
- Backend: Azure Container Apps
- AI: Azure AI Foundry OpenAI-compatible endpoint
- Data: Azure Blob Storage + Azure Cosmos DB

## 1. Deploy the models in Azure AI Foundry

You should deploy at least:

- `gpt-4o-mini` for ingestion and fallback flows
- `gpt-4.1` for the timeline merge step if you want the current default config to work as-is

If you do not want to deploy `gpt-4.1`, set `TIMELINE_MERGE_MODEL` to the name of another deployed model, such as the same `gpt-4o-mini` deployment.

### Recommended deployment names

To avoid extra config churn, use these deployment names:

- `gpt-4o-mini`
- `gpt-4.1`

If you choose different deployment names, update:

- `OPENAI_MODEL`
- `TIMELINE_LOCAL_MODEL`
- `TIMELINE_MERGE_MODEL`
- `TIMELINE_MERGE_FALLBACK_MODEL`
- `PLOT_HOLE_MODEL`
- `PLOT_HOLE_FALLBACK_MODEL`

### Portal steps for `gpt-4.1`

1. Open your Azure AI Foundry project.
2. Go to the model catalog or deployments area.
3. Search for `gpt-4.1`.
4. Select the model and choose deploy.
5. Pick a deployment type your subscription supports. For hackathon use, Global Standard is usually the simplest option when available.
6. Set the deployment name to `gpt-4.1` if you want to keep the current backend env defaults.
7. Repeat the process for `gpt-4o-mini` if it is not already deployed.
8. Test both deployments in the Foundry playground before wiring them into the app.

## 2. Create the Azure resources

Create or confirm these resources:

- Azure Container Registry
- Azure Container Apps Environment
- Azure Container App for the backend
- Azure Static Web App on the Standard plan
- Azure Blob Storage account and container
- Azure Cosmos DB account and database/container

## 3. Backend environment variables for Azure Container Apps

Set these app settings on the Container App:

- `PORT=8000`
- `PROJECT_KEY`
- `PROJECT_ENDPOINT`
- `OPENAI_ENDPOINT`
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
- `COSMOS_KEY`
- `COSMOS_DATABASE`
- `COSMOS_CONTAINER`
- `GREMLIN_ENDPOINT`
- `GREMLIN_KEY`
- `GREMLIN_DATABASE`
- `GREMLIN_GRAPH`
- `AZURE_BLOB_CONTAINER`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_ACCOUNT_URL`
- `FRONTEND_ORIGIN`

Set `FRONTEND_ORIGIN` to your Static Web App URL while you are using direct browser-to-backend access. Once your Static Web App is linked to the Container App and all frontend traffic goes through `/api`, CORS becomes less important for production traffic.

## 4. Create the backend Container App

Recommended settings:

- Ingress: enabled
- Ingress type: external
- Target port: `8000`
- Min replicas: `1`
- Max replicas: `1`

Use one replica for now because the app currently runs the ingestion pipeline as an in-process background task after upload.

## 5. Link the Static Web App to the Container App

This repo is configured so the backend serves routes under `/api/*`, which matches Azure Static Web Apps linked backend requirements.

Portal steps:

1. Open the Static Web App.
2. Go to `APIs`.
3. Choose `Link`.
4. Select backend resource type `Container App`.
5. Pick your backend Container App.
6. Complete the link.

After linking, requests from the frontend to `/api/...` are proxied to the Container App.

## 6. GitHub Actions setup

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

## 7. Runtime notes

- The backend Docker image is built from `backend/Dockerfile`.
- The frontend includes `staticwebapp.config.json` for SPA navigation fallback.
- Azure Static Web Apps linked backends require the API prefix to remain `/api`.
- Azure Static Web Apps bring-your-own API support requires the Standard plan.

## 8. Suggested production hardening after first deploy

- Move app secrets into Azure Key Vault.
- Use Azure Monitor and Log Analytics for backend logs.
- Add readiness checks for Blob/Cosmos/Foundry.
- Later, move the ingestion pipeline into a queue + worker model before scaling above one backend replica.
