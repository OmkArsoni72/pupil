"""
Simple FastAPI server without MongoDB for testing frontend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="PupilPrep Mock API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data
MOCK_SESSIONS = [
    {"session_id": "sess_001", "topic": "Newton's Laws", "grade": 10, "subject": "Physics", "status": "completed"},
    {"session_id": "sess_002", "topic": "Cell Structure", "grade": 10, "subject": "Biology", "status": "active"}
]

MOCK_CLASS_REPORT = {
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

# Content Generation Routes
@app.post("/api/v1/contentGenerationForAHS")
async def generate_ahs_content(data: dict):
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
            "doing": "Experiment: Ball rolling on different surfaces",
            "solving": "Problem: Calculate force given mass and acceleration",
            "debating": "Debate: Is friction helpful or harmful?",
            "listening": "Audio: Story of Newton's Apple"
        }
    }

# Assessment Routes
@app.post("/api/assessments/generate")
async def generate_assessment(data: dict):
    return {
        "success": True,
        "job_id": "assess_67890",
        "message": "Assessment generation started"
    }

@app.get("/api/assessments/status/{job_id}")
async def get_assessment_status(job_id: str):
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "result": {
            "title": "Physics Mid-term Test",
            "total_questions": 15,
            "total_marks": 50,
            "questions": [
                {
                    "question": "What is Newton's First Law?",
                    "type": "short_answer",
                    "marks": 5
                },
                {
                    "question": "Calculate the force when mass=10kg and acceleration=5m/s²",
                    "type": "numerical",
                    "marks": 10
                }
            ]
        }
    }

# Teacher Routes
@app.get("/api/teacher/class-report/grade/{grade}/section/{section}")
async def get_class_report(grade: int, section: str):
    return MOCK_CLASS_REPORT

@app.get("/api/teacher/sessions")
async def get_sessions():
    return {"sessions": MOCK_SESSIONS}

# Timetable Routes
@app.get("/api/timetable/daily-schedule")
async def get_daily_schedule(date: str = None, teacher_id: str = None):
    return [
        {"time": "09:00 AM", "subject": "Physics", "title": "Newton's Laws", "grade": 10, "section": "A"},
        {"time": "10:30 AM", "subject": "Chemistry", "title": "Chemical Reactions", "grade": 10, "section": "B"},
        {"time": "02:00 PM", "subject": "Biology", "title": "Cell Structure", "grade": 10, "section": "A"}
    ]

@app.post("/api/timetable/upload-pdf")
async def upload_timetable_pdf(file: dict):
    return {"success": True, "message": "Timetable uploaded successfully"}

# Health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "PupilPrep Mock API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting PupilPrep Mock API Server on http://localhost:8080")
    print("📋 API Docs: http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
