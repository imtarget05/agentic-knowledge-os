from app.mcp_server.server import mcp_server
from app.rag.retriever import hybrid_retriever_engine
from app.observability.logging import logger
import os

@mcp_server.resource("documents://all")
def get_all_documents() -> str:
    """
    Lists metadata summaries for all ingested documents in the RAG store.
    """
    logger.info("MCP Resource 'documents://all' requested")
    try:
        doc_ids = hybrid_retriever_engine.get_all_document_ids()
        if not doc_ids:
            return "No documents ingested yet."
            
        lines = ["Ingested Documents in RAG Database:", "---"]
        for idx, doc_id in enumerate(sorted(doc_ids)):
            # Get some metadata from first node with this doc_id
            nodes = hybrid_retriever_engine.get_document_nodes(doc_id)
            file_name = nodes[0]["metadata"].get("file_name", "unknown") if nodes else "unknown"
            source_type = nodes[0]["metadata"].get("source_type", "unknown") if nodes else "unknown"
            lines.append(f"{idx+1}. ID: {doc_id} | File: {file_name} | Type: {source_type} | Chunks: {len(nodes)}")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving document list: {str(e)}"

@mcp_server.resource("documents://{doc_id}")
def get_document_by_id(doc_id: str) -> str:
    """
    Returns full raw text chunks and location metadata for a specific ingested document.
    """
    logger.info(f"MCP Resource 'documents://{doc_id}' requested")
    try:
        nodes = hybrid_retriever_engine.get_document_nodes(doc_id)
        if not nodes:
            return f"Document '{doc_id}' not found."
            
        # Re-assemble text
        file_name = nodes[0]["metadata"].get("file_name", "unknown")
        lines = [f"=== Document: {file_name} (ID: {doc_id}) ===", "Chunks list:"]
        
        for idx, node in enumerate(nodes):
            meta = node.get("metadata", {})
            page = meta.get("page", idx+1)
            sec = meta.get("section", "General")
            lines.append(f"\n--- Chunk [{idx+1}] | Page {page} | Section '{sec}' ---")
            lines.append(node["text"])
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading document {doc_id}: {str(e)}"

@mcp_server.resource("repositories://all")
def get_all_repositories() -> str:
    """
    Lists names of all repositories indexed in the codebase store.
    """
    logger.info("MCP Resource 'repositories://all' requested")
    try:
        repos = set()
        for node in hybrid_retriever_engine.bm25_nodes:
            repo_name = node.get("metadata", {}).get("repo_name")
            if repo_name:
                repos.add(repo_name)
                
        if not repos:
            return "No repositories indexed yet."
            
        lines = ["Indexed Repositories in Codebase Store:", "---"]
        for idx, repo in enumerate(sorted(repos)):
            lines.append(f"{idx+1}. Name: {repo}")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing repositories: {str(e)}"

@mcp_server.resource("repositories://{repo_name}")
def get_repository_files(repo_name: str) -> str:
    """
    Lists relative paths of all code files indexed inside a specific repository.
    """
    logger.info(f"MCP Resource 'repositories://{repo_name}' requested")
    try:
        files = set()
        for node in hybrid_retriever_engine.bm25_nodes:
            meta = node.get("metadata", {})
            if meta.get("repo_name") == repo_name:
                file_path = meta.get("file_path")
                if file_path:
                    files.add(file_path)
                    
        if not files:
            return f"Repository '{repo_name}' not found or has no indexed files."
            
        lines = [f"=== Repository Files: {repo_name} ===", "Paths:"]
        for idx, path in enumerate(sorted(files)):
            lines.append(f"{idx+1}. {path}")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing repository files for '{repo_name}': {str(e)}"

@mcp_server.resource("evals://latest")
def get_latest_eval_report() -> str:
    """
    Fetches the full markdown evaluation report (eval_results.md) comparing Baseline vs Agentic.
    """
    logger.info("MCP Resource 'evals://latest' requested")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    eval_results_path = os.path.join(base_dir, "evals", "eval_results.md")
    if not os.path.exists(eval_results_path):
        return "No evaluation results available yet. Run evals/run_eval.py first."
        
    try:
        with open(eval_results_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading evaluation results: {str(e)}"
