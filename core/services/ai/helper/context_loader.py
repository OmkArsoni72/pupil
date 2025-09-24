from __future__ import annotations

from typing import Any, Dict, List, Optional

import anyio
from bson import ObjectId

from core.services.db_operations.base import (
    lessons_collection,
    sessions_collection,
    question_bank_collection,
)


def _safe_object_id(value: str):
    if ObjectId.is_valid(value):
        return ObjectId(value)
    return value


async def load_lesson_script(script_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not script_id:
        return None

    def _find():
        return lessons_collection.find_one({"_id": _safe_object_id(script_id)})

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, _find)
        if not doc:
            return None
        # Return only lightweight excerpt fields if present
        return {
            "_id": str(doc.get("_id")),
            "chapter": doc.get("chapterName") or doc.get("chapter") or None,
            "period": doc.get("period") or None,
            "script": (doc.get("script") or doc.get("lessonScript") or {}) if isinstance(doc.get("lessonScript"), dict) else doc.get("lessonScript"),
        }
    except Exception:
        return None


async def load_in_class_questions(question_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
    if not question_ids:
        return []

    ids = [_safe_object_id(qid) for qid in question_ids]

    def _find_many():
        cur = question_bank_collection.find({"_id": {"$in": ids}})
        return list(cur)

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(None, _find_many)
        result: List[Dict[str, Any]] = []
        for d in docs:
            result.append({
                "_id": str(d.get("_id")),
                "subject": d.get("subject"),
                "chapter": d.get("chapter"),
                "question": d.get("question"),
                "difficulty": d.get("difficulty"),
                "tags": d.get("tags") or [],
            })
        return result
    except Exception:
        return []


async def load_recent_sessions(session_ids: Optional[List[str]]) -> List[Dict[str, Any]]:
    if not session_ids:
        return []

    ids = [_safe_object_id(sid) for sid in session_ids]

    try:
        # Motor collections are already async, use them directly
        docs = await sessions_collection.find({"_id": {"$in": ids}}, {"afterHourSession": 1, "sessionTitle": 1}).to_list(length=None)
        result: List[Dict[str, Any]] = []
        for d in docs:
            result.append({
                "_id": str(d.get("_id")),
                "title": d.get("sessionTitle"),
                "afterHourSession": d.get("afterHourSession") or {},
            })
        return result
    except Exception:
        return []


async def build_context_bundle(context_refs: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve context_refs into a compact bundle for prompt conditioning."""
    lesson_script = await load_lesson_script(context_refs.get("lesson_script_id"))
    in_class_questions = await load_in_class_questions(context_refs.get("in_class_question_ids"))
    recent_sessions = await load_recent_sessions(context_refs.get("recent_session_ids"))
    return {
        "lesson_script": lesson_script,
        "in_class_questions": in_class_questions,
        "recent_sessions": recent_sessions,
        "recent_performance": context_refs.get("recent_performance") or {},
    }


