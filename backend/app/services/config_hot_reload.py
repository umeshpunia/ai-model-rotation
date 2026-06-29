from app.core.config import reload_settings
from app.core.scheduler import get_scheduler_manager
from app.core.logging import get_logger

_logger = get_logger("config_hot_reload")

def trigger_config_hot_reload() -> None:
    """Clear cached settings, reload them, and propagate updates to running components."""
    _logger.info("config.hot_reload.trigger")
    
    # Reload settings cache
    reload_settings()
    
    # Reschedule background jobs scheduler
    scheduler = get_scheduler_manager()
    try:
        scheduler.reload()
        _logger.info("config.hot_reload.scheduler_reloaded")
    except Exception as e:
        _logger.error("config.hot_reload.scheduler_reload_failed", error=str(e))
