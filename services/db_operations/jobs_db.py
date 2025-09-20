from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError

from services.db_operations.base import jobs_collection


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


async def create_job(job_id: str, route: str, payload: Dict[str, Any]) -> None:
    print(f"Creating job {job_id} in DB...")
    try:
        result = await jobs_collection.insert_one({
            "_id": job_id,
            "route": route,
            "status": "pending",
            "progress": 0,
            "error": None,
            "result_doc_id": None,
            "payload": payload,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        })
        print(f"Job {job_id} created in DB with result: {result.inserted_id}")
    except PyMongoError as e:
        print(f"PyMongoError creating job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (create_job): {str(e)}")
    except Exception as e:
        print(f"Unexpected error creating job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error (create_job): {str(e)}")


async def update_job(job_id: str, **fields: Any) -> None:
    try:
        fields["updated_at"] = _now_iso()
        await jobs_collection.update_one({"_id": job_id}, {"$set": fields})
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"DB error (update_job): {str(e)}")


async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    print(f"Getting job {job_id} from DB...")
    try:
        result = await jobs_collection.find_one({"_id": job_id})
        print(f"Job {job_id} query result: {result}")
        return result
    except PyMongoError as e:
        print(f"PyMongoError getting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (get_job): {str(e)}")
    except Exception as e:
        print(f"Unexpected error getting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error (get_job): {str(e)}")


