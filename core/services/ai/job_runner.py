import os
from typing import Dict, Any, Literal, Optional

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

from core.graphs.content_graph import (
	CHECKPOINTER,
	build_content_graph as build_graph,
	ContentState as State,
)
from core.services.db_operations.jobs_db import create_job, update_job
from core.services.ai.helper.collector_node import collector_node
from core.workers.content_worker import ContentWorker


class JobStatus(BaseModel):
	job_id: str
	status: Literal["pending", "in_progress", "completed", "failed"]
	progress: Optional[int] = None
	error: Optional[str] = None
	result_doc_id: Optional[str] = None


# In-memory job store (can be replaced by Redis)
JOBS: Dict[str, JobStatus] = {}


async def run_job(job_id: str, route: Literal["AHS", "REMEDY"], req: Dict[str, Any]) -> None:
	print(f"\n🚀 [JOB_RUNNER] Starting job {job_id} for route {route}")
	print(f"🚀 [JOB_RUNNER] Job request keys: {list(req.keys())}")
	print(f"🚀 [JOB_RUNNER] Requested modes: {req.get('modes', [])}")
	
	# Initialize job in JOBS dict if not exists
	if job_id not in JOBS:
		JOBS[job_id] = JobStatus(job_id=job_id, status="pending")
		print(f"🚀 [JOB_RUNNER] Initialized job {job_id} in JOBS dict")
	
	try:
		# Use Content Worker for processing
		content_worker = ContentWorker()
		params = {
			"job_id": job_id,
			"route": route,
			"req": req,
			"modes": req.get("modes", [])
		}
		
		print(f"🚀 [JOB_RUNNER] Delegating job {job_id} to Content Worker...")
		result = await content_worker.process_content_job(params)
		print(f"🚀 [JOB_RUNNER] Content Worker completed job {job_id}")

		# Update job status based on result
		JOBS[job_id].status = "completed"
		JOBS[job_id].progress = 100
		JOBS[job_id].result_doc_id = result.get("db_handles", {}).get("session_id") or result.get("db_handles", {}).get("remedy_id")
		print(f"🚀 [JOB_RUNNER] Job {job_id} completed successfully")
		
	except Exception as e:
		print(f"❌ [JOB_RUNNER] Error in job {job_id}: {str(e)}")
		import traceback
		traceback.print_exc()

		# Attempt partial success: run collector to finalize what's already persisted
		try:
			print(f"🚀 [JOB_RUNNER] Attempting partial completion via collector for job {job_id}...")
			# Build minimal state-like object expected by collector
			class _StateShim:
				def __init__(self, route_val, req_val):
					self.route = route_val
					self.req = req_val
					self.db_handles = {}
			shim_state = _StateShim(route, req)
			# Create cfg if it wasn't created due to early error
			if 'cfg' not in locals():
				cfg = RunnableConfig(configurable={"thread_id": job_id})
			await collector_node(shim_state, cfg)
			# Try to extract handles if collector added them
			try:
				handles = getattr(shim_state, "db_handles", {}) or {}
			except Exception:
				handles = {}
			result_doc_id = handles.get("session_doc") or handles.get("remedy_doc")
			print(f"🚀 [JOB_RUNNER] Partial result_doc_id: {result_doc_id}")
			JOBS[job_id].status = "completed"
			JOBS[job_id].progress = 90
			JOBS[job_id].result_doc_id = result_doc_id
			JOBS[job_id].error = str(e)
			print(f"🚀 [JOB_RUNNER] Marking job {job_id} as completed with partial success in DB...")
			await update_job(job_id, status="completed", progress=90, result_doc_id=result_doc_id, error=str(e))
			print(f"🚀 [JOB_RUNNER] Job {job_id} recorded as partial-complete")
		except Exception as partial_err:
			print(f"❌ [JOB_RUNNER] Collector partial completion failed: {str(partial_err)}")
			# Fall back to failed state
			JOBS[job_id].status = "failed"
			JOBS[job_id].error = str(e)
			print(f"🚀 [JOB_RUNNER] Updating job {job_id} to failed in DB...")
			try:
				await update_job(job_id, status="failed", error=str(e))
				print(f"🚀 [JOB_RUNNER] Job {job_id} marked as failed in DB")
			except Exception as db_error:
				print(f"❌ [JOB_RUNNER] Failed to update job {job_id} status in DB: {str(db_error)}")


