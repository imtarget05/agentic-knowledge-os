# MCP Standard Tools & Resources Reference

This document catalogs the standardized tools, resources, and prompt templates exposed by the Model Context Protocol (MCP) server.

## Exposed Tools

1. **`search_documents(query, top_k)`**
   - *Description*: Searches indexed technical PDFs and specifications using dense-sparse hybrid retrieval.
   - *Parameters*:
     - `query` (str): Search term.
     - `top_k` (int): Number of results (default: 5).

2. **`read_document_chunk(chunk_id)`**
   - *Description*: Retrieves precise raw text contents and page references for a specific chunk.

3. **`search_codebase(query, repo_name)`**
   - *Description*: Scans indexed codebase elements inside a specific indexed repository.

4. **`read_file(path)`**
   - *Description*: Reads local files inside the workspace securely. Prevents parent folder traversal.

5. **`summarize_repository(repo_name)`**
   - *Description*: Catalogues all indexed files and chunk distribution inside the codebase.

6. **`create_task(title, description, priority)`**
   - *Description*: Logs a structured actionable engineering task into the local SQLite database.

7. **`run_rag_evaluation(dataset_name)`**
   - *Description*: Spawns the python evaluation script asynchronously.

8. **`get_trace(run_id)`**
   - *Description*: Pulls trace timing logs and sub-agent thought steps.

---

## Resources & Prompts

### Resources List
- `documents://all`: Dynamic list of all ingested technical specifications.
- `documents://{doc_id}`: High-fidelity raw text chunks and page layouts.
- `repositories://all`: List of all indexed codebases.
- `evals://latest`: MD text containing benchmark stats.

### Prompts Templates
- `prompt://architecture_review`: Technical architectural reviews.
- `prompt://rag_answer_with_citations`: Verified grounded QA answers.
- `prompt://code_review`: Cataloguing security gaps and missing retry wrappers.
- `prompt://task_breakdown`: Project task decomposition roadmaps.
