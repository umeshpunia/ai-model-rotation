import webbrowser
import pystray
from PIL import Image, ImageDraw
import uvicorn

from app.core.logging import get_logger

_logger = get_logger("desktop_tray")

class SystemTrayManager:
    """Orchestrates the lifecycle of the Windows system tray icon wrapper."""

    def __init__(self, uvicorn_server: uvicorn.Server, port: int) -> None:
        self.server = uvicorn_server
        self.port = port
        self.icon: pystray.Icon | None = None

    def _create_icon_image(self) -> Image.Image:
        """Dynamically generate a premium violet themed circular tray icon."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Background violet circle
        d.ellipse([4, 4, 60, 60], fill=(139, 92, 246), outline=(99, 102, 241), width=4)
        # Center square symbol representing the gateway router
        d.rectangle([22, 22, 42, 42], fill=(255, 255, 255))
        return img

    def _open_dashboard(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Action handler to launch the dashboard in the user's default browser."""
        url = f"http://127.0.0.1:{self.port}/"
        _logger.info("tray.open_dashboard", url=url)
        webbrowser.open(url)

    def _exit_app(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Action handler to stop background loops and exit the application."""
        _logger.info("tray.exit_triggered")
        if self.icon:
            self.icon.stop()
        self.server.should_exit = True

    def run(self) -> None:
        """Run the system tray icon loop (blocks the main thread)."""
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", self._open_dashboard, default=True),
            pystray.MenuItem("Status: Active", lambda: None, enabled=False),
            pystray.MenuItem("Exit", self._exit_app)
        )
        self.icon = pystray.Icon(
            "aigateway",
            self._create_icon_image(),
            "AI Gateway Pro",
            menu
        )
        _logger.info("tray.icon_running")
        self.icon.run()
