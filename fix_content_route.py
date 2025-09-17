#!/usr/bin/env python3
"""
Fix for the /content GET route issues
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

async def check_database_jobs():
    """Check what jobs exist in the database."""
    logger.info("🔍 Checking Database Jobs")
    logger.info("=" * 40)
    
    try:
        from services.db_operations.base import jobs_collection
        import anyio
        
        # Get all jobs from database
        def _get_jobs():
            cursor = jobs_collection.find({}).sort("created_at", -1).limit(10)
            return list(cursor)
        
        jobs = await anyio.to_thread.run_sync(_get_jobs)
        
        if not jobs:
            logger.info("📭 No jobs found in database")
            return []
        
        logger.info(f"📊 Found {len(jobs)} jobs in database:")
        
        for job in jobs[:5]:  # Show first 5 jobs
            job_id = job.get("_id")
            status = job.get("status")
            route = job.get("route")
            progress = job.get("progress")
            created_at = job.get("created_at")
            
            logger.info(f"  📋 {job_id}: {status} ({route}) - {progress}% - {created_at}")
        
        if len(jobs) > 5:
            logger.info(f"  ... and {len(jobs) - 5} more jobs")
        
        return jobs
        
    except Exception as e:
        logger.error(f"❌ Error checking database jobs: {e}")
        return []

async def test_content_route_with_job(job_id: str):
    """Test the content route with a specific job ID."""
    logger.info(f"\n🧪 Testing Content Route with Job: {job_id}")
    logger.info("=" * 50)
    
    try:
        from services.db_operations.jobs_db import get_job
        
        # Get job from database
        db_job = await get_job(job_id)
        if not db_job:
            logger.error(f"❌ Job {job_id} not found in database")
            return
        
        logger.info(f"✅ Job found: {db_job.get('status')} ({db_job.get('route')})")
        
        # Simulate the content route logic
        status_val = db_job.get("status")
        progress_val = db_job.get("progress")
        route = db_job.get("route")
        payload = db_job.get("payload", {})
        result_doc_id = db_job.get("result_doc_id")
        
        logger.info(f"📊 Status: {status_val}")
        logger.info(f"📊 Progress: {progress_val}")
        logger.info(f"📊 Route: {route}")
        logger.info(f"📊 Result doc ID: {result_doc_id}")
        logger.info(f"📊 Payload keys: {list(payload.keys())}")
        
        if status_val != "completed":
            logger.info("⚠️  Job not completed yet - would return 202")
            return {
                "job_id": job_id,
                "status": status_val,
                "progress": progress_val,
            }
        
        # Test route-specific logic
        if route == "AHS":
            logger.info("\n📚 Testing AHS Route Logic")
            
            # Get session_id from result_doc_id or payload
            session_id = None
            if result_doc_id and isinstance(result_doc_id, str) and result_doc_id.startswith("sessions/"):
                session_id = result_doc_id.split("/", 1)[1]
            if not session_id:
                session_id = payload.get("session_id")
            
            logger.info(f"📊 Session ID: {session_id}")
            
            if not session_id:
                logger.error("❌ Missing session_id for AHS route")
                return {"error": "completed job missing session_id"}
            
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
                if not doc:
                    logger.error("❌ Session not found")
                    return {"error": "session not found"}
                
                logger.info("✅ Session found")
                after_hour_session = doc.get("afterHourSession", {})
                logger.info(f"📊 After hour session keys: {list(after_hour_session.keys())}")
                
                return {
                    "job_id": job_id,
                    "route": route,
                    "content": after_hour_session,
                }
                
            except Exception as e:
                logger.error(f"❌ Error looking up session: {e}")
                return {"error": str(e)}
        
        elif route == "REMEDY":
            logger.info("\n🎯 Testing REMEDY Route Logic")
            
            # Get student_id from payload or result_doc_id
            student_id = payload.get("student_id")
            if (not student_id) and isinstance(result_doc_id, str) and result_doc_id.startswith("student_reports/"):
                student_id = result_doc_id.split("/", 1)[1]
            
            logger.info(f"📊 Student ID: {student_id}")
            
            if not student_id:
                logger.error("❌ Missing student_id for REMEDY route")
                return {"error": "completed job missing student_id"}
            
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
                if not report_doc:
                    logger.error("❌ Student report not found")
                    return {"error": "student report not found"}
                
                logger.info("✅ Student report found")
                remedy_items = (((report_doc or {}).get("report") or {}).get("remedy_report") or [])
                logger.info(f"📊 Remedy items count: {len(remedy_items)}")
                
                return {
                    "job_id": job_id,
                    "route": route,
                    "student_id": student_id,
                    "content": remedy_items,
                }
                
            except Exception as e:
                logger.error(f"❌ Error looking up student report: {e}")
                return {"error": str(e)}
        
        else:
            logger.info(f"\n❓ Unknown Route: {route}")
            return {
                "job_id": job_id,
                "route": route,
                "content": None,
            }
        
    except Exception as e:
        logger.error(f"❌ Error testing content route: {e}")
        return {"error": str(e)}

async def main():
    """Main function."""
    logger.info("🔧 Content Route Fix Analysis")
    logger.info("=" * 50)
    
    # Check database jobs
    jobs = await check_database_jobs()
    
    if not jobs:
        logger.info("📭 No jobs to test with")
        return
    
    # Test with the first completed job
    completed_jobs = [job for job in jobs if job.get("status") == "completed"]
    
    if not completed_jobs:
        logger.info("📭 No completed jobs to test with")
        # Test with the first job anyway
        test_job = jobs[0]
    else:
        test_job = completed_jobs[0]
    
    job_id = test_job.get("_id")
    logger.info(f"🧪 Testing with job: {job_id}")
    
    # Test the content route
    result = await test_content_route_with_job(job_id)
    
    logger.info(f"\n📊 Test Result:")
    logger.info(f"  {result}")
    
    # Identify common issues and provide fixes
    logger.info(f"\n🔧 Common Issues and Fixes:")
    logger.info("=" * 40)
    
    if "error" in result:
        error = result["error"]
        if "missing session_id" in error:
            logger.info("❌ Issue: Missing session_id for AHS jobs")
            logger.info("🔧 Fix: Ensure result_doc_id is set to 'sessions/{session_id}' or payload contains session_id")
        elif "missing student_id" in error:
            logger.info("❌ Issue: Missing student_id for REMEDY jobs")
            logger.info("🔧 Fix: Ensure result_doc_id is set to 'student_reports/{student_id}' or payload contains student_id")
        elif "not found" in error:
            logger.info("❌ Issue: Referenced document not found")
            logger.info("🔧 Fix: Check if the referenced session/student report exists in the database")
        else:
            logger.info(f"❌ Issue: {error}")
    
    logger.info("\n✅ Analysis complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
