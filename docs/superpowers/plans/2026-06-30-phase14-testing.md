# Phase 14 Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish external client mocks, run test coverage audits, and implement executable smoke tests.

---

### Task 1: Provider Mocks & Key Rotation Scenarios

- [ ] **Step 1: Setup mock provider HTTP interceptors using `respx` or similar fixtures**
- [ ] **Step 2: Write tests in `backend/tests/unit/test_mock_rotation.py` verifying failover chains**
  - Verify key goes to cooldown on 429.
  - Verify key goes to invalid on 401.

---

### Task 2: Executable Smoke Tests

- [ ] **Step 1: Write `backend/tests/smoke/test_installer_smoke.py`**
  - Check if binary file `dist/aigateway.exe` exists.
  - Spawn subprocess, poll `/health` endpoint.
  - Shut down process and check lock release.

---

### Task 3: Coverage Audit & Final Report

- [ ] **Step 1: Run coverage and generate reports (`pytest --cov=app`)**
- [ ] **Step 2: Update status in `phase.md`**
