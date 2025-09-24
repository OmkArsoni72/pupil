"""
Content Worker - Background worker for content generation.
Handles async processing of content generation jobs for both AHS and Remedy routes.
"""

from typing import Dict, Any
from core.agents.content_agent import ContentAgent
from core.services.db_operations.jobs_db import update_job


class ContentWorker:
    """Background worker for content generation."""

    def __init__(self):
        self.agent = ContentAgent()

    async def process_content_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process content generation job."""
        job_id = params.get("job_id")

        if not job_id:
            raise ValueError("job_id is required for content processing")

        try:
            # Update status to in_progress
            await update_job(job_id, status="in_progress", progress=10)

            # Execute content generation workflow via the agent
            result = await self.agent.execute(params)

            # Update job status to completed
            await update_job(job_id, status="completed", progress=100, result_doc_id=result.get("db_handles", {}).get("session_id") or result.get("db_handles", {}).get("remedy_id"))

            return result

        except Exception as e:
            print(f"❌ [ContentWorker] Error processing job {job_id}: {str(e)}")
            await update_job(job_id, status="failed", error=str(e), progress=0)
            raise
