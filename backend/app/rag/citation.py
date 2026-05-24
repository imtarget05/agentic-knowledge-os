import re
from typing import List, Dict, Any, Tuple

class CitationHelper:
    @staticmethod
    def format_sources_for_llm(documents: List[Dict[str, Any]]) -> str:
        """
        Formats list of retrieved document chunks into a clean text block that 
        the LLM can read and cite.
        """
        if not documents:
            return "No sources available."
            
        formatted_blocks = []
        for idx, doc in enumerate(documents):
            source_index = idx + 1
            meta = doc.get("metadata", {})
            file_name = meta.get("file_name", "unknown")
            page = meta.get("page", 1)
            section = meta.get("section", "General")
            chunk_id = meta.get("chunk_id", doc.get("id", "unknown-chunk"))
            
            block = (
                f"Source [{source_index}]:\n"
                f"File: {file_name}\n"
                f"Location: Page {page}, Section '{section}'\n"
                f"ID: {chunk_id}\n"
                f"Content: {doc['text']}\n"
                f"---"
            )
            formatted_blocks.append(block)
            
        return "\n\n".join(formatted_blocks)

    @staticmethod
    def verify_and_extract_citations(text: str, documents: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Scans LLM output text for citation markers like [1], [2], or [Source 1], 
        validates them against the actual retrieved documents, and appends a structured 
        citations summary list to return to the frontend client.
        """
        if not documents:
            return text, []

        # Find patterns like [1], [2], [source: 1], [Source 1]
        patterns = [
            r'\[([0-9]+)\]',
            r'\[[sS]ource\s*([0-9]+)\]'
        ]
        
        referenced_indices = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                try:
                    referenced_indices.add(int(m) - 1)
                except ValueError:
                    pass

        citations = []
        for idx in sorted(referenced_indices):
            if 0 <= idx < len(documents):
                doc = documents[idx]
                meta = doc.get("metadata", {})
                citations.append({
                    "index": idx + 1,
                    "file_name": meta.get("file_name", "unknown"),
                    "page": meta.get("page", 1),
                    "section": meta.get("section", "General"),
                    "chunk_id": meta.get("chunk_id", doc.get("id", "unknown-chunk")),
                    "text_preview": doc["text"][:150] + "..." if len(doc["text"]) > 150 else doc["text"]
                })
                
        # If there are no inline citations but documents were retrieved, and we want to prevent
        # missed matches, we can optionally parse them from the end of the text.
        return text, citations

citation_helper = CitationHelper()
