from fastapi import APIRouter
from typing import List
from core.models.teacher import Teacher, Lecture, Chapter
from core.api.controllers.teacher_controller import TeacherController

router = APIRouter()


@router.post("/teacher/")
async def create_teacher(teacher: Teacher):
    """
    Create a new teacher.

    Args:
        teacher: Teacher object containing teacher details

    Returns:
        Created teacher with string ID
    """
    return await TeacherController.create_teacher(teacher)


@router.post("/teacher/{teacher_id}/lecture")
async def add_lecture(teacher_id: str, lecture: Lecture):
    """
    Add a lecture to teacher's schedule with calendar integration.

    Args:
        teacher_id: ID of the teacher
        lecture: Lecture object containing lecture details

    Returns:
        Success message with calendar event ID
    """
    return await TeacherController.add_lecture(teacher_id, lecture)


@router.delete("/teacher/{teacher_id}/lecture")
async def delete_lecture(teacher_id: str, topic: str):
    """
    Delete a lecture from teacher's schedule and calendar.

    Args:
        teacher_id: ID of the teacher
        topic: Topic of the lecture to delete

    Returns:
        Success message with deleted calendar event ID
    """
    return await TeacherController.delete_lecture(teacher_id, topic)


@router.get("/teacher_class_data/{class_id}/chapters", response_model=List[Chapter], tags=["TeacherClassData"])
async def get_all_chapters(class_id: str):
    """
    Get all chapters for a specific class.

    Args:
        class_id: ID of the class

    Returns:
        List of chapters for the class
    """
    return await TeacherController.get_all_chapters(class_id)


@router.put("/teacher_class_data/{class_id}/chapters", tags=["TeacherClassData"])
async def update_chapters(class_id: str, chapters: List[Chapter]):
    """
    Update chapters for a specific class.

    Args:
        class_id: ID of the class
        chapters: List of Chapter objects to update

    Returns:
        Success message
    """
    return await TeacherController.update_chapters(class_id, chapters)