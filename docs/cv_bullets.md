# CV Bullets: LLM & AI Engineer Roles

These high-impact, results-driven CV bullets are tailored for AI/LLM Engineer, Agent Developer, and AI Platform Engineer roles.

---

## Technical CV Bullets (Action Verb + Tech Detail + Impact)

1. **Designed and built Agentic Knowledge OS**, a production-grade multi-agent RAG platform utilizing **LangGraph**, **LlamaIndex**, **Qdrant**, and **FastAPI** for cited technical document QA, automated codebase walkthroughs, and task planning.
2. **Architected a stateful LangGraph multi-agent network** mapping Router, Query Decomposer, Hybrid Retriever, Evidence Grader, Answer Generator, and Critic nodes, boosting **Retrieval@5 Recall from 62% to 84%** and suppressing **hallucinations from 22% to 8%** on a 30-question golden dataset benchmark.
3. **Developed a custom Model Context Protocol (MCP) server** exposing 8 reusable tools (e.g., `search_documents`, `search_codebase`, `create_task`) and 5 standard resources, enabling LLM clients to safely parse files, write tasks, and execute RAG evaluations.
4. **Built a hybrid search retrieval engine** combining Qdrant dense vector search and BM25 sparse keyword search fused via **Reciprocal Rank Fusion (RRF)**, backed by a secondary semantic cosine-similarity reranker to prioritize evidence quality.
5. **Implemented a self-correcting agent loop** where a compliance **Critic Agent** validates draft answers against retrieved source contexts, triggering loop revisions to verify source grounding and increasing citation accuracy from **68% to 86%**.
6. **Added RAG evaluation and observability** using custom evaluation metrics over a **30-question golden dataset**, recording latency, retrieval recall, faithfulness, and logging structured execution steps seamlessly.
