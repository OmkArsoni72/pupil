from bson import ObjectId
from pymongo.errors import PyMongoError
from fastapi import HTTPException
from typing import List, Optional
from core.services.db_operations.user_db import UserBase, UserUpdate, UserResponse
from core.services.db_operations.base import user_collection


def find_user_by_email(email: str) -> Optional[dict]:
    try:
        user = user_collection.find_one({"email": email})
        return user
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



def create_user(user_data: UserBase) -> str:
    try:
        user_dict = user_data.dict()
        result = user_collection.insert_one(user_dict)
        return str(result.inserted_id)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_user(user_id: str) -> UserResponse:
    try:
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user["id"] = str(user.pop("_id"))
        return UserResponse(**user)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_users(skip: int = 0, limit: int = 10) -> List[UserResponse]:
    try:
        users = list(user_collection.find().skip(skip).limit(limit))
        return [UserResponse(**{**user, "id": str(user.pop("_id"))}) for user in users]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def update_user(user_id: str, user_update: UserUpdate) -> UserResponse:
    try:
        update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")

        result = user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return get_user(user_id)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def delete_user(user_id: str) -> bool:
    try:
        result = user_collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return True
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def find_user_by_email(email: str) -> Optional[dict]:
    try:
        user = user_collection.find_one({"email": email})

        return user
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def find_user_by_id(user_id):
    try:
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def find_user_by_uid(uid):
    try:
        user = user_collection.find_one({"uid": uid})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def serialize_mongo_document(document: dict):
    document["_id"] = str(document["_id"])
    return document


def create_user(user_data):
    try:
        result = user_collection.insert_one(user_data)
        return result.inserted_id
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def update_user_role(user_id, role, grade, section):
    try:
        result = user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"role": role, "grade": grade, "section": section}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def bind_code(user_id, code):
    try:
        result = user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"code": code}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def get_code(user_id):
    try:
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user.get("code", "")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
