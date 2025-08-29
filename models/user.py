



from bson import ObjectId
from pymongo.errors import PyMongoError
from fastapi import HTTPException

from services.db_operations.base import user_collection


def find_user_by_email(email):
    try:
        user = user_collection.find_one({"email": email})
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")
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
