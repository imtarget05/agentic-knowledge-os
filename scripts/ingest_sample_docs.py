import os
import sys

# Add backend app to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.rag.ingestion import ingestion_engine
from app.rag.retriever import hybrid_retriever_engine
from app.observability.logging import logger

def main():
    logger.info("Starting ingestion of sample documents...")
    
    # Path to sample files
    base_dir = os.path.dirname(os.path.dirname(__file__))
    sample_dir = os.path.join(base_dir, "data", "sample_docs")
    
    if not os.path.exists(sample_dir):
        logger.error(f"Sample directory not found: {sample_dir}")
        return
        
    for file in os.listdir(sample_dir):
        if file.endswith((".md", ".txt", ".pdf")):
            file_path = os.path.join(sample_dir, file)
            logger.info(f"Ingesting file: {file_path}")
            
            try:
                # Ingest file into nodes
                nodes = ingestion_engine.ingest_file(file_path, doc_id=f"sample-{file.replace('.', '-')}")
                
                # Save to Qdrant & BM25 database
                hybrid_retriever_engine.save_nodes(nodes)
                
                logger.info(f"Successfully indexed '{file}' with {len(nodes)} chunks.")
            except Exception as e:
                logger.error(f"Failed to ingest file '{file}': {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
