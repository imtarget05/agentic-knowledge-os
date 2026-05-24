from typing import List, Dict, Any, Tuple
from app.agents.llm import llm_service
from app.rag.citation import citation_helper
from app.observability.logging import logger

class DocumentQAAgent:
    def __init__(self):
        pass

    async def answer_query(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Synthesizes an answer based strictly on retrieved document chunks.
        Requires verified citations pointing to the source file name, page, and chunk_id.
        """
        logger.info(f"Document QA Agent answering query: '{query}' with {len(retrieved_chunks)} chunks.")
        
        if not retrieved_chunks:
            return "Không tìm thấy đủ bằng chứng trong tài liệu đã ingest.", []
            
        # Format chunks for LLM context
        sources_text = citation_helper.format_sources_for_llm(retrieved_chunks)
        
        system_prompt = (
            "You are the expert Document QA Agent of the Agentic Knowledge OS.\n"
            "Your objective is to answer the user's question with high fidelity, relying strictly on the retrieved source documents provided.\n"
            "Rules:\n"
            "1. You MUST ground every claim with a citation pointing to its source index, like [1], [2].\n"
            "2. If the provided sources do not contain enough facts or evidence to answer the query, you MUST say exactly:\n"
            "   'Không tìm thấy đủ bằng chứng trong tài liệu đã ingest.'\n"
            "3. Do NOT make up or hallucinate any facts not explicitly present in the sources.\n"
            "4. Answer in Vietnamese by default, maintaining a highly technical, precise, and professional tone."
        )
        
        prompt = (
            f"Câu hỏi của User: {query}\n\n"
            f"Nguồn dữ liệu được cung cấp:\n"
            f"{sources_text}\n\n"
            f"Câu trả lời:"
        )
        
        raw_answer = await llm_service.acomplete(prompt, system_prompt=system_prompt, temperature=0.1)
        
        # Verify and extract structured citations
        verified_answer, citations = citation_helper.verify_and_extract_citations(raw_answer, retrieved_chunks)
        
        # Double check "lack of evidence" clause
        if "không tìm thấy đủ bằng chứng" in verified_answer.lower():
            citations = []
            
        logger.info(f"Document QA Agent generated answer. Total citations: {len(citations)}")
        return verified_answer, citations

document_qa_agent = DocumentQAAgent()
