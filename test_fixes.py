
import threading
import time
import sys
import os
import asyncio
from unittest.mock import MagicMock
import dill
from gpuhost.state import GPUState
from gpuhost.api import verify_token, set_auth_token
from gpuhost.job_manager import execute_pickle
from fastapi import HTTPException
from fastapi import Request

# 1. Test Locking
def test_locking():
    print("Testing Locking...")
    state = GPUState()
    
    successes = 0
    
    def try_lock(i):
        nonlocal successes
        if state.lock(f"owner_{i}"):
            print(f"Thread {i} acquired lock")
            time.sleep(0.1)
            state.unlock(f"owner_{i}")
            successes += 1
        else:
            print(f"Thread {i} failed to acquire lock")

    threads = []
    for i in range(5):
        t = threading.Thread(target=try_lock, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print(f"Locking test finished. Total successes should be 5 (sequential) or less if race, but no crashes. Actually with sleep, if it works perfectly effectively, they might serialize.")

# 2. Test API Header Crash
async def test_auth_header():
    print("\nTesting Auth Header...")
    set_auth_token("secret123")
    
    # Case 1: Checking Malformed Header (Should not crash)
    req = MagicMock(spec=Request)
    req.query_params = {}
    req.headers = {"Authorization": "Bearer"} # No token part
    
    try:
        await verify_token(req)
        print("FAIL: Should have raised 403")
    except HTTPException as e:
        print(f"PASS: Raised {e.status_code} on malformed header")
    except Exception as e:
        print(f"FAIL: Crashed with {type(e)}: {e}")

    # Case 2: Good Header
    req.headers = {"Authorization": "Bearer secret123"}
    try:
        await verify_token(req)
        print("PASS: Accepted valid header")
    except Exception as e:
        print(f"FAIL: Rejected valid header with {e}")

# 3. Test Pickle Execution
def test_pickle():
    print("\nTesting Pickle Execution...")
    
    def hello():
        return "Hello World"
        
    pickle_hex = dill.dumps(hello).hex()
    
    result = execute_pickle(pickle_hex)
    if result["status"] == "success":
        res_obj = dill.loads(bytes.fromhex(result["result"]))
        if res_obj == "Hello World":
            print("PASS: Pickle executed and returned correct result")
        else:
            print(f"FAIL: Wrong result: {res_obj}")
    else:
        print(f"FAIL: Execution error: {result}")

if __name__ == "__main__":
    test_locking()
    asyncio.run(test_auth_header())
    test_pickle()
