from typing import Optional

from pydantic import BaseModel

from models.role import TEACHER


class UserBase(BaseModel):
    email: str
    name: str
    uid: str
    role: Optional[str] = TEACHER


class LoginUser(BaseModel):
    email: str


class RoleUpdate(BaseModel):
    role: str
    grade: str
    section: str


class CodeBind(BaseModel):
    userId: str
    code: str
