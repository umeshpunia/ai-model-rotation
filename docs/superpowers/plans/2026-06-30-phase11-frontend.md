# Phase 11 Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a stunning, high-performance React + TypeScript + Tailwind admin dashboard dashboard under `frontend/`.

---

### Task 1: Project Scaffolding & Setup

- [ ] **Step 1: Check options and initialize Vite + TS project in `frontend/`**
  - Run `npx create-vite@latest --help` first.
  - Run `npx create-vite@latest frontend --template react-ts` non-interactively.
- [ ] **Step 2: Install standard router, UI, state, and styling dependencies**
  - Install: `@tanstack/react-query`, `lucide-react`, `react-router-dom`, `zustand`, `tailwindcss`, `postcss`, `autoprefixer`, `recharts`.
- [ ] **Step 3: Setup Tailwind CSS configurations and base styles**
  - Configure `tailwind.config.js`, `postcss.config.js`, and `src/index.css`.
- [ ] **Step 4: Install shadcn/ui components (button, card, dialog, input, select, table, badge, toast)**

---

### Task 2: Layouts, Navigation & Themes

- [ ] **Step 1: Create theme store (Zustand) and provider supporting dark/light mode**
- [ ] **Step 2: Build a glassmorphic Sidebar layout with responsive navigation**
- [ ] **Step 3: Build standard reusable components (page wrapper, header, state badges, status icons)**

---

### Task 3: API Client & React Query Setup

- [ ] **Step 1: Create axios API client configured with auth header storage (JWT)**
- [ ] **Step 2: Declare fetch queries and mutations for Providers, Keys, Logs, Settings, Backups, and Stats**
- [ ] **Step 3: Setup React Query caching provider with periodic data polling for live dashboard metrics**

---

### Task 4: Page Implementations

- [ ] **Step 1: Implement Dashboard page with KPI widgets, charts (requests, latency), and live indicators**
- [ ] **Step 2: Implement Providers list, CRUD forms, and test connection action**
- [ ] **Step 3: Implement API Keys management page with status indicators, copy key, rotation triggers, and edit sliders**
- [ ] **Step 4: Implement Request Logs table with paginated filters**
- [ ] **Step 5: Implement Settings and Backup snaps CRUD triggers**

---

### Task 5: Testing & Integration

- [ ] **Step 1: Verify frontend builds successfully (`npm run build`)**
- [ ] **Step 2: Verify proxy settings connecting frontend to FastAPI backend**
- [ ] **Step 3: Update `phase.md` and commit all frontend code**
