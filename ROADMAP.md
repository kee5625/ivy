# StoryGraph AI - Hackathon Roadmap

**Current Stack**: FastAPI + Next.js + Tailwind  
**Goal**: Multi-agent narrative analysis with graph visualization  
**Target Categories**: Best Azure Integration | Best Multi-Agent System | Best Use of Microsoft Foundry | Grand Prize

---

## Week 1: Database Decision + Azure Foundation

### Goal
Choose graph database, set up Azure infrastructure, deploy initial stack

### Database Decision Matrix

| Option | Pros | Cons | Azure Points |
|--------|------|------|--------------|
| **Cosmos DB Gremlin** | Native Azure, managed service, scales infinitely | Gremlin query learning curve, more verbose | ⭐⭐⭐⭐⭐ |
| **Neo4j Aura** | Best graph UX, Cypher is intuitive, great docs | Third-party service, fewer Azure points | ⭐⭐ |
| **Azure PostgreSQL + AGE** | SQL familiarity, open source | Still in preview, less mature | ⭐⭐⭐ |

**Recommendation**: Cosmos DB Gremlin (maximize Azure Integration score)

### Tasks
- [ ] Create Azure resource group
- [ ] Deploy Azure Cosmos DB (Gremlin API)
- [ ] Create Azure Blob Storage container (for PDFs)
- [ ] Deploy Azure OpenAI Service
- [ ] Connect FastAPI to Cosmos DB
- [ ] Deploy frontend and backend to Azure

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

### Tools & One-Liners

| Tool | One-Line Explanation |
|------|---------------------|
| Azure Cosmos DB (Gremlin) | Cloud graph database storing characters as nodes and relationships as edges |
| Azure Blob Storage | Dropbox for uploaded PDFs |
| Azure OpenAI | The AI brain that reads and understands stories |
| Azure Container Apps | Docker hosting without server management |
| Azure Static Web Apps | Free hosting for Next.js with automatic deployments |
| Azure Functions | Run code without managing servers (pay per execution) |

---

## Week 2: Single-Agent Extraction Pipeline

### Goal
PDF → Structured Data → Graph using Microsoft Foundry

### Tasks
- [ ] Upload PDF endpoint → Blob Storage
- [ ] Parse PDF text (PyPDF2 or pdfplumber)
- [ ] Set up Microsoft Foundry project
- [ ] Create extraction prompt templates in Foundry
- [ ] Extract core entities:
  - Characters (name, description, first appearance)
  - Locations (name, description)
  - Events (description, timestamp, participants)
- [ ] Store in Cosmos DB as graph structure
- [ ] Build basic graph visualization page

### Foundry Workflow Design
```
PDF Upload
  ↓
[Foundry Pipeline]
  ├─ Step 1: Text Extraction
  ├─ Step 2: Entity Recognition (GPT-4o)
  ├─ Step 3: Relationship Mapping
  └─ Step 4: Graph Storage
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
Build true multi-agent orchestration using Microsoft Agent Framework

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
- [ ] Set up Microsoft Agent Framework
- [ ] Implement agent orchestrator (manages agent flow)
- [ ] **Ingestion Agent**: PDF parsing, chapter detection, chunking strategy
- [ ] **Entity Agent**: Character/location/object extraction with confidence scores
- [ ] **Timeline Agent**: Event extraction, temporal ordering, time reference resolution
- [ ] **Relationship Agent**: Build graph edges (who knows who, who was where)
- [ ] **Plot Hole Agent**: Cross-reference all data, detect inconsistencies
- [ ] Implement agent-to-agent messaging via Cosmos DB state
- [ ] Build agent status dashboard in frontend

### Tools & One-Liners

| Tool | One-Line Explanation |
|------|---------------------|
| Microsoft Agent Framework | A team of 5 AI specialists passing notes through a shared database |

---

## Week 4: Intelligence Layer + Azure AI Search

### Goal
Advanced reasoning, semantic search, and model optimization

### Tasks
- [ ] Implement "Narrative Consistency Score" (0-100)
  - Timeline coherence (30%)
  - Character consistency (30%)
  - Causal chain validity (20%)
  - Setup/payoff resolution (20%)
- [ ] Plot hole detection rules:
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
- [ ] Can upload 100-page PDF and see full graph in < 2 minutes
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
