# Troubleshooting & FAQs

Diagnostic instructions for solving common execution situations inside AI Gateway Pro.

---

## 1. Socket Lock Conflicts (Single Instance Lock)

### Issue
The backend process fails to start, displaying the log:
`run.exit, reason=AI Gateway Pro is already running.`

### Solution
AI Gateway Pro binds to local port `49200` to guarantee a single running instance.
1. Check if another instance of the gateway is running in the background (or check the Windows System Tray).
2. If the port is bound by an orphaned process, locate and kill it:
   - **Windows (Command Prompt):**
     ```cmd
     netstat -ano | findstr 49200
     taskkill /PID <PID> /F
     ```

---

## 2. Decryption & Encryption Failures

### Issue
The API client returns status 500 when executing chat completions with the error message `encryption_error`.

### Solution
This occurs when the backend is unable to decrypt stored credentials (API keys) because the environment's `SECRET_KEY` has changed or does not match the key used during creation.
1. Check the `SECRET_KEY` variable inside your `.env` configuration file.
2. If you changed the secret key, you must recreate the API keys inside the dashboard (which encrypts them with the new secret key).

---

## 3. Database is Locked (SQLite)

### Issue
Database transactions return errors indicating `database is locked`.

### Solution
SQLite database files can lock during intensive parallel writes.
1. AI Gateway Pro uses Alembic migrations and database repository wrappers structured to close sessions cleanly.
2. If this occurs, verify that there are no background restore operations running. If needed, restart the application wrapper via the tray icon.
