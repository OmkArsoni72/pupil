from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException
from pymongo.errors import PyMongoError

from services.db_operations.base import (
    sessions_collection,
    student_reports_collection,
    teacher_class_data_collection,
)
from bson import ObjectId


# ---------------- Helpers: AHS (sessions.afterHourSession) ----------------
async def append_ahs_item(session_id: str, key: str, item: Dict[str, Any]) -> str:
    try:
        content_id = f"{key}_{uuid4().hex[:8]}"
        update_key = f"afterHourSession.{key}"
        # Try update with ObjectId, then with string id
        matched_count = 0
        if ObjectId.is_valid(session_id):
            res = await sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$push": {update_key: {"id": content_id, **item}}},
                upsert=False,
            )
            matched_count += res.matched_count
            if matched_count == 0:
                res2 = await sessions_collection.update_one(
                    {"_id": session_id},
                    {"$push": {update_key: {"id": content_id, **item}}},
                    upsert=False,
                )
                matched_count += res2.matched_count
        else:
            res = await sessions_collection.update_one(
                {"_id": session_id},
                {"$push": {update_key: {"id": content_id, **item}}},
                upsert=False,
            )
            matched_count = res.matched_count
        if matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return content_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"DB error (append_ahs_item): {str(e)}")


async def set_ahs_object(session_id: str, key: str, value: Dict[str, Any]) -> str:
    try:
        content_id = f"{key}_{uuid4().hex[:8]}"
        update_key = f"afterHourSession.{key}"
        # Try update with ObjectId, then with string id
        matched_count = 0
        if ObjectId.is_valid(session_id):
            res = await sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {update_key: {"id": content_id, **value}}},
                upsert=False,
            )
            matched_count += res.matched_count
            if matched_count == 0:
                res2 = await sessions_collection.update_one(
                    {"_id": session_id},
                    {"$set": {update_key: {"id": content_id, **value}}},
                    upsert=False,
                )
                matched_count += res2.matched_count
        else:
            res = await sessions_collection.update_one(
                {"_id": session_id},
                {"$set": {update_key: {"id": content_id, **value}}},
                upsert=False,
            )
            matched_count = res.matched_count
        if matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return content_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"DB error (set_ahs_object): {str(e)}")


async def set_ahs_status(session_id: str, status: str) -> None:
    try:
        # Try update with ObjectId, then with string id
        matched_count = 0
        if ObjectId.is_valid(session_id):
            res = await sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"afterHourSession.status": status}},
                upsert=False,
            )
            matched_count += res.matched_count
            if matched_count == 0:
                res2 = await sessions_collection.update_one(
                    {"_id": session_id},
                    {"$set": {"afterHourSession.status": status}},
                    upsert=False,
                )
                matched_count += res2.matched_count
        else:
            res = await sessions_collection.update_one(
                {"_id": session_id},
                {"$set": {"afterHourSession.status": status}},
                upsert=False,
            )
            matched_count = res.matched_count
        if matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"DB error (set_ahs_status): {str(e)}")


# ---------------- Helpers: Remedy (student_reports.remedy_report) ----------------
async def create_remedy_entry(
    class_id: str,
    student_id: str,
    teacher_id: str,
    school_id: str,
    entry: Dict[str, Any],
) -> str:
    try:
        remedy_id = f"REM_{uuid4().hex[:8]}"
        filter_q = {"classId": class_id, "studentId": student_id}
        update_doc = {
            "$setOnInsert": {
                "classId": class_id,
                "studentId": student_id,
                "teacherId": teacher_id,
                "schoolId": school_id,
            },
            "$push": {
                "report.remedy_report": {
                    "remedyId": remedy_id,
                    **entry,
                }
            },
        }

        await student_reports_collection.update_one(
            filter_q, update_doc, upsert=True
        )
        return remedy_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"DB error (create_remedy_entry): {str(e)}")


async def resolve_teacher_class_context(teacher_class_id: str) -> Optional[Dict[str, Any]]:
    try:
        filter_id = ObjectId(teacher_class_id) if ObjectId.is_valid(teacher_class_id) else teacher_class_id
        doc = await teacher_class_data_collection.find_one({"_id": filter_id})
        if not doc:
            return None
        school = doc.get("school", {})
        return {
            "classId": doc.get("classId") or doc.get("className"),
            "teacherId": doc.get("teacherId"),
            "schoolId": school.get("schoolId") if isinstance(school, dict) else None,
        }
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"DB error (resolve_teacher_class_context): {str(e)}")


