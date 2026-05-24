import os
import uuid
from typing import List, Dict, Any
from datetime import datetime
from llama_index.core.schema import Document as LlamaDocument, TextNode
from app.rag.chunking import chunking_engine
from app.observability.logging import logger
from app.config import settings

class IngestionEngine:
    def __init__(self):
        pass

    def parse_file(self, file_path: str) -> List[LlamaDocument]:
        logger.info(f"Parsing file: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_name = os.path.basename(file_path)
        ext = file_name.split(".")[-1].lower() if "." in file_name else ""
        
        documents = []
        created_at = datetime.utcnow().strftime("%Y-%m-%d")
        
        try:
            if ext == "pdf":
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                logger.info(f"PDF parsing initiated. Total pages: {len(reader.pages)}")
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    doc = LlamaDocument(
                        text=text,
                        metadata={
                            "file_name": file_name,
                            "source_type": "pdf",
                            "page": idx + 1,
                            "created_at": created_at
                        }
                    )
                    documents.append(doc)
                    
            elif ext == "docx":
                import docx2txt
                text = docx2txt.process(file_path)
                doc = LlamaDocument(
                    text=text,
                    metadata={
                        "file_name": file_name,
                        "source_type": "docx",
                        "page": 1,
                        "created_at": created_at
                    }
                )
                documents.append(doc)
                
            elif ext in ["md", "markdown"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                doc = LlamaDocument(
                    text=text,
                    metadata={
                        "file_name": file_name,
                        "source_type": "markdown",
                        "page": 1,
                        "created_at": created_at
                    }
                )
                documents.append(doc)
                
            else:  # fallback to text
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                doc = LlamaDocument(
                    text=text,
                    metadata={
                        "file_name": file_name,
                        "source_type": "txt",
                        "page": 1,
                        "created_at": created_at
                    }
                )
                documents.append(doc)
                
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}", exc_info=True)
            raise e
            
        return documents

    def ingest_file(self, file_path: str, doc_id: str = None) -> List[TextNode]:
        doc_id = doc_id or f"doc-{uuid.uuid4().hex[:8]}"
        documents = self.parse_file(file_path)
        all_nodes = []
        
        for doc in documents:
            nodes = chunking_engine.chunk_document(doc, doc_id=doc_id)
            all_nodes.extend(nodes)
            
        logger.info(f"Ingested file {file_path} into {len(all_nodes)} nodes")
        return all_nodes

ingestion_engine = IngestionEngine()
