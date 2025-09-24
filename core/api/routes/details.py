from fastapi import APIRouter
from core.api.controllers.details_controller import DetailsController
from core.models.student_report import StudentReport
from core.models.class_report import ClassReport

router = APIRouter()


@router.get("/grades")
def get_grades():
    """
    API to fetch all grades
    """
    return DetailsController.get_grades()


@router.get("/grades/{grade_id}/sections")
async def get_sections(grade_id: str):
    """
    API to fetch sections for a specific grade
    """
    return await DetailsController.get_sections(grade_id)


@router.get("/grades/{grade_id}/sections/{section_name}")
async def get_subjects(grade_id: str, section_name: str):
    """
    API to fetch subjects for a specific section
    """
    return await DetailsController.get_subjects(grade_id, section_name)


@router.get("/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}")
async def get_chapters(grade_id: str, section_name: str, subject_board: str, subject_name: str):
    """
    API to fetch chapters of a subject
    """
    return await DetailsController.get_chapters(grade_id, section_name, subject_board, subject_name)


@router.get(
    "/grades/{grade_id}/sections/{section_name}/subjects/{subject_board}/{subject_name}/chapters/{chapter_name}/periods")
async def get_periods(grade_id: str, section_name: str, subject_board: str, subject_name: str, chapter_name: str):
    """
    API to fetch periods of a chapter
    """
    return await DetailsController.get_periods(grade_id, section_name, subject_board, subject_name, chapter_name)


@router.get("/student_report/{class_id}/{student_id}", response_model=StudentReport)
async def fetch_student_report(class_id: str, student_id: str):
    """
    API to fetch student report
    """
    return await DetailsController.fetch_student_report(class_id, student_id)


@router.get("/class_report/board/{board}/grade/{grade}/section/{section}", response_model=ClassReport)
async def fetch_class_report_by_board_grade_section(board: str, grade: str, section: str):
    """
    API to fetch class report by board, grade, and section
    """
    return await DetailsController.fetch_class_report_by_board_grade_section(board, grade, section)