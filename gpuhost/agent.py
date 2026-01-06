from gpuhost.api import app, set_auth_token
from gpuhost.state import state
from gpuhost.gpu import init_gpu, shutdown_gpu
from gpuhost.tunnel import start_tunnel, stop_tunnels
import uvicorn
import secrets
import webbrowser
import threading
import time
from typing import Optional


def start_agent(tunnel: bool = False, token: Optional[str] = None):
    """
    Starts the local GPU host agent
    """
    # 1. Setup Authentication
    if not token:
        token = secrets.token_hex(4) + "-" + secrets.token_hex(4)
    
    set_auth_token(token)
    state.auth_token = token
    print(f"\n🔑 API Key: {token}")

    # 2. Initialize GPU
    print("Initializing GPU connection...")
    if init_gpu():
        print("✅ GPU detected and initialized.")
    else:
        print("⚠️  Warning: Real NVIDIA GPU not detected (or drivers missing). Using Mock/Fallback.")

    # 3. Start Tunnel (Optional)
    public_url = None
    if tunnel:
        print("🚇 Starting secure tunnel...")
        try:
            public_url = start_tunnel(8848)
            state.public_url = public_url
            print(f"\n🌍 Public Share Link: {public_url}/?key={token}")
        except Exception as e:
            print(f"❌ Failed to start tunnel: {e}")

    # 4. Start Server
    local_url = f"http://localhost:8848/?key={token}"
    print(f"🚀 gpuhost agent starting on {local_url}")
    
    # 4. Auto-Open Browser (Delayed to wait for uvicorn start)
    def open_browser():
        time.sleep(1.5)
        print("🖥️ Opening dashboard in browser...")
        webbrowser.open(local_url)
    
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8848)
    finally:
        print("Shutting down...")
        if tunnel:
            print("Stopping tunnels...")
            stop_tunnels()
        print("Shutting down GPU connection...")
        shutdown_gpu()
