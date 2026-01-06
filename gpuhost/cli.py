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
