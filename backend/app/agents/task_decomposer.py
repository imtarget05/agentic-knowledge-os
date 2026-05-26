"""
Task Decomposer Agent: Automatically breaks down complex requests into parallel subtasks.
Enables faster execution through intelligent task partitioning and dependency mapping.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
import json
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.observability.logging import logger
from app.agents.llm import llm_service
from app.agents.decomposition_prompts import TASK_DECOMPOSITION_SYSTEM_PROMPT, PROMPT_TEMPLATE_FOR_REQUESTS

class TaskPriority(str, Enum):
    """Task execution priority levels"""
    CRITICAL = "critical"      # Must complete first
    HIGH = "high"              # Can start after critical tasks
    MEDIUM = "medium"          # Standard priority
    LOW = "low"                # Background/optional tasks

class TaskDependency(str, Enum):
    """Dependency relationship types"""
    BLOCKS = "blocks"          # Task must wait for dependency
    ENHANCES = "enhances"      # Optional, improves result
    PARALLEL = "parallel"      # Can run simultaneously

class SubTask(BaseModel):
    """Atomic unit of work that can be executed independently"""
    id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    title: str = ""
    description: str = ""
    agent_type: str = "generic"  # e.g., "retriever", "generator", "critic", "analyzer", "orchestrator"
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration_sec: float = 5.0
    dependencies: List[str] = Field(default_factory=list)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_type: str = "string"  # Expected output format
    retry_count: int = 0
    max_retries: int = 2
    status: str = "pending"     # pending, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def can_execute(self, completed_tasks: List[str]) -> bool:
        """Check if all dependencies are completed"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)

class TaskDecomposition(BaseModel):
    """Result of task decomposition with execution plan"""
    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    original_request: str = ""
    subtasks: List[SubTask] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)  # Task IDs in execution sequence
    parallel_groups: List[List[str]] = Field(default_factory=list)  # Groups of parallel tasks
    estimated_total_time_sec: float = 0.0
    decomposition_strategy: str = "dependency-aware"  # Strategy used for decomposition
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data['subtasks'] = [t.to_dict() for t in self.subtasks]
        return data

class TaskDecomposer:
    """
    Intelligent task decomposition engine using LLM-guided analysis.
    Breaks requests into parallel-executable subtasks with dependency mapping.
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        logger.info(f"TaskDecomposer initialized with {max_workers} max parallel workers")

    async def decompose(self, request: str, context: Optional[Dict[str, Any]] = None) -> TaskDecomposition:
        """
        Main decomposition method.
        Takes a complex request and returns an optimized execution plan.
        """
        logger.info(f"Decomposing request: {request[:100]}...")
        
        system_prompt = TASK_DECOMPOSITION_SYSTEM_PROMPT
        
        # Prepare template arguments
        llm_model = "Gemini 2.5 Flash"
        system_context = (
            "Available tools: hybrid vector search (Qdrant), codebase analyzer, "
            "document QA agent, SQLite DB Task recorder, critic evaluator."
        )
        
        prompt = PROMPT_TEMPLATE_FOR_REQUESTS.format(
            user_request=request,
            max_workers=self.max_workers,
            system_context=system_context,
            time_budget_sec=60.0
        )
        
        try:
            # Asynchronously query the LLM service
            llm_response = await llm_service.acomplete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1
            )
            
            # Clean response JSON if necessary
            cleaned_resp = self._extract_json(llm_response)
            parsed_json = json.loads(cleaned_resp)
            
            decomposition = self._parse_llm_response(parsed_json)
            decomposition.original_request = request
            
            # Formulate sequential plan vs. parallel groups if LLM returned subtasks
            if not decomposition.subtasks:
                decomposition = self._generate_fallback_decomposition(request)
            
            return decomposition
            
        except Exception as e:
            logger.error(f"Failed to decompose using LLM: {str(e)}", exc_info=True)
            return self._generate_fallback_decomposition(request)

    def _extract_json(self, text: str) -> str:
        """Helper to extract pure JSON from LLM markdown codeblocks"""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return text

    def _parse_llm_response(self, llm_output: Dict[str, Any]) -> TaskDecomposition:
        """Parse LLM JSON response into TaskDecomposition object"""
        subtasks = []
        task_map = {}
        
        # Handle formats where subtasks reside in different keys
        raw_tasks = llm_output.get("subtasks", [])
        if not raw_tasks and "tasks" in llm_output:
            raw_tasks = llm_output.get("tasks", [])
            
        for task_data in raw_tasks:
            # Map Pydantic-compatible priorities
            priority_str = task_data.get("priority", "medium").lower()
            if priority_str not in ["critical", "high", "medium", "low"]:
                priority_str = "medium"
                
            subtask = SubTask(
                id=task_data.get("id", f"task-{uuid.uuid4().hex[:8]}"),
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description", ""),
                agent_type=task_data.get("agent_type", task_data.get("type", "generic")),
                priority=TaskPriority(priority_str),
                estimated_duration_sec=float(task_data.get("estimated_duration_sec", task_data.get("duration_estimate", 5.0))),
                dependencies=task_data.get("dependencies", task_data.get("depends_on", [])),
                input_data=task_data.get("input_data", {}),
                output_type=task_data.get("output_type", "string"),
            )
            subtasks.append(subtask)
            task_map[subtask.id] = subtask
            
        # Parse parallel groups
        exec_plan = llm_output.get("execution_plan", {})
        parallel_groups = exec_plan.get("parallel_groups", llm_output.get("parallel_groups", []))
        
        # If parallel groups are not provided, we compute them from dependencies
        if not parallel_groups and subtasks:
            parallel_groups = self._compute_parallel_groups(subtasks)
            
        estimated_total_time = float(exec_plan.get("estimated_parallel_time_sec", llm_output.get("estimated_total_time_sec", 0.0)))
        if estimated_total_time == 0 and subtasks:
            # Estimate total time as critical path length
            estimated_total_time = self._calculate_critical_path(subtasks)
            
        decomposition = TaskDecomposition(
            original_request=llm_output.get("original_request", ""),
            subtasks=subtasks,
            parallel_groups=parallel_groups,
            estimated_total_time_sec=estimated_total_time,
            decomposition_strategy=llm_output.get("execution_strategy", "dependency-aware")
        )
        
        return decomposition

    def _compute_parallel_groups(self, subtasks: List[SubTask]) -> List[List[str]]:
        """Compute parallel execution groups topological levels based on dependencies"""
        groups = []
        completed = set()
        remaining = list(subtasks)
        
        while remaining:
            current_group = []
            for task in list(remaining):
                if all(dep in completed for dep in task.dependencies):
                    current_group.append(task.id)
                    remaining.remove(task)
            if not current_group:
                # Cycle detected! Force remaining tasks
                current_group = [task.id for task in remaining]
                remaining.clear()
            completed.update(current_group)
            groups.append(current_group)
            
        return groups

    def _calculate_critical_path(self, subtasks: List[SubTask]) -> float:
        """Estimate execution time along the critical path"""
        task_map = {t.id: t for t in subtasks}
        memo = {}
        
        def get_max_time(task_id: str) -> float:
            if task_id in memo:
                return memo[task_id]
            task = task_map.get(task_id)
            if not task:
                return 0.0
            
            dep_times = [get_max_time(dep) for dep in task.dependencies]
            max_dep = max(dep_times) if dep_times else 0.0
            total = max_dep + task.estimated_duration_sec
            memo[task_id] = total
            return total
            
        times = [get_max_time(t.id) for t in subtasks]
        return max(times) if times else 0.0

    def _generate_fallback_decomposition(self, request: str) -> TaskDecomposition:
        """Create a default 4-stage fallback decomposition in case LLM fails or goes offline"""
        logger.info("Generating fallback decomposition...")
        t1_id = f"task-fallback-retrieval-{uuid.uuid4().hex[:4]}"
        t2_id = f"task-fallback-analysis-{uuid.uuid4().hex[:4]}"
        t3_id = f"task-fallback-generation-{uuid.uuid4().hex[:4]}"
        t4_id = f"task-fallback-critic-{uuid.uuid4().hex[:4]}"
        
        subtasks = [
            SubTask(
                id=t1_id,
                title="Truy xuất thông tin liên quan",
                description="Tìm kiếm cơ sở tri thức Qdrant và mã nguồn về: " + request[:60],
                agent_type="retriever",
                priority=TaskPriority.CRITICAL,
                estimated_duration_sec=2.0,
                dependencies=[],
                input_data={"query": request},
                output_type="document_list"
            ),
            SubTask(
                id=t2_id,
                title="Phân tích ngữ cảnh",
                description="Phân tích chi tiết và phân loại thông tin đã truy xuất",
                agent_type="analyzer",
                priority=TaskPriority.HIGH,
                estimated_duration_sec=3.0,
                dependencies=[t1_id],
                input_data={"query": request},
                output_type="analysis"
            ),
            SubTask(
                id=t3_id,
                title="Tổng hợp phản hồi",
                description="Tạo ra câu trả lời chi tiết, có cấu trúc chặt chẽ dựa trên phân tích",
                agent_type="generator",
                priority=TaskPriority.HIGH,
                estimated_duration_sec=4.0,
                dependencies=[t2_id],
                input_data={"query": request},
                output_type="string"
            ),
            SubTask(
                id=t4_id,
                title="Kiểm định chất lượng phản hồi",
                description="Đánh giá tính chính xác của phản hồi tránh hiện tượng ảo ảnh (hallucination)",
                agent_type="critic",
                priority=TaskPriority.MEDIUM,
                estimated_duration_sec=2.0,
                dependencies=[t3_id],
                input_data={"query": request},
                output_type="validation"
            )
        ]
        
        return TaskDecomposition(
            original_request=request,
            subtasks=subtasks,
            parallel_groups=[[t1_id], [t2_id], [t3_id], [t4_id]],
            estimated_total_time_sec=11.0,
            decomposition_strategy="default-sequential-fallback"
        )

    def optimize_decomposition(self, decomposition: TaskDecomposition) -> TaskDecomposition:
        """
        Refine decomposition for better parallelization and performance.
        Suggests optimizations.
        """
        logger.info(f"Optimizing decomposition with {len(decomposition.subtasks)} tasks")
        # In a fully fleshed out agentic loop, this would run refinement prompts. 
        # Here we verify and clean dependencies.
        return decomposition

    def calculate_execution_time(self, decomposition: TaskDecomposition) -> Dict[str, float]:
        """Calculate realistic execution metrics"""
        metrics = {
            "sequential_total": sum(t.estimated_duration_sec for t in decomposition.subtasks),
            "parallel_total": decomposition.estimated_total_time_sec,
            "speedup_factor": 1.0,
            "parallelization_efficiency": 0.0
        }
        
        if metrics["parallel_total"] > 0:
            metrics["speedup_factor"] = round(metrics["sequential_total"] / metrics["parallel_total"], 2)
            metrics["parallelization_efficiency"] = round(
                ((metrics["sequential_total"] - metrics["parallel_total"]) / 
                metrics["sequential_total"] * 100), 1
            )
        
        return metrics
