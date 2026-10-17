import os
import json
from flask import Flask
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

connected_users = {}

# Render health check route (prevents cold starts / easy test)
@app.route("/")
def health_check():
    return {"status": "MissVoice Signaling Server Running", "active_users": list(connected_users.keys())}, 200

@sock.route("/ws/<user_id>")
def handle_socket(ws, user_id):
    connected_users[user_id] = ws
    print(f"[WS] User connected: {user_id} (Total: {len(connected_users)})")

    try:
        while True:
            message_raw = ws.receive()
            if message_raw is None:
                break

            data = json.loads(message_raw)
            target = data.get("target")

            # Forward WebRTC signaling (offer, answer, candidate, captions)
            if target and target in connected_users:
                target_ws = connected_users[target]
                try:
                    target_ws.send(json.dumps(data))
                except Exception as send_err:
                    print(f"[WS] Failed sending to {target}: {send_err}")
                    connected_users.pop(target, None)
            else:
                print(f"[WS] Target user {target} not connected or found")

    except Exception as e:
        print(f"[WS] Connection error with {user_id}: {e}")
    finally:
        connected_users.pop(user_id, None)
        print(f"[WS] User disconnected: {user_id} (Remaining: {len(connected_users)})")

if __name__ == "__main__":
    # Render assigns dynamic PORT; fall back to 8000 for local runs
    port = int(os.environ.get("PORT", 8000))
    # Must bind to 0.0.0.0 for cloud access
    app.run(host="0.0.0.0", port=port)