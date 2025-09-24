
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from core.models.role import TEACHER



class UserBase(BaseModel):
    email: str
    name: str
    uid: str
    role: Optional[str] = TEACHER

class ParentDetails(BaseModel):
    name: str
    email: EmailStr
    phone_number: str


class GamificationStats(BaseModel):
    points: int
    streaks: int
    badges: List[str]


class AssignedClass(BaseModel):
    classId: str
    className: str


class UserProfile(BaseModel):
    current_class_id: Optional[str] = None
    parent_details: Optional[List[ParentDetails]] = None
    gamification_stats: Optional[GamificationStats] = None
    specialized_subjects: Optional[List[str]] = None
    assigned_classes: Optional[List[AssignedClass]] = None


class UserBase(BaseModel):
    name: str
    email: EmailStr
    password_hash: str
    role: str = "student"  # Enum: ['student', 'teacher', 'hod', 'dean', 'admin']
    institution_id: str
    auth_tokens: List[str] = []
    profile: UserProfile
    created_at: datetime = datetime.utcnow()

    class Config:
        json_encoders = {
            ObjectId: str
        }


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    profile: Optional[UserProfile] = None


class UserInDB(UserBase):
    id: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    profile: UserProfile
    created_at: datetime



class LoginUser(BaseModel):
    email: str


class RoleUpdate(BaseModel):
    role: str
    grade: str
    section: str


class CodeBind(BaseModel):
    userId: str
    code: str
