import os
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime

from core.services.db_operations.content_db import (
    append_ahs_item,
    set_ahs_object,
    create_remedy_entry,
    resolve_teacher_class_context,
)
from core.services.db_operations.base import sessions_collection, validation_logs_collection
from bson import ObjectId

# ---------------- Utility: persist & create artifact refs ----------------
async def persist_artifact(route: str, kind: str, payload: Dict[str, Any], req: Dict[str, Any]) -> str:
    """
    Persists artifacts to the database and returns a reference ID.
    Based on the actual database structure from PRD/db_structure.md
    """
    print(f"🔧 [UTILS] Persisting artifact - Route: {route}, Kind: {kind}")
    
    # Map artifact kind to DB operations according to PRD and actual DB structure
    if route == "AHS":
        session_id = req.get("session_id")
        print(f"🔧 [UTILS] AHS session_id: {session_id}")
        if not session_id:
            print(f"❌ [UTILS] Missing session_id for AHS persist; kind={kind}")
            return f"ERR_NO_SESSION_ID_{kind}"
        
        # Debug: Check if session exists
        try:
            # Motor collections are already async, use them directly
            session_exists = False
            if ObjectId.is_valid(session_id):
                doc = await sessions_collection.find_one({"_id": ObjectId(session_id)})
                if doc:
                    print(f"🔧 [UTILS] Session found with ObjectId: {session_id}")
                    session_exists = True
            if not session_exists:
                doc = await sessions_collection.find_one({"_id": session_id})
                if doc:
                    print(f"🔧 [UTILS] Session found with string ID: {session_id}")
                    session_exists = True
                else:
                    print(f"🔧 [UTILS] Session NOT found: {session_id}")
            if not session_exists:
                print(f"🔧 [UTILS] WARNING: Session {session_id} does not exist in database!")
                print(f"🔧 [UTILS] This might be a test session or the session needs to be created first")
        except Exception as e:
            print(f"🔧 [UTILS] Error checking session existence: {str(e)}")
        
        # Based on the sessions.afterHourSession structure from db_structure.md
        if kind in ("READING",):
            print(f"🔧 [UTILS] Appending to afterHourSession.texts collection")
            return await append_ahs_item(session_id, "texts", payload)
        if kind in ("WRITING",):
            print(f"🔧 [UTILS] Appending to afterHourSession.texts collection (writing prompts)")
            return await append_ahs_item(session_id, "texts", payload)
        if kind in ("WATCHING",):
            print(f"🔧 [UTILS] Appending to afterHourSession.videos collection")
            return await append_ahs_item(session_id, "videos", payload)
        if kind in ("PLAYING",):
            print(f"🔧 [UTILS] Appending to afterHourSession.games collection")
            return await append_ahs_item(session_id, "games", payload)
        if kind in ("DOING",):
            print(f"🔧 [UTILS] Appending to afterHourSession.texts collection (tasks)")
            return await append_ahs_item(session_id, "texts", payload)
        if kind in ("SOLVING",):
            print(f"🔧 [UTILS] Setting afterHourSession.practiceQuestions object")
            return await set_ahs_object(session_id, "practiceQuestions", payload)
        if kind in ("DEBATING",):
            print(f"🔧 [UTILS] Appending to afterHourSession.texts collection (debate)")
            return await append_ahs_item(session_id, "texts", payload)
        if kind in ("AUDIO",):
            print(f"🔧 [UTILS] Appending to afterHourSession.texts collection (audio scripts)")
            return await append_ahs_item(session_id, "texts", payload)
        if kind in ("ASSESSMENT",):
            print(f"🔧 [UTILS] Setting afterHourSession.assessmentQuestions object")
            return await set_ahs_object(session_id, "assessmentQuestions", payload)
    else:
        # REMEDY: create/update remedy report for student
        print(f"🔧 [UTILS] Processing REMEDY route")
        teacher_class_id = req.get("teacher_class_id")
        print(f"🔧 [UTILS] Teacher class ID: {teacher_class_id}")
        student_id = req.get("student_id")
        if not student_id:
            print(f"❌ [UTILS] Missing student_id for REMEDY persist; kind={kind}")
            return f"ERR_NO_STUDENT_ID_{kind}"
        
        ctx = await resolve_teacher_class_context(teacher_class_id)
        if not ctx:
            # Do not abort saving; proceed with minimal identifiers per PRD
            print(f"🔧 [UTILS] Context not found for teacher_class_id={teacher_class_id}; proceeding with minimal context")
            ctx = {"classId": "UNKNOWN_CLASS", "teacherId": None, "schoolId": None}
        
        print(f"🔧 [UTILS] Creating remedy entry with context: {ctx}")

        # Normalize learning gaps to a concise string for PRD field
        raw_gaps = req.get("learning_gaps") or []
        gap_codes = []
        for gap in raw_gaps:
            if isinstance(gap, str):
                gap_codes.append(gap)
            elif isinstance(gap, dict):
                code = gap.get("code")
                if code:
                    gap_codes.append(code)

        # Derive topic for the remedy entry
        derived_topic = req.get("topic") or (gap_codes[0] if gap_codes else "Remedial Support")

        # Timestamps as strings per PRD (date, time)
        now = datetime.utcnow()
        date_str = now.date().isoformat()
        time_str = now.strftime("%H:%M:%S")

        # Build PRD-aligned remedy_report entry and embed the generated artifact
        remedy_entry = {
            "date": date_str,
            "time": time_str,
            "topic": derived_topic,
            "actionTaken": f"Generated {kind} content",
            "outcome": "generated",
            "learning_gaps": ", ".join(gap_codes) if gap_codes else "",
            "remarks": "",
            "report_url": None,
            # Keep the actual artifact data under explicit fields
            "artifact_kind": kind,
            "artifact": payload,
        }

        return await create_remedy_entry(
            class_id=ctx.get("classId"),
            student_id=req.get("student_id"),
            teacher_id=ctx.get("teacherId"),
            school_id=ctx.get("schoolId"),
            entry=remedy_entry,
        )
    
    # default synthetic id
    print(f"🔧 [UTILS] Using default synthetic ID")
    return f"{route}_{kind}_{uuid4().hex[:8]}"


async def log_validation_result(mode: str, is_valid: bool, errors: Dict[str, Any] | None, metadata: Dict[str, Any] | None = None):
    """Store schema validation results for content agent payloads."""
    try:
        # Motor collections are already async, use them directly
        await validation_logs_collection.insert_one({
            "mode": mode,
            "is_valid": is_valid,
            "errors": errors or {},
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        print(f"⚠️ [UTILS] Failed to log validation result: {e}")
