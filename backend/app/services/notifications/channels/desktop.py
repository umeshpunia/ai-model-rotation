import asyncio
import os
import sys
from typing import Any
from app.services.notifications.channels.base import BaseNotificationChannel
from app.core.logging import get_logger

_logger = get_logger("desktop_notification")

class DesktopNotificationChannel(BaseNotificationChannel):
    """Sends desktop notifications (uses Windows PowerShell script with structured log fallback)."""

    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        _logger.info("notification.desktop.dispatch", title=title, message=message)
        
        # Check if Windows
        if sys.platform == "win32":
            try:
                # Escape quotes
                safe_title = title.replace('"', '\\"')
                safe_message = message.replace('"', '\\"')
                
                # PowerShell balloon tip script
                ps_script = (
                    f'[void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms"); '
                    f'$icon = New-Object System.Windows.Forms.NotifyIcon; '
                    f'$icon.Icon = [System.Drawing.SystemIcons]::Information; '
                    f'$icon.BalloonTipIcon = "Info"; '
                    f'$icon.BalloonTipTitle = "{safe_title}"; '
                    f'$icon.BalloonTipText = "{safe_message}"; '
                    f'$icon.Visible = $True; '
                    f'$icon.ShowBalloonTip(5000)'
                )
                
                proc = await asyncio.create_subprocess_exec(
                    "powershell",
                    "-Command",
                    ps_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.wait()
                return proc.returncode == 0
            except Exception as e:
                _logger.error("notification.desktop.powershell_failed", error=str(e))
                
        # Non-Windows or script failure fallback is successful log dispatch
        return True
