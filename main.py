import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import details, user, timetable, afterhours,content
from services.ping_schedular import self_ping

PORT = int(os.getenv("PORT", 8080))

app = FastAPI()

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
app.include_router(timetable.router, prefix="/api")
app.include_router(afterhours.router, prefix="/api")
app.include_router(content.router, prefix="/api")


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
