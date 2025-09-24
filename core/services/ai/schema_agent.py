
# # services/ai/schema_agent.py
# # Fetch exam schema/template
from core.services.db_operations.assessment_db import get_template_by_target_exam

class SchemaAgent:
    @staticmethod
    async def fetch_template(target_exam: str) -> dict:
        tpl = await get_template_by_target_exam(target_exam)
        if not tpl:
            raise ValueError(f"No template found for {target_exam}")
        return tpl


# from services.db_operations.assessment_db import get_templates_collection

# # async def fetch_exam_template(target_exam: str) -> dict:
# #     """
# #     Fetches the exam schema/template for the given exam key from MongoDB.
# #     """
# #     collection = get_templates_collection()
# #     template = await collection.find_one({"target_exam": target_exam})

# #     if not template:
# #         raise ValueError(f"No template found for target_exam: {target_exam}")

# #     return template.get("schema", {})  # assuming structure: { target_exam, schema: {...} }

# from typing import Optional
# from pymongo import MongoClient
# from pydantic import BaseModel
# from fastapi import HTTPException

# # Mongo connection setup (adjust from your base.py if needed)
# client = MongoClient()  # Or use URI from .env
# db = client['Pupil_teach']
# templates_collection = db['templates']

# class ExamScheme(BaseModel):
#     target_exam: str
#     metadata: dict
#     scheme: dict
#     instructions: list

# class SchemaAgent:
#     @staticmethod
#     def fetch_template(target_exam: str) -> ExamScheme:
#         template_doc = templates_collection.find_one({"target_exam": target_exam})
#         if not template_doc:
#             raise HTTPException(status_code=404, detail=f"Template '{target_exam}' not found")
        
#         # Remove MongoDB internal fields if present
#         template_doc.pop("_id", None)
        
#         # Validate & parse using Pydantic model
#         try:
#             exam_scheme = ExamScheme(**template_doc)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Template validation error: {e}")
        
#         return exam_scheme
