from fastapi import APIRouter, Depends, Query, Header
from typing import List
from api.controllers.user_controller import UserController
from services.db_operations.user_db import (
    UserBase, UserUpdate, UserResponse, LoginUser, RoleUpdate, CodeBind
)

router = APIRouter()

# ---------------- AUTH ----------------

# Register user (default role = TEACHER)
@router.post("/user/register", tags=["Auth"])
def register_user(user: UserBase):
    return UserController.register_user(user)


# Login user (single active session)
@router.post("/user/login", tags=["Auth"])
def login(user: LoginUser):
    return UserController.login(user)


# Middleware to validate session + token
def get_current_user(authorization: str = Header(...)):
    return UserController.get_current_user(authorization)


# ---------------- USER CRUD ----------------

@router.post("/user/", response_model=UserResponse, tags=["User"])
def create_new_user(user: UserBase):
    return UserController.create_new_user(user)


@router.get("/user/", response_model=List[UserResponse], tags=["User"])
def read_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return UserController.read_users(skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=UserResponse, tags=["User"])
def read_user(user_id: str):
    return UserController.read_user(user_id)


@router.put("/user/{user_id}", response_model=UserResponse, tags=["User"])
def update_user_details(user_id: str, user_update: UserUpdate):
    return UserController.update_user_details(user_id, user_update)


@router.delete("/user/{user_id}", tags=["User"])
def delete_user_details(user_id: str):
    return UserController.delete_user_details(user_id)


# ---------------- ROLES ----------------

@router.put("/user/{user_id}/role", tags=["Role"])
def update_role(user_id: str, role_data: RoleUpdate, current_user: str = Depends(get_current_user)):
    return UserController.update_role(user_id, role_data, current_user)


# ---------------- SMARTBOARD ----------------

@router.post("/user/{user_id}/code", tags=["SmartBoard"])
def bind_code_to_smartBoard(user_id: str, data: CodeBind, current_user: str = Depends(get_current_user)):
    return UserController.bind_code_to_smartBoard(user_id, data, current_user)


@router.get("/user/{user_id}/code", tags=["SmartBoard"])
def get_code_from_smartBoard(user_id: str, current_user: str = Depends(get_current_user)):
    return UserController.get_code_from_smartBoard(user_id, current_user)


# ---------------- UID LOOKUP ----------------

@router.get("/user/uid/{uid}", response_model=UserResponse, tags=["User"])
def get_user_details(uid: str):
    return UserController.get_user_details(uid)