from fastapi import APIRouter, HTTPException, Depends, Header, Query
from typing import List
from pymongo.errors import PyMongoError

from models.role import TEACHER
from models.user import (
    find_user_by_email, create_user, get_user, get_users,
    update_user, delete_user, update_user_role, bind_code,
    get_code, find_user_by_uid, serialize_mongo_document
)
from services.auth.token import create_access_token, verify_token
from services.db_operations.user_db import (
    UserBase, UserUpdate, UserResponse, LoginUser, RoleUpdate, CodeBind
)

router = APIRouter()

# In-memory session tracking
active_sessions = {}

# ---------------- AUTH ----------------

# Register user (default role = TEACHER)
@router.post("/user/register", tags=["Auth"])
def register_user(user: UserBase):
    try:
        if find_user_by_email(user.email):
            raise HTTPException(status_code=400, detail="User already exists")

        user_data = user.model_dump()
        user_data["role"] = TEACHER
        user_id = create_user(user_data)
        return {"msg": "User registered", "user_id": str(user_id)}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Login user (single active session)
@router.post("/user/login", tags=["Auth"])
def login(user: LoginUser):
    try:
        db_user = find_user_by_email(user.email)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = str(db_user["_id"])

        if user_id in active_sessions:
            raise HTTPException(status_code=403, detail="User already logged in on another device")

        token = create_access_token({"user_id": user_id})
        active_sessions[user_id] = token

        return {
            "msg": "Login successful",
            "access_token": token,
            "user_id": user_id
        }
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Middleware to validate session + token
def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id or active_sessions.get(user_id) != token:
        raise HTTPException(status_code=403, detail="Session expired or logged in elsewhere")

    return user_id


# ---------------- USER CRUD ----------------

@router.post("/user/", response_model=UserResponse, tags=["User"])
def create_new_user(user: UserBase):
    try:
        if find_user_by_email(user.email):
            raise HTTPException(status_code=400, detail="User already exists")
        user_id = create_user(user)
        return get_user(user_id)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/user/", response_model=List[UserResponse], tags=["User"])
def read_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    return get_users(skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=UserResponse, tags=["User"])
def read_user(user_id: str):
    return get_user(user_id)


@router.put("/user/{user_id}", response_model=UserResponse, tags=["User"])
def update_user_details(user_id: str, user_update: UserUpdate):
    return update_user(user_id, user_update)


@router.delete("/user/{user_id}", tags=["User"])
def delete_user_details(user_id: str):
    return delete_user(user_id)


# ---------------- ROLES ----------------

@router.put("/user/{user_id}/role", tags=["Role"])
def update_role(user_id: str, role_data: RoleUpdate, current_user: str = Depends(get_current_user)):
    try:
        if user_id != current_user:
            raise HTTPException(status_code=403, detail="Unauthorized user ID")
        update_user_role(user_id, role_data.role, role_data.grade, role_data.section)
        return {"msg": "Role updated"}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ---------------- SMARTBOARD ----------------

@router.post("/user/{user_id}/code", tags=["SmartBoard"])
def bind_code_to_smartBoard(user_id: str, data: CodeBind, current_user: str = Depends(get_current_user)):
    try:
        if current_user != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized user ID")
        bind_code(user_id, data.code)
        return {"msg": "Code bound to user"}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/user/{user_id}/code", tags=["SmartBoard"])
def get_code_from_smartBoard(user_id: str, current_user: str = Depends(get_current_user)):
    try:
        if current_user != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized user ID")
        code = get_code(user_id)
        return {"code": code or ""}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ---------------- UID LOOKUP ----------------

@router.get("/user/uid/{uid}", response_model=UserResponse, tags=["User"])
def get_user_details(uid: str):
    try:
        user = find_user_by_uid(uid)
        return serialize_mongo_document(user)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
