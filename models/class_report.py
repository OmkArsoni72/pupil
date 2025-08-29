from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict

class StudentInfo(BaseModel):
    studentId: str
    name: str

class InClassReport(BaseModel):
    reportId: str
    date: str
    time: str
    chapterName: str
    averageScore: str
    participationRate: str
    notes: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class AfterHourSessionReport(BaseModel):
    sessionId: str
    date: str
    time: str
    worksheetId: str
    completionRate: str
    averageScore: str
    feedback: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class DailyReport(BaseModel):
    reportId: str
    date: str
    time: str
    attendanceSummary: Dict[str, int]
    classActivities: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class AssessmentReport(BaseModel):
    assessmentId: str
    date: str
    time: str
    chapterName: str
    averageScore: str
    gradeDistribution: Dict[str, int]
    comments: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class RemedyReport(BaseModel):
    remedyId: str
    date: str
    time: str
    topicsAddressed: Optional[str] = None
    actionsTaken: Optional[str] = None
    outcome: Optional[str] = None
    learning_gaps: Optional[str] = None
    remarks: Optional[str] = None
    report_url: Optional[HttpUrl] = None

class ReportSection(BaseModel):
    inclass_report: List[InClassReport] = Field(default_factory=list)
    after_hour_session_report: List[AfterHourSessionReport] = Field(default_factory=list)
    daily_report: List[DailyReport] = Field(default_factory=list)
    assessment_report: List[AssessmentReport] = Field(default_factory=list)
    remedy_report: List[RemedyReport] = Field(default_factory=list)

class ClassReport(BaseModel):
    _id: str  # Replaces classId to be MongoDB compatible
    teacherId: str
    schoolId: str
    board: str
    grade: str
    section: str
    students: List[StudentInfo] = Field(default_factory=list)
    report: ReportSection
