#!/usr/bin/env python3
"""
Test script to verify the refactored content graph works correctly.
This script tests the imports and basic functionality without running actual LLM calls.
"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🧪 Testing imports...")
    
    try:
        # Test main content graph
        from core.services.ai.content_graph import build_graph, State, CHECKPOINTER
        print("✅ services.ai.content_graph imported successfully")
        
        # Test helper nodes
        from core.services.ai.helper import (
            orchestrator_node,
            node_learn_by_reading,
            node_learn_by_writing,
            node_learn_by_watching,
            node_learn_by_playing,
            node_learn_by_doing,
            node_learn_by_solving,
            node_learn_by_questioning_debating,
            node_learn_by_listening_speaking,
            node_learning_by_assessment,
            collector_node,
            persist_artifact
        )
        print("✅ All helper nodes imported successfully")
        
        # Test schemas
        from core.services.ai.schemas import (
            LearnByReadingPayload,
            LearnByWritingPayload,
            LearnByDoingPayload,
            LearnByListeningSpeakingPayload
        )
        print("✅ All schemas imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_graph_building():
    """Test that the graph can be built successfully."""
    print("\n🧪 Testing graph building...")
    
    try:
        from core.services.ai.content_graph import build_graph
        
        # Test with a simple set of modes
        test_modes = ["learn_by_reading", "learn_by_writing"]
        graph = build_graph(test_modes)
        
        print(f"✅ Graph built successfully with {len(test_modes)} modes")
        print(f"✅ Graph nodes: {list(graph.nodes.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Graph building error: {e}")
        return False

def test_state_creation():
    """Test that State objects can be created."""
    print("\n🧪 Testing State creation...")
    
    try:
        from core.services.ai.content_graph import State
        
        # Test AHS state
        ahs_state = State(
            route="AHS",
            req={
                "topic": "Test Topic",
                "context_refs": {},
                "modes": ["learn_by_reading"],
                "session_id": "test_session_123"
            }
        )
        print("✅ AHS State created successfully")
        
        # Test REMEDY state
        remedy_state = State(
            route="REMEDY",
            req={
                "learning_gaps": [{"code": "MATH_001"}],
                "modes": ["learn_by_reading"],
                "teacher_class_id": "test_teacher_class_123",
                "student_id": "test_student_123"
            }
        )
        print("✅ REMEDY State created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ State creation error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting content graph refactoring tests...\n")
    
    tests = [
        test_imports,
        test_graph_building,
        test_state_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The refactoring was successful.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
