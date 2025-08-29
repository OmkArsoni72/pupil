from bson import ObjectId

from fastapi import APIRouter, HTTPException

from models.teacher import Teacher, Lecture
from services.calendar import create_event, delete_event
from services.db_operations.base import db

router = APIRouter()


@router.post("/teacher/")
async def create_teacher(teacher: Teacher):
    teacher_dict = teacher.model_dump()
    result = await db.teachers.insert_one(teacher_dict)
    teacher_dict["_id"] = str(result.inserted_id)
    return teacher_dict


@router.post("/teacher/{teacher_id}/lecture")
async def add_lecture(teacher_id: str, lecture: Lecture):
    teacher = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    for existing in teacher.get("lectures", []):
        if (
                lecture.start_time < existing["end_time"] and
                lecture.end_time > existing["start_time"]
        ):
            raise HTTPException(status_code=400, detail="Time conflict with existing lecture")

    event_id = await create_event(teacher["calendar_id"], lecture)

    lecture_dict = lecture.model_dump()
    lecture_dict["calendar_event_id"] = event_id

    await db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {"$push": {"lectures": lecture_dict}}
    )
    return {"message": "Lecture added", "event_id": event_id}


@router.delete("/teacher/{teacher_id}/lecture")
async def delete_lecture(teacher_id: str, topic: str):
    teacher = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    lectures = teacher.get("lectures", [])
    updated_lectures = []
    deleted_event_id = None

    for lec in lectures:
        if lec["topic"] == topic:
            await delete_event(lec["calendar_event_id"])
            deleted_event_id = lec["calendar_event_id"]
        else:
            updated_lectures.append(lec)

    await db.teachers.update_one(
        {"_id": ObjectId(teacher_id)},
        {"$set": {"lectures": updated_lectures}}
    )

    return {"message": "Lecture deleted", "calendar_event_id": deleted_event_id}
