import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from app.config import settings
from app.observability.logging import logger
from app.rag.ingestion import ingestion_engine
from app.rag.retriever import hybrid_retriever_engine
from llama_index.core import Document as LlamaDocument

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

class RepoIngestRequest(BaseModel):
    repo_path: str
    repo_name: str

class IngestResponse(BaseModel):
    status: str
    doc_id: str
    file_name: str
    chunk_count: int

@router.post("/document", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    doc_id: Optional[str] = Form(None)
):
    logger.info(f"Received document upload request: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ["pdf", "docx", "md", "markdown", "txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported types: PDF, DOCX, MD, TXT"
        )
        
    doc_id = doc_id or f"doc-{uuid.uuid4().hex[:8]}"
    save_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    try:
        with open(save_path, "wb") as f:
            content = await file.read()
            if len(content) > 15 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 15MB")
            f.write(content)
            
        logger.info(f"File saved to local cache: {save_path}")
        
        # Parse and chunk file using ingestion engine
        nodes = ingestion_engine.ingest_file(save_path, doc_id=doc_id)
        
        # Write to Qdrant
        hybrid_retriever_engine.save_nodes(nodes)
        
        return IngestResponse(
            status="success",
            doc_id=doc_id,
            file_name=file.filename,
            chunk_count=len(nodes)
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during document ingestion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/repo", response_model=IngestResponse)
async def ingest_repo(request: RepoIngestRequest):
    logger.info(f"Received codebase ingestion request for path: {request.repo_path}")
    
    if not os.path.exists(request.repo_path):
        raise HTTPException(
            status_code=404, 
            detail=f"Local repository path not found: {request.repo_path}"
        )
        
    try:
        doc_id = f"repo-{request.repo_name}-{uuid.uuid4().hex[:4]}"
        all_nodes = []
        
        allowed_extensions = {".py", ".ts", ".tsx", ".js", ".yaml", ".yml", ".json", ".sh", ".md"}
        allowed_exact_files = {"Dockerfile", "docker-compose.yml", "Makefile"}
        ignored_directories = {"node_modules", ".git", "venv", "dist", "build", "__pycache__", "qdrant_storage"}
        
        from app.rag.chunking import chunking_engine

        for root, dirs, files in os.walk(request.repo_path):
            dirs[:] = [d for d in dirs if d not in ignored_directories]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, request.repo_path)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in allowed_extensions or file in allowed_exact_files:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        if not content.strip():
                            continue

                        doc = LlamaDocument(
                            text=content,
                            metadata={
                                "file_name": file,
                                "file_path": rel_path,
                                "repo_name": request.repo_name,
                                "source_type": "codebase",
                                "created_at": datetime.utcnow().strftime("%Y-%m-%d")
                            }
                        )
                        
                        file_nodes = chunking_engine.chunk_document(doc, doc_id=doc_id)
                        all_nodes.extend(file_nodes)
                        
                    except Exception as fe:
                        logger.warning(f"Skipping file {rel_path} due to error: {str(fe)}")
                        
        if not all_nodes:
            raise HTTPException(status_code=400, detail="No parseable code files found.")
            
        hybrid_retriever_engine.save_nodes(all_nodes)
        
        return IngestResponse(
            status="success",
            doc_id=doc_id,
            file_name=request.repo_name,
            chunk_count=len(all_nodes)
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during repository ingestion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Codebase ingestion failed: {str(e)}")
