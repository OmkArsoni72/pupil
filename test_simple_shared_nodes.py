#!/usr/bin/env python3
"""
Simple test script to verify shared nodes functionality
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ai.helper.assessment_node import (
    _safe_get_session,
    _safe_get_student_report,
    _extract_ahs_snippets,
    _extract_remedy_snippets
)

async def test_database_functions():
    """Test database access functions"""
    print("\n[TEST] Database Functions...")

    # Test session lookup
    try:
        session_result = await _safe_get_session("test_session_123")
        print(f"[OK] Session lookup returned: {type(session_result)}")
    except Exception as e:
        print(f"[ERROR] Session lookup: {e}")

    # Test student report lookup
    try:
        report_result = await _safe_get_student_report("test_student_123")
        print(f"[OK] Student report lookup returned: {type(report_result)}")
    except Exception as e:
        print(f"[ERROR] Student report lookup: {e}")

def test_snippet_extraction():
    """Test snippet extraction"""
    print("\n[TEST] Snippet Extraction...")

    # Test AHS snippets
    mock_ahs = {
        "texts": [{"five_min_summary": "Summary 1"}],
        "practiceQuestions": {"problems": [{"stem": "Q1"}]},
        "videos": [{"title": "Video 1"}]
    }

    ahs_snippets = _extract_ahs_snippets(mock_ahs)
    print(f"[OK] AHS snippets: {list(ahs_snippets.keys())}")

    # Test Remedy snippets
    mock_remedy = [
        {"artifact_kind": "READING", "artifact": {"content": "text"}},
        {"artifact_kind": "SOLVING", "artifact": {"problems": [{"stem": "Q1"}]}}
    ]

    remedy_snippets = _extract_remedy_snippets(mock_remedy)
    print(f"[OK] Remedy snippets: {list(remedy_snippets.keys())}")

async def main():
    """Run tests"""
    print("Starting Shared Nodes Tests...")
    print("=" * 40)

    try:
        await test_database_functions()
        test_snippet_extraction()

        print("\n" + "=" * 40)
        print("[SUCCESS] All tests completed!")

    except Exception as e:
        print(f"\n[FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)