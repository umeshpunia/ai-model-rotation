import pytest
from unittest.mock import AsyncMock, patch
from sqlmodel import SQLModel, select

from app.core.database import session_scope, get_settings, dispose_engine, get_engine
from app.domain.entities.notification import Notification
from app.domain.enums import NotificationSeverity, NotificationChannel
from app.services.notifications.dispatcher import NotificationDispatcher

import os

@pytest.fixture(autouse=True)
def setup_test_db():
    settings = get_settings()
    original_url = settings.database.database_url
    original_test_url = settings.database.database_test_url
    db_file = "test_notifications.db"
    settings.database.database_url = f"sqlite:///{db_file}"
    settings.database.database_test_url = f"sqlite:///{db_file}"
    dispose_engine()
    
    SQLModel.metadata.create_all(get_engine())
    yield
    
    SQLModel.metadata.drop_all(get_engine())
    settings.database.database_url = original_url
    settings.database.database_test_url = original_test_url
    dispose_engine()
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

@pytest.mark.anyio
async def test_notification_dispatcher_persistence():
    dispatcher = NotificationDispatcher()
    
    # Mock all channels to return success immediately
    for key in dispatcher.channels:
        dispatcher.channels[key].send = AsyncMock(return_value=True)
        
    with session_scope() as session:
        notif = dispatcher.notify(
            session=session,
            severity=NotificationSeverity.INFO,
            event_type="test.event",
            title="Test Title",
            message="Test message details",
            meta={"key": "val"}
        )
        assert notif.id is not None
        assert notif.title == "Test Title"
        assert notif.severity == NotificationSeverity.INFO
        notif_id = notif.id
        
    # Wait a brief moment to let background task run after commit
    await asyncio_sleep_helper(0.1)
    
    # Query DB to check if persisted and updated in a new session
    with session_scope() as session:
        db_notif = session.get(Notification, notif_id)
        assert db_notif is not None
        assert db_notif.is_sent is True
        assert db_notif.delivery_error == ""

@pytest.mark.anyio
async def test_notification_dispatch_failure():
    dispatcher = NotificationDispatcher()
    
    # Mock desktop channel to fail and others to pass/fail
    for key in dispatcher.channels:
        dispatcher.channels[key].send = AsyncMock(return_value=False)
        
    with session_scope() as session:
        notif = dispatcher.notify(
            session=session,
            severity=NotificationSeverity.ERROR,
            event_type="test.fail",
            title="Fail Title",
            message="Fail message details"
        )
        assert notif.id is not None
        notif_id = notif.id
        
    await asyncio_sleep_helper(0.1)
    
    # Query DB to check if marked not sent and errors logged
    with session_scope() as session:
        db_notif = session.get(Notification, notif_id)
        assert db_notif is not None
        assert db_notif.is_sent is False
        assert "desktop failed" in db_notif.delivery_error

async def asyncio_sleep_helper(secs: float):
    import asyncio
    await asyncio.sleep(secs)
