from datetime import datetime
from typing import Optional, Dict

class GPUState:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GPUState, cls).__new__(cls)
            cls._instance.is_locked = False
            cls._instance.owner_id: Optional[str] = None
            cls._instance.workload_start_time: Optional[datetime] = None
            cls._instance.public_url = None
            cls._instance.auth_token = None
            
        return cls._instance

    def lock(self, owner_id: str) -> bool:
        """
        Attempts to lock the GPU for a specific owner.
        Returns True if successful, False if already locked.
        """
        if self.is_locked:
            return False
            
        self.is_locked = True
        self.owner_id = owner_id
        self.workload_start_time = datetime.now()
        return True

    def unlock(self, owner_id: str) -> bool:
        """
        Attempts to unlock the GPU.
        Only the owner can unlock.
        """
        if not self.is_locked:
            return True # Already free
            
        if self.owner_id != owner_id:
            return False # Unauthorized
            
        self.is_locked = False
        self.owner_id = None
        self.workload_start_time = None
        return True

    def get_status(self) -> Dict:
        return {
            "is_locked": self.is_locked,
            "owner_id": self.owner_id,
            "workload_duration": str(datetime.now() - self.workload_start_time) if self.workload_start_time else None
        }

state = GPUState()
