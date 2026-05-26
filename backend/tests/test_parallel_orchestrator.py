import pytest
import asyncio
from app.agents.task_decomposer import TaskDecomposer, TaskPriority, SubTask, TaskDecomposition
from app.agents.task_orchestrator import TaskOrchestrator, TaskStatus, TaskExecutionResult

@pytest.mark.asyncio
async def test_fallback_decomposition():
    """Verify that fallback decomposition operates when LLM is in mock mode"""
    decomposer = TaskDecomposer(max_workers=4)
    request = "Phân tích bảo mật codebase"
    
    plan = await decomposer.decompose(request)
    
    assert plan.original_request == request
    assert len(plan.subtasks) == 4
    assert len(plan.parallel_groups) == 4
    assert plan.subtasks[0].agent_type == "retriever"
    assert plan.subtasks[3].agent_type == "critic"

def test_compute_parallel_groups():
    """Verify topological level sorting based on subtask dependencies"""
    decomposer = TaskDecomposer(max_workers=4)
    
    t1 = SubTask(id="t1", title="Task 1", dependencies=[])
    t2 = SubTask(id="t2", title="Task 2", dependencies=["t1"])
    t3 = SubTask(id="t3", title="Task 3", dependencies=["t1"])
    t4 = SubTask(id="t4", title="Task 4", dependencies=["t2", "t3"])
    
    groups = decomposer._compute_parallel_groups([t1, t2, t3, t4])
    
    assert groups[0] == ["t1"]
    assert sorted(groups[1]) == ["t2", "t3"]
    assert groups[2] == ["t4"]

def test_calculate_critical_path():
    """Verify critical path duration estimation"""
    decomposer = TaskDecomposer(max_workers=4)
    
    t1 = SubTask(id="t1", estimated_duration_sec=2.0, dependencies=[])
    t2 = SubTask(id="t2", estimated_duration_sec=3.0, dependencies=["t1"])
    t3 = SubTask(id="t3", estimated_duration_sec=1.5, dependencies=["t1"])
    t4 = SubTask(id="t4", estimated_duration_sec=2.0, dependencies=["t2", "t3"])
    
    crit_path_time = decomposer._calculate_critical_path([t1, t2, t3, t4])
    # path: t1 -> t2 -> t4: 2.0 + 3.0 + 2.0 = 7.0
    assert crit_path_time == 7.0

@pytest.mark.asyncio
async def test_orchestrator_execution():
    """Test that parallel orchestrator successfully coordinates decomposed subtasks"""
    decomposer = TaskDecomposer(max_workers=4)
    orchestrator = TaskOrchestrator(max_workers=4)
    
    plan = await decomposer.decompose("Rà soát mã nguồn")
    
    result = await orchestrator.execute_decomposition(plan)
    
    assert result["status"] == "completed"
    assert result["metrics"]["total_tasks"] == 4
    assert result["metrics"]["completed_tasks"] == 4
    assert len(result["results"]) == 4
    
    # Check that execution details exist and statuses are completed
    for tid, info in result["results"].items():
        assert info["status"] == "completed"
