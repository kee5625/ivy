
# Roadmap
---

### Complete the Agent Pipeline

- [x] **Ingestion Pipeline**: PyMuPDF extraction + `gpt-4o-mini` extraction of summaries/events/characters (Concurrency tuned, Cosmos connection leaks fixed).
- [ ] **EntityAgent**: Query Cosmos DB for all characters extracted, deduplicate them, and ask the LLM to generate `traits`, `aliases`, and `role`. Save via `upsert_entity`.
- [ ] **TimelineAgent**: Pass key events to the LLM to link them (`causes`/`caused_by`) and establish chronological order.

### Plot holes

- [ ] **PlotHoleAgent**: Feed the combined timeline and entity traits to **`gpt-4o`** (hitting the Model Router track). Ask it to find logical inconsistencies, unresolved setups, or paradoxes. Save to Cosmos DB.

### The Knowledge Graph (Gremlin)

- [ ] **Graph Seeding Script**: Write a script that reads Cosmos DB entities/events and executes Gremlin queries to create Vertices (`Character`, `Event`, `Location`) and Edges (`PARTICIPATED_IN`, `CAUSED`).

---

### UI

- [ ] **Job Polling**: Update the React frontend to stop polling when `status == "ingestion_complete"`.
- [ ] **Dashboard View**:
  - Chapter list with summaries.
  - "Plot Holes Detected" alert card.
- [ ] **Graph Visualization**: Use `react-force-graph` or similar to visually render the Gremlin nodes.
- [ ] **Chat UI**: Add the Chat UI panel so the user can interact with the MCP-connected agent.

### Security, Deployment & Video

- [ ] **Foundry Switch**: Switch `openai_client.py` back to using the `PROJECT_ENDPOINT` and `DefaultAzureCredential` to hit the Foundry track.
- [ ] **Record Demo Video (2-3 mins)**:
  - Upload PDF.
  - Show graph generating.
  - Highlight plot holes being caught.
  - Ask the chatbot a highly specific graph-based question.
- [ ] **Submit**: Ensure GitHub repo is public and README is polished.

---

## TODO

| Component                 | Status  | Notes                                                               |
| ------------------------- | ------- | ------------------------------------------------------------------- |
| **Azure OpenAI Client**   | 🔄 WIP  | Temporarily using standard OpenAI. Must switch to Foundry for demo. |
| **Entity Agent**          | 🔲 TODO | Read characters, deduplicate, extract traits.                       |
| **Timeline Agent**        | 🔲 TODO | Link events causally.                                               |
| **Plot Hole Agent**       | 🔲 TODO | The "Wow" feature. Uses `gpt-4o`.                                   |
| **Gremlin Graph Builder** | 🔲 TODO | Script to map Cosmos docs to Gremlin edges/vertices.                |
| **MCP Server / Chat**     | 🔲 TODO | Tool for LLM to query the knowledge graph.                          |
| **Frontend UI**           | 🔲 TODO | Dashboard, Graph Viz, Chat pane.                                    |

---




