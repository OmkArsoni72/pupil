"""
Test script for Remedy Agent
Demonstrates the complete flow from classified gaps to remediation plans.
"""

import asyncio
import json
from services.ai.remedy_graph import build_remedy_graph, RemedyState, GapEvidence
from services.ai.remedy_job_runner import run_remedy_job

async def test_remedy_agent():
    """
    Test the Remedy Agent with sample classified gaps.
    """
    print("🧪 [TEST] Starting Remedy Agent test...")
    
    # Sample classified gaps from Reports Agent
    classified_gaps = [
        GapEvidence(
            code="algebra_basic_equations",
            evidence=["Student cannot solve simple linear equations", "Confuses variables with numbers"]
        ),
        GapEvidence(
            code="geometry_area_calculation", 
            evidence=["Cannot calculate area of rectangles", "Doesn't understand length × width formula"]
        ),
        GapEvidence(
            code="reading_comprehension",
            evidence=["Cannot answer questions about what was read", "Struggles with main idea identification"]
        )
    ]
    
    # Test data
    student_id = "test_student_123"
    teacher_class_id = "test_class_456"
    context_refs = {
        "grade_level": "grade_7",
        "subject": "mathematics",
        "recent_performance": {
            "algebra": 0.3,
            "geometry": 0.4,
            "reading": 0.2
        }
    }
    
    print(f"🧪 [TEST] Testing with {len(classified_gaps)} classified gaps")
    print(f"🧪 [TEST] Student: {student_id}, Class: {teacher_class_id}")
    
    # Build and run Remedy Agent graph
    try:
        remedy_graph = build_remedy_graph().compile()
        
        initial_state = RemedyState(
            classified_gaps=classified_gaps,
            student_id=student_id,
            teacher_class_id=teacher_class_id,
            context_refs=context_refs
        )
        
        print("🧪 [TEST] Running Remedy Agent graph...")
        final_state = await remedy_graph.ainvoke(initial_state)
        
        print("✅ [TEST] Remedy Agent completed successfully!")
        print(f"✅ [TEST] Generated {len(final_state.final_plans)} remediation plans")
        
        # Display results
        for i, plan in enumerate(final_state.final_plans):
            print(f"\n📋 [PLAN {i+1}]")
            print(f"   Gap Type: {plan.gap_type}")
            print(f"   Selected Modes: {plan.selected_modes}")
            print(f"   Duration: {plan.estimated_duration_minutes} minutes")
            print(f"   Gap Code: {plan.content_specifications['gap_code']}")
            
            if plan.gap_type == "foundational" and "prerequisites" in plan.content_specifications:
                prereqs = plan.content_specifications["prerequisites"]
                print(f"   Prerequisites: {len(prereqs)} topics")
                for prereq in prereqs[:2]:  # Show first 2
                    print(f"     - {prereq['topic']} (Grade: {prereq['grade_level']})")
        
        print(f"\n🔗 [TEST] Content Job IDs: {final_state.content_job_ids}")
        
        return final_state
        
    except Exception as e:
        print(f"❌ [TEST] Error in Remedy Agent test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def test_gap_classification():
    """
    Test just the gap classification logic.
    """
    print("\n🔍 [CLASSIFICATION_TEST] Testing gap classification...")
    
    from services.ai.remedy_graph import gap_classifier_node, RemedyState, GapEvidence
    
    test_gaps = [
        GapEvidence(code="basic_arithmetic_facts", evidence=["Cannot recall multiplication tables"]),
        GapEvidence(code="concept_of_fractions", evidence=["Doesn't understand what fractions represent"]),
        GapEvidence(code="problem_solving_steps", evidence=["Knows concepts but can't apply them"]),
        GapEvidence(code="foundational_reading_skills", evidence=["Struggles with basic phonics"]),
        GapEvidence(code="forgot_previous_lessons", evidence=["Previously mastered but now forgotten"]),
        GapEvidence(code="lack_of_motivation", evidence=["Shows no interest in learning"])
    ]
    
    state = RemedyState(
        classified_gaps=test_gaps,
        student_id="test",
        teacher_class_id="test"
    )
    
    result = await gap_classifier_node(state, None)
    
    print("🔍 [CLASSIFICATION_TEST] Classification Results:")
    for gap_key, analysis in result["gap_analysis"].items():
        gap = analysis["original_gap"]
        gap_type = analysis["gap_type"]
        confidence = analysis["confidence"]
        print(f"   '{gap.code}' → {gap_type} (confidence: {confidence:.2f})")
    
    return result

if __name__ == "__main__":
    print("🚀 Starting Remedy Agent Tests...")
    
    # Run tests
    asyncio.run(test_gap_classification())
    asyncio.run(test_remedy_agent())
    
    print("\n✅ All tests completed!")
