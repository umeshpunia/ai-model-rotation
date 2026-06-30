# Phase 12 Desktop Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement system tray integration, single instance lock, and auto-start registry handlers.

---

### Task 1: Scaffolding Desktop Tray Icon

- [ ] **Step 1: Install `pystray` and `Pillow` dependencies in backend**
  - Run `pip install pystray Pillow` in the virtualenv.
- [ ] **Step 2: Create a system tray manager class at `backend/app/core/desktop_tray.py`**
  - Add "Open Dashboard", "Status", and "Exit" actions.
- [ ] **Step 3: Hook tray menu events to browser opening and application termination loops**

---

### Task 2: Single Instance Lock & Registry Auto-start

- [ ] **Step 1: Implement named file lock or socket lock in `backend/app/core/single_instance.py`**
- [ ] **Step 2: Implement registry writer utility in `backend/app/core/windows_autostart.py`**
  - Read active settings to decide if startup entry should be written.

---

### Task 3: Integration & Testing

- [ ] **Step 1: Update main app entry point to spawn tray in a background thread**
- [ ] **Step 2: Write tests checking lock files and registry keys**
- [ ] **Step 3: Update status in `phase.md` and walkthrough logs**
