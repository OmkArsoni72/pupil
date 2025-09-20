import socketio


class WebSocketController:
    """
    Controller for WebSocket operations.
    Handles WebSocket event management and message broadcasting.
    """

    sio = socketio.AsyncServer(async_mode='asgi')

    @staticmethod
    def connect(sid, environ):
        print(f"Client connected: {sid}")

    @staticmethod
    def disconnect(sid):
        print(f"Client disconnected: {sid}")

    @staticmethod
    def message(sid, data):
        print(f"Message from {sid}: {data}")
        WebSocketController.sio.emit('message', data, skip_sid=sid)