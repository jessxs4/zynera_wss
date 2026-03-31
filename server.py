import asyncio
import websockets
import ssl
import json
from collections import defaultdict

# ==================== CONFIGURATION ====================
HOST = "0.0.0.0"          # Écoute sur toutes les interfaces
PORT = 443                # Port HTTPS/WSS standard
CERT_PATH = "/etc/letsencrypt/live/zynera.fr/fullchain.pem"
KEY_PATH = "/etc/letsencrypt/live/zynera.fr/privkey.pem"

# ==================== SSL ====================
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile=CERT_PATH, keyfile=KEY_PATH)

# ==================== GESTION DES CONNEXIONS ====================
# Format: {client_id: websocket}
clients = {}
staff = {}

# Pour bufferiser les commandes si le client n'est pas encore connecté
pending_commands = defaultdict(list)

# ==================== HANDLER ====================
async def handler(ws, path):
    try:
        # Première chose : identification
        msg = await ws.recv()
        data = json.loads(msg)
        role = data.get("role")
        user_id = str(data.get("id"))

        if role == "client":
            clients[user_id] = ws
            print(f"[+] Client connecté : {user_id}")
            # Envoyer les commandes en attente
            for cmd in pending_commands[user_id]:
                await ws.send(json.dumps(cmd))
            pending_commands[user_id].clear()
        elif role == "staff":
            staff[user_id] = ws
            print(f"[+] Staff connecté : {user_id}")
        else:
            await ws.close()
            return

        # ==================== LOOP PRINCIPALE ====================
        async for message in ws:
            try:
                data = json.loads(message)
                target_id = str(data.get("target_id"))
                # Si staff envoie à client
                if role == "staff" and target_id in clients:
                    await clients[target_id].send(json.dumps(data))
                # Si client envoie à staff
                elif role == "client" and target_id in staff:
                    await staff[target_id].send(json.dumps(data))
                # Si client pas connecté : bufferiser
                elif role == "staff":
                    pending_commands[target_id].append(data)
            except Exception as e:
                print(f"Erreur traitement message : {e}")

    except websockets.ConnectionClosed:
        pass
    finally:
        # Nettoyage
        if role == "client":
            if user_id in clients:
                del clients[user_id]
                print(f"[-] Client déconnecté : {user_id}")
        elif role == "staff":
            if user_id in staff:
                del staff[user_id]
                print(f"[-] Staff déconnecté : {user_id}")

# ==================== LANCEMENT DU SERVEUR ====================
async def main():
    async with websockets.serve(handler, HOST, PORT, ssl=ssl_context):
        print(f"[+] WSS Server démarré sur wss://zynera.fr:{PORT}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
