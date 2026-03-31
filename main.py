import os
from fastapi import FastAPI
import socketio
import uvicorn

# ===================== CONFIGURATION =====================
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    ping_timeout=60,
    ping_interval=25
)

app = FastAPI()
sio_app = socketio.ASGIApp(sio, app)

# Stockage en mémoire (pour le moment)
clients = {}   # token → client_sid
staffs = {}    # token → staff_sid

# ===================== SOCKET.IO EVENTS =====================

@sio.event
async def connect(sid, environ):
    print(f"[+] Connexion : {sid}")

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
        
        # Si le client est déjà connecté → on prévient le staff
        if token in clients:
            await sio.emit('session_ready', {'status': 'ok', 'message': 'Client connecté'}, to=sid)
        else:
            await sio.emit('waiting_client', {'message': 'En attente du client...'}, to=sid)

@sio.event
async def screen_frame(sid, data):
    """Reçoit l'écran du client et le renvoie au staff"""
    token = data.get('token')
    if token in staffs:
        await sio.emit('screen_update', data, to=staffs[token])

@sio.event
async def mouse_event(sid, data):
    """Staff → Client : contrôle souris"""
    token = data.get('token')
    if token in clients:
        await sio.emit('control_mouse', data, to=clients[token])

@sio.event
async def keyboard_event(sid, data):
    """Staff → Client : contrôle clavier"""
    token = data.get('token')
    if token in clients:
        await sio.emit('control_keyboard', data, to=clients[token])

@sio.event
async def leave(sid, data):
    token = data.get('token')
    clients.pop(token, None)
    staffs.pop(token, None)
    print(f"[-] Déconnexion token : {token}")

# ===================== HEALTH CHECK (important pour Railway) =====================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_sessions": len(clients),
        "staff_connected": len(staffs)
    }

@app.get("/")
async def root():
    return {"message": "Zynera WebSocket Server is running 🚀"}

# ===================== LANCEMENT =====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(sio_app, host="0.0.0.0", port=port)
