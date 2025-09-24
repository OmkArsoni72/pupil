"""
Content Agent - Main agent for generating educational content.
Handles the complete content generation workflow for both AHS and Remedy routes.
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from core.graphs.content_graph import build_content_graph


class ContentAgent(BaseAgent):
    """Content Agent for generating educational content."""

    def __init__(self):
        super().__init__("content")
        self.graph = build_content_graph

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute content generation workflow."""
        job_id = params.get("job_id") or self.generate_job_id()
        
        # Add job_id to params if not present
        params["job_id"] = job_id
        
        await self.log_agent_activity("Starting content generation", {
            "route": params.get("route"),
            "modes": params.get("modes", []),
            "job_id": job_id
        })
        
        # Build the graph with active modes
        active_modes = params.get("modes", [])
        graph = self.graph(active_modes)
        compiled_graph = graph.compile()
        
        # Invoke the compiled graph
        result = await compiled_graph.ainvoke(params)
        
        await self.log_agent_activity("Completed content generation", {
            "job_id": job_id,
            "status": "completed",
            "db_handles": result.get("db_handles", {})
        })
        
        return result
