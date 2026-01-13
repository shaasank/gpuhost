<<<<<<< HEAD
import typer
from gpuhost.agent import start_agent

app = typer.Typer(help="gpuhost – self-hosted GPU sharing agent")


@app.callback()
def main():
    """
    Manage the gpuhost agent.
    """
    pass


@app.command()
def start(
    tunnel: bool = typer.Option(False, "--tunnel", help="Expose agent via secure tunnel"),
    token: str = typer.Option(None, "--token", help="Manually set API Key")
):
    """Start the GPU host agent"""
    start_agent(tunnel=tunnel, token=token)

import requests
import json
import sys

@app.command(name="clan-create")
def clan_create():
    """[Host] Initialize a Clan on this machine."""
    try:
        # Assuming local agent is running on 8848
        # We need the local token. For now, assume user knows it or we read from a config file?
        # V1 didn't save config. User passed token or it was generated.
        # Quick hack: Ask user for their local key if we can't find it?
        # Better: Just try to call it. If auth fails, prompt.
        
        # Actually, for 'clan create' we can perhaps bypass auth if on localhost? 
        # No, api requires it.
        # Let's ask user for their local key.
        token = typer.prompt("Enter your local Agent API Key (from gpuhost start output)", hide_input=True)
        
        resp = requests.post(f"http://localhost:8848/v2/clan/create?key={token}")
        if resp.status_code == 200:
            data = resp.json()
            print("\n✅ Clan Created Successfully!")
            print(f"Clan ID: {data['keys']['clan_id']}")
            print(f"👷 Worker Join Key: {data['keys']['worker_key']}")
            print(f"🧠 Client Access Key: {data['keys']['client_key']}")
            print("\nShare the Worker Key with System B to pool GPUs.")
        else:
            print(f"❌ Error: {resp.text}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}. Is gpuhost running?")

@app.command(name="clan-join")
def clan_join(host_url: str, worker_key: str):
    """[Worker] Join a remote Clan."""
    try:
        # 1. Get Local Info
        local_token = typer.prompt("Enter your local Agent API Key", hide_input=True)
        info_resp = requests.get(f"http://localhost:8848/info?key={local_token}")
        if info_resp.status_code != 200:
             print("❌ Could not get local info. Check key/server.")
             return
             
        local_info = info_resp.json()
        local_public_url = local_info["connection"]["public_url"]
        
        if not local_public_url:
            print("⚠️  No public URL found. Did you run 'gpuhost start --tunnel'?")
            confirm = typer.confirm("Continue with localhost URL? (Only works if Host is on same network)")
            if not confirm: return
            local_public_url = "http://localhost:8848"

        # 2. Join Remote
        payload = {
            "name": local_info["gpu"]["name"] + "-Worker",
            "url": local_public_url,
            "hardware": local_info["gpu"]
        }
        
        print(f"Connecting to Clan Host at {host_url}...")
        join_resp = requests.post(
            f"{host_url}/v2/clan/join", 
            headers={"Authorization": f"Bearer {worker_key}"},
            json=payload
        )
        
        if join_resp.status_code == 200:
            print(f"✅ Successfully joined Clan as node {join_resp.json()['node_id']}!")
        else:
            print(f"❌ Setup Failed: {join_resp.text}")
            
    except Exception as e:
         print(f"❌ Error: {e}")

if __name__ == "__main__":
    app()
=======
import typer
from gpuhost.agent import start_agent

app = typer.Typer(help="gpuhost – self-hosted GPU sharing agent")


@app.callback()
def main():
    """
    Manage the gpuhost agent.
    """
    pass


@app.command()
def start(
    tunnel: bool = typer.Option(False, "--tunnel", help="Expose agent via secure tunnel"),
    token: str = typer.Option(None, "--token", help="Manually set API Key")
):
    """Start the GPU host agent"""
    start_agent(tunnel=tunnel, token=token)

if __name__ == "__main__":
    app()
>>>>>>> 4b092473e6530ba53ab90c2e3dca88d9034ff8f5
