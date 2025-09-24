"""
Remedy Agent - Main agent for generating remediation plans and orchestrating content generation.
Handles the complete remediation workflow including gap classification, plan generation, and content orchestration.
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from graphs.remedy_graph import build_remedy_graph


class RemedyAgent(BaseAgent):
    """Remedy Agent for generating remediation plans and orchestrating content generation."""

    def __init__(self):
        super().__init__("remedy")
        self.graph = build_remedy_graph

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute remediation workflow."""
        job_id = params.get("job_id") or self.generate_job_id()
        
        # Add job_id to params if not present
        params["job_id"] = job_id
        
        await self.log_agent_activity("Starting remediation workflow", {
            "student_id": params.get("student_id"),
            "classified_gaps": len(params.get("classified_gaps", [])),
            "job_id": job_id
        })
        
        # Build the graph
        graph = self.graph()
        compiled_graph = graph.compile()
        
        # Invoke the compiled graph
        result = await compiled_graph.ainvoke(params)
        
        await self.log_agent_activity("Completed remediation workflow", {
            "job_id": job_id,
            "status": "completed",
            "final_plans": len(result.get("final_plans", []))
        })
        
        return result
