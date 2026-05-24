from app.agents.llm import llm_service
from app.observability.logging import logger
from typing import List, Dict, Any, Tuple

class CriticAgent:
    def __init__(self):
        pass

    async def evaluate_answer(self, query: str, context: List[Dict[str, Any]], answer: str) -> Tuple[bool, str]:
        """
        Critically evaluates the answer for:
        1. Faithfulness: Is it grounded in context?
        2. Answer Relevance: Does it address the query?
        3. Citation Integrity: Are citations correct?
        """
        logger.info("Critic Agent evaluating response quality...")
        
        context_text = "\n".join([f"[{i+1}] {c.get('text', '')}" for i, c in enumerate(context)])
        
        system_prompt = (
            "You are the senior 'Grader/Critic' in a high-stakes RAG system.\n"
            "Your role is to strictly audit the assistant's answer based on the provided context.\n\n"
            "Criteria:\n"
            "1. NO HALLUCINATION: Every claim must be supported by the context.\n"
            "2. RELEVANCE: The answer must directly and fully answer the user query.\n"
            "3. CITATION: If sources are provided, the answer should cite them using [1], [2] notation.\n\n"
            "Output Format:\n"
            "If the answer is perfect, output ONLY 'PASSED'.\n"
            "If there are issues, output 'FAILED: [Reason for failure and how to fix]'."
        )
        
        prompt = f"""
        User Query: {query}
        ---
        Retrieved Context:
        {context_text}
        ---
        Assistant's Answer:
        {answer}
        """
        
        evaluation = await llm_service.acomplete(prompt, system_prompt=system_prompt, temperature=0.0)
        
        if evaluation.strip().upper() == "PASSED":
            logger.info("Critic evaluation: PASSED")
            return True, ""
        else:
            feedback = evaluation.replace("FAILED:", "").strip()
            logger.warning(f"Critic evaluation: FAILED - {feedback}")
            return False, feedback

critic_agent = CriticAgent()
