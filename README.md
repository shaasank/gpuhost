# gpuhost

**gpuhost** is a self-hosted GPU sharing agent that turns your local machine into a private GPU cloud.

## Features
- **One-Command Setup**: `gpuhost start --tunnel`
- **Secure Tunnels**: Automatically exposes a public URL.
- **Smart Locking**: Ensures exclusive 1-user-at-a-time access.
- **Job Execution**: Submit Python scripts remotely.
- **Client Library**: Includes `gpuhost.client` for automation.

## Installation

```bash
pip install gpuhost
```

## Usage

**On Host (with NVIDIA GPU):**
```bash
gpuhost start --tunnel
```

**On Client (Remote):**
```python
from gpuhost.client import GPUClient

client = GPUClient("https://<your-url>", "<token>")
if client.lock():
    client.submit_job("print('Running on GPU!')")
    client.unlock()
```
