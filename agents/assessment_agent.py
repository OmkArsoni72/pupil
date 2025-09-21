"""
Assessment Agent - Main agent for generating educational assessments.
Handles the complete assessment generation workflow.
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from graphs.assessment_graph import build_assessment_graph


class AssessmentAgent(BaseAgent):
    """Assessment Agent for generating educational assessments."""
    
    def __init__(self):
        super().__init__("assessment")
        self.graph = build_assessment_graph()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assessment generation workflow."""
        job_id = params.get("job_id") or self.generate_job_id()
        
        # Add job_id to params if not present
        params["job_id"] = job_id
        
        await self.log_agent_activity("Starting assessment generation", {
            "target_exam": params.get("target_exam"),
            "exam_type": params.get("exam_type"),
            "subject": params.get("subject")
        })
        
        try:
            # Execute the graph
            result = await self.graph.ainvoke(params)
            
            await self.log_agent_activity("Assessment generation completed", {
                "job_id": job_id,
                "questions_generated": len(result.get("questions", []))
            })
            
            return {
                "job_id": job_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            await self.log_agent_activity("Assessment generation failed", {
                "job_id": job_id,
                "error": str(e)
            })
            raise
    
    async def get_assessment_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an assessment generation job."""
        # This would typically query the database for job status
        # For now, return basic status info
        return {
            "job_id": job_id,
            "agent": self.agent_name,
            "status": "checking"
        }
