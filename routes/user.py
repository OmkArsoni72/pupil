from fastapi import APIRouter, HTTPException, Depends, Header
from pymongo.errors import PyMongoError

from models.role import TEACHER
from models.user import find_user_by_email, create_user, update_user_role, bind_code, get_code, find_user_by_uid, \
    serialize_mongo_document
from services.auth.token import create_access_token, verify_token
from services.db_operations.user_db import UserBase, LoginUser, RoleUpdate, CodeBind

router = APIRouter()

# In-memory session tracking
active_sessions = {}


# Register user
@router.post("/user/register")
def register_user(user: UserBase):
    try:
        if find_user_by_email(user.email):
            raise HTTPException(status_code=400, detail="User already exists")

        user_data = user.model_dump()  # Set default role to 'teacher'
        user_data["role"] = TEACHER

        user_id = create_user(user_data)
        return {"msg": "User registered", "user_id": str(user_id)}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    except Exception as e:
        print("Unhandled error:", e)  # 👈 Log it for debugging
        import traceback
        traceback.print_exc()  # 👈 See full traceback in console
        raise HTTPException(status_code=500, detail=str(e))


# Login user
@router.post("/user/login")
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


# Middleware
def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id or active_sessions.get(user_id) != token:
        raise HTTPException(status_code=403, detail="Session expired or logged in elsewhere")

    return user_id


# Update role
@router.put("/user/role")
def update_role(role_data: RoleUpdate, user_id: str = Depends(get_current_user)):
    try:
        update_user_role(user_id, role_data.role, role_data.grade, role_data.section)
        return {"msg": "Role updated"}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Bind code to SmartBoard
@router.post("/user/codeToSmartBoard/")
def bind_code_to_smartBoard(data: CodeBind, user_id: str = Depends(get_current_user)):
    try:
        if user_id != data.userId:
            raise HTTPException(status_code=403, detail="Unauthorized user ID")
        bind_code(user_id, data.code)
        return {"msg": "Code bound to user"}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Get SmartBoard code
@router.get("/user/codeToSmartBoard")
def get_code_from_smartBoard(user_id: str = Depends(get_current_user)):
    try:
        code = get_code(user_id)
        return {"code": code or ""}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")




@router.get("/user-details/{uid}")
def get_user_details(uid: str):
    try:
        user = find_user_by_uid(uid)
        return serialize_mongo_document(user)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
