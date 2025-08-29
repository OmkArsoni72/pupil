import os
from typing import Dict, Any, Literal, Optional

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

from services.ai.content_graph import (
	CHECKPOINTER,
	build_graph,
	State,
)
from services.db_operations.jobs_db import create_job, update_job
from services.ai.helper.collector_node import collector_node


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
	
	try:
		JOBS[job_id].status = "in_progress"
		print(f"🚀 [JOB_RUNNER] Updating job {job_id} to in_progress in DB...")
		await update_job(job_id, status="in_progress")
		print(f"🚀 [JOB_RUNNER] Job {job_id} updated to in_progress successfully")
		
		cfg = RunnableConfig(configurable={"thread_id": job_id})
		print(f"🚀 [JOB_RUNNER] Building graph for job {job_id} with modes: {req.get('modes', [])}")
		
		graph = build_graph(req["modes"]).compile(checkpointer=CHECKPOINTER)
		init_state = State(route=route, req=req)
		print(f"🚀 [JOB_RUNNER] Invoking graph for job {job_id}...")
		
		final_state = await graph.ainvoke(init_state, cfg)
		print(f"🚀 [JOB_RUNNER] Graph completed for job {job_id}")

		# choose final doc handle (support dict or Pydantic model)
		try:
			if isinstance(final_state, dict):
				handles = final_state.get("db_handles", {}) or {}
			else:
				handles = getattr(final_state, "db_handles", {}) or {}
		except Exception:
			handles = {}

		result_doc_id = handles.get("session_doc") or handles.get("remedy_doc")
		print(f"🚀 [JOB_RUNNER] Job {job_id} result_doc_id: {result_doc_id}")

		JOBS[job_id].status = "completed"
		JOBS[job_id].progress = 100
		JOBS[job_id].result_doc_id = result_doc_id
		print(f"🚀 [JOB_RUNNER] Updating job {job_id} to completed in DB...")
		await update_job(job_id, status="completed", progress=100, result_doc_id=result_doc_id)
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


