# PDF Indexer + Graph Visualizer

## Goal

Parse ANY pdf -> Turn into a graph network (visual too)

---

## Architecture

Tauri (UI)
    ↓
Python Backend (API)
    ↓
HelixDB (Graph + Vectors)

---

## Data Model (HelixDB)

### Nodes
- Book
- Chapter
- Section
- Chunk (stores text + embedding)

### Edges
- Book -> Chapter (CONTAINS)
- Chapter -> Section (CONTAINS)
- Section -> Chunk (CONTAINS)
- Chunk -> Chunk (SIMILAR_TO)

---

## Backend Responsibilities

### 1. Ingest PDF
- Extract text
- Detect chapters/sections
- Split into chunks (300–800 tokens)

### 2. Store Structure
- Create Book node
- Create Chapter nodes
- Create Section nodes
- Create Chunk nodes
- Connect with CONTAINS edges

### 3. Generate Embeddings
- Create embedding for each chunk
- Store on Chunk node

### 4. Create Similarity Edges (Optional)
- For each chunk:
  - Find top K similar chunks
  - Create SIMILAR_TO edges
  - Avoid duplicates

---

## Tauri App Responsibilities

- Upload PDF
- Trigger indexing
- Fetch graph
- Render graph
- Allow node click to expand neighbors

---

## Visualization Rules

- Structural edges = solid lines
- Similarity edges = dashed lines
- Larger nodes for higher hierarchy levels

---

## Implementation Order

1. Build structural graph only
2. Add embeddings
3. Add similarity edges
4. Add interactive graph exploration

---

## Constraints

- Use top-K similarity (not full pairwise)
- Keep graph sparse
- Preserve hierarchy
- Keep backend separate from UI
