from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os
import secrets

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
        return

    # 2. Check Header (for Programmatic access)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token == AUTH_TOKEN:
            return
            
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
    code: str

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
        "agent_version": "0.1.0"
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

    # Execute
    result = execute_code(req.code)
    return result
