from pydantic import BaseModel, EmailStr
from typing import List, Optional
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