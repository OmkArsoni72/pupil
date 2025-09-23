#!/usr/bin/env python3
"""
Fixed Content Route Implementation
Addresses common issues with the /v1/jobs/{job_id}/content route
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedContentRoute:
    """
    Fixed implementation of the content route with better error handling and debugging.
    """
    
    def __init__(self):
        self.pinecone_available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if required services are available."""
        try:
            from services.ai.pinecone_client import is_pinecone_available
            self.pinecone_available = is_pinecone_available()
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
    
    async def get_job_content(self, job_id: str, response: Response) -> Dict[str, Any]:
        """
        Fixed implementation of the job content route.
        """
        logger.info(f"🔍 Getting content for job: {job_id}")
        
        try:
            from services.db_operations.jobs_db import get_job
            from services.ai.job_runner import JOBS
            from services.ai.integrated_remedy_runner import INTEGRATED_REMEDY_JOBS
            
            # Step 1: Get job from all possible sources
            db_job = await get_job(job_id)
            mem_job = JOBS.get(job_id)
            integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
            
            logger.info(f"📊 Job sources: DB={bool(db_job)}, MEM={bool(mem_job)}, INT={bool(integrated_job)}")
            
            # Step 2: Determine the authoritative job record
            if not db_job and not mem_job and not integrated_job:
                logger.error(f"❌ Job {job_id} not found in any source")
                raise HTTPException(404, "job not found")
            
            # Prefer DB job for complete record, fallback to memory
            authoritative_job = db_job or mem_job or integrated_job
            
            # Step 3: Determine status and progress
            if db_job:
                status_val = db_job.get("status")
                progress_val = db_job.get("progress", 0)
                route = db_job.get("route")
                payload = db_job.get("payload", {})
                result_doc_id = db_job.get("result_doc_id")
            elif mem_job:
                status_val = mem_job.status
                progress_val = mem_job.progress
                route = getattr(mem_job, 'route', None)
                payload = getattr(mem_job, 'payload', {})
                result_doc_id = getattr(mem_job, 'result_doc_id', None)
            else:  # integrated_job
                status_val = integrated_job.status
                progress_val = integrated_job.progress
                route = "REMEDY"  # Integrated jobs are always REMEDY
                payload = {}  # Integrated jobs don't store payload in memory
                result_doc_id = integrated_job.remedy_plan_id
            
            logger.info(f"📊 Job status: {status_val}, progress: {progress_val}, route: {route}")
            
            # Step 4: Check if job is completed
            if status_val != "completed":
                logger.info(f"⚠️  Job {job_id} not completed yet: {status_val}")
                response.status_code = 202
                return {
                    "job_id": job_id,
                    "status": status_val,
                    "progress": progress_val,
                    "message": "Job not completed yet"
                }
            
            # Step 5: Route-specific content retrieval
            if route == "AHS":
                return await self._get_ahs_content(job_id, payload, result_doc_id)
            elif route == "REMEDY":
                return await self._get_remedy_content(job_id, payload, result_doc_id, integrated_job)
            else:
                logger.warning(f"⚠️  Unknown route: {route}")
                return {
                    "job_id": job_id,
                    "route": route,
                    "content": None,
                    "message": f"Unknown route: {route}"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error getting content for job {job_id}: {e}")
            raise HTTPException(500, f"Internal server error: {str(e)}")
    
    async def _get_ahs_content(self, job_id: str, payload: Dict[str, Any], result_doc_id: Optional[str]) -> Dict[str, Any]:
        """Get AHS (After Hour Session) content."""
        logger.info(f"📚 Getting AHS content for job: {job_id}")
        
        # Get session_id from result_doc_id or payload
        session_id = None
        if result_doc_id and isinstance(result_doc_id, str) and result_doc_id.startswith("sessions/"):
            session_id = result_doc_id.split("/", 1)[1]
        if not session_id:
            session_id = payload.get("session_id")
        
        logger.info(f"📊 Session ID: {session_id}")
        
        if not session_id:
            logger.error("❌ Missing session_id for AHS route")
            raise HTTPException(500, "completed job missing session_id")
        
        # Get session from database
        try:
            from services.db_operations.base import sessions_collection
            from bson import ObjectId
            import anyio
            
            def _find():
                if ObjectId.is_valid(session_id):
                    doc = sessions_collection.find_one({"_id": ObjectId(session_id)}, {"afterHourSession": 1})
                    if doc:
                        return doc
                return sessions_collection.find_one({"_id": session_id}, {"afterHourSession": 1})
            
            doc = await anyio.to_thread.run_sync(_find)
            if not doc:
                logger.error(f"❌ Session {session_id} not found")
                raise HTTPException(404, "session not found")
            
            after_hour_session = doc.get("afterHourSession", {})
            logger.info(f"✅ AHS content retrieved: {len(after_hour_session)} keys")
            
            return {
                "job_id": job_id,
                "route": "AHS",
                "session_id": session_id,
                "content": after_hour_session,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error retrieving AHS content: {e}")
            raise HTTPException(500, f"Error retrieving session content: {str(e)}")
    
    async def _get_remedy_content(self, job_id: str, payload: Dict[str, Any], result_doc_id: Optional[str], integrated_job: Optional[Any]) -> Dict[str, Any]:
        """Get REMEDY content."""
        logger.info(f"🎯 Getting REMEDY content for job: {job_id}")
        
        # Get student_id from payload or result_doc_id
        student_id = payload.get("student_id")
        if (not student_id) and isinstance(result_doc_id, str) and result_doc_id.startswith("student_reports/"):
            student_id = result_doc_id.split("/", 1)[1]
        
        logger.info(f"📊 Student ID: {student_id}")
        
        if not student_id:
            logger.error("❌ Missing student_id for REMEDY route")
            raise HTTPException(500, "completed job missing student_id")
        
        # Get student report from database
        try:
            from services.db_operations.base import student_reports_collection
            import anyio
            from bson import ObjectId
            
            def _find_student_report():
                # Try by studentId (string)
                doc = student_reports_collection.find_one({"studentId": student_id}, {"report.remedy_report": 1})
                if doc:
                    return doc
                # Try by studentId as ObjectId (if DB uses ObjectId)
                if ObjectId.is_valid(student_id):
                    doc = student_reports_collection.find_one({"studentId": ObjectId(student_id)}, {"report.remedy_report": 1})
                    if doc:
                        return doc
                # As a last resort, if caller passed an actual document id as student_id, try _id
                if ObjectId.is_valid(student_id):
                    doc = student_reports_collection.find_one({"_id": ObjectId(student_id)}, {"report.remedy_report": 1})
                    if doc:
                        return doc
                return None
            
            report_doc = await anyio.to_thread.run_sync(_find_student_report)
            if not report_doc:
                logger.error(f"❌ Student report for {student_id} not found")
                raise HTTPException(404, "student report not found")
            
            remedy_items = (((report_doc or {}).get("report") or {}).get("remedy_report") or [])
            logger.info(f"✅ REMEDY content retrieved: {len(remedy_items)} items")
            
            return {
                "job_id": job_id,
                "route": "REMEDY",
                "student_id": student_id,
                "content": remedy_items,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error retrieving REMEDY content: {e}")
            raise HTTPException(500, f"Error retrieving student report: {str(e)}")
    
    async def debug_job_status(self, job_id: str) -> Dict[str, Any]:
        """Debug endpoint to check job status across all sources."""
        logger.info(f"🔍 Debugging job status for: {job_id}")
        
        try:
            from services.db_operations.jobs_db import get_job
            from services.ai.job_runner import JOBS
            from services.ai.integrated_remedy_runner import INTEGRATED_REMEDY_JOBS
            
            # Check all sources
            db_job = await get_job(job_id)
            mem_job = JOBS.get(job_id)
            integrated_job = INTEGRATED_REMEDY_JOBS.get(job_id)
            
            debug_info = {
                "job_id": job_id,
                "sources": {
                    "database": {
                        "found": bool(db_job),
                        "status": db_job.get("status") if db_job else None,
                        "route": db_job.get("route") if db_job else None,
                        "progress": db_job.get("progress") if db_job else None,
                        "result_doc_id": db_job.get("result_doc_id") if db_job else None,
                        "payload_keys": list(db_job.get("payload", {}).keys()) if db_job else []
                    },
                    "memory": {
                        "found": bool(mem_job),
                        "status": mem_job.status if mem_job else None,
                        "progress": mem_job.progress if mem_job else None,
                        "error": mem_job.error if mem_job else None,
                        "result_doc_id": getattr(mem_job, 'result_doc_id', None) if mem_job else None
                    },
                    "integrated": {
                        "found": bool(integrated_job),
                        "status": integrated_job.status if integrated_job else None,
                        "progress": integrated_job.progress if integrated_job else None,
                        "error": integrated_job.error if integrated_job else None,
                        "remedy_plan_id": integrated_job.remedy_plan_id if integrated_job else None,
                        "content_job_ids": integrated_job.content_job_ids if integrated_job else []
                    }
                }
            }
            
            return debug_info
            
        except Exception as e:
            logger.error(f"❌ Error debugging job {job_id}: {e}")
            return {"error": str(e)}

# Create a simple test function
async def test_fixed_content_route():
    """Test the fixed content route with a sample job."""
    logger.info("🧪 Testing Fixed Content Route")
    logger.info("=" * 40)
    
    try:
        from services.db_operations.base import jobs_collection
        import anyio
        
        # Get a sample job from database
        def _get_sample_job():
            cursor = jobs_collection.find({"status": "completed"}).limit(1)
            return list(cursor)
        
        jobs = await anyio.to_thread.run_sync(_get_sample_job)
        
        if not jobs:
            logger.info("📭 No completed jobs found for testing")
            return
        
        test_job = jobs[0]
        job_id = test_job.get("_id")
        
        logger.info(f"🧪 Testing with job: {job_id}")
        
        # Test the fixed content route
        fixed_route = FixedContentRoute()
        
        # Test debug endpoint first
        debug_info = await fixed_route.debug_job_status(job_id)
        logger.info(f"📊 Debug info: {debug_info}")
        
        # Test content retrieval
        from fastapi import Response
        response = Response()
        content_result = await fixed_route.get_job_content(job_id, response)
        
        logger.info(f"✅ Content retrieved successfully:")
        logger.info(f"  Job ID: {content_result.get('job_id')}")
        logger.info(f"  Route: {content_result.get('route')}")
        logger.info(f"  Content keys: {list(content_result.get('content', {}).keys()) if isinstance(content_result.get('content'), dict) else len(content_result.get('content', []))}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function."""
    await test_fixed_content_route()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️  Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


