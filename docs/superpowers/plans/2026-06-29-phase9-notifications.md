# Phase 9 Notification System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design and build the dispatch system, concrete notification channels (desktop, email, Slack, Discord, Telegram, and generic webhooks), integrate notification triggers, persist history, and write unit/integration tests.

---

### Task 1: Create Notification Channels & Dispatcher

**Files:**
- Create: `backend/app/services/notifications/channels/base.py`
- Create: `backend/app/services/notifications/channels/desktop.py`
- Create: `backend/app/services/notifications/channels/email.py`
- Create: `backend/app/services/notifications/channels/slack.py`
- Create: `backend/app/services/notifications/channels/discord.py`
- Create: `backend/app/services/notifications/channels/telegram.py`
- Create: `backend/app/services/notifications/channels/webhook.py`
- Create: `backend/app/services/notifications/dispatcher.py`

- [ ] **Step 1: Write notification base channel class**
- [ ] **Step 2: Write Desktop notifications implementation**
- [ ] **Step 3: Write SMTP email notification implementation**
- [ ] **Step 4: Write Slack, Discord, Telegram, and generic webhook channel implementations**
- [ ] **Step 5: Write the primary NotificationDispatcher logic**

---

### Task 2: Integrate Event Triggers

**Files:**
- Modify: `backend/app/services/gateway_service.py`
- Modify: `backend/app/services/scheduler_jobs.py`

- [ ] **Step 1: Add triggers for key invalidation/disabling in `gateway_service.py`**
- [ ] **Step 2: Add triggers for cooldown/unknown and recovery checks in `scheduler_jobs.py`**
- [ ] **Step 3: Commit Task 1 and Task 2 changes**

---

### Task 3: Create Notification System Tests

**Files:**
- Create: `backend/tests/unit/test_notifications.py`

- [ ] **Step 1: Write unit tests verifying dispatches, mock channels, and trigger handlers**
- [ ] **Step 2: Run all tests to confirm compliance**
- [ ] **Step 3: Commit test suite additions**

---

### Task 4: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Check off Phase 9 checklists**
- [ ] **Step 2: Update Phase 9 summary status table**
- [ ] **Step 3: Commit phase tracking updates**
