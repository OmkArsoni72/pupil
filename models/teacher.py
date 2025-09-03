
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime

class Lecture(BaseModel):
    topic: str
    start_time: datetime
    end_time: datetime
    calendar_event_id: Optional[str] = None

class Teacher(BaseModel):
    id: Optional[str]
    name: str
    email: EmailStr
    calendar_id: str

    lectures: List[Lecture] = []

class ChapterSession(BaseModel):
    # Define fields as per your schema, placeholder for now
    # e.g. sessionId: str, title: str, ...
    ...

class UploadedContent(BaseModel):
    # Define fields as per your schema, placeholder for now
    ...

class Chapter(BaseModel):
    chapterId: str
    title: str
    status: str
    chapterSessions: Optional[List[ChapterSession]] = None
    uploadedContent: Optional[UploadedContent] = None

class Curriculum(BaseModel):
    indexPdfUrl: Optional[HttpUrl] = None
    chapters: List[Chapter]

class School(BaseModel):
    board: str
    teacherId: str
    teacherName: str

class TeacherClassData(BaseModel):
    id: str
    className: str
    subject: str
    academicYear: str
    school: School
    sessions: Optional[Dict] = None
    curriculum: Curriculum

