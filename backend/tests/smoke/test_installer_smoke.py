import os
import subprocess
import time
import pytest
import httpx

def test_executable_smoke() -> None:
    """Verifies that the compiled PyInstaller executable starts up, responds on /health, and shuts down cleanly."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exe_path = os.path.join(root, "backend", "dist", "aigateway.exe")

    if not os.path.exists(exe_path):
        pytest.skip(f"Smoke test skipped: compiled binary not found at {exe_path}")

    # Start packaged binary process
    process = subprocess.Popen(
        [exe_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Allow time for server initialization
    time.sleep(3)

    try:
        # Check running instance responds
        res = httpx.get("http://127.0.0.1:8080/api/v1/health", timeout=5)
        assert res.status_code == 200
        assert res.json().get("status") == "healthy"
    finally:
        # Terminate and wait
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
