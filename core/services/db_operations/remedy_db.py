from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from core.services.db_operations.base import remedy_plans_collection
from datetime import datetime

async def create_remedy_plan(
    remedy_id: str,
    student_id: str,
    teacher_class_id: str,
    classified_gaps: List[Dict[str, Any]],
    remediation_plans: List[Dict[str, Any]],
    context_refs: Optional[Dict[str, Any]] = None,
    prerequisite_discoveries: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new remedy plan document in the database.
    """
    try:
        remedy_doc = {
            "_id": remedy_id,
            "student_id": student_id,
            "teacher_class_id": teacher_class_id,
            "classified_gaps": classified_gaps,
            "remediation_plans": remediation_plans,
            "context_refs": context_refs or {},
            "prerequisite_discoveries": prerequisite_discoveries or {},
            "status": "created",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "content_job_ids": [],
            "completion_status": {
                "total_plans": len(remediation_plans),
                "completed_plans": 0,
                "failed_plans": 0
            }
        }
        
        result = await remedy_plans_collection.insert_one(remedy_doc)
        print(f"[REMEDY_DB] Created remedy plan: {remedy_id}")
        return str(result.inserted_id)
        
    except Exception as e:
        print(f"[REMEDY_DB] Error creating remedy plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (create_remedy_plan): {str(e)}")

async def update_remedy_plan_status(
    remedy_id: str,
    status: str,
    content_job_ids: Optional[List[str]] = None,
    completion_status: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the status of a remedy plan.
    """
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if content_job_ids is not None:
            update_data["content_job_ids"] = content_job_ids
            
        if completion_status is not None:
            update_data["completion_status"] = completion_status
        
        result = await remedy_plans_collection.update_one(
            {"_id": remedy_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Remedy plan not found")
        
        print(f"[REMEDY_DB] Updated remedy plan {remedy_id} status to {status}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[REMEDY_DB] Error updating remedy plan status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (update_remedy_plan_status): {str(e)}")

async def get_remedy_plan(remedy_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a remedy plan by ID.
    """
    try:
        result = await remedy_plans_collection.find_one({"_id": remedy_id})
        if result:
            result["_id"] = str(result["_id"])  # Convert ObjectId to string
        return result
        
    except Exception as e:
        print(f"[REMEDY_DB] Error getting remedy plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (get_remedy_plan): {str(e)}")

async def get_latest_remedy_plan_for(student_id: str, teacher_class_id: str) -> Optional[Dict[str, Any]]:
    """Find the most recent remedy plan for a given student and teacher_class_id."""
    try:
        cursor = remedy_plans_collection.find({
            "student_id": student_id,
            "teacher_class_id": teacher_class_id
        }).sort("created_at", -1).limit(1)
        docs = await cursor.to_list(length=1)
        result = docs[0] if docs else None
        if result:
            result["_id"] = str(result["_id"])
        return result
    except Exception as e:
        print(f"[REMEDY_DB] Error getting latest remedy plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (get_latest_remedy_plan_for): {str(e)}")

async def get_remedy_plans_by_student(student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get remedy plans for a specific student.
    """
    try:
        cursor = remedy_plans_collection.find(
            {"student_id": student_id}
        ).sort("created_at", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        
        # Convert ObjectIds to strings
        for result in results:
            result["_id"] = str(result["_id"])
        
        print(f"[REMEDY_DB] Found {len(results)} remedy plans for student {student_id}")
        return results
        
    except Exception as e:
        print(f"[REMEDY_DB] Error getting remedy plans by student: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (get_remedy_plans_by_student): {str(e)}")

async def update_remedy_plan_completion(
    remedy_id: str,
    plan_index: int,
    status: str,  # "completed" or "failed"
    content_result: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the completion status of a specific remediation plan within a remedy plan.
    """
    try:
        # Get current completion status
        doc = await remedy_plans_collection.find_one({"_id": remedy_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Remedy plan not found")
        
        completion_status = doc.get("completion_status", {
            "total_plans": 0,
            "completed_plans": 0,
            "failed_plans": 0
        })
        
        # Update counts
        if status == "completed":
            completion_status["completed_plans"] += 1
        elif status == "failed":
            completion_status["failed_plans"] += 1
        
        # Update the specific plan with result
        update_data = {
            f"remediation_plans.{plan_index}.completion_status": status,
            f"remediation_plans.{plan_index}.completed_at": datetime.utcnow(),
            "completion_status": completion_status,
            "updated_at": datetime.utcnow()
        }
        
        if content_result:
            update_data[f"remediation_plans.{plan_index}.content_result"] = content_result
        
        result = await remedy_plans_collection.update_one(
            {"_id": remedy_id},
            {"$set": update_data}
        )
        if result and result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Remedy plan not found")
        
        print(f"[REMEDY_DB] Updated remedy plan {remedy_id} plan {plan_index} to {status}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[REMEDY_DB] Error updating remedy plan completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (update_remedy_plan_completion): {str(e)}")

async def get_remedy_plan_summary(remedy_id: str) -> Dict[str, Any]:
    """
    Get a summary of a remedy plan including completion status.
    """
    try:
        remedy_plan = await get_remedy_plan(remedy_id)
        if not remedy_plan:
            raise HTTPException(status_code=404, detail="Remedy plan not found")
        
        completion_status = remedy_plan.get("completion_status", {})
        remediation_plans = remedy_plan.get("remediation_plans", [])
        
        # Count gap types
        gap_types = {}
        for plan in remediation_plans:
            gap_type = plan.get("gap_type", "unknown")
            gap_types[gap_type] = gap_types.get(gap_type, 0) + 1
        
        summary = {
            "remedy_id": remedy_id,
            "student_id": remedy_plan.get("student_id"),
            "teacher_class_id": remedy_plan.get("teacher_class_id"),
            "status": remedy_plan.get("status"),
            "created_at": remedy_plan.get("created_at"),
            "updated_at": remedy_plan.get("updated_at"),
            "total_plans": completion_status.get("total_plans", 0),
            "completed_plans": completion_status.get("completed_plans", 0),
            "failed_plans": completion_status.get("failed_plans", 0),
            "gap_types": gap_types,
            "content_job_ids": remedy_plan.get("content_job_ids", [])
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[REMEDY_DB] Error getting remedy plan summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DB error (get_remedy_plan_summary): {str(e)}")
