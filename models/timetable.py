from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, values):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class TeacherInfo(BaseModel):
    teacher_id: str
    name: str


class PDFTimetable(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    class_id: str
    school_id: str
    academic_year: str
    generated_by_user_id: str
    file_name: str
    encoded_file: str  # Base64 encoded PDF
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TimetableEvent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    class_id: str
    teacher_id: str
    scheduled_date: datetime
    duration_minutes: int
    event_type: str = "class_session"
    planned_lesson_id: Optional[str] = None
    status: str = "scheduled"
    is_holiday: bool = False
    rescheduled_to_event_id: Optional[str] = None
    school_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Lesson(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    chapter_id: str
    class_id: str
    teacher_id: str
    lesson_title: str
    sequence_number: int
    teleprompter_script: str
    status: str = "draft"
    associated_timetable_event_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
