import socket
from app.core.logging import get_logger

_logger = get_logger("single_instance")

class SingleInstanceLock:
    """Uses a local loopback socket binding lock to guarantee only one backend instance runs."""

    def __init__(self, port: int = 49200) -> None:
        self.port = port
        self.sock: socket.socket | None = None

    def acquire(self) -> bool:
        """Attempt to bind to the lock port. Returns True if successful, False if already bound."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(("127.0.0.1", self.port))
            _logger.info("instance_lock.acquired", port=self.port)
            return True
        except socket.error:
            _logger.warning("instance_lock.failed", port=self.port, reason="Already running.")
            self.sock = None
            return False

    def release(self) -> None:
        """Close the socket to release the instance lock."""
        if self.sock:
            try:
                self.sock.close()
                _logger.info("instance_lock.released")
            except Exception as e:
                _logger.error("instance_lock.release_failed", error=str(e))
            finally:
                self.sock = None
