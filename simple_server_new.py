"""
Simple FastAPI server with working auth endpoints for testing frontend
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI(title="PupilPrep Mock API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "student"

class LoginRequest(BaseModel):
    email: str
    password: str

# Mock Data
MOCK_USERS = {}  # Will store {email: {password, user_obj}}

# Authentication Routes
@app.post("/api/v1/users/register")
async def register(data: RegisterRequest):
    email = data.email
    name = data.name
    password = data.password
    role = data.role
    
    if email in MOCK_USERS:
        return JSONResponse({"message": "User already exists"}, status_code=400)
    
    user = {
        "_id": f"user_{len(MOCK_USERS) + 1}",
        "email": email,
        "name": name,
        "role": role,
        "profile": {"avatar": None, "phone": None, "grade": None, "section": None},
        "gamification": {"points": 0, "level": 1, "badges": []}
    }
    
    MOCK_USERS[email] = {"password": password, "user": user}
    
    return {
        "access_token": f"token_{email}",
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/v1/users/login")
async def login(data: LoginRequest):
    email = data.email
    password = data.password
    
    if email not in MOCK_USERS:
        return JSONResponse({"message": "Invalid credentials"}, status_code=401)
    
    user_data = MOCK_USERS[email]
    if user_data["password"] != password:
        return JSONResponse({"message": "Invalid credentials"}, status_code=401)
    
    return {
        "access_token": f"token_{email}",
        "token_type": "bearer",
        "user": user_data["user"]
    }

@app.get("/api/v1/users/me")
async def get_current_user():
    return {
        "_id": "user_1",
        "email": "test@example.com",
        "name": "Test User",
        "role": "student",
        "profile": {"avatar": None, "phone": None, "grade": "10", "section": "A"},
        "gamification": {"points": 250, "level": 3, "badges": ["Quick Learner"]}
    }

@app.get("/api/v1/teacher/classes")
async def get_teacher_classes():
    return {
        "classes": [
            {"class_id": "class_1", "name": "Grade 10 - A", "subject": "Physics", "students_count": 45},
            {"class_id": "class_2", "name": "Grade 10 - B", "subject": "Chemistry", "students_count": 42}
        ]
    }

# Content Generation Routes
@app.post("/api/v1/contentGenerationForAHS")
async def generate_ahs_content():
    return {
        "success": True,
        "job_id": "job_12345",
        "message": "Content generation started"
    }

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "result": {
            "reading": "Newton's First Law states that...",
            "writing": "Exercise: Write about inertia...",
            "watching": "Video: Understanding Newton's Laws",
            "playing": "Game: Force and Motion",
            "doing": "Experiment: Ball rolling",
            "solving": "Problem: Calculate force",
            "debating": "Debate: Is friction helpful?",
            "listening": "Audio: Story of Newton's Apple"
        }
    }

# Teacher Routes
@app.get("/api/teacher/class-report/grade/{grade}/section/{section}")
async def get_class_report(grade: int, section: str):
    return {
        "class_average": 85.5,
        "total_students": 45,
        "completion_rate": 92.3,
        "learning_gaps": 23,
        "students": [
            {"name": "Ananya Sharma", "roll_no": 1, "average": 88, "attendance": 95, "gaps": 2},
            {"name": "Rahul Verma", "roll_no": 2, "average": 82, "attendance": 90, "gaps": 3},
            {"name": "Priya Patel", "roll_no": 3, "average": 91, "attendance": 98, "gaps": 1}
        ]
    }

# Health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "PupilPrep Mock API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting PupilPrep Mock API Server on http://localhost:8080")
    print("API Docs: http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
