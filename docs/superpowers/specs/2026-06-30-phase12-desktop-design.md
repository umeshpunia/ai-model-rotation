# Design Specification: Phase 12 Desktop Integration

## 1. Goal
Integrate the AI Gateway Pro backend service and frontend dashboard as a headless Windows background application that minimizes to the Windows System Tray, supports auto-starting with Windows, guarantees a single instance lock, and exits safely.

## 2. System Tray Implementation
- **Library**: `pystray` for lightweight native system tray icon management.
- **Menu Options**:
  * **Open Dashboard**: Opens the local browser pointing to `http://localhost:8080`.
  * **Start/Stop Gateway**: Pauses or resumes API request processing.
  * **System Status**: Disabled informational menu item showing current state.
  * **Exit**: Fully terminates background jobs, database sessions, and closes the tray.
- **Icon Assets**: A 16x16 / 32x32 PNG file representing the logo icon.

## 3. Auto-Start & Single Instance Lock
- **Auto-Start**:
  * Write a Registry Key to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` with the path to the application executable.
- **Single Instance Lock**:
  * Acquire a local TCP socket lock on a dedicated lock port, or initialize a named system Mutex using Python's `win32event` to prevent launching multiple duplicate backend instances.
