from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class StatusEnum(str, Enum):
    pending = "pending"
    completed = "completed"

class AttendanceEnum(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"

class InClassReport(BaseModel):
    reportId: str
    date: str
    time: str
    chapterName: str
    score: str
    grade: str
    notes: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class AfterHourSessionReport(BaseModel):
    sessionId: str
    date: str
    time: str
    worksheetId: str
    status: StatusEnum
    score: str
    feedback: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class DailyReport(BaseModel):
    reportId: str
    date: str
    time: str
    attendance: AttendanceEnum
    behaviorNotes: Optional[str] = None
    activities: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class AssessmentReport(BaseModel):
    assessmentId: str
    date: str
    time: str
    chapterName: str
    score: str
    grade: str
    comments: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class RemedyReport(BaseModel):
    remedyId: str
    date: str
    time: str
    topic: str
    actionTaken: str
    outcome: str
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class ReportSection(BaseModel):
    inclass_report: List[InClassReport] = Field(default_factory=list)
    after_hour_session_report: List[AfterHourSessionReport] = Field(default_factory=list)
    daily_report: List[DailyReport] = Field(default_factory=list)
    assessment_report: List[AssessmentReport] = Field(default_factory=list)
    remedy_report: List[RemedyReport] = Field(default_factory=list)

class StudentReport(BaseModel):
    classId: str
    studentId: str
    teacherId: str
    schoolId: str
    report: ReportSection 