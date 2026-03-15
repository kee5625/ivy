# Ivy

Ivy is a platform for building, running, and visualizing data processing pipelines.  
It features:
- A Python FastAPI backend that manages pipeline jobs, integrates with Azure services, and provides a REST API for job submission, status tracking, and results retrieval.
- A modern React + Vite frontend for users to submit jobs, monitor progress, and explore results through interactive graphs and visualizations.
- Support for authentication, cloud-based storage, and scalable job orchestration.
- Designed for extensibility, allowing integration with additional data sources and processing modules.

## Folders

- `backend` - FastAPI backend
- `ivy-client` - React + Vite frontend

## Run

### Backend

- `cd backend`
- `uv run main.py`

### Frontend

- `cd ivy-client`
- `npm install`
- `npm run dev`
