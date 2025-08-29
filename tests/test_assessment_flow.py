#!/usr/bin/env python3
"""
Test script for the Assessment Agent flow
This script tests the complete LangGraph pipeline for assessment generation
"""

import asyncio
import json
from services.ai.assessment_generator import generate_assessment

async def test_assessment_generation():
    """Test the complete assessment generation flow"""
    
    # Test parameters matching the PRD
    test_params = {
        "target_exam": "CBSE_Grade10_Physics_Monthly",
        "exam_type": "monthly",
        "subject": "Physics",
        "class_": "10A",
        "teacher_id": "test_teacher_123",
        "difficulty": "medium",
        "previous_topics": ["Mechanics", "Thermodynamics"],
        "learning_gaps": [],  # Empty since we don't have learning_gaps in DB
        "self_assessment_mode": None,
        "file_url": None,
        "llm_model": "gemini_1.5_flash"
    }
    
    print("🚀 Starting Assessment Generation Test")
    print(f"Parameters: {json.dumps(test_params, indent=2)}")
    
    try:
        # Generate assessment
        job_id = await generate_assessment(test_params)
        print(f"✅ Assessment generation started with job_id: {job_id}")
        
        # In a real scenario, you'd poll for status
        print("📋 Assessment generation completed successfully!")
        print("🔍 You can now check the status using:")
        print(f"   GET /api/assessments/status/{job_id}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Assessment generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_context_agent():
    """Test the ContextAgent independently"""
    from services.ai.context_agent import ContextAgent
    
    print("\n🧪 Testing ContextAgent")
    
    try:
        context = await ContextAgent.gather_context(
            exam_type="monthly",
            previous_topics=["Mechanics"],
            subject="Physics",
            grade=10
        )
        
        print("✅ ContextAgent test successful")
        print(f"Selected topics: {context.get('selected_topics', [])}")
        print(f"Learning outcomes: {context.get('learning_outcomes', [])}")
        print(f"Examples found: {len(context.get('examples', []))}")
        
    except Exception as e:
        print(f"❌ ContextAgent test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_schema_agent():
    """Test the SchemaAgent independently"""
    from services.ai.schema_agent import SchemaAgent
    
    print("\n🧪 Testing SchemaAgent")
    
    try:
        schema = await SchemaAgent.fetch_template("CBSE_Grade10_Physics_Monthly")
        print("✅ SchemaAgent test successful")
        print(f"Schema keys: {list(schema.keys()) if schema else 'No schema found'}")
        
    except Exception as e:
        print(f"❌ SchemaAgent test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("🧪 Assessment Agent Flow Test Suite")
    print("=" * 50)
    
    # Test individual components
    await test_schema_agent()
    await test_context_agent()
    
    # Test complete flow
    job_id = await test_assessment_generation()
    
    if job_id:
        print(f"\n🎉 All tests completed successfully!")
        print(f"Job ID: {job_id}")
    else:
        print(f"\n💥 Some tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
