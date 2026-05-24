from typing import List, Dict, Any
from app.agents.llm import llm_service
from app.observability.logging import logger

class CodebaseAgent:
    def __init__(self):
        pass

    async def process_codebase_query(self, query: str, evidence: List[Dict[str, Any]]) -> str:
        """
        Processes queries related to the codebase using provided evidence chunks.
        """
        logger.info(f"Codebase Agent executing query: '{query}' with {len(evidence)} chunks.")
        
        if not evidence:
            return "Không tìm thấy đoạn mã nguồn nào liên quan trong dữ liệu đã ingest."
            
        code_context = []
        for idx, doc in enumerate(evidence):
            meta = doc.get("metadata", {})
            file_path = meta.get("file_path", meta.get("file_name", "unknown_file"))
            lang = meta.get("language", "text")
            
            block = (
                f"Source [{idx+1}]:\n"
                f"File: {file_path} (Language: {lang})\n"
                f"```{lang}\n"
                f"{doc['text']}\n"
                f"```\n"
                f"---"
            )
            code_context.append(block)
            
        context_str = "\n\n".join(code_context)
        
        system_prompt = (
            "You are the expert Codebase Agent of the Agentic Knowledge OS.\n"
            "Your objective is to help engineering teams understand codebase architecture, review code files, locate entry points, and detect bugs.\n"
            "Guidelines:\n"
            "1. Ground your explanations in the provided code snippets. Refer to them as Source [1], [2], etc.\n"
            "2. When reviewing code, categorize observations into priorities:\n"
            "   - 'P0' (Critical production-grade issues like safety/validation flaws)\n"
            "   - 'P1' (Flaws in connection, missing retries, or error logs)\n"
            "   - 'P2' (Documentation or missing unit tests)\n"
            "3. Present code-walkthroughs step-by-step with filename headers.\n"
            "4. Respond in Vietnamese in a clear, concise, and highly professional engineer-to-engineer tone."
        )
        
        prompt = (
            f"User Query: {query}\n\n"
            f"Retrieved Codebase Chunks:\n"
            f"{context_str}\n\n"
            f"Codebase Agent Analysis & Response:"
        )
        
        analysis = await llm_service.acomplete(prompt, system_prompt=system_prompt, temperature=0.2)
        return analysis

codebase_agent = CodebaseAgent()
