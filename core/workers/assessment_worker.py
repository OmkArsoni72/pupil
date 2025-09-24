"""
Assessment Worker - Background worker for assessment generation.
Handles async processing of assessment generation jobs.
"""

from typing import Dict, Any
from core.agents.assessment_agent import AssessmentAgent
from core.services.db_operations.assessment_db import update_job_status, mark_job_failed


class AssessmentWorker:
    """Background worker for assessment generation."""
    
    def __init__(self):
        self.agent = AssessmentAgent()
    
    async def process_assessment_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process assessment generation job."""
        job_id = params.get("job_id")
        
        if not job_id:
            raise ValueError("job_id is required for assessment processing")
        
        try:
            # Update status to in_progress
            await update_job_status(job_id, "in_progress")
            
            # Execute assessment agent
            result = await self.agent.execute(params)
            
            # Update status to completed
            await update_job_status(job_id, "completed")
            
            return result
            
        except Exception as e:
            # Mark job as failed
            await mark_job_failed(job_id, str(e))
            raise
    
    async def get_worker_status(self) -> Dict[str, Any]:
        """Get worker status information."""
        return {
            "worker_type": "assessment",
            "agent_info": self.agent.get_agent_info(),
            "status": "active"
        }
