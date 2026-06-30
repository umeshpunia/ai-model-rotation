# Installation & Setup Guide

This guide describes how to set up the local development environment for **AI Gateway Pro** and launch the application.

---

## Prerequisites

Before starting, ensure you have the following installed on your machine:

- **Python 3.11+**
- **Node.js 18+** (with npm)
- **MySQL 8.0+** (Optional, falls back to SQLite)

---

## 1. Backend Setup

### Step 1: Initialize Virtual Environment
Navigate to the `backend` folder and create a Python virtual environment:
```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Linux/macOS:**
  ```bash
  source .venv/bin/activate
  ```

### Step 2: Install Package Dependencies
Install the backend dependencies in editable development mode:
```bash
pip install -e ".[dev]"
```

### Step 3: Configure Environment Settings
Copy the template `.env.example` file to create your local `.env` configuration:
```bash
copy .env.example .env
```
Edit the `.env` file to customize host, port, database connections, and security secret keys.

### Step 4: Run Database Migrations
Initialize and upgrade your database schema to the latest version using Alembic:
```bash
alembic upgrade head
```

### Step 5: Start the Backend Server
- **Run as Desktop App (with System Tray wrapper):**
  ```bash
  python run.py
  ```
- **Run as standard FastAPI server (with hot reload enabled):**
  ```bash
  uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
  ```

---

## 2. Frontend Dashboard Setup

### Step 1: Install Package Dependencies
Navigate to the `frontend` folder and install Node packages:
```bash
cd ../frontend
npm install
```

### Step 2: Run Development Server
Start the local Vite development server:
```bash
npm run dev
```
The dashboard will open automatically in your browser at `http://localhost:5173`. All backend REST API queries starting with `/api/v1` and `/v1` are reverse-proxied to the FastAPI service at `http://127.0.0.1:8080` automatically.

### Step 3: Build Production Bundle
To bundle the frontend assets for single-executable packaging:
```bash
npm run build
```
Compiled static assets will be located in the `frontend/dist` directory.
