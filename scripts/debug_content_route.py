#!/usr/bin/env python3
"""
Debug script for the /content GET route issues
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_content_route():
    """Debug the content route issues."""
    logger.info("🔍 Debugging Content Route Issues")
    logger.info("=" * 50)
    
    try:
        from services.db_operations.jobs_db import get_job
        from services.ai.job_runner import JOBS
        from services.ai.integrated_remedy_runner import INTEGRATED_REMEDY_JOBS
        
        # Get a sample job ID to test with
        logger.info("📋 Available Jobs:")
        logger.info(f"  Regular JOBS: {list(JOBS.keys())}")
        logger.info(f"  Integrated REMEDY JOBS: {list(INTEGRATED_REMEDY_JOBS.keys())}")
        
        # Test with the first available job
        test_job_id = None
        if JOBS:
            test_job_id = list(JOBS.keys())[0]
        elif INTEGRATED_REMEDY_JOBS:
            test_job_id = list(INTEGRATED_REMEDY_JOBS.keys())[0]
        
        if not test_job_id:
            logger.warning("⚠️  No jobs found in memory stores")
            return
        
        logger.info(f"🧪 Testing with job ID: {test_job_id}")
        
        # Test 1: Check job in memory stores
        logger.info("\n📊 Test 1: Memory Store Check")
        mem_job = JOBS.get(test_job_id)
        integrated_job = INTEGRATED_REMEDY_JOBS.get(test_job_id)
        
        if mem_job:
            logger.info(f"  ✅ Found in JOBS: {mem_job.status} (progress: {mem_job.progress})")
        else:
            logger.info("  ❌ Not found in JOBS")
        
        if integrated_job:
            logger.info(f"  ✅ Found in INTEGRATED_REMEDY_JOBS: {integrated_job.status} (progress: {integrated_job.progress})")
        else:
            logger.info("  ❌ Not found in INTEGRATED_REMEDY_JOBS")
        
        # Test 2: Check job in database
        logger.info("\n📊 Test 2: Database Check")
        try:
            db_job = await get_job(test_job_id)
            if db_job:
                logger.info(f"  ✅ Found in DB: {db_job.get('status')} (progress: {db_job.get('progress')})")
                logger.info(f"  📋 Route: {db_job.get('route')}")
                logger.info(f"  📋 Payload keys: {list(db_job.get('payload', {}).keys())}")
                logger.info(f"  📋 Result doc ID: {db_job.get('result_doc_id')}")
            else:
                logger.info("  ❌ Not found in DB")
        except Exception as e:
            logger.error(f"  ❌ Error getting job from DB: {e}")
        
        # Test 3: Simulate content route logic
        logger.info("\n📊 Test 3: Content Route Logic Simulation")
        
        # Replicate the logic from job_content function
        if not db_job and not mem_job:
            logger.error("  ❌ Job not found in memory or DB")
            return
        
        # Determine status
        status_val = (mem_job.status if mem_job else db_job.get("status")) or db_job.get("status")
        progress_val = (mem_job.progress if mem_job else db_job.get("progress"))
        
        logger.info(f"  📊 Status: {status_val}")
        logger.info(f"  📊 Progress: {progress_val}")
        
        if status_val != "completed":
            logger.info("  ⚠️  Job not completed yet - would return 202")
            return
        
        route = db_job.get("route") if db_job else None
        payload = db_job.get("payload") if db_job else {}
        
        logger.info(f"  📊 Route: {route}")
        logger.info(f"  📊 Payload: {payload}")
        
        # Test 4: Route-specific logic
        if route == "AHS":
            logger.info("\n📊 Test 4A: AHS Route Logic")
            result_doc_id = (mem_job.result_doc_id if mem_job else db_job.get("result_doc_id"))
            session_id = None
            
            if result_doc_id and isinstance(result_doc_id, str) and result_doc_id.startswith("sessions/"):
                session_id = result_doc_id.split("/", 1)[1]
            if not session_id:
                session_id = (payload or {}).get("session_id")
            
            logger.info(f"  📊 Result doc ID: {result_doc_id}")
            logger.info(f"  📊 Session ID: {session_id}")
            
            if not session_id:
                logger.error("  ❌ Missing session_id for AHS route")
            else:
                # Test session lookup
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
                    if doc:
                        logger.info("  ✅ Session found in DB")
                        logger.info(f"  📊 After hour session keys: {list(doc.get('afterHourSession', {}).keys())}")
                    else:
                        logger.error("  ❌ Session not found in DB")
                        
                except Exception as e:
                    logger.error(f"  ❌ Error looking up session: {e}")
        
        elif route == "REMEDY":
            logger.info("\n📊 Test 4B: REMEDY Route Logic")
            result_doc_id = (mem_job.result_doc_id if mem_job else db_job.get("result_doc_id"))
            student_id = (payload or {}).get("student_id")
            
            if (not student_id) and isinstance(result_doc_id, str) and result_doc_id.startswith("student_reports/"):
                student_id = result_doc_id.split("/", 1)[1]
            
            logger.info(f"  📊 Result doc ID: {result_doc_id}")
            logger.info(f"  📊 Student ID: {student_id}")
            
            if not student_id:
                logger.error("  ❌ Missing student_id for REMEDY route")
            else:
                # Test student report lookup
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
                    if report_doc:
                        logger.info("  ✅ Student report found in DB")
                        remedy_items = (((report_doc or {}).get("report") or {}).get("remedy_report") or [])
                        logger.info(f"  📊 Remedy items count: {len(remedy_items)}")
                    else:
                        logger.error("  ❌ Student report not found in DB")
                        
                except Exception as e:
                    logger.error(f"  ❌ Error looking up student report: {e}")
        
        else:
            logger.info(f"\n📊 Test 4C: Unknown Route: {route}")
            logger.info("  ⚠️  Unknown route - would return empty content")
        
        # Test 5: Check for common issues
        logger.info("\n📊 Test 5: Common Issues Check")
        
        # Check if job is in integrated jobs but not regular jobs
        if integrated_job and not mem_job:
            logger.warning("  ⚠️  Job is in INTEGRATED_REMEDY_JOBS but not in regular JOBS")
            logger.warning("  ⚠️  This might cause issues with the content route")
        
        # Check if result_doc_id is properly set
        if db_job and not db_job.get("result_doc_id"):
            logger.warning("  ⚠️  No result_doc_id in DB job")
        
        # Check if payload has required fields
        if route == "AHS" and not (payload or {}).get("session_id"):
            logger.warning("  ⚠️  AHS job missing session_id in payload")
        
        if route == "REMEDY" and not (payload or {}).get("student_id"):
            logger.warning("  ⚠️  REMEDY job missing student_id in payload")
        
        logger.info("\n✅ Debug analysis complete!")
        
    except Exception as e:
        logger.error(f"❌ Error in debug analysis: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function."""
    await debug_content_route()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️  Debug interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
