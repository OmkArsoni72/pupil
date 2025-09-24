from fastapi import APIRouter
from core.api.controllers.websocket_controller import WebSocketController

router = APIRouter()
sio = WebSocketController.sio

@sio.event
def connect(sid, environ):
    return WebSocketController.connect(sid, environ)

@sio.event
def disconnect(sid):
    return WebSocketController.disconnect(sid)

@sio.event
def message(sid, data):
    return WebSocketController.message(sid, data)

# To mount this in FastAPI, you need to use ASGIApp in your main.py:
# from api.routes.websocket import sio
# app.mount('/ws', socketio.ASGIApp(sio))