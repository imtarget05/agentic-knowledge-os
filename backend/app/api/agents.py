from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

from app.observability.logging import logger
from app.config import settings

router = APIRouter(prefix="/api/agents", tags=["Agents"])

class AgentRunRequest(BaseModel):
    agent_name: str  # e.g., router, document_qa, codebase, task_planner, critic
    query: str
    context_data: Optional[Dict[str, Any]] = None

class AgentRunResponse(BaseModel):
    agent_name: str
    output: str
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@router.post("/run", response_model=AgentRunResponse)
async def run_individual_agent(request: AgentRunRequest):
    logger.info(f"Direct execution requested for agent '{request.agent_name}' with query: '{request.query}'")
    
    agent_name = request.agent_name.lower()
    valid_agents = {"router", "document_qa", "codebase", "task_planner", "critic"}
    
    if agent_name not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent name '{request.agent_name}'. Must be one of {valid_agents}"
        )
        
    try:
        # Import agents dynamically to avoid circular dependencies
        if agent_name == "router":
            from app.agents.router_agent import router_agent
            intent = await router_agent.classify_intent(request.query)
            return AgentRunResponse(
                agent_name=agent_name,
                output=f"Intent classified: {intent}",
                citations=[],
                metadata={"intent": intent}
            )
            
        elif agent_name == "document_qa":
            from app.agents.document_qa_agent import document_qa_agent
            from app.rag.hybrid_search import hybrid_search_engine
            
            chunks = hybrid_search_engine.search(request.query, top_k=4)
            result, citations = await document_qa_agent.answer_query(request.query, chunks)
            return AgentRunResponse(
                agent_name=agent_name,
                output=result,
                citations=citations,
                metadata={"chunk_count": len(chunks)}
            )
            
        elif agent_name == "codebase":
            from app.agents.codebase_agent import codebase_agent
            from app.rag.hybrid_search import hybrid_search_engine
            
            chunks = hybrid_search_engine.search(request.query, top_k=6)
            result = await codebase_agent.process_codebase_query(request.query, chunks)
            return AgentRunResponse(
                agent_name=agent_name,
                output=result,
                citations=[],
                metadata={"chunk_count": len(chunks)}
            )
            
        elif agent_name == "task_planner":
            from app.agents.task_planner_agent import task_planner_agent
            result = await task_planner_agent.generate_tasks(request.query)
            return AgentRunResponse(
                agent_name=agent_name,
                output=result,
                citations=[],
                metadata={}
            )
            
        elif agent_name == "critic":
            from app.agents.critic_agent import critic_agent
            from app.rag.hybrid_search import hybrid_search_engine
            
            chunks = hybrid_search_engine.search(request.query, top_k=2)
            passed, feedback = await critic_agent.evaluate_answer(request.query, chunks, "Sample answer draft")
            return AgentRunResponse(
                agent_name=agent_name,
                output=f"Passed: {passed}. Feedback: {feedback}",
                citations=[],
                metadata={"passed": passed}
            )
            
    except Exception as e:
        logger.error(f"Error during direct agent execution of {agent_name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(e)}"
        )
