import pynvml
from typing import Dict, Any, Optional

def init_gpu():
    try:
        pynvml.nvmlInit()
        return True
    except pynvml.NVMLError:
        return False

def shutdown_gpu():
    try:
        pynvml.nvmlShutdown()
    except pynvml.NVMLError:
        pass

def get_gpu_info() -> Optional[Dict[str, Any]]:
    """
    Returns information about the primary GPU (index 0).
    If no GPU is found or nvml fails, returns a mock dict for testing capability
    on non-GPU machines, or None if completely unable to run.
    """
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        # Handle bytes vs string return type for older pynvml versions
        if isinstance(name, bytes):
            name = name.decode("utf-8")
            
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        driver_version = pynvml.nvmlSystemGetDriverVersion()
        if isinstance(driver_version, bytes):
            driver_version = driver_version.decode("utf-8")

        return {
            "name": name,
            "memory_total": memory_info.total,
            "memory_free": memory_info.free,
            "memory_used": memory_info.used,
            "driver_version": driver_version
        }
    except pynvml.NVMLError:
        # Fallback for dev/testing on non-GPU implementations
        # In production this might return None or raise
        print("Warning: GPU not detected or NVML error. Returning Mock Data.")
        return {
            "name": "Mock NVIDIA GPU (Simulated)",
            "memory_total": 24000 * 1024 * 1024,
            "memory_free": 24000 * 1024 * 1024,
            "memory_used": 0,
            "driver_version": "535.00 (Mock)"
        }
