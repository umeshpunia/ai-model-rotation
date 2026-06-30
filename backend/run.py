import os
import sys
import threading
import time
import uvicorn

from app.core.config import get_settings
from app.core.single_instance import SingleInstanceLock
from app.core.windows_autostart import set_autostart
from app.core.desktop_tray import SystemTrayManager
from app.core.logging import get_logger

_logger = get_logger("run")

def main() -> None:
    # 1. Acquire single instance lock
    lock = SingleInstanceLock()
    if not lock.acquire():
        _logger.warning("run.exit", reason="AI Gateway Pro is already running.")
        sys.exit(1)

    settings = get_settings()
    host = settings.host.host_bind
    port = settings.host.host_port

    # 2. Configure Windows autostart based on configuration settings
    try:
        executable = sys.executable
        script_path = os.path.abspath(__file__)
        # If running as a bundled executable (via PyInstaller), sys.executable is the binary path
        app_path = executable if getattr(sys, "frozen", False) else f'"{executable}" "{script_path}"'
        set_autostart("AIGatewayPro", app_path, settings.tray.auto_start_with_windows)
    except Exception as e:
        _logger.error("run.autostart_config_failed", error=str(e))

    # 3. Disable standard uvicorn signal handlers to let the tray control exit loops cleanly
    class UvicornServer(uvicorn.Server):
        def install_signal_handlers(self) -> None:
            pass

    config = uvicorn.Config("app.main:app", host=host, port=port, log_level="info")
    server = UvicornServer(config)

    # 4. Start the FastAPI server inside a background thread
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    _logger.info("run.server_thread_started", host=host, port=port)

    # 5. Launch System Tray Icon on the main thread if enabled, else block
    if settings.tray.tray_enabled:
        tray = SystemTrayManager(server, port)
        try:
            tray.run()
        finally:
            server.should_exit = True
            lock.release()
    else:
        _logger.info("run.blocking_main_thread")
        try:
            while not server.should_exit:
                time.sleep(1)
        except KeyboardInterrupt:
            server.should_exit = True
        finally:
            lock.release()

if __name__ == "__main__":
    main()
