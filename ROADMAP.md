# Ivy Roadmap

---

## Week 1: Database Decision + Azure Foundation

### Tasks
- [X] Create Azure resource group
- [X] Deploy Azure Cosmos DB (Gremlin API)
- [X] Create Azure Blob Storage container (for PDFs)
- [X] Deploy Azure OpenAI Service
- [X] Connect FastAPI to Cosmos DB
- [X] Deploy frontend and backend to Azure

### Deployment Options

#### Option A: Azure Container Apps (Recommended for Production Feel)
**Best for**: Full control, microservices architecture, better for Grand Prize

| Component | Service | Why |
|-----------|---------|-----|
| Frontend | Azure Container Apps | Docker container with Next.js |
| Backend | Azure Container Apps | Docker container with FastAPI |
| Database | Cosmos DB Gremlin | Managed graph database |
| Storage | Blob Storage | PDF uploads |
| AI | Azure OpenAI | GPT-4o + embeddings |

**Pros**: Shows production architecture, scaling, environment variables  
**Cons**: More complex setup, Docker knowledge required

#### Option B: Azure Static Web Apps + Functions (Faster Setup)
**Best for**: Quick deployment, serverless, lower complexity

| Component | Service | Why |
|-----------|---------|-----|
| Frontend | Static Web Apps | Next.js export, automatic HTTPS |
| Backend | Azure Functions | Serverless FastAPI with Functions integration |
| Database | Cosmos DB Gremlin | Same as Option A |
| Storage | Blob Storage | Same as Option A |
| AI | Azure OpenAI | Same as Option A |

**Pros**: Simpler deployment, free tier, faster cold starts  
**Cons**: Less "production" feel, Functions have timeouts

**Verdict**: Start with Option B for Week 1-2, migrate to Option A in Week 5 if time permits

---

## Product Priorities (Updated)

1. **Story Timeline First (MVP)**
   - Show chapter-by-chapter summaries and key events in order.
2. **Character Linkage Second**
   - Show character co-occurrence and relationship context from the timeline.
3. **Plot Hole Detection Third**
   - Run consistency checks only after timeline + character linkage are reliable.

---

## Week 2: Single-Agent Extraction Pipeline

### Goal
PDF (Blob) -> Parse + Chunk -> Timeline output using Microsoft Foundry/OpenAI

### Tasks
- [X] Upload PDF endpoint → Blob Storage
- [ ] Pull PDF bytes from Blob Storage in backend worker/service
- [ ] Parse PDF text (pdfplumber primary, PyPDF2 fallback)
- [ ] Detect chapters and create chunking strategy
- [X] Set up Microsoft Foundry project
- [ ] Create timeline extraction prompt templates in Foundry
- [ ] Extract timeline outputs:
  - Chapter summary (3-5 bullets)
  - Key events per chapter
  - Global event ordering
- [ ] Store timeline results + job status in Cosmos DB
- [ ] Build basic timeline visualization page

### Foundry Workflow Design
```
PDF Upload
  ↓
[Foundry Pipeline]
  ├─ Step 1: Text Extraction
  ├─ Step 2: Chapter Detection + Chunking
  ├─ Step 3: Timeline Extraction (GPT-4o/GPT-4o-mini)
  └─ Step 4: Persist Timeline + Job State
  ↓
Cosmos DB
```

### Tools & One-Liners

| Tool | One-Line Explanation |
|------|---------------------|
| Microsoft Foundry | Mission control for managing AI workflows and prompts |
| Azure OpenAI | Extracts structured story data from unstructured text |

---

## Week 3: Multi-Agent System (5 Agents)

### Goal
Character linkage layer + optional multi-agent orchestration with Microsoft Agent Framework

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

### Tools & One-Liners

| Tool | One-Line Explanation |
|------|---------------------|
| Microsoft Agent Framework | A team of 5 AI specialists passing notes through a shared database |

---

## Week 4: Intelligence Layer + Azure AI Search

### Goal
Plot hole detection + advanced reasoning on top of timeline and character linkage

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

### Tools & One-Liners

| Tool | One-Line Explanation |
|------|---------------------|
| Azure AI Search | Google for your story that understands "find betrayal scenes" |
| Microsoft Foundry (Routing) | Smart traffic controller sending easy tasks to cheap AI, hard tasks to smart AI |

---

## Week 5: Polish + Demo Preparation

### Goal
Production quality, stunning demo, winning submission

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

### Tools & One-Liners

| Tool | One-Line Explanation |
|------|---------------------|
| GitHub Copilot Agent Mode | Senior developer pair-programming with you, writing boilerplate and suggesting fixes |

---

## 🏆 Category Winning Strategy

### Best Azure Integration
**Must-haves:**
- ✅ Cosmos DB Gremlin (native Azure graph database)
- ✅ Blob Storage (PDF storage)
- ✅ Azure OpenAI (AI services)
- ✅ Azure AI Search (semantic search)
- ✅ Either Container Apps or Static Web Apps + Functions
- ✅ Architecture diagram showing all services

**Bonus points:**
- Azure Key Vault for secrets
- Azure Application Insights for monitoring
- Azure CDN for frontend assets

### Best Multi-Agent System
**Must-haves:**
- ✅ 5 distinct agents with clear responsibilities
- ✅ Agent Framework orchestration
- ✅ Real agent-to-agent communication (not just sequential calls)
- ✅ Shared state/memory (Cosmos DB)
- ✅ Agent status tracking and visualization

**Bonus points:**
- Agent retry logic and error handling
- Parallel agent execution where possible
- Agent confidence scoring

### Best Use of Microsoft Foundry
**Must-haves:**
- ✅ Prompt management and versioning
- ✅ Model routing (cheap vs. expensive models)
- ✅ Evaluation pipeline for output quality
- ✅ Structured extraction workflows

**Bonus points:**
- A/B testing different prompts
- Custom evaluation metrics
- Foundry deployment as managed endpoint

### Grand Prize
**Must demonstrate:**
- ✅ Solves real problem (authors fixing plot holes)
- ✅ Production-ready deployment
- ✅ Novel AI application (narrative analysis)
- ✅ Clean, maintainable architecture
- ✅ Impressive demo with wow factor

---

## 📋 Weekly Checklist Template

Copy this for each week:

```markdown
### Week X Goals
- [ ] Goal 1
- [ ] Goal 2

### Daily Breakdown
**Day 1-2:** Task A  
**Day 3-4:** Task B  
**Day 5-6:** Task C  
**Day 7:** Buffer/testing

### Risks
- Risk 1 and mitigation
- Risk 2 and mitigation

### Deliverables
- [ ] Working feature X
- [ ] Documentation update
- [ ] Deployment verified
```

---

## 🚨 Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Cosmos DB Gremlin too complex | Medium | Start with simple node/edge queries, expand gradually; have Neo4j backup plan |
| 5 agents too much for 5 weeks | Medium | Agents share 80% of code (only prompts differ); build base agent class first |
| Plot hole detection doesn't work well | Low | Have fallback: manual plot hole tagging with AI suggestions |
| Azure deployment issues | Medium | Test deployment in Week 1, not Week 5; use Azure CLI for reproducibility |
| Demo video too long | Low | Script it, practice 3 times, trim ruthlessly |

---

## 💡 Success Metrics

By end of hackathon:
- [ ] Can upload 100-page PDF and see timeline + chapter summaries in < 2 minutes
- [ ] Character linkage view is accurate enough for demo (major characters + interactions)
- [ ] Plot hole detection finds ≥ 3 real issues in test novels
- [ ] What-If mode propagates changes correctly
- [ ] System deployed and accessible via public URL
- [ ] All 5 agents communicate correctly via shared state
- [ ] Demo video under 2 minutes, shows full workflow
- [ ] Code is well-documented and GitHub repo is public

---

## 🛠 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 + React 19 + Tailwind CSS |
| Backend | FastAPI (Python) |
| Graph DB | Azure Cosmos DB (Gremlin API) |
| File Storage | Azure Blob Storage |
| AI Models | Azure OpenAI (GPT-4o, GPT-4o-mini, text-embedding-3-small) |
| Search | Azure AI Search |
| Agent Framework | Microsoft Agent Framework |
| AI Orchestration | Microsoft Foundry |
| Deployment | Azure Container Apps OR Static Web Apps + Functions |
| Graph Viz | Cytoscape.js or React Flow |

---

## 📂 Suggested Project Structure

    ivy/
      ROADMAP.md
      docker-compose.yml
      .github/workflows/

      backend/
        app/
          __init__.py
          main.py                     # FastAPI app entry point
          config.py                   # Environment config (pydantic-settings)
          dependencies.py             # Shared DI (clients from app.state)

          api/
            __init__.py
            routes/
              __init__.py
              health.py
              documents.py            # Upload + job creation
              jobs.py                 # Job status/progress/results
              graph.py                # Graph query endpoints
              search.py               # AI Search query endpoints
            schemas/
              __init__.py
              documents.py
              jobs.py
              graph.py
              search.py

          services/
            __init__.py
            ingestion_service.py      # Upload -> Blob -> parse trigger
            parse_service.py          # PDF extraction/chunking
            extraction_service.py     # Foundry/OpenAI extraction
            graph_service.py          # Cosmos graph writes/reads
            scoring_service.py        # Consistency score, plot holes
            whatif_service.py         # What-if propagation logic

          agents/
            __init__.py
            orchestrator.py
            base_agent.py
            ingestion_agent.py
            entity_agent.py
            timeline_agent.py
            relationship_agent.py
            plot_hole_agent.py

          integrations/
            __init__.py
            azure/
              __init__.py
              blob_client.py          # BlobServiceClient lifecycle
              blob_repository.py      # Upload/download helpers
              openai_client.py
              ai_search_client.py
            cosmos/
              __init__.py
              gremlin_client.py
              graph_repository.py

          domain/
            __init__.py
            models/
              __init__.py
              document.py
              entity.py
              event.py
              relationship.py
              job.py

          utils/
            __init__.py
            logging.py

          tests/
            __init__.py
            unit/
            integration/

        pyproject.toml
        .env.example

      ivy-client/
        src/
          app/
            pages/
              UploadPage.tsx
              JobStatusPage.tsx
              GraphPage.tsx
            components/
              upload/
              graph/
              jobs/
            api/
              documents.ts
              jobs.ts
              graph.ts
              search.ts
            hooks/
              useUpload.ts
              useJobPolling.ts
            types/
              api.ts
              graph.ts
          main.tsx
          style.css

        package.json
        vite.config.ts

---

## 📝 Submission Checklist

- [ ] Working project deployed to Azure
- [ ] Public GitHub repository with clean code
- [ ] 2-minute demo video (YouTube/Vimeo)
- [ ] Architecture diagram (draw.io, Lucidchart, or Excalidraw)
- [ ] Project description document
- [ ] Team member information with Microsoft Learn usernames
- [ ] README with setup instructions
- [ ] No third-party trademarks/copyrights without permission

---

**Start Date**: [Fill in]  
**Submission Deadline**: [Fill in]  
**Current Week**: [Update as you progress]
