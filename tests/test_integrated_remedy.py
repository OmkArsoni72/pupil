"""
Test script for integrated Remedy Agent → Content Agent flow
Tests the contentGenerationForRemedies route with internal Remedy Agent integration.
"""

import asyncio
import json
from services.ai.integrated_remedy_runner import run_integrated_remedy_job, INTEGRATED_REMEDY_JOBS

async def test_integrated_remedy_flow():
    """
    Test the integrated Remedy Agent → Content Agent flow.
    """
    print("🧪 [INTEGRATED_TEST] Starting integrated remedy flow test...")
    
    # Sample classified gaps from Reports Agent
    classified_gaps = [
        {
            "code": "algebra_basic_equations",
            "evidence": ["Student cannot solve simple linear equations", "Confuses variables with numbers"]
        },
        {
            "code": "geometry_area_calculation", 
            "evidence": ["Cannot calculate area of rectangles", "Doesn't understand length × width formula"]
        }
    ]
    
    # Test data
    student_id = "test_student_123"
    teacher_class_id = "test_class_456"
    context_refs = {
        "grade_level": "grade_7",
        "subject": "mathematics",
        "recent_performance": {
            "algebra": 0.3,
            "geometry": 0.4
        }
    }
    
    job_id = "TEST_INTEGRATED_REMEDY_123"
    
    print(f"🧪 [INTEGRATED_TEST] Testing with {len(classified_gaps)} classified gaps")
    print(f"🧪 [INTEGRATED_TEST] Student: {student_id}, Class: {teacher_class_id}")
    print(f"🧪 [INTEGRATED_TEST] Job ID: {job_id}")
    
    try:
        # Initialize job status
        INTEGRATED_REMEDY_JOBS[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0
        }
        
        # Run integrated remedy job
        print("🧪 [INTEGRATED_TEST] Running integrated remedy job...")
        await run_integrated_remedy_job(
            job_id=job_id,
            classified_gaps=classified_gaps,
            student_id=student_id,
            teacher_class_id=teacher_class_id,
            context_refs=context_refs
        )
        
        # Check results
        job_status = INTEGRATED_REMEDY_JOBS.get(job_id)
        if job_status:
            print(f"✅ [INTEGRATED_TEST] Job completed with status: {job_status.status}")
            print(f"✅ [INTEGRATED_TEST] Progress: {job_status.progress}%")
            print(f"✅ [INTEGRATED_TEST] Remedy Plan ID: {job_status.remedy_plan_id}")
            print(f"✅ [INTEGRATED_TEST] Content Job IDs: {job_status.content_job_ids}")
            
            if job_status.status == "completed":
                print("✅ [INTEGRATED_TEST] Integrated remedy flow test PASSED")
                return True
            else:
                print(f"❌ [INTEGRATED_TEST] Job failed with error: {job_status.error}")
                return False
        else:
            print("❌ [INTEGRATED_TEST] Job status not found")
            return False
            
    except Exception as e:
        print(f"❌ [INTEGRATED_TEST] Error in integrated remedy flow test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_remedy_agent_integration():
    """
    Test just the Remedy Agent integration part.
    """
    print("\n🔍 [REMEDY_INTEGRATION_TEST] Testing Remedy Agent integration...")
    
    from services.ai.remedy_graph import build_remedy_graph, RemedyState, GapEvidence
    
    # Test data
    classified_gaps = [
        GapEvidence(
            code="basic_arithmetic_facts",
            evidence=["Cannot recall multiplication tables"]
        ),
        GapEvidence(
            code="concept_of_fractions",
            evidence=["Doesn't understand what fractions represent"]
        )
    ]
    
    state = RemedyState(
        classified_gaps=classified_gaps,
        student_id="test_student",
        teacher_class_id="test_class",
        context_refs={"grade_level": "grade_5"}
    )
    
    try:
        # Build and run Remedy Agent graph
        remedy_graph = build_remedy_graph().compile()
        result = await remedy_graph.ainvoke(state)
        
        print(f"🔍 [REMEDY_INTEGRATION_TEST] Remedy Agent completed")
        print(f"🔍 [REMEDY_INTEGRATION_TEST] Generated {len(result.final_plans)} remediation plans")
        
        # Display results
        for i, plan in enumerate(result.final_plans):
            print(f"\n📋 [PLAN {i+1}]")
            print(f"   Gap Type: {plan.gap_type}")
            print(f"   Selected Modes: {plan.selected_modes}")
            print(f"   Duration: {plan.estimated_duration_minutes} minutes")
            print(f"   Gap Code: {plan.content_specifications['gap_code']}")
        
        print("✅ [REMEDY_INTEGRATION_TEST] Remedy Agent integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ [REMEDY_INTEGRATION_TEST] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_flow_simulation():
    """
    Simulate the API flow for contentGenerationForRemedies.
    """
    print("\n🌐 [API_FLOW_TEST] Simulating API flow...")
    
    # Simulate the request payload
    request_payload = {
        "student_id": "api_test_student",
        "teacher_class_id": "api_test_class",
        "classified_gaps": [
            {
                "code": "reading_comprehension",
                "evidence": ["Cannot answer questions about what was read"]
            }
        ],
        "context_refs": {
            "grade_level": "grade_6",
            "subject": "english"
        }
    }
    
    print(f"🌐 [API_FLOW_TEST] Request payload: {json.dumps(request_payload, indent=2)}")
    
    # Simulate the integrated remedy job
    job_id = "API_TEST_JOB_456"
    
    try:
        await run_integrated_remedy_job(
            job_id=job_id,
            classified_gaps=request_payload["classified_gaps"],
            student_id=request_payload["student_id"],
            teacher_class_id=request_payload["teacher_class_id"],
            context_refs=request_payload["context_refs"]
        )
        
        # Check job status
        job_status = INTEGRATED_REMEDY_JOBS.get(job_id)
        if job_status and job_status.status == "completed":
            print("✅ [API_FLOW_TEST] API flow simulation PASSED")
            print(f"✅ [API_FLOW_TEST] Final job status: {job_status.status}")
            return True
        else:
            print(f"❌ [API_FLOW_TEST] API flow failed: {job_status.error if job_status else 'No job status'}")
            return False
            
    except Exception as e:
        print(f"❌ [API_FLOW_TEST] Error in API flow simulation: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Integrated Remedy Agent Tests...")
    
    # Run tests
    results = []
    results.append(asyncio.run(test_remedy_agent_integration()))
    results.append(asyncio.run(test_integrated_remedy_flow()))
    results.append(asyncio.run(test_api_flow_simulation()))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Integrated Remedy Agent is working correctly.")
    else:
        print("❌ Some tests FAILED. Please check the implementation.")
    
    print("\n✅ Integrated Remedy Agent testing completed!")
