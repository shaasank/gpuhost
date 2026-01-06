import requests
import uuid
import time
import dill
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

class GPUClient:
    def __init__(self, url: str, token: Optional[str] = None):
        # Robust URL parsing to handle "Free-link" copy-hasting
        parsed = urlparse(url)
        
        # 1. Extract token from URL if not explicitly provided
        if not token and parsed.query:
            qs = parse_qs(parsed.query)
            if "key" in qs:
                token = qs["key"][0]

        # 2. Clean Base URL (remove query params and trailing slash)
        # Reconstruct: scheme://netloc/path
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        self.url = clean_url.rstrip("/")
        
        if not token:
            raise ValueError("API Token is required (either passed as arg or in URL ?key=)")
            
        self.token = token
        self.owner_id = str(uuid.uuid4())
        self.headers = {"Authorization": f"Bearer {token}"}
        
    def get_info(self) -> Dict[str, Any]:
        """Fetch GPU status"""
        res = requests.get(f"{self.url}/info", headers=self.headers)
        if res.status_code == 403:
            raise PermissionError("Invalid API Key")
        res.raise_for_status()
        return res.json()

    def lock(self) -> bool:
        """Attempt to lock the GPU"""
        try:
            res = requests.post(
                f"{self.url}/lock", 
                json={"owner_id": self.owner_id},
                headers=self.headers
            )
            if res.status_code == 503:
                print("❌ Link is being used (GPU is busy).")
                return False
            res.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            print(f"Lock failed: {e}")
            return False

    def unlock(self) -> bool:
        """Unlock the GPU"""
        try:
            res = requests.post(
                f"{self.url}/unlock", 
                json={"owner_id": self.owner_id},
                headers=self.headers
            )
            res.raise_for_status()
            return True
        except Exception as e:
            print(f"Unlock failed: {e}")
            return False

    def submit_job(self, code: str) -> Dict[str, Any]:
        """Submit python code for execution"""
        res = requests.post(
            f"{self.url}/submit",
            json={"owner_id": self.owner_id, "code": code},
            headers=self.headers
        )
        res.raise_for_status()
        return res.json()
    
    def run_file(self, file_path: str) -> Dict[str, Any]:
        """Read and submit a local python file"""
        with open(file_path, "r") as f:
            code = f.read()
        return self.submit_job(code)

    def remote(self, func):
        """
        Decorator to execute a function on the remote GPU.
        The function and its closure are serialized and sent to the host.
        Returns the result of the function execution.
        """
        def wrapper(*args, **kwargs):
            # Serialize the function execution (closure + args)
            if args or kwargs:
                job_func = lambda: func(*args, **kwargs)
            else:
                job_func = func
            
            # Pickle
            pickle_hex = dill.dumps(job_func).hex()
            
            # Submit
            res = requests.post(
                f"{self.url}/submit",
                json={
                    "owner_id": self.owner_id, 
                    "type": "pickle", 
                    "pickle_data": pickle_hex
                },
                headers=self.headers
            )
            res.raise_for_status()
            data = res.json()
            
            if data["status"] == "success":
                # Deserialize Result
                return dill.loads(bytes.fromhex(data["result"]))
            else:
                raise RuntimeError(f"Remote execution failed:\n{data['stderr']}")
                
        return wrapper
