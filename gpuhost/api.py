from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import secrets
import time

from gpuhost.state import state
from gpuhost.gpu import get_gpu_info
from gpuhost.job_manager import execute_code

app = FastAPI(title="gpuhost")

# Authentication
AUTH_TOKEN = None

def set_auth_token(token: str):
    global AUTH_TOKEN
    AUTH_TOKEN = token

async def verify_token(request: Request):
    if AUTH_TOKEN is None:
        return # Dev mode / Unprotected if no token set (should not happen in prod flow)
    
    # 1. Check Query Param (for Free-links)
    token = request.query_params.get("key")
    if token == AUTH_TOKEN:
        return token

    # 2. Check Header (for Programmatic access)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        parts = auth_header.split(" ")
        if len(parts) == 2:
            token = parts[1]
            # V1 Check
            if token == AUTH_TOKEN:
                return token
            # V2 Clan Checks
            from gpuhost.clan import clan
            if token in [clan.admin_key, clan.worker_join_key, clan.client_access_key]:
                return token
            
    # 3. GUI Static files - Allow (but data endpoints will fail)
    # Actually, we want the GUI to load, but it needs the key to make requests.
    # If this is a data endpoint, reject.
    # The middleware/dependency approach is cleaner.
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, 
        detail="Invalid or missing API Key" 
    )

# Ensure static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

class LockRequest(BaseModel):
    owner_id: str

class SubmitRequest(BaseModel):
    owner_id: str
    code: Optional[str] = None
    pickle_data: Optional[str] = None
    type: str = "code" # "code" or "pickle"

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/info", dependencies=[Depends(verify_token)])
def get_info():
    gpu_info = get_gpu_info()
    status = state.get_status()
    return {
        "gpu": gpu_info,
        "status": status,
        "agent_version": "0.1.0",
        "connection": {
            "public_url": state.public_url,
            "token": state.auth_token
        }
    }

@app.post("/lock", dependencies=[Depends(verify_token)])
def lock_gpu(req: LockRequest):
    # Check if already locked by someone else
    status = state.get_status()
    if status["is_locked"] and status["owner_id"] != req.owner_id:
        raise HTTPException(
            status_code=503, # Service Unavailable / Busy
            detail="Link is being used" 
        )

    success = state.lock(req.owner_id)
    if not success:
         # Should be covered above, but race condition safety
        raise HTTPException(status_code=503, detail="Link is being used")
    return {"status": "locked", "owner_id": req.owner_id}

@app.post("/unlock", dependencies=[Depends(verify_token)])
def unlock_gpu(req: LockRequest):
    success = state.unlock(req.owner_id)
    if not success:
        raise HTTPException(status_code=403, detail="Unauthorized unlock attempt")
    return {"status": "unlocked"}

@app.post("/submit", dependencies=[Depends(verify_token)])
def submit_job(req: SubmitRequest):
    # Enforce Locking
    status = state.get_status()
    if not status["is_locked"]:
         raise HTTPException(status_code=400, detail="GPU must be locked to submit jobs")
    
    if status["owner_id"] != req.owner_id:
        raise HTTPException(status_code=403, detail="Unauthorized: You do not own the lock")

    # Execute based on Type
    if req.type == "pickle":
        if not req.pickle_data:
             raise HTTPException(status_code=400, detail="Missing pickle_data")
        from gpuhost.job_manager import execute_pickle
        return execute_pickle(req.pickle_data)
        
    else:
        # Default: Code
        if not req.code:
             raise HTTPException(status_code=400, detail="Missing code")
        result = execute_code(req.code)
        return result

# --- V2 CLAN API ---
from gpuhost.clan import clan, Node

@app.post("/v2/clan/create")
def create_clan():
    # Only the local owner can do this effectively (or protected by initial token)
    # For now, we assume this is called locally or by owner.
    # We use the existing state.gpu_info which now should be detailed.
    
    # Refresh GPU info to be sure
    gpu_info = get_gpu_info()
    
    host_node = Node(
        id=state.owner_id if state.owner_id else "host-node-" + secrets.token_hex(4),
        role="host",
        name="HostSystem",
        url=state.public_url if state.public_url else "http://localhost:8848",
        hardware=gpu_info
    )
    
    keys = clan.create_clan(host_node, state.auth_token)
    return {"status": "Clan Created", "keys": keys, "host_info": host_node.model_dump()}

class JoinRequest(BaseModel):
    name: str
    url: str
    hardware: dict

@app.post("/v2/clan/join")
def join_clan(req: JoinRequest, token: str = Depends(verify_token)):
    # Validate Worker Key
    if token != clan.worker_join_key:
        raise HTTPException(status_code=403, detail="Invalid Worker Join Key")
        
    worker_node = Node(
        id="worker-" + secrets.token_hex(4),
        role="worker",
        name=req.name,
        url=req.url,
        hardware=req.hardware
    )
    
    success = clan.add_worker(worker_node)
    if not success:
        raise HTTPException(status_code=400, detail="Hardware Incompatible with Clan Host")
        
    return {"status": "Joined", "node_id": worker_node.id}

@app.get("/v2/clan/status")
def clan_status(token: str = Depends(verify_token)):
    # Allow Admin or Client to see status (maybe restricted view for client later)
    if token not in [clan.admin_key, clan.client_access_key]:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return clan.get_aggregated_stats()

# --- V2 CLIENT API (Standardized) ---

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    max_tokens: Optional[int] = 100

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, token: str = Depends(verify_token)):
    if token != clan.client_access_key and token != clan.admin_key:
         raise HTTPException(status_code=403, detail="Invalid Client Key")

    # Distributed Logic Placeholder
    # 1. Check if we have nodes
    if not clan.nodes:
        raise HTTPException(status_code=503, detail="No active GPU nodes in Clan")

    # 2. Naive Scheduling: Send to Host (System A) or Worker (System B)
    # Real logic would check load/availability.
    # For this MVP, we just verify we CAN run it.
    
    return {
        "id": "chatcmpl-" + secrets.token_hex(4),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"Processed by GPUHOST Clan. [Nodes: {len(clan.nodes)}] [Mock Response]" 
            },
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    }
