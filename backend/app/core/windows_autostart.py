import sys
from app.core.logging import get_logger

_logger = get_logger("windows_autostart")

def set_autostart(app_name: str, app_path: str, enable: bool) -> bool:
    """Add or remove windows autostart registry entries under HKCU CurrentVersion Run."""
    if sys.platform != "win32":
        _logger.info("autostart.skipped", reason="Not running on Windows.")
        return False

    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            _logger.info("autostart.enabled", app=app_name, path=app_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
                _logger.info("autostart.disabled", app=app_name)
            except FileNotFoundError:
                pass
                
        winreg.CloseKey(key)
        return True
    except Exception as e:
        _logger.error("autostart.failed", error=str(e))
        return False
