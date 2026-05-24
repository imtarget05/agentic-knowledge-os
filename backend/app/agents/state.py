from typing import List, Dict, Any, TypedDict, Optional

class AgentState(TypedDict):
    # Core inputs
    user_query: str
    trace_id: str
    history: List[Dict[str, str]]
    
    # Internal agent parameters
    intent: str  # Classified query type (e.g., document_qa, codebase_qa, code_review, etc.)
    sub_questions: List[str]  # Query decomposition results
    selected_tools: List[str]  # Tools selected by router
    
    # Retrieval products
    retrieved_contexts: List[Dict[str, Any]]  # Chunks pulled from RAG
    graded_evidence: List[Dict[str, Any]]  # Filtered/verified chunks after grading
    needs_web_search: Optional[bool]  # CRAG flag for fallback
    
    # Reasoning drafts
    draft_answer: str
    citations: List[Dict[str, Any]]  # Validated source references
    
    # Feedback loop parameters
    critic_feedback: Optional[str]
    critic_attempts: int  # Prevent infinite loops in self-correction
    
    # Final product
    final_answer: str
    thought_steps: List[str]  # Reasoning trace steps displayed in the Frontend UI
