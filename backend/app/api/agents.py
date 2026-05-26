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

# --- New Task Decomposition & Parallel Execution API ---
from app.agents.task_decomposer import TaskDecomposer, TaskDecomposition
from app.agents.task_orchestrator import TaskOrchestrator
from fastapi.responses import StreamingResponse
from fastapi import BackgroundTasks

class DecompositionRequest(BaseModel):
    """Request for task decomposition"""
    request: str
    max_workers: int = 4
    time_budget_sec: Optional[float] = None
    enable_optimization: bool = True

class DecompositionResponse(BaseModel):
    """Response containing task decomposition"""
    request_id: str
    original_request: str
    total_subtasks: int
    estimated_total_time_sec: float
    estimated_speedup_factor: float
    subtasks: List[Dict[str, Any]]
    parallel_groups: List[List[str]]
    execution_strategy: str
    optimization_suggestions: List[str] = []

# Instantiate services
decomposer = TaskDecomposer(max_workers=4)
orchestrator = TaskOrchestrator(max_workers=4)

@router.post("/decompose", response_model=DecompositionResponse)
async def decompose_request(req: DecompositionRequest):
    """
    Decompose a complex request into parallel subtasks and estimate latency speedup.
    """
    try:
        logger.info(f"API: Decomposing request: '{req.request[:60]}...'")
        
        # Asynchronously decompose
        decomposition = await decomposer.decompose(
            request=req.request,
            context={"max_workers": req.max_workers}
        )
        
        if req.enable_optimization:
            decomposition = decomposer.optimize_decomposition(decomposition)
            
        # Compute performance metrics
        metrics = decomposer.calculate_execution_time(decomposition)
        
        # Auto-register major tasks into SQLite Task Manager Database
        try:
            from app.tools.task_tools import task_db_manager
            for task in decomposition.subtasks:
                priority_map = {"critical": "P0", "high": "P0", "medium": "P1", "low": "P2"}
                db_priority = priority_map.get(task.priority.value, "P1")
                task_db_manager.create_task(
                    title=task.title,
                    description=task.description or f"Subtask of: {decomposition.original_request}",
                    priority=db_priority
                )
            logger.info(f"Auto-registered {len(decomposition.subtasks)} subtasks in SQLite database.")
        except Exception as db_err:
            logger.warning(f"Could not auto-register subtasks in database: {str(db_err)}")
            
        return DecompositionResponse(
            request_id=decomposition.request_id,
            original_request=decomposition.original_request,
            total_subtasks=len(decomposition.subtasks),
            estimated_total_time_sec=decomposition.estimated_total_time_sec,
            estimated_speedup_factor=metrics.get("speedup_factor", 1.0),
            subtasks=[t.to_dict() for t in decomposition.subtasks],
            parallel_groups=decomposition.parallel_groups,
            execution_strategy=decomposition.decomposition_strategy,
            optimization_suggestions=[
                "Nhóm các Retriever lên nhóm thực thi song song đầu tiên để nạp dữ liệu sớm",
                "Đồng bộ kết quả từ Retriever trực tiếp vào Analyzer và Generator",
                "Sử dụng Critic Node để kiểm định trước khi trả về câu trả lời cuối cùng"
            ]
        )
    except Exception as e:
        logger.error(f"Decomposition endpoint failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Task decomposition failed: {str(e)}")

@router.post("/execute")
async def execute_decomposition_stream(req: DecompositionRequest):
    """
    Execute task decomposition with streaming progress updates using NDJSON.
    """
    async def progress_generator():
        try:
            logger.info(f"API Stream: Starting decomposition for request: '{req.request[:60]}...'")
            
            # Step 1: Decompose
            decomposition = await decomposer.decompose(req.request)
            if req.enable_optimization:
                decomposition = decomposer.optimize_decomposition(decomposition)
                
            yield json.dumps({
                "phase": "decomposition_complete",
                "request_id": decomposition.request_id,
                "total_tasks": len(decomposition.subtasks),
                "decomposition": decomposition.to_dict()
            }) + "\n"
            
            # Step 2: Set up async progress queue
            queue = asyncio.Queue()
            
            def progress_callback(update):
                queue.put_nowait(update)
                
            # Start parallel orchestrator task in background
            exec_task = asyncio.create_task(
                orchestrator.execute_decomposition(
                    decomposition,
                    progress_callback=progress_callback
                )
            )
            
            # Step 3: Stream progress events from queue
            while not exec_task.done() or not queue.empty():
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=0.5)
                    yield json.dumps({
                        "phase": "progress",
                        "completed": update["completed"],
                        "total": update["total"],
                        "current_task": update["current_task"],
                        "status": update["status"]
                    }) + "\n"
                except asyncio.TimeoutError:
                    continue
                    
            # Get final execution outcome
            result = await exec_task
            
            yield json.dumps({
                "phase": "execution_complete",
                "request_id": result['request_id'],
                "status": result['status'],
                "metrics": result['metrics'],
                "results": result['results']
            }) + "\n"
            
        except Exception as e:
            logger.error(f"Streaming execution failed: {str(e)}", exc_info=True)
            yield json.dumps({
                "phase": "error",
                "error": str(e)
            }) + "\n"
            
    return StreamingResponse(
        progress_generator(),
        media_type="application/x-ndjson",
        headers={
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

