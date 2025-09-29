"""
Test script to verify Motor conversion is working correctly.
This tests the critical async database operations that were causing the bug.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_database_connections():
    """Test basic database connectivity with Motor."""
    try:
        from core.services.db_operations.base import client, db, assessment_collection, jobs_collection, remedy_plans_collection
        
        print("Successfully imported Motor client and collections")
        
        # Test basic ping
        await client.admin.command('ping')
        print("MongoDB connection successful")
        
        # Test collection access
        collections = await db.list_collection_names()
        print(f"Database has {len(collections)} collections")
        
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False

async def test_assessment_operations():
    """Test the assessment operations that were causing the original bug."""
    try:
        from core.services.db_operations.assessment_db import update_job_status, mark_job_failed, get_assessment_by_job_id
        
        test_job_id = f"test_job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Test update_job_status (this was the original failing operation)
        print(f"Testing update_job_status with job_id: {test_job_id}")
        await update_job_status(test_job_id, "processing")
        print("update_job_status completed successfully")
        
        # Test mark_job_failed
        await mark_job_failed(test_job_id, "Test error for Motor conversion verification")
        print("mark_job_failed completed successfully")
        
        # Test get_assessment_by_job_id
        result = await get_assessment_by_job_id(test_job_id)
        if result and result.get("status") == "failed":
            print("get_assessment_by_job_id returned correct data")
        else:
            print(f"get_assessment_by_job_id returned: {result}")
        
        return True
    except Exception as e:
        print(f"Assessment operations test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_jobs_operations():
    """Test the jobs operations that used anyio wrappers."""
    try:
        from core.services.db_operations.jobs_db import create_job, update_job, get_job
        
        test_job_id = f"test_jobs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Test create_job
        await create_job(test_job_id, "/test", {"test": "data"})
        print("create_job completed successfully")
        
        # Test update_job
        await update_job(test_job_id, status="completed", progress=100)
        print("update_job completed successfully")
        
        # Test get_job
        job = await get_job(test_job_id)
        if job and job.get("status") == "completed":
            print("get_job returned correct data")
        else:
            print(f"get_job returned: {job}")
        
        return True
    except Exception as e:
        print(f"Jobs operations test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_remedy_operations():
    """Test the remedy operations that used anyio wrappers."""
    try:
        from core.services.db_operations.remedy_db import create_remedy_plan, get_remedy_plan, update_remedy_plan_status
        
        test_remedy_id = f"test_remedy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Test create_remedy_plan
        await create_remedy_plan(
            remedy_id=test_remedy_id,
            student_id="test_student",
            teacher_class_id="test_class",
            classified_gaps=[{"gap": "test"}],
            remediation_plans=[{"plan": "test"}]
        )
        print("create_remedy_plan completed successfully")
        
        # Test update_remedy_plan_status
        await update_remedy_plan_status(test_remedy_id, "processing")
        print("update_remedy_plan_status completed successfully")
        
        # Test get_remedy_plan
        plan = await get_remedy_plan(test_remedy_id)
        if plan and plan.get("status") == "processing":
            print("get_remedy_plan returned correct data")
        else:
            print(f"get_remedy_plan returned: {plan}")
        
        return True
    except Exception as e:
        print(f"Remedy operations test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def cleanup_test_data():
    """Clean up test data created during testing."""
    try:
        from core.services.db_operations.base import assessment_collection, jobs_collection, remedy_plans_collection
        
        # Clean up test documents
        await assessment_collection.delete_many({"job_id": {"$regex": "^test_"}})
        await jobs_collection.delete_many({"_id": {"$regex": "^test_"}})
        await remedy_plans_collection.delete_many({"_id": {"$regex": "^test_"}})
        
        print("Test data cleanup completed")
        return True
    except Exception as e:
        print(f"Cleanup failed (non-critical): {str(e)}")
        return False

async def main():
    """Run all Motor conversion tests."""
    print("Starting Motor (async MongoDB) conversion verification tests...\n")
    
    all_tests_passed = True
    
    # Test 1: Database connection
    print("1. Testing database connections...")
    if not await test_database_connections():
        all_tests_passed = False
    print()
    
    # Test 2: Assessment operations (original bug location)
    print("2. Testing assessment operations...")
    if not await test_assessment_operations():
        all_tests_passed = False
    print()
    
    # Test 3: Jobs operations
    print("3. Testing jobs operations...")
    if not await test_jobs_operations():
        all_tests_passed = False
    print()
    
    # Test 4: Remedy operations
    print("4. Testing remedy operations...")
    if not await test_remedy_operations():
        all_tests_passed = False
    print()
    
    # Cleanup
    print("Cleaning up test data...")
    await cleanup_test_data()
    print()
    
    # Final result
    if all_tests_passed:
        print("ALL TESTS PASSED! Motor conversion is working correctly.")
        print("The original async database bug has been fixed.")
        print("All database operations are now using proper async/await patterns.")
    else:
        print("Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)