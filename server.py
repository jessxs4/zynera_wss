from fastapi import FastAPI
import socketio
import uvicorn
import base64
from PIL import Image
import io

sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode='asgi')
app = FastAPI()
sio_app = socketio.ASGIApp(sio, app)

clients = {}   # token → client_sid
staffs = {}    # token → staff_sid

@sio.event
async def connect(sid, environ):
    print(f"Connecté: {sid}")

@sio.event
async def join(sid, data):
    token = data['token']
    role = data['role']
    
    if role == 'client':
        clients[token] = sid
        await sio.emit('client_joined', {'status': 'ok'}, to=sid)
        print(f"Client connecté pour token {token}")
    elif role == 'staff':
        staffs[token] = sid
        print(f"Staff connecté pour token {token}")

    # Si les deux sont là → on peut démarrer
    if token in clients and token in staffs:
        await sio.emit('session_ready', {}, to=staffs[token])

@sio.event
async def screen_frame(sid, data):
    token = data['token']
    if token in staffs:
        await sio.emit('screen_update', data, to=staffs[token])

@sio.event
async def mouse_event(sid, data):
    token = data['token']
    if token in clients:
        await sio.emit('control_mouse', data, to=clients[token])

@sio.event
async def keyboard_event(sid, data):
    token = data['token']
    if token in clients:
        await sio.emit('control_keyboard', data, to=clients[token])

@sio.event
async def leave(sid, data):
    token = data.get('token')
    clients.pop(token, None)
    staffs.pop(token, None)

if __name__ == "__main__":
    uvicorn.run(sio_app, host="0.0.0.0", port=8000)
