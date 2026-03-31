import os
from fastapi import FastAPI
import socketio
import uvicorn

# ===================== CONFIGURATION =====================
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    ping_timeout=60,
    ping_interval=25,
    logger=True,           # ← Ajouté pour debug
    engineio_logger=True   # ← Ajouté pour debug
)

app = FastAPI()
sio_app = socketio.ASGIApp(sio, app, socketio_path='/socket.io')

# Stockage
clients = {}
staffs = {}

# ===================== EVENTS =====================
@sio.event
async def connect(sid, environ):
    print(f"[+] Connexion SID: {sid}")

@sio.event
async def join(sid, data):
    token = data.get('token')
    role = data.get('role')
    
    if not token or not role:
        await sio.emit('error', {'message': 'Token ou rôle manquant'}, to=sid)
        return

    if role == 'client':
        clients[token] = sid
        print(f"[CLIENT] Connecté → Token: {token}")
        await sio.emit('status', {'message': '✅ Connecté au serveur Zynera'}, to=sid)
        
    elif role == 'staff':
        staffs[token] = sid
        print(f"[STAFF] Connecté → Token: {token}")
        if token in clients:
            await sio.emit('session_ready', {'status': 'ok'}, to=sid)
        else:
            await sio.emit('waiting_client', {'message': 'En attente du client...'}, to=sid)

@sio.event
async def screen_frame(sid, data):
    token = data.get('token')
    if token in staffs:
        await sio.emit('screen_update', data, to=staffs[token])

@sio.event
async def mouse_event(sid, data):
    token = data.get('token')
    if token in clients:
        await sio.emit('control_mouse', data, to=clients[token])

@sio.event
async def keyboard_event(sid, data):
    token = data.get('token')
    if token in clients:
        await sio.emit('control_keyboard', data, to=clients[token])

@sio.event
async def leave(sid, data):
    token = data.get('token')
    clients.pop(token, None)
    staffs.pop(token, None)

# ===================== ROUTES =====================
@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(clients), "staffs": len(staffs)}

@app.get("/")
async def root():
    return {"message": "Zynera Socket.IO Server is running 🚀"}

# ===================== LANCEMENT =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Serveur démarré sur le port {port}")
    uvicorn.run(sio_app, host="0.0.0.0", port=port)
