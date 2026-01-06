import requests
import uuid
import time
from typing import Optional, Dict, Any

class GPUClient:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
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
