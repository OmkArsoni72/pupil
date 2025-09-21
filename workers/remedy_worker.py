"""
Remedy Worker - Background worker for remediation plan generation.
Handles async processing of remediation jobs.
"""

from typing import Dict, Any
from agents.remedy_agent import RemedyAgent
from services.db_operations.jobs_db import update_job


class RemedyWorker:
    """Background worker for remediation plan generation."""

    def __init__(self):
        self.agent = RemedyAgent()

    async def process_remedy_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process remediation plan generation job."""
        job_id = params.get("job_id")

        if not job_id:
            raise ValueError("job_id is required for remediation processing")

        try:
            # Update status to in_progress
            await update_job(job_id, status="in_progress", progress=10)

            # Execute remediation workflow via the agent
            result = await self.agent.execute(params)

            # Update job status to completed
            await update_job(job_id, status="completed", progress=100, result_doc_id=result.get("remedy_plan_id"))

            return result

        except Exception as e:
            print(f"❌ [RemedyWorker] Error processing job {job_id}: {str(e)}")
            await update_job(job_id, status="failed", error=str(e), progress=0)
            raise
