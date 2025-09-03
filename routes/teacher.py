from bson import ObjectId
from fastapi import APIRouter, HTTPException
from services.calendar import create_event, delete_event

from typing import List
from models.teacher import Teacher, Lecture, Chapter
# from services.calendar import create_event, delete_event
from services.db_operations.base import db, get_all_chapters_from_teacher_class_data, update_chapters_in_teacher_class_data

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

@router.get("/teacher_class_data/{class_id}/chapters", response_model=List[Chapter], tags=["TeacherClassData"])
async def get_all_chapters(class_id: str):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class_id format.")
    chapters = await get_all_chapters_from_teacher_class_data(class_id)
    if chapters is None:
        raise HTTPException(status_code=404, detail="Class data not found")
    return chapters


@router.put("/teacher_class_data/{class_id}/chapters", tags=["TeacherClassData"])
async def update_chapters(class_id: str, chapters: List[Chapter]):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class_id format.")
    updated = await update_chapters_in_teacher_class_data(class_id, [chapter.dict() for chapter in chapters])
    if not updated:
        raise HTTPException(status_code=404, detail="Class data not found or not updated")
    return {"message": "Chapters updated successfully"}
