from bson import ObjectId
from fastapi import HTTPException
from services.calendar import create_event, delete_event
from typing import List
from models.teacher import Teacher, Lecture, Chapter
from services.db_operations.base import db, get_all_chapters_from_teacher_class_data, update_chapters_in_teacher_class_data


class TeacherController:
    """
    Controller for teacher operations.
    Handles business logic for teacher management, lecture scheduling with calendar integration,
    time conflict detection, and chapter management.
    """

    @staticmethod
    async def create_teacher(teacher: Teacher):
        """
        Create a new teacher in the database.

        Args:
            teacher: Teacher object containing teacher details

        Returns:
            Dictionary containing the created teacher with string ID

        Raises:
            HTTPException: If database operation fails
        """
        try:
            teacher_dict = teacher.model_dump()
            result = await db.teachers.insert_one(teacher_dict)
            teacher_dict["_id"] = str(result.inserted_id)
            return teacher_dict
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create teacher: {str(e)}")

    @staticmethod
    async def add_lecture(teacher_id: str, lecture: Lecture):
        """
        Add a lecture to a teacher's schedule with calendar integration and time conflict detection.

        Args:
            teacher_id: ID of the teacher
            lecture: Lecture object containing lecture details

        Returns:
            Dictionary with success message and calendar event ID

        Raises:
            HTTPException: If teacher not found, time conflict exists, or calendar integration fails
        """
        try:
            # Validate teacher exists
            teacher = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
            if not teacher:
                raise HTTPException(status_code=404, detail="Teacher not found")

            # Check for time conflicts with existing lectures
            existing_lectures = teacher.get("lectures", [])
            for existing in existing_lectures:
                if (
                    lecture.start_time < existing["end_time"] and
                    lecture.end_time > existing["start_time"]
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Time conflict with existing lecture"
                    )

            # Create calendar event with enhanced error handling
            event_id = None
            try:
                calendar_id = teacher.get("calendar_id")
                if not calendar_id:
                    print("Warning: Teacher calendar_id not configured, proceeding without calendar integration")
                    event_id = None
                else:
                    event_id = await create_event(calendar_id, lecture)
                    # event_id can be None if calendar service is unavailable - this is acceptable

            except Exception as calendar_error:
                # Handle external calendar service failures gracefully - don't fail the entire operation
                print(f"Warning: Calendar integration failed: {str(calendar_error)}")
                event_id = None

            # Prepare lecture data for database
            lecture_dict = lecture.model_dump()
            lecture_dict["calendar_event_id"] = event_id

            # Update teacher with new lecture
            await db.teachers.update_one(
                {"_id": ObjectId(teacher_id)},
                {"$push": {"lectures": lecture_dict}}
            )

            return {"message": "Lecture added", "event_id": event_id}

        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add lecture: {str(e)}")

    @staticmethod
    async def delete_lecture(teacher_id: str, topic: str):
        """
        Delete a lecture from teacher's schedule and remove from calendar.

        Args:
            teacher_id: ID of the teacher
            topic: Topic of the lecture to delete

        Returns:
            Dictionary with success message and deleted calendar event ID

        Raises:
            HTTPException: If teacher not found or calendar deletion fails
        """
        try:
            # Validate teacher exists
            teacher = await db.teachers.find_one({"_id": ObjectId(teacher_id)})
            if not teacher:
                raise HTTPException(status_code=404, detail="Teacher not found")

            lectures = teacher.get("lectures", [])
            updated_lectures = []
            deleted_event_id = None

            # Find and remove the lecture with matching topic
            for lec in lectures:
                if lec["topic"] == topic:
                    # Delete from calendar with error handling
                    try:
                        await delete_event(lec["calendar_event_id"])
                        deleted_event_id = lec["calendar_event_id"]
                    except Exception as calendar_error:
                        # Log the error but don't fail the operation
                        # This allows cleanup even if calendar service is down
                        print(f"Warning: Failed to delete calendar event {lec['calendar_event_id']}: {str(calendar_error)}")
                        deleted_event_id = lec["calendar_event_id"]
                else:
                    updated_lectures.append(lec)

            # If no lecture was found with the topic
            if deleted_event_id is None:
                raise HTTPException(status_code=404, detail=f"Lecture with topic '{topic}' not found")

            # Update teacher's lecture list
            await db.teachers.update_one(
                {"_id": ObjectId(teacher_id)},
                {"$set": {"lectures": updated_lectures}}
            )

            return {"message": "Lecture deleted", "calendar_event_id": deleted_event_id}

        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete lecture: {str(e)}")

    @staticmethod
    async def get_all_chapters(class_id: str) -> List[Chapter]:
        """
        Get all chapters for a specific class.

        Args:
            class_id: ID of the class

        Returns:
            List of Chapter objects

        Raises:
            HTTPException: If class_id is invalid or class data not found
        """
        try:
            if not ObjectId.is_valid(class_id):
                raise HTTPException(status_code=400, detail="Invalid class_id format.")

            chapters = await get_all_chapters_from_teacher_class_data(class_id)
            if chapters is None:
                raise HTTPException(status_code=404, detail="Class data not found")

            return chapters
        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get chapters: {str(e)}")

    @staticmethod
    async def update_chapters(class_id: str, chapters: List[Chapter]):
        """
        Update chapters for a specific class.

        Args:
            class_id: ID of the class
            chapters: List of Chapter objects to update

        Returns:
            Dictionary with success message

        Raises:
            HTTPException: If class_id is invalid or update fails
        """
        try:
            if not ObjectId.is_valid(class_id):
                raise HTTPException(status_code=400, detail="Invalid class_id format.")

            # Convert chapters to dictionaries
            chapters_dict = [chapter.dict() for chapter in chapters]
            updated = await update_chapters_in_teacher_class_data(class_id, chapters_dict)

            if not updated:
                raise HTTPException(status_code=404, detail="Class data not found or not updated")

            return {"message": "Chapters updated successfully"}
        except HTTPException:
            # Re-raise HTTP exceptions as they are already properly formatted
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update chapters: {str(e)}")