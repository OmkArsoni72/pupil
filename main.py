
import os
from datetime import datetime, date

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

from core.api.routes import content, afterhours, details, teacher, user, timetable, assessment, rag
from core.api.routes.websocket import sio  # socketio server
from core.services.ping_schedular import self_ping
from core.services.ai.performance_dashboard import router as performance_router
import socketio

PORT = int(os.getenv("PORT", 8080))


# Enhanced JSON Response
class EnhancedJSONResponse(JSONResponse):
    @staticmethod
    def _encode_content(content):
        return jsonable_encoder(
            content,
            custom_encoder={
                ObjectId: str,
                datetime: lambda v: v.isoformat(),
                date: lambda v: v.isoformat(),
            },
        )

    def render(self, content) -> bytes:
        safe_content = self._encode_content(content)
        return super().render(safe_content)


app = FastAPI(default_response_class=EnhancedJSONResponse)

# CORS Configuration
origins = [
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # Allow all origins for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Routers
app.include_router(details.router, prefix="/api")
app.include_router(teacher.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(timetable.router, prefix="/api")
app.include_router(afterhours.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")
app.include_router(performance_router, prefix="/api")
app.include_router(rag.router, prefix="/api")

# Mount Socket.IO
app.mount("/ws", socketio.ASGIApp(sio))


@app.get("/")
def read_root():
    return {"message": "API is running!"}


# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(self_ping, "interval", minutes=10)
scheduler.start()

# Run with Uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
