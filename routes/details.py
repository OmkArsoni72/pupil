




from bson import ObjectId
from fastapi import APIRouter, HTTPException

from services.db_operations.base import db
import urllib.parse

router = APIRouter()


# ✅ API to fetch all grades
@router.get("/grades")
def get_grades():
    try:
        grades = db["lesson_script"].find()
        return [{"id": str(grade["_id"]), "grade": grade["grade"]} for grade in grades]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ API to fetch sections for a specific grade
@router.get("/grades/{grade_id}/sections")
def get_sections(grade_id: str):
    try:
        grade = db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
        if not grade:
            raise HTTPException(status_code=404, detail="Grade not found")

        sections = grade.get("sections", [])
        if not sections:
            raise HTTPException(status_code=404, detail="No sections found for this grade")

        return [{"sectionName": section["section"]} for section in sections]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ API to fetch subjects for a specific section
@router.get("/grades/{grade_id}/sections/{section_name}")
def get_subjects(grade_id: str, section_name: str):
    try:
        grade = db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
        if not grade:
            raise HTTPException(status_code=404, detail="Grade not found")

        section = next((s for s in grade.get("sections", []) if s["section"] == section_name), None)
        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")

        return [
            {"subjectName": subject["name"], "board": subject["board"]}
            for subject in section.get("subjects", [])
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ API to fetch chapters of a subject
@router.get("/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}")
def get_chapters(grade_id: str, section_name: str, subject_board: str, subject_name: str):
    try:
        grade = db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
        if not grade:
            raise HTTPException(status_code=404, detail="Grade not found")

        section = next((s for s in grade.get("sections", []) if s["section"] == section_name), None)
        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")

        subject = next(
            (s for s in section.get("subjects", []) if s["name"] == subject_name and s["board"] == subject_board), None)
        if not subject:
            raise HTTPException(status_code=404,
                                detail=f"Subject '{subject_name}' with board '{subject_board}' not found")

        return subject.get("chapters", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ API to fetch periods of a chapter
@router.get(
    "/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}/chapters/{chapter_name}/periods")
def get_periods(grade_id: str, section_name: str, subject_board: str, subject_name: str, chapter_name: str):
    try:
        chapter_name = urllib.parse.unquote(chapter_name)

        grade = db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
        if not grade:
            raise HTTPException(status_code=404, detail="Grade not found")

        section = next((s for s in grade.get("sections", []) if s["section"] == section_name), None)
        if not section:
            raise HTTPException(status_code=404, detail=f"Section '{section_name}' not found")

        subject = next(
            (s for s in section.get("subjects", []) if s["name"] == subject_name and s["board"] == subject_board), None)
        if not subject:
            raise HTTPException(status_code=404,
                                detail=f"Subject '{subject_name}' with board '{subject_board}' not found")

        chapter = next((c for c in subject.get("chapters", []) if c["name"] == chapter_name), None)
        if not chapter:
            raise HTTPException(status_code=404, detail=f"Chapter '{chapter_name}' not found")

        return chapter.get("periods", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
