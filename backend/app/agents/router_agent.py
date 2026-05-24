from app.agents.llm import llm_service
from app.observability.logging import logger

class RouterAgent:
    def __init__(self):
        pass

    async def classify_intent(self, query: str) -> str:
        """
        Classifies the user query intent to select the appropriate specialized sub-agent.
        Possible outputs: document_qa | codebase_qa | architecture_summary | code_review | task_planning | unknown
        """
        logger.info(f"Router Agent classifying intent for query: '{query}'")
        
        system_prompt = (
            "You are the expert Router Agent of the Agentic Knowledge OS.\n"
            "Your task is to classify the intent of the user's query into EXACTLY one of the following categories:\n"
            "- 'document_qa': General questions about text documents, manuals, specs, or reports (e.g. 'autoscaling works how in report?').\n"
            "- 'codebase_qa': Specific questions about the code, entry points, or file paths (e.g. 'where is the entry point?').\n"
            "- 'architecture_summary': High-level questions asking to summarize the repository structure or layers (e.g. 'what is the architecture of this repo?').\n"
            "- 'code_review': Requests to review code, search for production bugs, or check standard conformity (e.g. 'review the ingestion module for me').\n"
            "- 'task_planning': Requests to create checklists, roadmaps, task breakdowns, or project tasks (e.g. 'create a 7-day roadmap to improve RAG accuracy').\n"
            "- 'unknown': If it does not fit any of the above categories.\n\n"
            "Constraint: You MUST output ONLY the category string. Do not include any explanation, punctuation, or extra words."
        )
        
        prompt = f"User query to classify: \"{query}\"\nCategory:"
        
        intent = await llm_service.acomplete(prompt, system_prompt=system_prompt, temperature=0.0)
        intent = intent.strip().lower().replace("'", "").replace('"', "")
        
        valid_intents = {"document_qa", "codebase_qa", "architecture_summary", "code_review", "task_planning", "unknown"}
        if intent not in valid_intents:
            logger.warning(f"Router returned invalid intent '{intent}'. Defaulting to 'document_qa'.")
            intent = "document_qa"
            
        logger.info(f"Router Agent resolved intent: '{intent}'")
        return intent

router_agent = RouterAgent()
