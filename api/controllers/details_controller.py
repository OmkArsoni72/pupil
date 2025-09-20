from bson import ObjectId
from fastapi import HTTPException
from services.db_operations.base import db, get_student_report, get_class_report_by_board_grade_section
import urllib.parse
from models.student_report import StudentReport
from models.class_report import ClassReport
from typing import List, Dict, Any


class DetailsController:
    """
    Controller for details operations.
    Handles business logic for grades, sections, subjects, chapters, periods and reports.
    """

    @staticmethod
    def get_grades() -> List[Dict[str, str]]:
        """
        Fetch all grades from lesson_script collection.

        Returns:
            List of dictionaries containing id and grade information

        Raises:
            HTTPException: If database operation fails
        """
        try:
            grades = db["lesson_script"].find()
            return [{"id": str(grade["_id"]), "grade": grade["grade"]} for grade in grades]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_sections(grade_id: str) -> List[Dict[str, str]]:
        """
        Fetch sections for a specific grade.

        Args:
            grade_id: The ObjectId of the grade

        Returns:
            List of dictionaries containing section names

        Raises:
            HTTPException: If grade not found or database operation fails
        """
        try:
            grade = await db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
            if not grade:
                raise HTTPException(status_code=404, detail="Grade not found")

            sections = grade.get("sections", [])
            if not sections:
                raise HTTPException(status_code=404, detail="No sections found for this grade")

            return [{"sectionName": section["section"]} for section in sections]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_subjects(grade_id: str, section_name: str) -> List[Dict[str, str]]:
        """
        Fetch subjects for a specific section within a grade.

        Args:
            grade_id: The ObjectId of the grade
            section_name: Name of the section

        Returns:
            List of dictionaries containing subject names and boards

        Raises:
            HTTPException: If grade or section not found, or database operation fails
        """
        try:
            grade = await db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
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

    @staticmethod
    async def get_chapters(grade_id: str, section_name: str, subject_board: str, subject_name: str) -> List[Any]:
        """
        Fetch chapters of a specific subject.

        Args:
            grade_id: The ObjectId of the grade
            section_name: Name of the section
            subject_board: Board of the subject
            subject_name: Name of the subject

        Returns:
            List of chapters for the subject

        Raises:
            HTTPException: If grade, section, or subject not found, or database operation fails
        """
        try:
            grade = await db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
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

    @staticmethod
    async def get_periods(grade_id: str, section_name: str, subject_board: str, subject_name: str, chapter_name: str) -> List[Any]:
        """
        Fetch periods of a specific chapter.

        Args:
            grade_id: The ObjectId of the grade
            section_name: Name of the section
            subject_board: Board of the subject
            subject_name: Name of the subject
            chapter_name: Name of the chapter (URL encoded)

        Returns:
            List of periods for the chapter

        Raises:
            HTTPException: If grade, section, subject, or chapter not found, or database operation fails
        """
        try:
            chapter_name = urllib.parse.unquote(chapter_name)

            grade = await db["lesson_script"].find_one({"_id": ObjectId(grade_id)})
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

    @staticmethod
    async def fetch_student_report(class_id: str, student_id: str) -> StudentReport:
        """
        Fetch student report for a specific student and class.

        Args:
            class_id: The ID of the class
            student_id: The ID of the student

        Returns:
            StudentReport object

        Raises:
            HTTPException: If student report not found
        """
        report = await get_student_report(student_id=student_id, class_id=class_id)
        if not report:
            raise HTTPException(status_code=404, detail="Student report not found")
        return report

    @staticmethod
    async def fetch_class_report_by_board_grade_section(board: str, grade: str, section: str) -> ClassReport:
        """
        Fetch class report by board, grade, and section.

        Args:
            board: The board name
            grade: The grade level
            section: The section name

        Returns:
            ClassReport object

        Raises:
            HTTPException: If class report not found
        """
        report = await get_class_report_by_board_grade_section(board=board, grade=grade, section=section)
        if not report:
            raise HTTPException(status_code=404, detail="Class report not found for given board, grade, and section")
        return report