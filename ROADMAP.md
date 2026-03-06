# Ivy Roadmap

---

## Week 1: Database Decision + Azure Foundation

### Tasks

- [x] Create Azure resource group
- [x] Deploy Azure Cosmos DB (Gremlin API)
- [x] Create Azure Blob Storage container (for PDFs)
- [x] Deploy Azure OpenAI Service
- [x] Connect FastAPI to Cosmos DB
- [x] Deploy frontend and backend to Azure

---

## Product Priorities

1. **Story Timeline First (MVP)**
   - Show chapter-by-chapter summaries and key events in order.
2. **Character Linkage Second**
   - Show character co-occurrence and relationship context from the timeline.
3. **Plot Hole Detection Third**
   - Run consistency checks only after timeline + character linkage are reliable.

---

## Week 2: Single-Agent Extraction Pipeline

### Tasks

- [x] Upload PDF endpoint → Blob Storage
- [ ] Pull PDF bytes from Blob Storage in backend worker/service
- [ ] Parse PDF text (pdfplumber primary, PyPDF2 fallback)
- [ ] Detect chapters and create chunking strategy
- [x] Set up Microsoft Foundry project
- [ ] Create timeline extraction prompt templates in Foundry
- [ ] Extract timeline outputs:
  - Chapter summary (3-5 bullets)
  - Key events per chapter
  - Global event ordering
- [ ] Store timeline results + job status in Cosmos DB
- [ ] Build basic timeline visualization page

---

## Week 3: Multi-Agent System (5 Agents)

### Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Uploads PDF                          │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
            ┌──────────────────────┐
            │   INGESTION AGENT    │
            │  ├─ Parse PDF        │
            │  ├─ Extract raw text │
            │  ├─ Detect chapters  │
            │  └─ Chunk content    │
            └──────────┬───────────┘
                       ↓
            ┌──────────────────────┐
            │  ENTITY AGENT        │
            │  ├─ Identify chars   │
            │  ├─ Identify locs    │
            │  ├─ Identify objects │
            │  └─ Output: Entities │
            └──────────┬───────────┘
                       ↓
            ┌──────────────────────┐
            │  TIMELINE AGENT      │
            │  ├─ Extract events   │
            │  ├─ Order events     │
            │  ├─ Detect time refs │
            │  └─ Output: Timeline │
            └──────────┬───────────┘
                       ↓
            ┌──────────────────────┐
            │ RELATIONSHIP AGENT   │
            │  ├─ Map char→char    │
            │  ├─ Map char→loc     │
            │  ├─ Map event→char   │
            │  └─ Output: Edges    │
            └──────────┬───────────┘
                       ↓
            ┌──────────────────────┐
            │  PLOT HOLE AGENT     │
            │  ├─ Check timeline   │
            │  ├─ Check char logic │
            │  ├─ Check causality  │
            │  └─ Output: Issues   │
            └──────────────────────┘
```

### Agent Communication Protocol

All agents read/write to shared state in Cosmos DB:

```python
# Shared state structure
{
  "job_id": "uuid",
  "status": "in_progress",
  "current_agent": "entity_agent",
  "data": {
    "raw_text": "...",
    "entities": [...],
    "timeline": [...],
    "relationships": [...],
    "plot_holes": [...]
  },
  "metadata": {
    "book_title": "...",
    "uploaded_at": "...",
    "completed_agents": ["ingestion", "entity"]
  }
}
```

### Tasks

- [ ] Extract characters from timeline-aware chunks with confidence scores
- [ ] Resolve aliases (same character with different names)
- [ ] Build character linkage model:
  - Character-to-character interactions
  - Character-to-event participation
  - Character chapter presence map
- [ ] Persist character linkage results in Cosmos DB
- [ ] Build character linkage visualization in frontend
- [ ] (Optional stretch) Set up Agent Framework orchestrator for ingestion/entity/timeline/relationship flow

---

## Week 4: Intelligence Layer + Azure AI Search

### Tasks

- [ ] Implement "Narrative Consistency Score" (0-100)
  - Timeline coherence (30%)
  - Character consistency (30%)
  - Causal chain validity (20%)
  - Setup/payoff resolution (20%)
- [ ] Plot hole detection rules (initially rules-first, then LLM-assisted):
  - Character appears before introduction
  - Dead character speaks
  - Timeline paradox (event A causes B, but B happens first)
  - Unresolved setup (Chekhov's gun check)
  - Character in two places at once
- [ ] **Killer Feature**: What-If Mode
  - Change any event in the graph
  - Propagate changes through relationships
  - Recalculate consistency score
  - Show new plot holes introduced
- [ ] Set up Azure AI Search
  - Index: Characters, locations, events
  - Semantic search: Natural language queries
  - Example: "Show me all scenes where the villain appears without the hero"
- [ ] Microsoft Foundry model routing:
  - GPT-4o-mini: Fast extraction tasks
  - GPT-4o: Complex reasoning and plot hole detection
  - Text-embedding-3-small: Vector search
- [ ] Create evaluation pipeline in Foundry for output quality

---

## Week 5: Polish + Demo Preparation

### Tasks

- [ ] Interactive graph visualization
  - Library: Cytoscape.js or React Flow
  - Features: Zoom, pan, node selection
  - Visual styles: Characters (circles), locations (squares), events (diamonds)
  - Edge types: Solid (relationships), dashed (timeline), red (plot holes)
- [ ] Advanced filtering:
  - Filter by character (show only their subgraph)
  - Filter by timeline range
  - Filter by location
  - Filter by relationship type
- [ ] "Plot Hole Overlay" mode:
  - Highlight inconsistent nodes in red
  - Show explanation tooltips
  - Suggest fixes
- [ ] Performance optimization:
  - Optimize Gremlin queries
  - Implement pagination for large graphs
  - Add loading states
- [ ] Demo video (2 minutes max):
  - Hook: "What if you could see your story's plot holes before your readers do?"
  - Upload PDF
  - Show agent processing
  - Reveal interactive graph
  - Demonstrate plot hole detection
  - Show What-If feature
- [ ] Documentation:
  - Architecture diagram
  - Agent interaction flow
  - Setup instructions
  - Copilot usage documentation (what it helped write)

---

### System

- Agent retry logic and error handling
- Parallel agent execution where possible
- Agent confidence scoring

### Microsoft Foundry

- A/B testing different prompts
- Custom evaluation metrics
- Foundry deployment as managed endpoint

---

## 💡 Success Metrics

By end of hackathon:

- [ ] Can upload 100-page PDF and see timeline + chapter summaries in < 2 minutes
- [ ] Character linkage view is accurate enough for demo (major characters + interactions)
- [ ] Plot hole detection finds ≥ 3 real issues in test novels
- [ ] System deployed and accessible via public URL
- [ ] All 5 agents communicate correctly via shared state
- [ ] Code is well-documented and GitHub repo is public

---

## Tech Stack Summary

| Layer            | Technology                                                 |
| ---------------- | ---------------------------------------------------------- |
| Frontend         | Next.js 16 + React 19 + Tailwind CSS                       |
| Backend          | FastAPI (Python)                                           |
| Graph DB         | Azure Cosmos DB (Gremlin API)                              |
| File Storage     | Azure Blob Storage                                         |
| AI Models        | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-small) |
| Search           | Azure AI Search                                            |
| Agent Framework  | Microsoft Agent Framework                                  |
| AI Orchestration | Microsoft Foundry                                          |
| Deployment       | Azure Container Apps OR Static Web Apps + Functions        |
| Graph Viz        | Cytoscape.js or React Flow                                 |

---

## Actual Project Structure

    ivy/
      ROADMAP.md
      README.md
      .gitignore

      backend/
        app.py                        # FastAPI app entry point + app.state startup
        main.py                       # uvicorn entrypoint
        config.py                     # Environment config + Gremlin client builder

        api/
          __init__.py                 # Registers all routers
          routes/
            __init__.py
            document.py               # POST /pdf/upload, GET /jobs/{id}, GET /jobs/{id}/chapters
            system.py                 # Health check

        agents/
          __init__.py                 # Exports all agents
          ingestion_agent.py          # ✅ Step 1: download → parse → chunk → LLM → Cosmos
          entity_agent.py             # TODO: Step 2: extract characters/locations/objects
          timeline_agent.py           # TODO: Step 3: order events + causal chains
          relationship_agent.py       # TODO: Step 4: build edges between entities
          plot_hole_agent.py          # TODO: Step 5: consistency checks

        services/
          __init__.py
          parse_service.py            # ✅ PDF byte extraction via pdfplumber (no LLM)
          ingestion_service.py        # Thin glue: boots IngestionAgent, returns job_id

        integrations/
          azure/
            blob_client.py            # ✅ BlobServiceClient lifecycle
            blob_repository.py        # ✅ upload / download / delete blob helpers
            openai_client.py          # TODO: AsyncAzureOpenAI client (Foundry endpoint)
          cosmos/
            cosmos_client.py          # ✅ CosmosClient + container helpers
            cosmos_repository.py      # ✅ CRUD for job/chapter/entity/timeline/plot_hole docs

        utils/
          clients.py                  # Pydantic models (ToDoItem — to be replaced)

        pyproject.toml
        uv.lock

      ivy-client/
        src/
          App.tsx                     # Root component (bare scaffold)
          main.tsx
          style.css

        index.html
        package.json
        vite.config.ts
        tsconfig.json

      tests/
        harry-potter-and-the-philosophers-stone-by-jk-rowling.pdf   # local test PDF

### What's built vs TODO

| File                    | Status  | Notes                                        |
| ----------------------- | ------- | -------------------------------------------- |
| `parse_service.py`      | ✅ Done | pdfplumber TOC extraction + chapter bounds   |
| `blob_repository.py`    | ✅ Done | upload / download / delete                   |
| `cosmos_repository.py`  | ✅ Done | all document types + queries                 |
| `ingestion_agent.py`    | ✅ Done | full async pipeline, parallel LLM calls      |
| `document.py` route     | ✅ Done | upload → job → background agent → poll       |
| `openai_client.py`      | 🔲 TODO | AsyncAzureOpenAI pointed at Foundry endpoint |
| `app.py` startup        | 🔲 TODO | register openai_client on app.state          |
| `entity_agent.py`       | 🔲 TODO |                                              |
| `timeline_agent.py`     | 🔲 TODO |                                              |
| `relationship_agent.py` | 🔲 TODO | writes edges to Gremlin                      |
| `plot_hole_agent.py`    | 🔲 TODO |                                              |
| frontend pages          | 🔲 TODO | upload, job status, graph viz                |

---

## Submission Checklist

- [ ] Working project deployed to Azure
- [ ] Public GitHub repository with clean code
- [ ] 2-minute demo video (YouTube/Vimeo)
- [ ] Architecture diagram (draw.io, Lucidchart, or Excalidraw)
- [ ] Project description document
- [ ] Team member information with Microsoft Learn usernames
- [ ] README with setup instructions
- [ ] No third-party trademarks/copyrights without permission

---
