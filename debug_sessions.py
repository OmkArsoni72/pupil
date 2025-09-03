#!/usr/bin/env python3
"""
Debug script to check the sessions collection and understand the database structure.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def debug_sessions():
    """Debug the sessions collection to understand the structure."""
    try:
        from services.db_operations.base import sessions_collection
        from bson import ObjectId
        
        print("🔍 [DEBUG] Checking sessions collection...")
        
        # Count total sessions
        total_sessions = sessions_collection.count_documents({})
        print(f"🔍 [DEBUG] Total sessions in database: {total_sessions}")
        
        if total_sessions == 0:
            print("🔍 [DEBUG] No sessions found in database!")
            print("🔍 [DEBUG] This explains why the session ID is not found")
            return
        
        # Get a few sample sessions
        sample_sessions = list(sessions_collection.find().limit(3))
        print(f"🔍 [DEBUG] Sample sessions:")
        
        for i, session in enumerate(sample_sessions):
            print(f"🔍 [DEBUG] Session {i+1}:")
            print(f"  - _id: {session.get('_id')}")
            print(f"  - sessionTitle: {session.get('sessionTitle', 'N/A')}")
            print(f"  - status: {session.get('status', 'N/A')}")
            print(f"  - afterHourSession: {session.get('afterHourSession', 'N/A')}")
            print()
        
        # Check if the specific session ID exists
        test_session_id = "687747d1ca5bf0d745f5d3a5"
        print(f"🔍 [DEBUG] Checking if session {test_session_id} exists...")
        
        if ObjectId.is_valid(test_session_id):
            doc = sessions_collection.find_one({"_id": ObjectId(test_session_id)})
            if doc:
                print(f"🔍 [DEBUG] Session {test_session_id} found with ObjectId!")
                print(f"  - sessionTitle: {doc.get('sessionTitle', 'N/A')}")
                print(f"  - status: {doc.get('status', 'N/A')}")
            else:
                print(f"🔍 [DEBUG] Session {test_session_id} NOT found with ObjectId")
        
        doc = sessions_collection.find_one({"_id": test_session_id})
        if doc:
            print(f"🔍 [DEBUG] Session {test_session_id} found with string ID!")
        else:
            print(f"🔍 [DEBUG] Session {test_session_id} NOT found with string ID either")
        
        # Check the structure of afterHourSession field
        print(f"🔍 [DEBUG] Checking afterHourSession structure...")
        session_with_ahs = sessions_collection.find_one({"afterHourSession": {"$exists": True}})
        if session_with_ahs:
            ahs = session_with_ahs.get("afterHourSession", {})
            print(f"🔍 [DEBUG] afterHourSession structure:")
            print(f"  - texts: {type(ahs.get('texts', []))} - {len(ahs.get('texts', []))} items")
            print(f"  - videos: {type(ahs.get('videos', []))} - {len(ahs.get('videos', []))} items")
            print(f"  - games: {type(ahs.get('games', []))} - {len(ahs.get('games', []))} items")
            print(f"  - practiceQuestions: {type(ahs.get('practiceQuestions', {}))}")
            print(f"  - assessmentQuestions: {type(ahs.get('assessmentQuestions', {}))}")
            print(f"  - status: {ahs.get('status', 'N/A')}")
        else:
            print(f"🔍 [DEBUG] No sessions with afterHourSession field found")
        
    except Exception as e:
        print(f"❌ [DEBUG] Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_sessions())
