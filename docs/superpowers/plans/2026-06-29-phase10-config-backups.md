# Phase 10 Configuration, Profiles & Backups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement settings profiles, hot-reload, backup CRUD, manual backups, backup restores, and write full test coverage.

---

### Task 1: Scaffolding Backup Service & Router

**Files:**
- Create: `backend/app/services/backup_service.py`
- Create: `backend/app/routers/backups.py`
- Modify: `backend/app/routers/__init__.py`

- [ ] **Step 1: Write BackupService handling directory configuration, ZIP creation, and database replacement**
- [ ] **Step 2: Create Backups router endpoints (`list`, `create`, `delete`, `restore`)**
- [ ] **Step 3: Register Backups router in `api_router` in `backend/app/routers/__init__.py`**

---

### Task 2: Implement Settings Profiles & Hot-Reload Handler

**Files:**
- Modify: `backend/app/routers/settings.py`
- Create: `backend/app/services/config_hot_reload.py`

- [ ] **Step 1: Write `config_hot_reload.py` to reload logger configuration and reschedule scheduler intervals on settings update**
- [ ] **Step 2: Integrate hot-reload triggers in `settings.py`'s CRUD PUT and IMPORT operations**

---

### Task 3: Configuration & Backups System Testing

**Files:**
- Create: `backend/tests/unit/test_backups.py`
- Modify: `backend/tests/integration/test_api.py`

- [ ] **Step 1: Write unit tests verifying backup creation, deletion, and DB restores**
- [ ] **Step 2: Run all tests to confirm correct behavior**
- [ ] **Step 3: Commit all changes**

---

### Task 4: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Check off Phase 10 checklists**
- [ ] **Step 2: Update Phase 10 summary status table**
- [ ] **Step 3: Commit phase tracking updates**
