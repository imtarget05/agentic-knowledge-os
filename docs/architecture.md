# System Architecture & Core Pipeline

This document details the software architecture and core data processing pipelines of **Agentic Knowledge OS**.

## System Architecture Layers

The platform is designed around 4 distinct layers:
1. **API Layer (FastAPI)**: Serves endpoints for ingestion (`/api/ingest/document`, `/api/ingest/repo`), real-time agent execution (`/api/chat`), and testing/evaluations.
2. **Orchestration Layer (LangGraph)**: Directs query flow using stateful, looping graphs. Manages router, QA, codebase, planner, and critic agents.
3. **Hybrid RAG Engine (LlamaIndex + BM25)**: Integrates vector search (Qdrant) and keyword search (BM25Okapi) fused via Reciprocal Rank Fusion (RRF).
4. **Data Layer**: Ingests unstructured technical specifications (PDF, DOCX, MD, TXT) and codebase structures.

---

## Technical Pipeline Detail

### 1. Ingestion & Chunking
- When a document is ingested, it is stripped of redundant spacing and broken down into token-approximate chunks of **500 tokens** with **50 tokens overlap**.
- Every chunk is dynamically tagged with high-fidelity metadata:
  ```json
  {
    "doc_id": "doc-uuid-string",
    "source_type": "pdf",
    "file_name": "report.pdf",
    "page": 12,
    "section": "Architecture",
    "chunk_id": "doc-uuid-string-c003",
    "created_at": "2026-05-24"
  }
  ```

### 2. Embeddings & Dense Storage
- The ingestion pipeline embeds document text chunks using **HuggingFace `sentence-transformers/all-MiniLM-L6-v2`** by default (dimension: 384), with fully integrated client support for **OpenAI** and **Gemini** embeddings.
- Embeddings are written in batches to a **Qdrant** database, utilizing Cosine distance metrics.

### 3. Sparse Indexing
- Concurrently, chunks are mapped to a local tokenized corpus and processed into a **BM25Okapi** keyword index, which is serialized and stored on the local disk.

### 4. Hybrid Dense-Sparse Fusion
- When a query is initiated, the engine executes parallel dense searches (Qdrant) and sparse keyword matches (BM25).
- Scores from both search types are normalized and fused using **Reciprocal Rank Fusion (RRF)**:
  $$RRF(doc) = \sum_{m \in M} \frac{1}{60 + Rank_m(doc)}$$
- A secondary semantic cosine-similarity reranker prioritizes the top 8 fused candidate chunks.
