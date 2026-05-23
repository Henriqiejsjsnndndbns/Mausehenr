import os
import sys

VENV = "venv"

# =========================
# VENV AUTO
# =========================
if not os.path.exists(VENV):
    print("📦 criando venv...")
    os.system("python3 -m venv venv")

if sys.prefix == sys.base_prefix:
    print("📦 entrando no venv...")
    os.system(f"{VENV}/bin/pip install flask flask-socketio pynput")
    os.execv(f"{VENV}/bin/python", [f"{VENV}/bin/python"] + sys.argv)

# =========================
# APP
# =========================
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller, Button
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

mouse = Controller()
clients = set()

PASSWORD = str(random.randint(1000, 9999))

# =========================
# UI LIMPA
# =========================
@app.route("/")
def home():
    return render_template_string(f"""
    <html>
    <body style="
        margin:0;
        background:#000;
        overflow:hidden;
        color:#0f0;
        font-family:monospace;
    ">

    <div style="
        width:100vw;
        height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
        flex-direction:column;
    ">

        <h3 style="opacity:0.6;">🖱 MOUSE REMOTO</h3>
        <p style="opacity:0.4;">Senha: {PASSWORD}</p>

        <!-- TOUCHPAD -->
        <div id="pad"
            style="
                width:95vw;
                height:75vh;
                background:#050505;
                border:2px solid #0f0;
            ">
        </div>

        <p style="opacity:0.3;">toque e arraste | duplo toque = clique</p>

    </div>

    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

    <script>
        let socket = io();
        let ok = false;

        socket.emit("auth", {{password:"{PASSWORD}"}});

        socket.on("ok", () => ok = true);

        let pad = document.getElementById("pad");

        let lx = 0, ly = 0;
        let lastTap = 0;

        pad.addEventListener("touchstart", e => {{
            let t = e.touches[0];
            lx = t.clientX;
            ly = t.clientY;

            // DETECTA DOUBLE TAP
            let now = Date.now();
            if (now - lastTap < 300) {{
                socket.emit("click", {{button:"left"}});
            }}
            lastTap = now;
        }});

        pad.addEventListener("touchmove", e => {{
            if(!ok) return;

            let t = e.touches[0];

            let dx = t.clientX - lx;
            let dy = t.clientY - ly;

            lx = t.clientX;
            ly = t.clientY;

            socket.emit("move", {{x:dx, y:dy}});
        }});
    </script>

    </body>
    </html>
    """)

# =========================
# SOCKET
# =========================
@socketio.on("auth")
def auth(data):
    if data.get("password") == PASSWORD:
        clients.add(request.sid)
        emit("ok")
        print("✔ conectado")
    else:
        emit("fail")

@socketio.on("move")
def move(data):
    if request.sid not in clients:
        return
    mouse.move(float(data["x"]), float(data["y"]))

@socketio.on("click")
def click(data):
    if request.sid in clients:
        mouse.click(Button.left, 1)

# =========================
# START
# =========================
if __name__ == "__main__":
    print("🚀 rodando mouse remoto")
    print("🔐 senha:", PASSWORD)
    socketio.run(app, host="0.0.0.0", port=5000)
        
