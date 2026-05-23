import os
import sys
import subprocess

# ======================
# AUTO INSTALL
# ======================
def install(pkg):
    subprocess.call([sys.executable, "-m", "pip", "install", pkg])

try:
    import flask
    import flask_socketio
    import pynput
    import qrcode
    from PIL import Image
except ImportError:
    print("📦 Instalando dependências...")
    install("flask")
    install("flask-socketio")
    install("pynput")
    install("qrcode")
    install("pillow")

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller, Button
import socket
import qrcode
import base64
from io import BytesIO
import random

# ======================
# APP
# ======================
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

mouse = Controller()
clients = set()

PASSWORD = str(random.randint(1000, 9999))
SENSITIVITY = 1.6

# ======================
# IP
# ======================
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

# ======================
# QR
# ======================
def make_qr(data):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# ======================
# UI
# ======================
@app.route("/")
def home():
    ip = get_ip()
    url = f"http://{ip}:5000"
    qr = make_qr(url)

    return render_template_string(f"""
    <html>
    <body style="background:#000;color:#0f0;font-family:monospace;text-align:center;">
        <h2>🖱 Mouse Remote</h2>
        <p>IP: {ip}:5000</p>
        <p>Senha: {PASSWORD}</p>

        <img src="data:image/png;base64,{qr}" width="140">

        <br><br>
        <input id="pass" placeholder="senha" type="password">
        <button onclick="connect()">Conectar</button>

        <div id="pad" style="width:300px;height:200px;background:#111;margin:20px auto;"></div>

        <button onclick="clickMouse()">CLICK</button>

        <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
        <script>
            let socket;
            let ok = false;
            let lx = 0, ly = 0;

            function connect() {{
                socket = io();

                socket.emit("auth", {{
                    password: document.getElementById("pass").value
                }});

                socket.on("ok", () => {{
                    ok = true;
                    alert("Conectado");
                }});

                socket.on("fail", () => alert("Senha errada"));
            }}

            const pad = document.getElementById("pad");

            pad.addEventListener("touchstart", e => {{
                const t = e.touches[0];
                lx = t.clientX;
                ly = t.clientY;
            }});

            pad.addEventListener("touchmove", e => {{
                if(!ok) return;
                e.preventDefault();

                const t = e.touches[0];

                let dx = t.clientX - lx;
                let dy = t.clientY - ly;

                lx = t.clientX;
                ly = t.clientY;

                socket.emit("move", {{x: dx, y: dy}});
            }});

            function clickMouse() {{
                if(socket) socket.emit("click");
            }}
        </script>
    </body>
    </html>
    """)

# ======================
# SOCKET
# ======================
@socketio.on("auth")
def auth(data):
    if data.get("password") == PASSWORD:
        clients.add(request.sid)
        emit("ok")
        print("✔ Conectado")
    else:
        emit("fail")

@socketio.on("move")
def move(data):
    if request.sid not in clients:
        return

    x = float(data.get("x", 0))
    y = float(data.get("y", 0))

    mouse.move(x * SENSITIVITY, y * SENSITIVITY)

@socketio.on("click")
def click():
    if request.sid in clients:
        mouse.click(Button.left, 1)

# ======================
# START
# ======================
if __name__ == "__main__":
    print("🚀 Mouse Remote iniciado")
    print(f"🔐 Senha: {PASSWORD}")
    socketio.run(app, host="0.0.0.0", port=5000)
