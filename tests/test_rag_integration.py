#!/usr/bin/env python3
"""
Test script for RAG integration with Remedy Agent
Tests the enhanced RAG functionality with sample data.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from core.services.ai.enhanced_rag_integration import enhanced_rag
from core.services.ai.pinecone_client import is_pinecone_available

# Load environment variables
load_dotenv()

async def test_prerequisite_discovery():
    """Test prerequisite discovery with sample gap codes."""
    print("🧪 Testing Enhanced RAG Prerequisite Discovery...")
    
    # Test cases from your sample input
    test_cases = [
        {
            "gap_code": "basic_mechanics_missing",
            "grade_level": "grade_10",
            "subject": "physics",
            "description": "Foundational gap - missing basic mechanics concepts"
        },
        {
            "gap_code": "definitions_of_force_terms",
            "grade_level": "grade_10", 
            "subject": "physics",
            "description": "Knowledge gap - incorrect definitions"
        },
        {
            "gap_code": "vector_addition_gap",
            "grade_level": "grade_10",
            "subject": "physics", 
            "description": "Application gap - struggles with vector addition"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"   Gap Code: {test_case['gap_code']}")
        print(f"   Grade: {test_case['grade_level']}")
        print(f"   Subject: {test_case['subject']}")
        
        try:
            prerequisites = await enhanced_rag.discover_prerequisites(
                gap_code=test_case["gap_code"],
                grade_level=test_case["grade_level"],
                subject=test_case["subject"]
            )
            
            print(f"   ✅ Found {len(prerequisites)} prerequisites:")
            for j, prereq in enumerate(prerequisites[:3], 1):  # Show first 3
                source = prereq.get("source", "unknown")
                success_rate = prereq.get("success_rate", 0)
                print(f"      {j}. {prereq.get('topic', 'Unknown')} (Source: {source}, Success: {success_rate:.2f})")
            
            if len(prerequisites) > 3:
                print(f"      ... and {len(prerequisites) - 3} more")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

async def test_learning_path_generation():
    """Test learning path generation."""
    print("\n🗺️ Testing Learning Path Generation...")
    
    # Sample prerequisites
    sample_prerequisites = [
        {
            "topic": "basic_arithmetic",
            "grade_level": "grade_6",
            "priority": 1,
            "description": "Basic addition, subtraction, multiplication, division",
            "source": "vector_search",
            "success_rate": 0.85
        },
        {
            "topic": "fractions",
            "grade_level": "grade_7", 
            "priority": 2,
            "description": "Understanding fractions and decimals",
            "source": "vector_search",
            "success_rate": 0.78
        },
        {
            "topic": "algebra_basics",
            "grade_level": "grade_8",
            "priority": 3,
            "description": "Basic algebraic concepts",
            "source": "llm_fallback",
            "success_rate": 0.65
        }
    ]
    
    try:
        learning_path = await enhanced_rag.get_prerequisite_learning_path(sample_prerequisites)
        
        print(f"   ✅ Generated learning path:")
        print(f"      Total prerequisites: {learning_path['total_prerequisites']}")
        print(f"      Estimated duration: {learning_path['estimated_duration_hours']} hours")
        print(f"      Strategy: {learning_path['learning_strategy']}")
        print(f"      Assessment checkpoints: {len(learning_path['assessment_checkpoints'])}")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

async def test_system_availability():
    """Test system availability and configuration."""
    print("🔍 Testing System Availability...")
    
    # Check Pinecone availability
    pinecone_available = is_pinecone_available()
    print(f"   Pinecone: {'✅ Available' if pinecone_available else '❌ Not Available'}")
    
    # Check environment variables
    required_vars = ["PINECONE_API_KEY", "GEMINI_API_KEY"]
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ Set" if value else "❌ Missing"
        print(f"   {var}: {status}")
    
    return pinecone_available

async def main():
    """Main test function."""
    print("🧪 RAG Integration Test Suite")
    print("=" * 50)
    
    # Test system availability
    system_ok = await test_system_availability()
    
    if not system_ok:
        print("\n⚠️ System not fully configured. Some tests may fail.")
        print("Please ensure all environment variables are set and Pinecone is accessible.")
    
    # Test prerequisite discovery
    await test_prerequisite_discovery()
    
    # Test learning path generation
    await test_learning_path_generation()
    
    print("\n🎯 Test suite completed!")
    print("\nNote: If you see fallback results, it means:")
    print("- Vector database is not populated yet, OR")
    print("- No similar gaps found in the database")
    print("- This is normal for initial setup!")

if __name__ == "__main__":
    asyncio.run(main())
