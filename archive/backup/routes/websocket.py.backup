import socketio
from fastapi import APIRouter

sio = socketio.AsyncServer(async_mode='asgi')
router = APIRouter()

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
def message(sid, data):
    print(f"Message from {sid}: {data}")
    sio.emit('message', data, skip_sid=sid)

# To mount this in FastAPI, you need to use ASGIApp in your main.py:
# from routes.websocket import sio
# app.mount('/ws', socketio.ASGIApp(sio))
