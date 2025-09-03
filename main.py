import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from datetime import datetime, date
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware

from routes import details, user, timetable, content,assessment
from services.ping_schedular import self_ping
from routes.websocket import sio  # Import the socketio server
import socketio

PORT = int(os.getenv("PORT", 8080))

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

app.include_router(details.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")
# Mount Socket.IO ASGI app
app.mount('/ws', socketio.ASGIApp(sio))

@app.get("/")
def read_root():
    return {"message": "API is running!"}


scheduler = BackgroundScheduler()
scheduler.add_job(self_ping, 'interval', minutes=10)
scheduler.start()

# Optional if running via `uvicorn main:app --reload`
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
