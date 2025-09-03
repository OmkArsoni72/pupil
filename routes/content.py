from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from bson import ObjectId
import logging
from services.db_operations.base import get_chapter_content, get_after_hour_session_content, get_lesson_content, update_after_hour_session, update_lesson_script, update_in_class_questions
from models.content import AfterHourSession, LessonScript, InClassQuestions


router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/content/{class_id}/{chapter_id}", tags=["Content"])
async def get_content_for_chapter(class_id: str, chapter_id: str):
    """
    Fetches in-class questions and lesson scripts for a specific chapter in a class.
    """
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class_id format.")

    logger.info(f"Fetching content for class_id: {class_id} and chapter_id: {chapter_id}")
    
    content = await get_chapter_content(class_id, chapter_id)
    
    if content is None:
        logger.warning(f"No content found for class_id: {class_id}, chapter_id: {chapter_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found for the given class and chapter.")
    
    if not content:
        logger.info(f"Empty content for class_id: {class_id}, chapter_id: {chapter_id}")
    
    return content


@router.get("/content/session/{session_id}/after-hour", tags=["Content", "Session"])
async def get_after_hour_content(session_id: str):
    """
    Fetches after-hour session content for a specific session.
    """
    logger.info(f"Fetching after-hour content for session_id: {session_id}")
    
    content = await get_after_hour_session_content(session_id)
    
    if content is None:
        logger.warning(f"No after-hour content found for session_id: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="After-hour content not found for the given session."
        )
    
    return content


@router.get("/content/session/{session_id}/lesson-material", tags=["Content", "Session"])
async def get_lesson_material(session_id: str):
    """
    Fetches lesson script and in-class questions for a specific session.
    """
    logger.info(f"Fetching lesson material for session_id: {session_id}")
    
    content = await get_lesson_content(session_id)
    
    if content is None:
        logger.warning(f"No lesson material found for session_id: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lesson material not found for the given session."
        )
        
    return content


@router.put("/content/session/{session_id}/after-hour", tags=["Content", "Session"])
async def set_after_hour_content(session_id: str, content: AfterHourSession):
    """
    Updates or sets the after-hour session content for a specific session.
    """
    logger.info(f"Updating after-hour content for session_id: {session_id}")
    
    success = await update_after_hour_session(session_id, content.model_dump())
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found or content not updated."
        )
        
    return {"message": "After-hour content updated successfully."}


@router.put("/content/session/{session_id}/lesson-script", tags=["Content", "Session"])
async def set_lesson_script(session_id: str, content: LessonScript):
    """
    Updates or sets the lesson script for a specific session.
    """
    logger.info(f"Updating lesson script for session_id: {session_id}")
    
    success = await update_lesson_script(session_id, content.model_dump())
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found or lesson script not updated."
        )
        
    return {"message": "Lesson script updated successfully."}


@router.put("/content/session/{session_id}/in-class-questions", tags=["Content", "Session"])
async def set_in_class_questions(session_id: str, content: InClassQuestions):
    """
    Updates or sets the in-class questions for a specific session.
    """
    logger.info(f"Updating in-class questions for session_id: {session_id}")
    
    success = await update_in_class_questions(session_id, content.model_dump())
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Session not found or in-class questions not updated."
        )
        
    return {"message": "In-class questions updated successfully."} 