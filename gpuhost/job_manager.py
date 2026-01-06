import subprocess
import tempfile
import os
import uuid

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
            ["python", file_path],
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
