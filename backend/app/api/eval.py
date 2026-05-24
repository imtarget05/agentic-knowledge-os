import os
import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.config import settings
from app.observability.logging import logger

router = APIRouter(prefix="/api/eval", tags=["Evaluation"])

class EvalRunResponse(BaseModel):
    status: str
    message: str
    trace_id: Optional[str] = None

class EvalMetrics(BaseModel):
    metric: str
    baseline: str
    agentic: str
    improvement: str
    status_label: str

class EvalLatestResponse(BaseModel):
    results_markdown: str
    golden_dataset_count: int
    metrics: List[EvalMetrics]

@router.post("/run", response_model=EvalRunResponse)
async def run_evaluation(background_tasks: BackgroundTasks):
    logger.info("RAG evaluation request received.")
    
    # Path to evals/run_eval.py relative to this file
    eval_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "evals", 
        "run_eval.py"
    )
    
    if not os.path.exists(eval_script):
        # Try one more path if not found (root of repo)
        eval_script = "evals/run_eval.py"
        
    def execute_eval_script():
        logger.info(f"Executing {eval_script} in background task...")
        import subprocess
        import sys
        try:
            # Set PYTHONPATH to root so 'app' module is found
            env = os.environ.copy()
            env["PYTHONPATH"] = os.getcwd() + "/backend"
            
            result = subprocess.run(
                [sys.executable, eval_script],
                capture_output=True,
                text=True,
                env=env
            )
            if result.returncode == 0:
                logger.info("Evaluation completed successfully.")
            else:
                logger.error(f"Evaluation script failed with code {result.returncode}: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running evaluation script: {str(e)}")
            
    background_tasks.add_task(execute_eval_script)
    
    return EvalRunResponse(
        status="running",
        message="Evaluation has been started in the background. Results will be available in 10-20 seconds."
    )

@router.get("/latest", response_model=EvalLatestResponse)
async def get_latest_eval():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    eval_results_path = os.path.join(root_dir, "evals", "eval_results.md")
    questions_path = os.path.join(root_dir, "evals", "questions.jsonl")
    
    dataset_count = 0
    if os.path.exists(questions_path):
        try:
            with open(questions_path, "r", encoding="utf-8") as f:
                dataset_count = sum(1 for line in f if line.strip())
        except Exception: pass
            
    if not os.path.exists(eval_results_path):
        return EvalLatestResponse(
            results_markdown="# No results found",
            golden_dataset_count=dataset_count,
            metrics=[]
        )
        
    try:
        with open(eval_results_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            
        # Parse table rows from markdown
        # Format: | **Metric** | baseline | agentic | improvement | status |
        metrics = []
        lines = md_content.split("\n")
        for line in lines:
            if line.strip().startswith("|") and "**" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 5:
                    metrics.append(EvalMetrics(
                        metric=parts[0].replace("**", ""),
                        baseline=parts[1],
                        agentic=parts[2],
                        improvement=parts[3],
                        status_label=parts[4]
                    ))
        
        return EvalLatestResponse(
            results_markdown=md_content,
            golden_dataset_count=dataset_count,
            metrics=metrics
        )
    except Exception as e:
        logger.error(f"Error parsing eval results: {str(e)}")
        return EvalLatestResponse(
            results_markdown=f"Error reading results: {str(e)}",
            golden_dataset_count=dataset_count,
            metrics=[]
        )
