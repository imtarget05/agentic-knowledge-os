import uuid
import re
from typing import List, Dict, Any
from datetime import datetime
from llama_index.core.schema import Document as LlamaDocument, TextNode
from llama_index.core.node_parser import SentenceSplitter, CodeSplitter

class ChunkingEngine:
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Initialize LlamaIndex splitters
        self.text_splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def clean_text(self, text: str) -> str:
        # Basic cleanup: normalized whitespace, removed redundant newlines
        if not text:
            return ""
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def get_code_splitter(self, language: str):
        """
        Returns a CodeSplitter for the given language.
        Supported languages in LlamaIndex: python, javascript, typescript, go, ruby, etc.
        """
        try:
            return CodeSplitter(
                language=language,
                chunk_lines=40,  # Split by 40 lines of code
                chunk_lines_overlap=10,
                max_chars=self.chunk_size * 4
            )
        except Exception:
            # Fallback to text splitter if language not supported or error
            return self.text_splitter

    def chunk_document(self, doc: LlamaDocument, doc_id: str = None) -> List[TextNode]:
        doc_id = doc_id or doc.doc_id or f"doc-{uuid.uuid4().hex[:8]}"
        raw_text = self.clean_text(doc.text)
        
        # Meta info from LlamaIndex document
        file_name = doc.metadata.get("file_name", "unknown.txt")
        source_type = doc.metadata.get("source_type", file_name.split(".")[-1] if "." in file_name else "txt")
        created_at = doc.metadata.get("created_at", datetime.utcnow().strftime("%Y-%m-%d"))
        
        # Mapping common extensions to CodeSplitter languages
        code_lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "tsx": "typescript",
            "jsx": "javascript",
            "go": "go",
            "rb": "ruby",
            "cpp": "cpp",
            "c": "c",
            "java": "java"
        }

        # Choose appropriate splitter
        if source_type in code_lang_map:
            splitter = self.get_code_splitter(code_lang_map[source_type])
            # CodeSplitter returns nodes directly
            nodes = splitter.get_nodes_from_documents([doc])
        else:
            # For MD and TXT, use SentenceSplitter
            nodes = self.text_splitter.get_nodes_from_documents([doc])

        # Post-process nodes to ensure our metadata structure
        processed_nodes = []
        for idx, node in enumerate(nodes):
            chunk_id = f"{doc_id}-c{idx:03d}"
            
            # Enrich metadata
            node.metadata.update({
                "doc_id": doc_id,
                "source_type": source_type,
                "file_name": file_name,
                "chunk_id": chunk_id,
                "created_at": created_at
            })
            node.id_ = chunk_id
            processed_nodes.append(node)
            
        return processed_nodes

chunking_engine = ChunkingEngine()
