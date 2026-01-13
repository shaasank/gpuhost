import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app and clan state
from gpuhost.api import app
from gpuhost.clan import clan

client = TestClient(app)

class TestGPUHostV2(unittest.TestCase):
    
    def setUp(self):
        # Reset Clan State
        clan.nodes = {}
        clan.clan_id = None
        clan.host_id = None
    
    @patch("gpuhost.api.get_gpu_info")
    def test_clan_flow(self, mock_gpu):
        # 1. SETUP HOST (System A) with RTX 3050 (Ampere)
        mock_gpu.return_value = {
            "name": "NVIDIA GeForce RTX 3050",
            "arch": "Ampere",
            "cuda_capability": "8.6",
            "tensor_cores": True,
            "memory_total": 8 * 1024 * 1024 * 1024, # 8GB
        }
        
        # Create Clan (Auth needed? api.py says depends on verify_token -> checks global AUTH_TOKEN)
        # We need to set auth token first
        from gpuhost.api import set_auth_token
        set_auth_token("admin-secret")
        
        resp = client.post("/v2/clan/create?key=admin-secret")
        self.assertEqual(resp.status_code, 200)
        keys = resp.json()["keys"]
        worker_key = keys["worker_key"]
        client_key = keys["client_key"]
        
        print("\n[TEST] Clan Created. Keys:", keys)
        
        # 2. WORKER JOIN SUCCESS (System B) with RTX 3050
        worker_payload = {
            "name": "Worker-SystemB",
            "url": "http://192.168.1.5:8848",
            "hardware": {
                "name": "NVIDIA GeForce RTX 3050",
                "arch": "Ampere", # Same Arch
                "cuda_capability": "8.6",
                "tensor_cores": True,
                "memory_total": 8 * 1024 * 1024 * 1024 # Same VRAM
            }
        }
        
        join_resp = client.post(
            "/v2/clan/join",
            headers={"Authorization": f"Bearer {worker_key}"},
            json=worker_payload
        )
        self.assertEqual(join_resp.status_code, 200)
        print("[TEST] Worker B Joined Successfully.")
        
        # 3. WORKER JOIN FAIL (System X) with GTX 1080 (Pascal)
        # Should fail due to Arch Mismatch or CUDA Cap
        incompatible_payload = {
            "name": "Worker-SystemX",
            "url": "http://192.168.1.9:8848",
            "hardware": {
                "name": "NVIDIA GeForce GTX 1080",
                "arch": "Pascal", # Mismatch!
                "cuda_capability": "6.1",
                "tensor_cores": False, # Mismatch!
                "memory_total": 8 * 1024 * 1024 * 1024
            }
        }
        
        fail_resp = client.post(
            "/v2/clan/join",
            headers={"Authorization": f"Bearer {worker_key}"},
            json=incompatible_payload
        )
        self.assertEqual(fail_resp.status_code, 400)
        print(f"[TEST] Incompatible Worker Rejected as expected: {fail_resp.json()['detail']}")

        # 4. CLIENT ACCESS (System C)
        chat_req = {
            "model": "llama3-8b",
            "messages": [{"role": "user", "content": "Hello Clan"}]
        }
        
        chat_resp = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {client_key}"},
            json=chat_req
        )
        self.assertEqual(chat_resp.status_code, 200)
        print("[TEST] Client Request Processed:", chat_resp.json())

if __name__ == "__main__":
    unittest.main()
