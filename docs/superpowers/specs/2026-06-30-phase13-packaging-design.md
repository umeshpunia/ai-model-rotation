# Design Specification: Phase 13 Packaging & Distribution

## 1. Goal
Bundle the FastAPI backend service and compiled React frontend dashboard assets into a single self-contained Windows executable (`.exe`) using PyInstaller, and generate a professional Windows installer/uninstaller using Inno Setup.

## 2. Single-Executable Packaging
- **Tool**: PyInstaller.
- **Embedded Static Assets**:
  * The frontend static assets in `frontend/dist` will be bundled into the executable package using the `--add-data` flag.
  * The FastAPI application will detect if it is running in a PyInstaller frozen state (`sys.frozen`) and mount the static directory from the temporary path `sys._MEIPASS` using `StaticFiles`.
- **Command**:
  ```bash
  pyinstaller --noconsole --onefile --add-data "frontend/dist;frontend/dist" --icon=app.ico backend/run.py
  ```

## 3. Windows Installer (.exe)
- **Tool**: Inno Setup (`.iss` script template).
- **Installer Specifications**:
  * Standard wizard screens (License, Destination folder selection).
  * Creates Start Menu and Desktop shortcuts.
  * Installs the native uninstaller.
  * Configures optionally running the application immediately after installation completes.
