#!/usr/bin/env python3
"""
Utility to create a test session for debugging the content generation.
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def create_test_session():
    """Create a test session for debugging."""
    try:
        from services.db_operations.base import sessions_collection
        from bson import ObjectId
        
        print("🔧 [TEST] Creating test session...")
        
        # Create a test session document
        test_session = {
            "_id": ObjectId("687747d1ca5bf0d745f5d3a5"),  # Use the same ID from the error
            "teacherClassDataId": "test_teacher_class_123",
            "chapterId": "test_chapter_123",
            "lessonNumber": 1,
            "sessionTitle": "Test Session for Content Generation",
            "sessionDate": datetime.now(),
            "status": "pending",
            "learningOutcomes": ["Test learning outcome"],
            "inClassQuestions": {},
            "lessonScript": {
                "scriptId": "test_script_123",
                "creationMethod": "manual",
                "estimatedReadingTimeInMinutes": 5,
                "scriptContent": "Test script content"
            },
            "afterHourSession": {
                "texts": [],
                "videos": [],
                "games": [],
                "practiceQuestions": {},
                "assessmentQuestions": {},
                "status": "pending"
            }
        }
        
        # Check if session already exists
        existing = sessions_collection.find_one({"_id": test_session["_id"]})
        if existing:
            print(f"🔧 [TEST] Session {test_session['_id']} already exists!")
            print(f"🔧 [TEST] Session title: {existing.get('sessionTitle', 'N/A')}")
            print(f"🔧 [TEST] Session status: {existing.get('status', 'N/A')}")
            return str(test_session["_id"])
        
        # Insert the test session
        result = sessions_collection.insert_one(test_session)
        print(f"🔧 [TEST] Test session created successfully!")
        print(f"🔧 [TEST] Session ID: {result.inserted_id}")
        print(f"🔧 [TEST] Session title: {test_session['sessionTitle']}")
        
        return str(result.inserted_id)
        
    except Exception as e:
        print(f"❌ [TEST] Error creating test session: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import asyncio
    session_id = asyncio.run(create_test_session())
    if session_id:
        print(f"🔧 [TEST] Use session ID: {session_id} for testing content generation")
