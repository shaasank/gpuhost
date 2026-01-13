<<<<<<< HEAD
import subprocess
import tempfile
import os
import uuid
import dill
import sys

def execute_code(code: str) -> dict:
    """
    Executes the provided Python code in a subprocess.
    Returns dictionary with stdout, stderr, and return_code.
    """
    job_id = str(uuid.uuid4())
    filename = f"job_{job_id}.py"
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    try:
        # Write code to temp file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Execute
        # Timeout after 600 seconds (10 mins) to allow for LLM loading
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=600
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "status": "success" if result.returncode == 0 else "error"
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out (60s limit)",
            "return_code": -1,
            "status": "timeout"
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "status": "internal_error"
        }
    finally:
        # Cleanup
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

def execute_pickle(pickle_hex: str) -> dict:
    """
    Executes a pickled function in a subprocess.
    Returns the pickled result or stderr.
    """
    job_id = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    
    input_path = os.path.join(temp_dir, f"in_{job_id}.pkl")
    output_path = os.path.join(temp_dir, f"out_{job_id}.pkl")
    runner_path = os.path.join(temp_dir, f"runner_{job_id}.py")
    
    # 1. Runner Script
    runner_code = """
import dill
import sys

try:
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "rb") as f:
        func = dill.load(f)
    
    # Run the function
    # Note: We assume the function takes no args for this simple implementation
    # or that args were bound in the closure.
    result = func()
    
    with open(output_path, "wb") as f:
        dill.dump(result, f)
        
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
"""

    try:
        # Write Input Pickle
        with open(input_path, "wb") as f:
            f.write(bytes.fromhex(pickle_hex))
            
        # Write Runner
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(runner_code)
            
        # Execute
        proc = subprocess.run(
            [sys.executable, runner_path, input_path, output_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if proc.returncode != 0:
            return {
                "status": "error",
                "stderr": proc.stderr or "Unknown error",
                "stdout": proc.stdout
            }
            
        # Read Result
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                res_bytes = f.read()
            return {
                "status": "success",
                "result": res_bytes.hex(),
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }
        else:
             return {
                "status": "error",
                "stderr": "No output file produced",
                "stdout": proc.stdout
            }
            
    except Exception as e:
        return {"status": "internal_error", "stderr": str(e)}
    finally:
        for p in [input_path, output_path, runner_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
=======
import subprocess
import tempfile
import os
import uuid
import dill
import sys

def execute_code(code: str) -> dict:
    """
    Executes the provided Python code in a subprocess.
    Returns dictionary with stdout, stderr, and return_code.
    """
    job_id = str(uuid.uuid4())
    filename = f"job_{job_id}.py"
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    try:
        # Write code to temp file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Execute
        # Timeout after 600 seconds (10 mins) to allow for LLM loading
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=600
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "status": "success" if result.returncode == 0 else "error"
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Execution timed out (60s limit)",
            "return_code": -1,
            "status": "timeout"
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "status": "internal_error"
        }
    finally:
        # Cleanup
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

def execute_pickle(pickle_hex: str) -> dict:
    """
    Executes a pickled function in a subprocess.
    Returns the pickled result or stderr.
    """
    job_id = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    
    input_path = os.path.join(temp_dir, f"in_{job_id}.pkl")
    output_path = os.path.join(temp_dir, f"out_{job_id}.pkl")
    runner_path = os.path.join(temp_dir, f"runner_{job_id}.py")
    
    # 1. Runner Script
    runner_code = f"""
import dill
import sys

try:
    with open(r"{input_path}", "rb") as f:
        func = dill.load(f)
    
    # Run the function
    # Note: We assume the function takes no args for this simple implementation
    # or that args were bound in the closure.
    result = func()
    
    with open(r"{output_path}", "wb") as f:
        dill.dump(result, f)
        
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
"""

    try:
        # Write Input Pickle
        with open(input_path, "wb") as f:
            f.write(bytes.fromhex(pickle_hex))
            
        # Write Runner
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(runner_code)
            
        # Execute
        proc = subprocess.run(
            [sys.executable, runner_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if proc.returncode != 0:
            return {
                "status": "error",
                "stderr": proc.stderr or "Unknown error",
                "stdout": proc.stdout
            }
            
        # Read Result
        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                res_bytes = f.read()
            return {
                "status": "success",
                "result": res_bytes.hex(),
                "stdout": proc.stdout,
                "stderr": proc.stderr
            }
        else:
             return {
                "status": "error",
                "stderr": "No output file produced",
                "stdout": proc.stdout
            }
            
    except Exception as e:
        return {"status": "internal_error", "stderr": str(e)}
    finally:
        for p in [input_path, output_path, runner_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
>>>>>>> 4b092473e6530ba53ab90c2e3dca88d9034ff8f5
