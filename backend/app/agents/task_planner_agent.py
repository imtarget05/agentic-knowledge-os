from app.agents.llm import llm_service
from app.observability.logging import logger

class TaskPlannerAgent:
    def __init__(self):
        pass

    async def generate_tasks(self, query: str) -> str:
        """
        Decomposes technical suggestions or user requests into action items and roadmaps.
        Automatically registers task listings inside the SQLite database if possible.
        """
        logger.info(f"Task Planner Agent generating execution checklist for query: '{query}'")
        
        system_prompt = (
            "You are the expert Task Planner Agent of the Agentic Knowledge OS.\n"
            "Your objective is to decompose technical suggestions, roadmaps, and requirements into detailed action-item checklists.\n"
            "Rules:\n"
            "1. Output a clear day-by-day or step-by-step roadmap.\n"
            "2. For each task, estimate the priority (P0, P1, P2) and provide a concise title and description.\n"
            "3. Format your response in a beautiful markdown list with checkmarks (e.g. - [ ] Day 1: Task Title).\n"
            "4. Respond in Vietnamese using a clean, well-structured, and highly actionable tone."
        )
        
        prompt = f"User Request: {query}\n\nTask Breakdown:"
        
        roadmap_text = await llm_service.acomplete(prompt, system_prompt=system_prompt, temperature=0.3)
        
        # Proactively register tasks inside our SQLite database
        try:
            from app.tools.task_tools import task_db_manager
            
            # Simple heuristic parsing to auto-register tasks in SQLite
            import re
            lines = roadmap_text.split("\n")
            registered_count = 0
            
            for line in lines:
                # Find lines like "- [ ] Day 1: Build Golden Dataset" or similar
                match = re.search(r'-\s*\[\s*\]\s*(Day\s*\d+|Step\s*\d+|Task\s*\d+)?\s*:?\s*(.+)', line)
                if match:
                    title = match.group(2).strip()
                    desc = f"Auto-generated task from query: {query}"
                    priority = "P1"
                    if "P0" in line or "urgent" in line.lower() or "critical" in line.lower():
                        priority = "P0"
                    elif "P2" in line or "minor" in line.lower():
                        priority = "P2"
                        
                    if len(title) > 5:
                        task_db_manager.create_task(title, desc, priority)
                        registered_count += 1
                        
            if registered_count > 0:
                logger.info(f"Task Planner Agent automatically registered {registered_count} tasks in SQLite.")
                roadmap_text += f"\n\n*💡 Hệ thống đã tự động ghi nhận **{registered_count} công việc** vào cơ sở dữ liệu Task Manager.*"
        except Exception as e:
            logger.warning(f"Could not auto-register tasks in database: {str(e)}")
            
        return roadmap_text

task_planner_agent = TaskPlannerAgent()
