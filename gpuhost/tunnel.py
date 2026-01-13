from pyngrok import ngrok
from typing import Optional

def start_tunnel(port: int, authtoken: Optional[str] = None) -> str:
    """
    Starts an ngrok tunnel to the specified port.
    Returns the Public URL.
    """
    if authtoken:
        ngrok.set_auth_token(authtoken)

    # Start an HTTP tunnel to localhost:port
    # pyngrok handles the process lifecycle
    tunnel = ngrok.connect(port)
    public_url = tunnel.public_url
    return public_url

def stop_tunnels():
    ngrok.kill()
