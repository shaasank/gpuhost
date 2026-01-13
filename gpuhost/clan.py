from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import time
import uuid

class Node(BaseModel):
    id: str
    role: str # "host" or "worker"
    name: str # e.g. "SystemA"
    url: str
    hardware: Dict[str, Any]
    status: str = "active"
    last_heartbeat: float = 0.0

class ClanState:
    def __init__(self):
        self.clan_id: Optional[str] = None
        self.host_id: Optional[str] = None
        self.nodes: Dict[str, Node] = {}
        self.admin_key: Optional[str] = None
        self.worker_join_key: Optional[str] = None
        self.client_access_key: Optional[str] = None
    
    def create_clan(self, host_node: Node, admin_key: str):
        self.clan_id = str(uuid.uuid4())
        self.host_id = host_node.id
        self.nodes[host_node.id] = host_node
        self.admin_key = admin_key
        self.worker_join_key = str(uuid.uuid4())
        self.client_access_key = str(uuid.uuid4())
        return {
            "clan_id": self.clan_id,
            "worker_key": self.worker_join_key,
            "client_key": self.client_access_key
        }

    def add_worker(self, worker_node: Node) -> bool:
        # Check Hardware Compatibility with Host
        host = self.nodes.get(self.host_id)
        if not host:
            return False # Should not happen

        if not self.check_compatibility(host.hardware, worker_node.hardware):
            print(f"[FAIL] Worker {worker_node.name} rejected: Incompatible Hardware.")
            return False

        self.nodes[worker_node.id] = worker_node
        print(f"[OK] Worker {worker_node.name} joined the Clan!")
        return True

    def check_compatibility(self, host_hw: Dict, worker_hw: Dict) -> bool:
        """
        Enforce strict safety checks to prevent crashes/errors.
        """
        # 1. Architecture Check (Must match for safe tensor parallelism usually, or at least feature set)
        # For this strict implementation, we require same Arch family.
        if host_hw.get("arch") != worker_hw.get("arch"):
            print(f"Compat Fail: Arch Mismatch ({host_hw.get('arch')} vs {worker_hw.get('arch')})")
            return False
            
        # 2. CUDA Capability (Must be very close, ideally identical)
        if host_hw.get("cuda_capability") != worker_hw.get("cuda_capability"):
             print(f"Compat Fail: CUDA Cap Mismatch")
             return False

        # 3. VRAM (Should be somewhat balanced, but strict equality not always required. 
        # For V2 prompts "balanced VRAM", let's warn but allow diffs if not too large?)
        # Let's enforce they are within 10% of each other for true pooling stability in this 'safe' clan.
        host_mem = host_hw.get("memory_total", 0)
        worker_mem = worker_hw.get("memory_total", 0)
        
        # Avoid div by zero mock
        if host_mem == 0: return True 

        ratio = worker_mem / host_mem
        if ratio < 0.9 or ratio > 1.1:
             print(f"Compat Fail: VRAM Imbalance ({host_mem} vs {worker_mem})")
             return False

        return True

    def get_aggregated_stats(self):
        total_vram = sum(n.hardware.get("memory_total", 0) for n in self.nodes.values())
        active_nodes = len(self.nodes)
        return {
            "total_vram": total_vram,
            "active_nodes": active_nodes,
            "nodes": [n.model_dump() for n in self.nodes.values()]
        }

# Global State Instance
clan = ClanState()
