# Phase 13 Packaging & Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package Vite frontend assets inside PyInstaller executable and create Inno Setup installer rules.

---

### Task 1: Configure FastAPI to Serve Frontend Assets

- [ ] **Step 1: Update `backend/app/main.py` to mount static directory**
  - Mount `frontend/dist` or the temp `sys._MEIPASS/frontend/dist` path as static files at root route `/`.
- [ ] **Step 2: Add fallback wildcard path to support React Router client-side URL routing**
  - Ensure that accessing paths like `/providers` or `/keys` directly returns the index HTML page.

---

### Task 2: PyInstaller Scaffolding

- [ ] **Step 1: Install `pyinstaller` in virtualenv**
- [ ] **Step 2: Create a spec file `backend/aigateway.spec` to configure data files and folder structures**
- [ ] **Step 3: Write a wrapper script `scripts/build_executable.py` that builds the frontend and runs pyinstaller**

---

### Task 3: Inno Setup Script

- [ ] **Step 1: Write an Inno Setup file at `scripts/installer_setup.iss`**
- [ ] **Step 2: Define registry keys, desktop/startup shortcuts, and uninstaller rules**
- [ ] **Step 3: Document compiler instructions in the README**
