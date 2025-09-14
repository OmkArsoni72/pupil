
import os
from datetime import datetime, date

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

from routes import details, user, timetable, afterhours, content, assessment
from routes.websocket import sio  # socketio server
from services.ping_schedular import self_ping
from services.ai.performance_dashboard import router as performance_router
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
origins = ["http://localhost:8080"]  # Add your frontend origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Routers
app.include_router(details.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(timetable.router, prefix="/api")
app.include_router(afterhours.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")
app.include_router(performance_router, prefix="/api")

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
