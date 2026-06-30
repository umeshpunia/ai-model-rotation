import sys
from app.core.single_instance import SingleInstanceLock
from app.core.windows_autostart import set_autostart

def test_single_instance_lock():
    # Use a custom test port to avoid conflicts
    lock1 = SingleInstanceLock(port=49299)
    lock2 = SingleInstanceLock(port=49299)

    try:
        # First acquire should succeed
        assert lock1.acquire() is True
        # Second acquire on same port should fail
        assert lock2.acquire() is False
    finally:
        lock1.release()
        lock2.release()

    # After release, it should be acquirable again
    try:
        assert lock1.acquire() is True
    finally:
        lock1.release()

def test_windows_autostart():
    # Calling set_autostart should execute without raising exceptions
    res = set_autostart("TestAIGateway", "dummy_path", False)
    if sys.platform == "win32":
        assert res is True
    else:
        assert res is False
