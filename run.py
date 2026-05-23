import os
import socket
import random
import base64
from io import BytesIO

# =========================
# AUTO INSTALL (KALI SAFE)
# =========================
def install():
    os.system("python3 -m venv venv")
    os.system("venv/bin/pip install --upgrade pip")
    os.system("venv/bin/pip install flask flask-socketio pynput qrcode pillow")

if not os.path.exists("venv"):
    print("📦 Instalando ambiente...")
    install()

# ativa ambiente virtual automaticamente via exec python
import sys
sys.path.insert(0, "venv/lib/python3.*/site-packages")

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from pynput.mouse import Controller, Button
import qrcode

# =========================
# APP
# =========================
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

mouse = Controller()
clients = set()

PASSWORD = str(random.randint(1000, 9999))
SENS = 1.6

# =========================
# IP
# =========================
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

# =========================
# QR CODE
# =========================
def make_qr(data):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# =========================
# INTERFACE
# =========================
@app.route("/")
def home():
    ip = get_ip()
    url = f"http://{ip}:5000"
    qr = make_qr(url)

    return render_template_string(f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Mouse Remote</title>
        <style>
            body {{
                margin:0;
                background:#000;
                color:#0f0;
                font-family: monospace;
                text-align:center;
            }}

            .box {{
                width:360px;
                margin:40px auto;
                padding:15px;
                border:2px solid #0f0;
            }}

            .pad {{
                height:200px;
                background:#111;
                margin:10px 0;
            }}

            input, button {{
                width:90%;
                padding:10px;
                margin:5px;
                background:#000;
                color:#0f0;
                border:1px solid #0f0;
            }}
        </style>
    </head>

    <body>
        <div class="box">
            <h3>🖱 Mouse Remote</h3>
            <p>Senha: {PASSWORD}</p>

            <img src="data:image/png;base64,{qr}" width="160">

            <input id="pass" type="password" placeholder="senha">
            <button onclick="connect()">Conectar</button>

            <div class="pad" id="pad"></div>

            <button onclick="clickMouse()">CLICK</button>
        </div>

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

                let dx = (t.clientX - lx) * {SENS};
                let dy = (t.clientY - ly) * {SENS};

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

# =========================
# SOCKET
# =========================
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

    mouse.move(float(data.get("x",0)), float(data.get("y",0)))

@socketio.on("click")
def click():
    if request.sid in clients:
        mouse.click(Button.left, 1)

# =========================
# START
# =========================
if __name__ == "__main__":
    print("🚀 Mouse Remote iniciado")
    print(f"🔐 Senha: {PASSWORD}")
    socketio.run(app, host="0.0.0.0", port=5000)
