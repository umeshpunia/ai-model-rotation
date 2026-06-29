# Design Specification: Phase 9 Notification System

## 1. Goal
Implement a plugin-based Notification System supporting desktop, SMTP email, Slack, Discord, Telegram, and generic HTTP webhook integrations. The system will persist alerts history and support standard triggers.

## 2. Requirements & Scope
- **Notification Dispatcher**: Create `NotificationService` that resolves active notification channels dynamically and dispatches alerts asynchronously.
- **Channels**:
  - **Desktop**: Cross-platform notifier using system toast commands/logs.
  - **Email**: SMTP MIME notifier using python's built-in `smtplib`.
  - **Slack**: Send markdown payloads to Slack Webhooks.
  - **Discord**: Send embeds payloads to Discord Webhooks.
  - **Telegram**: Send text alerts using Bot API `/sendMessage`.
  - **Generic Webhook**: HTTP POST payload requests.
- **Triggers**:
  - Key invalid, disabled, or provider offline.
  - Key/provider recovery.
  - Quota limit reaches.
  - All providers unavailable.
- **Persistence**: Log all triggered notifications to the database `notifications` table.

## 3. Architecture Details

```
backend/app/services/notifications/
  ├── __init__.py (Service registry)
  ├── dispatcher.py (Aggregates triggers and schedules dispatches)
  └── channels/
        ├── base.py
        ├── desktop.py
        ├── email.py
        ├── slack.py
        ├── discord.py
        ├── telegram.py
        └── webhook.py
```
Event triggers will invoke `dispatcher.notify(...)` which persists the record in the SQLite database and spawns background tasks for configured channels.
